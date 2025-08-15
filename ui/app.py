import os, gradio as gr, requests

API_URL = os.getenv("API_URL", "https://<ton-api>.onrender.com/process")
API_KEY = os.getenv("API_KEY", "")

def fill_quitus(source_pdf, quitus_pdf, doc_type):
    files = {
        "source_pdf": ("source.pdf", source_pdf, "application/pdf"),
        "quitus_pdf": ("quitus.pdf", quitus_pdf, "application/pdf"),
    }
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    r = requests.post(API_URL, files=files, data={"doc_type": doc_type}, headers=headers)
    if r.status_code != 200:
        return None, f"Erreur API: {r.status_code} - {r.text}"
    return (r.content, "quitus_filled.pdf"), "OK"

with gr.Blocks() as demo:
    gr.Markdown("## Remplir Quitus (Licence/Master)")
    with gr.Row():
        src = gr.File(label="PDF source (licence/master)", file_types=[".pdf"])
        q = gr.File(label="Modèle Quitus (PDF)", file_types=[".pdf"])
    doc_type = gr.Radio(["licence","master"], value="licence", label="Type de document")
    out_pdf = gr.File(label="Quitus rempli")
    status = gr.Textbox(label="Statut")
    btn = gr.Button("Remplir et télécharger")
    btn.click(fill_quitus, inputs=[src,q,doc_type], outputs=[out_pdf, status])

demo.launch()
