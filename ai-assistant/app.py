import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("DATABASE_URL", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
AI_MODEL = os.getenv("AI_MODEL", "openrouter/free")

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"

SYSTEM_PROMPT = """Ты — My AI, личный ИИ-ассистент пользователя.
Отвечай на русском, если пользователь не просит другой язык.
Будь практичным, коротким и конкретным. Помогай с проектами, кодом, задачами,
работой, финансами и планированием. Не выдумывай факты. Если данных не хватает,
скажи, что именно нужно уточнить. Учитывай сохранённую память пользователя.
"""

app = FastAPI(title="My AI Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def demo_answer(text: str) -> str:
    t = text.lower().strip()
    if "привет" in t or "здрав" in t:
        return "Привет! Я My AI. База данных уже подключена. Добавь AI_API_KEY, и я перейду из MVP-режима в настоящий AI-режим."
    return "Сообщение сохранено. Сейчас я работаю без AI_API_KEY. Подключи бесплатный OpenRouter API-ключ, чтобы включить настоящую модель."


def call_ai(messages: list[dict]) -> str:
    if not AI_API_KEY:
        return demo_answer(messages[-1]["content"])

    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1200,
    }
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        f"{AI_BASE_URL}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {AI_API_KEY}",
            "HTTP-Referer": "https://github.com/lolkes/MasterPro1",
            "X-Title": "My AI Assistant",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        answer = data["choices"][0]["message"]["content"]
        if isinstance(answer, list):
            answer = "".join(
                part.get("text", "") for part in answer if isinstance(part, dict)
            )
        return str(answer).strip()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:500]
        return f"AI API вернул ошибку ({exc.code}). Проверь API-ключ и настройки модели. {detail}"
    except (URLError, TimeoutError) as exc:
        return f"Не удалось связаться с AI API: {exc}"
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        return f"AI API вернул неожиданный ответ: {exc}"


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "ai_connected": bool(AI_API_KEY),
        "ai_model": AI_MODEL,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/conversations")
def conversations():
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id,title,created_at,updated_at FROM conversations ORDER BY updated_at DESC")
        return cur.fetchall()


@app.post("/api/conversations")
def new_conversation():
    with db() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO conversations DEFAULT VALUES RETURNING id,title,created_at,updated_at")
        row = cur.fetchone()
        conn.commit()
        return row


@app.get("/api/conversations/{conversation_id}/messages")
def messages(conversation_id: int):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id,role,content,created_at FROM messages WHERE conversation_id=%s ORDER BY id",
            (conversation_id,),
        )
        return cur.fetchall()


def build_ai_messages(conversation_id: int, user_text: str) -> list[dict]:
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT content FROM memories ORDER BY id DESC LIMIT 20")
        memories_rows = cur.fetchall()
        cur.execute(
            "SELECT role,content FROM messages WHERE conversation_id=%s ORDER BY id DESC LIMIT 20",
            (conversation_id,),
        )
        history = list(reversed(cur.fetchall()))

    memory_text = "\n".join(f"- {row['content']}" for row in memories_rows)
    system = SYSTEM_PROMPT
    if memory_text:
        system += f"\n\nПамять пользователя:\n{memory_text}"

    result = [{"role": "system", "content": system}]
    result.extend({"role": row["role"], "content": row["content"]} for row in history)
    result.append({"role": "user", "content": user_text})
    return result


@app.post("/api/chat")
def chat(payload: dict):
    conversation_id = int(payload["conversation_id"])
    text = str(payload.get("message", "")).strip()
    if not text:
        return {"error": "Пустое сообщение"}

    ai_messages = build_ai_messages(conversation_id, text)
    answer = call_ai(ai_messages)

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO messages (conversation_id,role,content) VALUES (%s,'user',%s)",
            (conversation_id, text),
        )
        cur.execute(
            "INSERT INTO messages (conversation_id,role,content) VALUES (%s,'assistant',%s)",
            (conversation_id, answer),
        )
        cur.execute(
            "UPDATE conversations SET updated_at=NOW(), title=CASE WHEN title='Новый чат' THEN LEFT(%s, 60) ELSE title END WHERE id=%s",
            (text, conversation_id),
        )
        conn.commit()
    return {"answer": answer, "ai_connected": bool(AI_API_KEY), "model": AI_MODEL}


@app.get("/api/memories")
def memories():
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id,content,created_at FROM memories ORDER BY id DESC")
        return cur.fetchall()


@app.post("/api/memories")
def add_memory(payload: dict):
    content = str(payload.get("content", "")).strip()
    if not content:
        return {"error": "Пустая память"}
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO memories(content) VALUES(%s) RETURNING id,content,created_at",
            (content,),
        )
        row = cur.fetchone()
        conn.commit()
        return row


@app.get("/api/tasks")
def tasks():
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id,title,completed,created_at,completed_at FROM tasks ORDER BY completed,id DESC")
        return cur.fetchall()


@app.post("/api/tasks")
def add_task(payload: dict):
    title = str(payload.get("title", "")).strip()
    if not title:
        return {"error": "Пустая задача"}
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO tasks(title) VALUES(%s) RETURNING id,title,completed,created_at,completed_at",
            (title,),
        )
        row = cur.fetchone()
        conn.commit()
        return row


@app.patch("/api/tasks/{task_id}")
def toggle_task(task_id: int):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE tasks SET completed=NOT completed, completed_at=CASE WHEN completed THEN NULL ELSE NOW() END WHERE id=%s RETURNING id,title,completed,created_at,completed_at",
            (task_id,),
        )
        row = cur.fetchone()
        conn.commit()
        return row
