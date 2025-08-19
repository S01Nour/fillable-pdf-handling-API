# API/app/build_ui.py
import os, re, tempfile, requests, gradio as gr
from urllib.parse import urlparse
from dotenv import load_dotenv

def build_demo(default_api_url: str = "/process"):
    load_dotenv()
    # --- config UI ---
    # couleur de fond (env > défaut)
    UI_BG_COLOR = os.getenv("UI_BG_COLOR", "#0f172a")  # change-la à ton goût
    # chemin logo (env > défaut local)
    LOGO_PATH = os.getenv("UI_LOGO_PATH") or str(Path(__file__).parent / "assets" / "logo.png")
    HAS_LOGO = os.path.exists(LOGO_PATH)

    # CSS minimal : fond + un peu de spacing
    css = f"""
    body, .gradio-container {{
        background: {UI_BG_COLOR} !important;
    }}
    #header {{
        display:flex; align-items:center; gap:12px; margin-bottom: 8px;
    }}
    #brand-title {{
        color: #e5e7eb; font-weight: 600; font-size: 1.125rem; /* slate-200 */
    }}
    #subtitle {{
        color: #94a3b8; font-size: 0.875rem; margin-top:-6px;  /* slate-400 */
    }}
    """
    API_URL = os.getenv("API_URL", default_api_url)   # peut être absolue ou relative
    API_KEY = os.getenv("API_KEY", "")

    # --- helpers URL absolue ---
    def _service_base(request: gr.Request) -> str:
        h = request.request.headers
        proto = h.get("x-forwarded-proto") or "https"
        host  = h.get("x-forwarded-host") or h.get("host") or "localhost"
        return f"{proto}://{host}"

    def _abs_url(path_or_url: str, request: gr.Request) -> str:
        u = (path_or_url or "").strip()
        if u.startswith("http://") or u.startswith("https://"):
            return u
        if not u.startswith("/"):
            u = "/" + u
        return _service_base(request) + u

    def _to_bytes(f):
        if f is None: return None
        if isinstance(f, (bytes, bytearray)): return bytes(f)
        path = getattr(f, "name", f)
        with open(path, "rb") as fh: return fh.read()

    # ------------ actions ------------
    def fill_quitus(source_pdf, doc_type, request: gr.Request):
        api = _abs_url(API_URL or "/process", request)   # <-- URL absolue
        payload = _to_bytes(source_pdf)
        if not payload:
            return None, "Fichier vide ou introuvable."

        files = {"source_pdf": ("source.pdf", payload, "application/pdf")}
        data  = {"doc_type": (doc_type or "licence").lower()}
        headers = {"X-API-Key": API_KEY} if API_KEY else {}

        try:
            r = requests.post(api, files=files, data=data, headers=headers, timeout=90)
        except Exception as e:
            return None, f"Erreur réseau: {e}"

        ctype = (r.headers.get("content-type") or "").split(";")[0].strip().lower()
        if r.status_code != 200 or ctype != "application/pdf":
            return None, f"Erreur API: {r.status_code} - {r.text}"

        # Nom de fichier renvoyé par l’API
        filename = f"quitus_{data['doc_type']}.pdf"
        cd = r.headers.get("content-disposition", "")
        m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, re.IGNORECASE)
        if m: filename = m.group(1)

        tmp_dir = tempfile.mkdtemp()
        out_path = os.path.join(tmp_dir, filename)
        with open(out_path, "wb") as f: f.write(r.content)
        return out_path, "OK"

    def download_excel(request: gr.Request):
        # base service depuis API_URL (si absolue) sinon depuis la requête
        if API_URL and (API_URL.startswith("http://") or API_URL.startswith("https://")):
            p = urlparse(API_URL)
            base = f"{p.scheme}://{p.netloc}"
        else:
            base = _service_base(request)
        url = base + "/download/excel"
        headers = {"X-API-Key": API_KEY} if API_KEY else {}

        try:
            r = requests.get(url, headers=headers, timeout=60)
        except Exception as e:
            return None, f"Erreur réseau: {e}"
        if r.status_code != 200:
            return None, f"Erreur API: {r.status_code} - {r.text}"

        filename = "students_data.xlsx"
        cd = r.headers.get("content-disposition", "")
        m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, re.IGNORECASE)
        if m: filename = m.group(1)

        tmp_dir = tempfile.mkdtemp()
        out_path = os.path.join(tmp_dir, filename)
        with open(out_path, "wb") as f: f.write(r.content)
        return out_path, "OK"

    # ------------ UI ------------
    with gr.Blocks(title="Quitus Filler", css=css) as demo:
        with gr.Row(elem_id="header"):
            if HAS_LOGO:
                gr.Image(value=LOGO_PATH, show_label=False, height=56)
            with gr.Column(scale=1):
                gr.Markdown('<div id="brand-title">Quitus Filler</div>')
                gr.Markdown('<div id="subtitle">Generate filled quitus & log data to Sheets</div>')

        with gr.Row():
            src   = gr.File(label="PDF source (licence/master)", file_types=[".pdf"])
            dtype = gr.Radio(["licence","master"], value="licence", label="Type de document")

        out_pdf   = gr.File(label="Quitus rempli")
        excel_dl  = gr.File(label="students_data.xlsx")
        status    = gr.Textbox(label="Statut", interactive=False)

        with gr.Row():
            gr.Button("Remplir et télécharger").click(
                fill_quitus, inputs=[src, dtype], outputs=[out_pdf, status]
            )
            gr.Button("Télécharger l’Excel").click(
                download_excel, inputs=[], outputs=[excel_dl, status]
            )
    return demo
