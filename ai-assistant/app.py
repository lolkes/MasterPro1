import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("DATABASE_URL", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")

app = FastAPI(title="My AI Assistant")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def demo_answer(text: str) -> str:
    t = text.lower().strip()
    if "привет" in t or "здрав" in t:
        return "Привет! Я твой My AI. Сейчас я работаю в режиме MVP: сохраняю чаты, память и задачи. Подключим настоящую AI-модель следующим шагом."
    if "задач" in t:
        return "Я могу хранить задачи. Открой раздел «Задачи» и добавь первую."
    if "памят" in t:
        return "Память подключена к PostgreSQL. Важные заметки можно сохранять отдельно."
    return "Я получил сообщение и сохранил его. Сейчас включён безопасный MVP-режим без внешнего AI API."


@app.get("/")
def index():
    return FileResponse("web/index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "ai_connected": bool(AI_API_KEY), "time": datetime.utcnow().isoformat()}


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
        cur.execute("SELECT id,role,content,created_at FROM messages WHERE conversation_id=%s ORDER BY id", (conversation_id,))
        return cur.fetchall()


@app.post("/api/chat")
def chat(payload: dict):
    conversation_id = int(payload["conversation_id"])
    text = str(payload.get("message", "")).strip()
    if not text:
        return {"error": "Пустое сообщение"}

    answer = demo_answer(text)
    with db() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO messages (conversation_id,role,content) VALUES (%s,'user',%s)", (conversation_id, text))
        cur.execute("INSERT INTO messages (conversation_id,role,content) VALUES (%s,'assistant',%s)", (conversation_id, answer))
        cur.execute("UPDATE conversations SET updated_at=NOW() WHERE id=%s", (conversation_id,))
        conn.commit()
    return {"answer": answer, "ai_connected": bool(AI_API_KEY)}


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
        cur.execute("INSERT INTO memories(content) VALUES(%s) RETURNING id,content,created_at", (content,))
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
        cur.execute("INSERT INTO tasks(title) VALUES(%s) RETURNING id,title,completed,created_at,completed_at", (title,))
        row = cur.fetchone()
        conn.commit()
        return row


@app.patch("/api/tasks/{task_id}")
def toggle_task(task_id: int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("UPDATE tasks SET completed=NOT completed, completed_at=CASE WHEN completed THEN NULL ELSE NOW() END WHERE id=%s RETURNING id,title,completed,created_at,completed_at", (task_id,))
        row = cur.fetchone()
        conn.commit()
        return row
