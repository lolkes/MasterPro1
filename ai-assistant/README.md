# My AI Assistant v1

Mobile-first personal assistant MVP.

## Included
- Chat history
- PostgreSQL persistence via Neon
- Tasks
- Memory notes
- AI-ready backend
- Demo mode until an AI provider key is configured

## Run
```bash
pip install -r requirements.txt
export DATABASE_URL='...'
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open `/` in a browser.

## Environment
`DATABASE_URL` — Neon PostgreSQL connection string.
`AI_API_KEY` — reserved for the real AI provider integration in the next version.
