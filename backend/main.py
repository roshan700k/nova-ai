import threading
import time

from pydantic import BaseModel, Field

from database.database import create_table
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from brain.brain import AstraBrain

app = FastAPI()

create_table()
brain = AstraBrain()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
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
        "message": "ASTRA AI Backend Running"
    }


@app.post("/chat")
def chat(data: ChatRequest):

    reply = brain.think(data.message)

    return {
        "reply": reply
    }


@app.get("/notifications")
def notifications():
    """Proactive messages ASTRA starts on her own (check-ins, self-issues)."""
    msgs = list(brain.outbox)
    brain.outbox.clear()
    return {"messages": msgs}


@app.get("/self-check")
def self_check():
    """On-demand internal health report."""
    return {"issues": brain.self_check.run()}


def _proactive_loop():
    while True:
        time.sleep(60)
        try:
            for issue in brain.self_check.new_issues():
                brain.outbox.append(f"[ASTRA-ALERT] {issue}")
            if brain.companion.checkin_due():
                brain.outbox.append(brain.companion.checkin_message())
        except Exception:
            pass


threading.Thread(target=_proactive_loop, daemon=True).start()
