# Deploy on Render from Android

1. Open https://render.com/ and sign in with GitHub.
2. New -> Web Service.
3. Select `lolkes/MasterPro1`.
4. Branch: `ai-assistant-v1`.
5. Root Directory: `ai-assistant`.
6. Build Command: `pip install -r requirements.txt`.
7. Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
8. Plan: Free.
9. Add environment variables:
   - `DATABASE_URL`: your Neon connection string.
   - `AI_API_KEY`: your OpenRouter API key.
   - `AI_BASE_URL`: `https://openrouter.ai/api/v1`
   - `AI_MODEL`: `openrouter/free`
10. Create Web Service.

The Neon database is already prepared. Never commit the real DATABASE_URL or AI_API_KEY to GitHub.
