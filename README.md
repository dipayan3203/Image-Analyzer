# Gemini Image Analyzer Microservice

Purpose: Python microservice providing an interface for a Gemini multimodal model.

Quick start

1. Install deps:

```bash
python -m pip install -r requirements.txt
```

2. Run locally:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Environment

- `GEMINI_API_KEY`: API key for Gemini service (required unless `GEMINI_MOCK=true`).
- `GEMINI_MOCK=true`: Enable deterministic mock responses for testing.

Endpoint: `POST /analyze`

Supports multipart file upload, or JSON body with `image` (base64 data URI or local path), `analysis_type`, and `metadata`.

Response: Structured JSON matching the schema in `app/schemas.py`.
