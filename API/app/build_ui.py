import os, re, tempfile, requests, gradio as gr
from dotenv import load_dotenv

def build_demo(default_api_url: str = "/process"):
    load_dotenv()
    API_URL = os.getenv("API_URL", default_api_url)    # par défaut, même service
    API_KEY = os.getenv("API_KEY", "")

    def _to_bytes(f):
        if f is None: return None
        if isinstance(f, (bytes, bytearray)): return bytes(f)
        path = getattr(f, "name", f)
        with open(path, "rb") as fh: return fh.read()

    def fill_quitus(source_pdf, doc_type):
        if not API_URL: return None, "API_URL manquante."
        payload = _to_bytes(source_pdf)
        if not payload: return None, "Fichier vide ou introuvable."
        files = {"source_pdf": ("source.pdf", payload, "application/pdf")}
        data = {"doc_type": (doc_type or "licence").lower()}
        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        try:
            r = requests.post(API_URL, files=files, data=data, headers=headers, timeout=90)
        except Exception as e:
            return None, f"Erreur réseau: {e}"
        ctype = (r.headers.get("content-type") or "").split(";")[0].strip().lower()
        if r.status_code != 200 or ctype != "application/pdf":
            return None, f"Erreur API: {r.status_code} - {r.text}"
        # nom de fichier renvoyé par l’API
        filename = f"quitus_{data['doc_type']}.pdf"
        cd = r.headers.get("content-disposition", "")
        m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, re.IGNORECASE)
        if m: filename = m.group(1)
        tmp_dir = tempfile.mkdtemp()
        out_path = os.path.join(tmp_dir, filename)
        with open(out_path, "wb") as f: f.write(r.content)
        return out_path, "OK"

    def download_excel():
        base = re.sub(r"/process/?$", "", API_URL or "")
        url = f"{base}/download/excel"
        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        try:
            r = requests.get(url, headers=headers, timeout=60)
        except Exception as e:
            return None, f"Erreur réseau: {e}"
        if r.status_code != 200: return None, f"Erreur API: {r.status_code} - {r.text}"
        filename = "students_data.xlsx"
        cd = r.headers.get("content-disposition", "")
        m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, re.IGNORECASE)
        if m: filename = m.group(1)
        tmp_dir = tempfile.mkdtemp()
        out_path = os.path.join(tmp_dir, filename)
        with open(out_path, "wb") as f: f.write(r.content)
        return out_path, "OK"

    with gr.Blocks(title="Quitus Filler") as demo:
        gr.Markdown("## Remplir Quitus (Licence/Master)")
        with gr.Row():
            src = gr.File(label="PDF source (licence/master)", file_types=[".pdf"])
            dtype = gr.Radio(["licence", "master"], value="licence", label="Type de document")
        out_pdf = gr.File(label="Quitus rempli")
        excel_file = gr.File(label="students_data.xlsx")
        status = gr.Textbox(label="Statut", interactive=False)
        with gr.Row():
            gr.Button("Remplir et télécharger").click(fill_quitus, [src, dtype], [out_pdf, status])
            gr.Button("Télécharger l’Excel").click(download_excel, [], [excel_file, status])
    return demo
