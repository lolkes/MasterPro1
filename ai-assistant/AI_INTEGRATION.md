# AI integration

The assistant is prepared for an OpenAI-compatible provider.

Environment variables:

```text
AI_API_KEY=your-key
AI_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL=openrouter/free
```

The app sends recent conversation history and saved memories to `/chat/completions` and stores the response in Neon.

`openrouter/free` is a free-model router. Availability and limits can change, so check the provider dashboard before production use.
