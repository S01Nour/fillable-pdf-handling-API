# Google Sheets setup

## 1) Service Account
- In Google Cloud Console:
  - Create a **Service Account**
  - Enable **Google Sheets API** (and **Drive API** if you want the app to create sheets)
  - Create a **JSON key** and download it

## 2) Share the spreadsheet
- Create/open your Google Spreadsheet
- Share with the Service Account email (Editor role)

## 3) Configure env vars (Render)
```
EXCEL_MODE=gsheets
GCP_SA_JSON=<paste full JSON content>
GSHEET_ID=<spreadsheet id> # recommended
GSHEET_NAME=quitus-students # optional alternative
GSHEET_CREATE=0 # 1 to allow creation through Drive API
```


## 4) Tabs
The app writes in:
- `Licence`
- `Master`

Headers are dynamic: if a new field appears in the source PDF, a new column is added automatically.
