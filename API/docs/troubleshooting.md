# `docs/troubleshooting.md`
```markdown
# Troubleshooting

## 400 – Bad Request
- **Missing `doc_type`** → send `licence` or `master`
- **Invalid/empty PDF** → make sure the file starts with `%PDF` and isn’t corrupted

## 401 – Invalid API key
- Add header `X-API-Key: <secret>`; set it as an env var on Render

## 404 – No Excel yet
- Only in local mode (`EXCEL_MODE=local`): call `/process` once to create `data/students_data.xlsx`

## 423 – Excel file locked
- Windows locks files while open → close the `.xlsx` and retry

## 500 – Template not found
- Ensure `API/app/templates/quitus.pdf` exists in production
- Check service logs on Render

## UI loads but buttons fail
- If the UI can’t reach the API, ensure:
  - You’re using the **same origin** (UI at `/app`, API at `/`)
  - No proxy/CDN is blocking POST uploads
