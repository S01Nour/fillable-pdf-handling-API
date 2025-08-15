import io
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import openpyxl
from .settings import settings

app = FastAPI(title="Quitus Filler API")
DATA_DIR = Path("./data"); DATA_DIR.mkdir(exist_ok=True)
EXCEL_PATH = DATA_DIR / "students_data.xlsx"

def require_api_key(x_api_key: str | None = Header(default=None)):
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

def get_fields_safe(reader: PdfReader):
    try:
        return reader.get_fields() or {}
    except Exception:
        return {}

def val(fields, name):
    v = fields.get(name, {})
    return (v.get("/V", "") or "").strip()

def ensure_excel():
    if not EXCEL_PATH.exists():
        wb = openpyxl.Workbook()
        wb.create_sheet("Licence", 0); wb["Licence"].append(["student_nom","student_prenom","cin","filiere"])
        wb.create_sheet("Master", 1); wb["Master"].append(["student_nom","student_prenom","cin","filiere"])
        if "Sheet" in wb.sheetnames: del wb["Sheet"]
        wb.save(EXCEL_PATH)

def append_row(doc_type, row):
    ensure_excel()
    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb["Licence"] if doc_type.lower()=="licence" else wb["Master"]
    ws.append(row)
    wb.save(EXCEL_PATH)

def fill_acroform(base_reader: PdfReader, mapping: dict) -> bytes:
    writer = PdfWriter()
    writer.clone_document_from_reader(base_reader)
    root = writer._root_object
    if "/AcroForm" in root:
        acro = root["/AcroForm"]
        acro[NameObject("/NeedAppearances")] = BooleanObject(True)
    writer.update_page_form_field_values(writer.pages[0], mapping)
    buf = io.BytesIO(); writer.write(buf); buf.seek(0)
    return buf.read()

def overlay_text(base_reader: PdfReader, lines: list[tuple[str, float, float]]) -> bytes:
    writer = PdfWriter()
    for p in base_reader.pages: writer.add_page(p)
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4); c.setFont("Helvetica", 12)
    for txt, x, y in lines: c.drawString(x, y, txt)
    c.save(); packet.seek(0)
    overlay_pdf = PdfReader(packet)
    writer.pages[0].merge_page(overlay_pdf.pages[0])
    out = io.BytesIO(); writer.write(out); out.seek(0)
    return out.read()

@app.get("/")
def root():
    return {"status":"ok","endpoints":["POST /process"]}

@app.post("/process")
async def process_quitus(
    source_pdf: UploadFile = File(...),
    quitus_pdf: UploadFile = File(...),
    doc_type: str = Form(...),          # "licence" | "master"
    x_api_key: str | None = Header(default=None)
):
    require_api_key(x_api_key)

    src_reader = PdfReader(io.BytesIO(await source_pdf.read()), strict=False)
    sf = get_fields_safe(src_reader)
    nom, prenom, cin = val(sf,"student_nom"), val(sf,"student_prenom"), val(sf,"cin")
    filiere_lic, filiere_master = val(sf,"filiere_lic"), val(sf,"filiere_master")
    full_name = f"{nom} {prenom}".strip()
    filiere = filiere_lic if doc_type.lower()=="licence" else (filiere_master or filiere_lic)

    append_row(doc_type, [nom, prenom, cin, filiere])

    q_reader = PdfReader(io.BytesIO(await quitus_pdf.read()), strict=False)
    mapping = {"student_nom": full_name, "cin": cin, "filiere_lic": filiere, "filiere_master": filiere}
    fields = get_fields_safe(q_reader)

    if fields:
        pdf_out = fill_acroform(q_reader, mapping)
    else:
        # ajuste x/y ici selon ton modèle
        lines = [(full_name,120,690), (cin,160,665), (filiere,160,640)]
        pdf_out = overlay_text(q_reader, lines)

    fn = f"quitus_filled_{doc_type.lower()}.pdf"
    return StreamingResponse(io.BytesIO(pdf_out), media_type="application/pdf",
                             headers={"Content-Disposition": f'attachment; filename="{fn}"'})
