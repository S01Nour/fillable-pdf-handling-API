
# 📄 Admission – Reception des FI (Quitus Filler)  

[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Gradio](https://img.shields.io/badge/Gradio-3.x-orange?logo=gradio)](https://gradio.app)
[![Deploy on Render](https://img.shields.io/badge/Deploy-Render-000000?logo=render)](https://render.com)

Automated PDF processing system that generates filled **Quitus** documents (Licence/Master) and logs all extracted student data.

🔗 **Live Demo**: [https://pdf-quitus.onrender.com/app/](https://pdf-quitus.onrender.com/app/)

---

## ✨ Features

✔ **PDF Processing**  
- Reads form fields from uploaded PDFs (`student_nom`, `cin`, `filiere_lic`, etc.)  
- Generates filled `quitus.pdf` with student data  
- Special handling for Master students (`filiere_master` → `filiere_lic`)  

✔ **Data Logging**  
- **Production**: Syncs to Google Sheets  
- **Development**: Local Excel file (`data/students_data.xlsx`)  

✔ **Modern Stack**  
- FastAPI backend + Gradio UI  
- Zero CORS issues (UI mounted at `/app`)  

---

## 🚀 Quick Start

```bash
cd API
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start dev server (EXCEL_MODE=local)
uvicorn app.main:app --reload
```

**Access:**  
- UI: [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)  
- API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  

### 🔧 Configuration (`.env`)
```ini
# Required
API_KEY=your_secret_key

# Data storage
EXCEL_MODE=local           # local | gsheets
GCP_SA_JSON=               # Required for gsheets
GSHEET_ID=                 # OR use GSHEET_NAME
GSHEET_NAME=quitus-students

# UI Customization
UI_BG_COLOR=#F8FAFC
UI_ACCENT=#0F172A
UI_LOGO_PATH=API/app/assets/logo.png
```

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/process` | POST | Generate filled PDF |
| `/download/excel` | GET | Download Excel data |
| `/health` | GET | System status |

📚 Full API Documentation: [docs/api.md](docs/api.md)

---

## 🛠 Production Deployment (Render)

**Procfile:**
```yaml
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**Required Env Vars:**
- `API_KEY`
- `EXCEL_MODE=gsheets` 
- Google Sheets credentials (`GCP_SA_JSON` + `GSHEET_ID`/`GSHEET_NAME`)

📘 Guide: [deploy-render.md](docs/deploy-render.md) | [google-sheets.md](docs/google-sheets.md)

---

## 🚨 Troubleshooting

| Code | Issue | Solution |
|------|-------|----------|
| 400 | Invalid PDF/doc_type | Check PDF validity and doc_type parameter |
| 401 | Unauthorized | Verify `X-API-Key` header |
| 404 | Missing Excel | Run `/process` first in local mode |
| 500 | Template error | Ensure `quitus.pdf` exists in templates |

🔍 Detailed troubleshooting: [troubleshooting.md](docs/troubleshooting.md)

---

## 📂 Repository Structure

```
API/
├── app/               # Application code
│   ├── templates/     # PDF templates
│   └── assets/        # UI resources
├── data/              # Local Excel storage
docs/                  # Documentation
├── api.md             # API specifications
└── deploy-render.md   # Deployment guide
```

---

## 📜 License & Contribution

- **License**: MIT
- **Contributions**: PRs welcome!
- **Contact**: [smiainour01@gmail.com](mailto:smiainour01@gmail.com)
