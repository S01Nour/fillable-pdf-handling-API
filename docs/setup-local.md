# Local setup

## 1) Requirements
- Python 3.10
- Git

## 2) Install
```bash
cd API
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
## 3) Configure

Copy .env.example to .env (root of repo) and adjust if needed:
```
EXCEL_MODE=local
```

Make sure the template exists:
```
API/app/templates/quitus.pdf
```
## 4) Run
```
uvicorn app.main:app --reload
```

UI: http://127.0.0.1:8000/app

Docs: http://127.0.0.1:8000/docs

## 5) Test (curl)
```
curl -X POST "http://127.0.0.1:8000/process" \
  -F "doc_type=licence" \
  -F "source_pdf=@/path/to/source.pdf;type=application/pdf" \
  -o quitus_filled.pdf
```
