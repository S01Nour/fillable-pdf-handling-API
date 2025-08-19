# API reference

Base URL: same origin as the UI (prod UI is at `/app`, API is `/`).

## POST /process
Create a filled Quitus.

**Headers**
- `X-API-Key: <secret>` (required in production)

**Form data**
- `source_pdf` (file, required)
- `doc_type` (string, required: `licence` or `master`)

**Responses**
- `200 application/pdf` — bytes of the filled PDF (`quitus_<fullname>.pdf`)
- Errors: `400`, `401`, `423`, `500` (see Troubleshooting)

**Curl**
```bash
curl -X POST "https://pdf-quitus.onrender.com/process" \
  -H "X-API-Key: $API_KEY" \
  -F "doc_type=master" \
  -F "source_pdf=@/path/to/source.pdf;type=application/pdf" \
  -o quitus_filled.pdf
```

## GET /download/excel

Download the local Excel file (dev/local mode).

**Headers**

* `X-API-Key` (prod)

**Responses**

* `200 application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
* `404 No Excel yet`
## GET /health

Minimal status + template presence flags.




