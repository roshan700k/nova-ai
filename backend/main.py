import os
import threading
import time

from fastapi import Request

from pydantic import BaseModel, Field

from database.database import (
    create_table,
    create_conversation,
    list_conversations,
    get_conversation,
    get_messages,
    add_message,
    set_conversation_title,
    set_conversation_pinned,
    delete_conversation,
    delete_all_conversations,
    get_user_settings,
    set_user_settings,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from brain.brain import AstraBrain
from api.auth import router as auth_router, current_user
from api.voice import router as voice_router
from api.actions import router as actions_router
from api.admin import router as admin_router
from api.monitor import router as monitor_router
from api.tasks import router as tasks_router
from api.research import router as research_router
from api.automation import router as automation_router
from api.agent import router as agent_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(voice_router)
app.include_router(actions_router)
app.include_router(admin_router)
app.include_router(monitor_router)
app.include_router(tasks_router)
app.include_router(research_router)
app.include_router(automation_router)
app.include_router(agent_router)

create_table()
brain = AstraBrain()

_extra_origins = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://10.82.230.101:5173",
        "http://10.82.230.101:8000",
        "http://192.168.1.100:5173",
        "http://192.168.1.100:8000",
    ] + _extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(default="", max_length=4000)
    conversation_id: int | None = None


@app.get("/")
def home():
    return {
        "message": "NOVA AI Backend Running"
    }


@app.post("/chat")
def chat(data: ChatRequest, request: Request):

    user = current_user(request)
    user_id = user["id"] if user else None

    # Resolve or create conversation
    conv_id = data.conversation_id
    conv = get_conversation(conv_id, user_id) if conv_id else None
    if conv_id and conv is None:
        conv_id = None  # stale/foreign id -> start fresh
    if conv_id is None:
        conv_id = create_conversation(user_id)

    # Research command: "research X" / "analyse X" / "what's happening"
    low = data.message.lower().strip()
    for prefix in ("research ", "analyse ", "analyze ", "research on ", "what's happening"):
        if low.startswith(prefix):
            from api.research import do_research
            add_message(conv_id, "user", data.message)
            set_conversation_title(conv_id, data.message[:40])
            q = data.message[len(prefix):].strip() or data.message
            res = do_research(q, llm=brain.llm)
            lines = [f"**Research: {res['heading']}**\n", res["answer"], ""]
            if res["sources"]:
                lines.append("Sources:")
                for s in res["sources"][:4]:
                    lines.append(f"- [{s['title']}]({s['url']})")
            reply = "\n".join(lines)
            add_message(conv_id, "nova", reply)
            return {
                "reply": reply,
                "user": user["name"] if user else None,
                "conversation_id": conv_id,
            }

    # PC agent command: "pc open notepad", "my pc youtube lofi", "computer files"
    if low.startswith(("pc ", "my pc ", "computer ", "device ", "laptop ")):
        from api.agent import parse_pc_command
        from database.database import get_device, enqueue_command
        action, args = parse_pc_command(data.message)
        add_message(conv_id, "user", data.message)
        set_conversation_title(conv_id, data.message[:40])
        if user_id is None:
            reply = "PC agent needs you to sign in first — your commands run on your own device."
        elif get_device(user_id) is None:
            reply = ("No PC is linked yet. Open the ＋ menu → 'PC Agent' to get your "
                     "agent token, then run agent/nova_agent.py on your computer.")
        elif action == "unknown":
            reply = ("I can do this on your PC: **open &lt;app&gt;**, **open &lt;website&gt;**, "
                     "**youtube &lt;query&gt;**, **google &lt;query&gt;**, "
                     "**files in &lt;downloads/documents/desktop&gt;**, **read &lt;file&gt;**, "
                     "**status**. Try: \"pc open notepad\"")
        else:
            cid = enqueue_command(user_id, action, args)
            reply = (f"📟 Sent to your PC — I'll report back as soon as it's done.\n"
                     f"_(command #{cid}: {action})_")
        add_message(conv_id, "nova", reply)
        return {
            "reply": reply,
            "user": user["name"] if user else None,
            "conversation_id": conv_id,
        }

    # Automation command: "automate X" / "step by step X" / "plan and do X"
    for prefix in ("automate ", "automation ", "step by step ", "plan and do ", "run plan "):
        if low.startswith(prefix):
            from api.automation import run_automation, format_report
            goal = data.message[len(prefix):].strip() or data.message
            add_message(conv_id, "user", data.message)
            set_conversation_title(conv_id, data.message[:40])
            res = run_automation(goal, user_id, brain.llm)
            reply = format_report(res)
            add_message(conv_id, "nova", reply)
            return {
                "reply": reply,
                "user": user["name"] if user else None,
                "conversation_id": conv_id,
            }

    # Email draft: "email boss about leave", "write email to team"
    from api.email import looks_like_email_command, draft_email
    if looks_like_email_command(data.message):
        add_message(conv_id, "user", data.message)
        set_conversation_title(conv_id, data.message[:40])
        ns = f"u{user_id}" if user_id else None
        mems = brain.memory.all(ns) if ns else {
            k: v for k, v in brain.memory.all(None).items() if ":" not in k
        }
        reply = draft_email(data.message, brain.llm, mems) or (
            "I couldn't draft that right now — try rephrasing, e.g. "
            "\"email to boss about tomorrow's leave\"."
        )
        add_message(conv_id, "nova", reply)
        return {
            "reply": reply,
            "user": user["name"] if user else None,
            "conversation_id": conv_id,
        }

    add_message(conv_id, "user", data.message)
    set_conversation_title(conv_id, data.message[:40])  # only applies while title is 'New chat'

    reply = brain.think(data.message, user_id=user_id)
    add_message(conv_id, "nova", reply)

    return {
        "reply": reply,
        "user": user["name"] if user else None,
        "conversation_id": conv_id,
    }


# ---------- chat history ----------

@app.get("/chats")
def chats(request: Request):
    user = current_user(request)
    user_id = user["id"] if user else None
    pinned = [c for c in list_conversations(user_id) if c["pinned"]]
    recents = [c for c in list_conversations(user_id) if not c["pinned"]]
    return {"pinned": pinned, "recents": recents}


@app.get("/chats/{conv_id}/messages")
def chat_messages(conv_id: int, request: Request):
    user = current_user(request)
    user_id = user["id"] if user else None
    if get_conversation(conv_id, user_id) is None:
        return {"error": "not found"}
    return {"messages": get_messages(conv_id)}


class PinRequest(BaseModel):
    pinned: bool = False


@app.put("/chats/{conv_id}/pin")
def pin_chat(conv_id: int, data: PinRequest, request: Request):
    user = current_user(request)
    user_id = user["id"] if user else None
    if get_conversation(conv_id, user_id) is None:
        return {"error": "not found"}
    set_conversation_pinned(conv_id, user_id, data.pinned)
    return {"ok": True}


@app.delete("/chats/{conv_id}")
def remove_chat(conv_id: int, request: Request):
    user = current_user(request)
    user_id = user["id"] if user else None
    delete_conversation(conv_id, user_id)
    return {"ok": True}


@app.delete("/chats")
def clear_all_chats(request: Request):
    user = current_user(request)
    user_id = user["id"] if user else None
    delete_all_conversations(user_id)
    return {"ok": True}


# ---------- user settings & data ----------

@app.get("/settings")
def get_settings(request: Request):
    user = current_user(request)
    if not user:
        return {"settings": {}}
    return {"settings": get_user_settings(user["id"])}


class SettingsRequest(BaseModel):
    settings: dict = Field(default_factory=dict)


@app.put("/settings")
def update_settings(data: SettingsRequest, request: Request):
    user = current_user(request)
    if not user:
        return {"error": "login required"}
    set_user_settings(user["id"], data.settings)
    return {"ok": True}


@app.delete("/memory")
def clear_memory(request: Request):
    user = current_user(request)
    user_id = user["id"] if user else None
    ns = f"u{user_id}" if user_id else None
    brain.memory.clear_ns(ns)
    return {"ok": True, "cleared": ns or "public"}


@app.get("/notifications")
def notifications(request: Request):
    """Proactive messages NOVA starts on her own (check-ins, self-issues, agent results)."""
    msgs = list(brain.outbox)
    brain.outbox.clear()
    user = current_user(request)
    if user:
        try:
            from api.agent import agent_notifications
            msgs += agent_notifications(user["id"])
        except Exception:
            pass
    return {"messages": msgs}


@app.get("/self-check")
def self_check():
    """On-demand internal health report."""
    return {"issues": brain.self_check.run()}


@app.get("/system-status")
def system_status():
    import os
    import time as _t
    mem_file = os.environ.get("MEMORY_FILE_PATH", "memory.json")
    db_file = os.environ.get("ASTRA_DB_PATH", "astra.db")
    mem_size = os.path.getsize(mem_file) if os.path.exists(mem_file) else 0
    db_size = os.path.getsize(db_file) if os.path.exists(db_file) else 0
    return {
        "status": "online",
        "version": "0.2.0",
        "llm_provider": brain.llm.provider,
        "llm_model": os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite") if brain.llm.provider == "gemini" else (os.environ.get("OLLAMA_MODEL", "qwen2.5:7b") if brain.llm.provider == "ollama" else None),
        "memory_entries": len(brain.memory.data),
        "memory_size_kb": round(mem_size / 1024, 1),
        "db_size_kb": round(db_size / 1024, 1),
        "uptime_seconds": int(_t.time() - brain.started_at),
        "modules": sorted(brain.loader.all().keys()),
        "issues": brain.self_check.run(),
        "dev_auth": os.environ.get("DEV_AUTH", "true").lower() == "true",
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
