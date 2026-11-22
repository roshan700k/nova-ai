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

@app.get("/")
def home():
    return {
        "message": "ASTRA AI Backend Running"
    }

@app.post("/chat")
def chat(data: dict):

    message = data.get("message", "")

    reply = brain.think(message)

    return {
        "reply": reply
    }