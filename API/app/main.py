import io
from typing import Optional, Dict, Any, List
from pathlib import Path
import sys, logging, re, unicodedata
from fastapi.responses import FileResponse
from pypdf.errors import PdfReadError, PdfStreamError
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import openpyxl

from .settings import settings

# --- logging global (lisible sur Render aussi) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("quitus-api")

# --- helper nom de fichier propre (pour quitus_fullname.pdf) ---
def safe_filename(full_name: str, fallback: str = "document") -> str:
    s = unicodedata.normalize("NFKD", (full_name or "")).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s or fallback

# --------------------------- App & chemins ---------------------------
app = FastAPI(title="Quitus Filler API")

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"          # un seul modèle: quitus.pdf
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
EXCEL_PATH = DATA_DIR / "students_data.xlsx"

# ------------------------------ Sécurité ----------------------------
def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# --------------------------- Helpers PDF ----------------------------
def get_fields(reader: PdfReader) -> Dict[str, Dict[str, Any]]:
    try:
        return reader.get_fields() or {}
    except Exception:
        return {}

def as_text(v: Any) -> str:
    if isinstance(v, dict):
        v = v.get("/V", "")
    return "" if v is None else str(v).strip()

def extract_all_values(fields: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    return {name: as_text(obj) for name, obj in fields.items()}

def fill_acroform(base_reader: PdfReader, mapping: Dict[str, str]) -> bytes:
    writer = PdfWriter()
    writer.clone_document_from_reader(base_reader)
    if "/AcroForm" in writer._root_object:
        writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)
    writer.update_page_form_field_values(writer.pages[0], mapping)
    buf = io.BytesIO(); writer.write(buf); buf.seek(0)
    return buf.read()

def overlay_text(base_reader: PdfReader, lines: List[tuple[str, float, float]]) -> bytes:
    writer = PdfWriter()
    for p in base_reader.pages:
        writer.add_page(p)
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4); c.setFont("Helvetica", 12)
    for txt, x, y in lines: c.drawString(x, y, txt)
    c.save(); packet.seek(0)
    overlay_pdf = PdfReader(packet)
    writer.pages[0].merge_page(overlay_pdf.pages[0])
    out = io.BytesIO(); writer.write(out); out.seek(0)
    return out.read()

def get_template_path() -> Path:
    path = TEMPLATES_DIR / "quitus.pdf"   # <— modèle unique
    if not path.exists():
        raise HTTPException(status_code=500, detail="Template not found: quitus.pdf")
    return path

# --------------------------- Helpers Excel --------------------------
def ensure_sheet(wb: openpyxl.Workbook, name: str):
    return wb[name] if name in wb.sheetnames else wb.create_sheet(title=name)

def read_header(ws) -> List[str]:
    return [(c.value or "").strip() for c in ws[1]] if ws.max_row >= 1 else []

def write_header(ws, header: List[str]) -> None:
    if ws.max_row == 0:
        ws.append(header)
    else:
        for i, h in enumerate(header, start=1):
            ws.cell(row=1, column=i).value = h

def append_row_all_fields(doc_type: str, values: Dict[str, str]) -> None:
    """Log TOUS les champs du PDF source. Feuille selon doc_type."""
    sheet = "Licence" if doc_type == "licence" else "Master"
    wb = openpyxl.load_workbook(EXCEL_PATH) if EXCEL_PATH.exists() else openpyxl.Workbook()
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]
    ws = ensure_sheet(wb, sheet)
    header = read_header(ws)
    # ajoute les nouvelles colonnes à la volée
    for k in values.keys():
        if k not in header:
            header.append(k)
    write_header(ws, header)
    ws.append([values.get(col, "") for col in header])
    wb.save(EXCEL_PATH)

# ------------------------------- Routes -----------------------------
@app.get("/")
def root():
    return {"status": "ok", "endpoints": ["POST /process"]}

@app.post("/process")
async def process_quitus(
    source_pdf: UploadFile = File(...),
    doc_type: Optional[str] = Form(None),     # accept form
    doc_type_q: Optional[str] = Query(None),  # ou query
    x_api_key: Optional[str] = Header(default=None),
):
    require_api_key(x_api_key)
    dt = (doc_type or doc_type_q or "licence").lower()
    if dt not in {"licence", "master"}:
        raise HTTPException(status_code=400, detail="doc_type must be 'licence' or 'master'")

    # 1) lire les octets UNE fois + valider (%PDF)
    data = await source_pdf.read()
    if not data or len(data) < 5 or not data.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid or empty PDF (missing %PDF header)")
    try:
        src_reader = PdfReader(io.BytesIO(data), strict=False)
    except (PdfReadError, PdfStreamError) as e:
        raise HTTPException(status_code=400, detail=f"Unreadable PDF: {e}")

    # 2) extraire champs
    all_values = extract_all_values(get_fields(src_reader))
    nom = all_values.get("student_nom", "")
    prenom = all_values.get("student_prenom", "")
    cin = all_values.get("cin", "")
    filiere_lic = all_values.get("filiere_lic", "")
    filiere_master = all_values.get("filiere_master", "")
    full_name = f"{nom} {prenom}".strip()
    filiere_finale = filiere_lic if dt == "licence" else (filiere_master or filiere_lic)

    # 3) Excel (TOUS les champs) + gestion fichier verrouillé
    try:
        append_row_all_fields(dt, all_values)
    except PermissionError:
        raise HTTPException(status_code=423, detail="Close Excel then retry (students_data.xlsx is locked)")

    # 4) remplir modèle
    with open(get_template_path(), "rb") as fh:
        q_reader = PdfReader(io.BytesIO(fh.read()), strict=False)
    mapping = {"student_nom": full_name, "cin": cin, "filiere_lic": filiere_finale}
    q_fields = get_fields(q_reader)
    if q_fields:
        pdf_out = fill_acroform(q_reader, mapping)
    else:
        lines = [(full_name, 120, 690), (cin, 160, 665), (filiere_finale, 160, 640)]
        pdf_out = overlay_text(q_reader, lines)

    # 5) nommage quitus_<fullname>.pdf
    slug = safe_filename(full_name, fallback=dt)
    filename = f"quitus_{slug}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_out),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/health")
def health():
    return {
        "ok": True,
        "excel_exists": EXCEL_PATH.exists(),
        "excel_path": str(EXCEL_PATH),
        "template_exists": (TEMPLATES_DIR / "quitus.pdf").exists(),
    }

@app.get("/download/excel")
def download_excel(x_api_key: Optional[str] = Header(default=None)):
    require_api_key(x_api_key)
    if not EXCEL_PATH.exists():
        raise HTTPException(status_code=404, detail="No Excel yet")
    return FileResponse(
        EXCEL_PATH,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="students_data.xlsx",
    )
