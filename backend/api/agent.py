"""Local Agent API — lets a user's own PC execute permitted commands.

Flow: user registers a device token -> local agent script polls /agent/poll
with that token -> executes locally -> posts result to /agent/result.
Commands are queued via /agent/command (or chat "pc ..." commands).
"""

import re

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from api.auth import current_user
from database.database import (
    get_device, register_device, device_by_token, touch_device,
    enqueue_command, pending_commands, command_result, get_command,
    unnotified_results,
)

router = APIRouter(prefix="/agent", tags=["agent"])

ALLOWED_ACTIONS = {"open_app", "open_url", "open_path", "list_dir", "read_file", "status"}


def _require_user(request: Request):
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required for PC agent")
    return user


def _agent_user(request: Request):
    token = request.query_params.get("token") or request.headers.get("x-agent-token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing agent token")
    uid = device_by_token(token)
    if uid is None:
        raise HTTPException(status_code=401, detail="Invalid agent token")
    return uid


class RegisterIn(BaseModel):
    name: str = Field(default="My PC", max_length=60)


@router.post("/register")
def register(data: RegisterIn, request: Request):
    """Link this user account to a PC. Returns the agent token (store it locally)."""
    user = _require_user(request)
    token = register_device(user["id"], data.name.strip() or "My PC")
    return {"token": token, "device": data.name, "user": user["name"]}


@router.get("/status")
def status(request: Request):
    """Is a PC agent linked and recently seen?"""
    user = _require_user(request)
    dev = get_device(user["id"])
    if not dev:
        return {"linked": False, "online": False}
    online = False
    if dev["last_seen"]:
        try:
            from datetime import datetime
            seen = datetime.fromisoformat(dev["last_seen"].replace("Z", "+00:00"))
            online = (datetime.now(seen.tzinfo) - seen).total_seconds() < 45
        except Exception:
            online = False
    return {"linked": True, "online": online, "name": dev["name"],
            "last_seen": dev["last_seen"]}


class CommandIn(BaseModel):
    action: str = Field(min_length=1, max_length=40)
    args: dict = Field(default_factory=dict)


@router.post("/command")
def send_command(data: CommandIn, request: Request):
    user = _require_user(request)
    if get_device(user["id"]) is None:
        raise HTTPException(status_code=400, detail="No PC linked — register first")
    if data.action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail=f"Action not allowed: {data.action}")
    cid = enqueue_command(user["id"], data.action, data.args)
    return {"ok": True, "command_id": cid}


@router.get("/poll")
def poll(request: Request):
    """Agent polls this. Token identifies the device."""
    uid = _agent_user(request)
    touch_device(uid)
    return {"commands": pending_commands(uid)}


class ResultIn(BaseModel):
    id: int
    ok: bool = True
    output: str = Field(default="", max_length=3900)


@router.post("/result")
def result(data: ResultIn, request: Request):
    uid = _agent_user(request)
    command_result(uid, data.id, data.ok, data.output)
    return {"ok": True}


@router.get("/commands/{command_id}")
def command_status(command_id: int, request: Request):
    user = _require_user(request)
    cmd = get_command(command_id, user["id"])
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    return cmd


PC_PREFIXES = ("pc ", "my pc ", "computer ", "device ", "laptop ")


def parse_pc_command(text: str):
    """Parse 'open notepad', 'youtube lofi', 'files in downloads' etc.
    Returns (action, args) or None if unrecognised."""
    t = text.strip().lower()
    # strip device prefixes
    for p in PC_PREFIXES:
        if t.startswith(p):
            t = t[len(p):].strip()
            break
    else:
        return None

    m = re.match(r"open\s+(?:the\s+)?(?:app\s+|application\s+)?(.+)", t)
    if m:
        target = m.group(1).strip()
        if re.match(r"^(https?://|www\.|[\w-]+\.(com|org|net|in|io|dev|app)\b)", target):
            url = target if target.startswith("http") else f"https://{target}"
            return "open_url", {"url": url}
        return "open_app", {"name": target}

    m = re.match(r"(?:search\s+)?youtube\s+(?:for\s+)?(.+)", t)
    if m:
        q = m.group(1).strip().replace(" ", "+")
        return "open_url", {"url": f"https://www.youtube.com/results?search_query={q}"}

    m = re.match(r"(?:search\s+)?google\s+(?:for\s+)?(.+)", t)
    if m:
        q = m.group(1).strip().replace(" ", "+")
        return "open_url", {"url": f"https://www.google.com/search?q={q}"}

    m = re.match(r"(?:go to|visit)\s+(.+)", t)
    if m:
        url = m.group(1).strip()
        if not url.startswith("http"):
            url = "https://" + url
        return "open_url", {"url": url}

    if re.match(r"^(?:list\s+)?(?:files|folders|directory|what'?s in)\b.*", t) or \
       re.match(r"^(downloads|documents|desktop|pictures)\b", t):
        path = ""
        m2 = re.search(r"(?:in|of|from)\s+(downloads|documents|desktop|pictures)", t)
        if m2:
            path = m2.group(1)
        elif re.match(r"^(downloads|documents|desktop|pictures)\b", t):
            path = t.split()[0]
        return "list_dir", {"path": path}

    m = re.match(r"read\s+(?:file\s+|the\s+file\s+)?(.+)", t)
    if m:
        return "read_file", {"path": m.group(1).strip()}

    if t in ("status", "agent status"):
        return "status", {}

    return "unknown", {}


QUESTION_START = re.compile(
    r"^(kya|kyu|kyon|kaise|kab|kahan|kitna|kitni|who|what|why|how|when|"
    r"where|which|can|could|should|would|do|does|did|is|are|was|were|"
    r"mere|mera|meri|mujhe|hum|aap|tum)\b"
)

# Common site names -> direct URLs (more reliable than guessing apps)
WEB_TARGETS = {
    "youtube": "https://www.youtube.com",
    "yt": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "chatgpt": "https://chatgpt.com",
    "github": "https://github.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "maps": "https://maps.google.com",
    "calendar": "https://calendar.google.com",
    "drive": "https://drive.google.com",
}


def parse_loose_command(text: str):
    """Hinglish commands without the 'pc' prefix:
    'whatsapp kholo', 'notepad open karo', 'bittu ko hii msg karo'.
    Returns (action, args) or (None, None)."""
    t = re.sub(r"\s+", " ", text.strip().lower())
    t = re.sub(r"^(please|pls|bhai|bro|yaar|oye|hey|ok|okay)[,\s]+", "", t)

    # "X ko Y msg/message bhejo/likho" -> messaging intent
    m = re.match(
        r"^(.+?)\s+ko\s+(.+?)\s*(?:ka|ki|ka\s+unko|unhe)?\s*"
        r"(?:msg|message|whatsapp|wa|sms|text|pm)\s*"
        r"(?:karo|bhej(?:o|do)?|likh(?:o|do)?|send)?\s*$", t)
    if m:
        contact, msg = m.group(1).strip(), m.group(2).strip()
        # compound commands: "whatsapp kholo or bittu ko msg" -> keep last part
        contact = re.split(r"\s+(?:or|aur|and|ya)\s+", contact)[-1].strip()
        contact = re.sub(r"\s+(?:khol(?:o|do)?|open(?:\s+karo)?|chalu|app)\b.*$", "", contact).strip()
        if contact and msg and not QUESTION_START.match(contact):
            return "message", {"contact": contact, "text": msg}

    # "X kholo / X open karo / X chalu karo / X launch karo"
    m = re.match(
        r"^(.+?)\s+(?:ko\s+)?(?:khol(?:o|do)?|open(?:\s+karo)?|"
        r"chalu(?:\s+karo)?|launch(?:\s+karo)?)\s*(?:karo|do|de)?\s*$", t)
    if m:
        target = m.group(1).strip()
        target = re.sub(r"\s+(?:app|application|wala|wala\s+app)$", "", target)
        if target and not QUESTION_START.match(target) and len(target.split()) <= 4:
            # websites / urls -> open_url, otherwise app name
            if re.match(r"^(https?://|www\.|[\w-]+\.(com|org|net|in|io|dev|app)\b)", target):
                url = target if target.startswith("http") else f"https://{target}"
                return "open_url", {"url": url}
            if re.search(r"\b(site|website|page|link|url)\b", target):
                q = re.sub(r"\b(site|website|page|link|url|khol|open)\b", "", target)
                q = re.sub(r"\s+", " ", q).strip(" ?.!")
                if q:
                    return "open_url", {"url": f"https://www.google.com/search?q={q.replace(' ', '+')}"}
            if target in WEB_TARGETS:
                return "open_url", {"url": WEB_TARGETS[target]}
            return "open_app", {"name": target}

    return None, None


def agent_notifications(user_id):
    """Drain finished agent results for the notifications feed."""
    out = []
    for r in unnotified_results(user_id):
        icon = "✅" if r["status"] == "done" else "❌"
        out.append(f"{icon} PC agent: {r['action']} — {r['result'][:200]}")
    return out
