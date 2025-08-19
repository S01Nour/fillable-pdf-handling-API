


# Deploy on Render

## 1) Create a new Web Service
- Repo root: use the `API/` folder as the working dir (Render detects `requirements.txt`).
- Start command (Procfile):


web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}


## 2) Environment variables
Required in production:

```
API_KEY=<your-secret>
EXCEL_MODE=gsheets
GCP_SA_JSON=<full service account JSON as single value>
GSHEET_ID=<spreadsheet id> # or GSHEET_NAME
```
### optional
```
GSHEET_CREATE=1
UI_BG_COLOR=#F8FAFC
UI_ACCENT=#0F172A
UI_LOGO_PATH=API/app/assets/logo.png
```

## 3) First visit
- UI is served at `/app` → `https://<service>.onrender.com/app/`
- API stays under the same origin (`/process`, `/health`, `/download/excel`)