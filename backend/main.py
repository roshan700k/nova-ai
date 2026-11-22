import threading
import time

from fastapi import Request

from pydantic import BaseModel, Field

from database.database import create_table
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from brain.brain import AstraBrain
from api.auth import router as auth_router, current_user
from api.voice import router as voice_router
from api.actions import router as actions_router
from api.admin import router as admin_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(voice_router)
app.include_router(actions_router)
app.include_router(admin_router)

create_table()
brain = AstraBrain()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://10.82.230.101:5173",
        "http://10.82.230.101:8000",
        "http://192.168.1.100:5173",
        "http://192.168.1.100:8000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(default="", max_length=4000)


@app.get("/")
def home():
    return {
        "message": "NOVA AI Backend Running"
    }


@app.post("/chat")
def chat(data: ChatRequest, request: Request):

    user = current_user(request)
    user_id = user["id"] if user else None

    reply = brain.think(data.message, user_id=user_id)

    return {
        "reply": reply,
        "user": user["name"] if user else None,
    }


@app.get("/notifications")
def notifications():
    """Proactive messages NOVA starts on her own (check-ins, self-issues)."""
    msgs = list(brain.outbox)
    brain.outbox.clear()
    return {"messages": msgs}


@app.get("/self-check")
def self_check():
    """On-demand internal health report."""
    return {"issues": brain.self_check.run()}


@app.get("/system-status")
def system_status():
    import os
    import time as _t
    mem_file = "memory.json"
    mem_size = os.path.getsize(mem_file) if os.path.exists(mem_file) else 0
    return {
        "status": "online",
        "version": "0.2.0",
        "llm_provider": brain.llm.provider,
        "llm_model": os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite") if brain.llm.provider == "gemini" else (os.environ.get("OLLAMA_MODEL", "qwen2.5:7b") if brain.llm.provider == "ollama" else None),
        "memory_entries": len(brain.memory.data),
        "memory_size_kb": round(mem_size / 1024, 1),
        "uptime_seconds": int(_t.time() - brain.started_at),
        "modules": sorted(brain.loader.all().keys()),
        "issues": brain.self_check.run(),
    }


@app.get("/activity")
def activity():
    import time as _t
    now = _t.time()
    items = []
    for a in reversed(brain.activity[-30:]):
        ago = int(now - a["time"])
        ago_str = f"{ago}s ago" if ago < 60 else f"{ago // 60}m ago" if ago < 3600 else f"{ago // 3600}h ago"
        items.append({"kind": a["kind"], "text": a["text"], "ago": ago_str})
    return {"activity": items}


@app.get("/memory")
def memory_list(request: Request):
    user = current_user(request)
    ns = f"u{user['id']}" if user else None
    mems = brain.memory.all(ns)
    if ns is None:
        mems = {k: v for k, v in mems.items() if ":" not in k}
    return {"memories": mems, "user": user["name"] if user else None}


def _proactive_loop():
    while True:
        time.sleep(60)
        try:
            for issue in brain.self_check.new_issues():
                brain.outbox.append(f"[NOVA-ALERT] {issue}")
            if brain.companion.checkin_due():
                brain.outbox.append(brain.companion.checkin_message())
        except Exception:
            pass


threading.Thread(target=_proactive_loop, daemon=True).start()
