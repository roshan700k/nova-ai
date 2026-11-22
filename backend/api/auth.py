import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from database.database import upsert_user, get_user_by_id

for candidate in (".env", os.path.join("..", ".env")):
    load_dotenv(candidate)

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "astra-dev-secret-change-me")
SESSION_COOKIE = "astra_session"
SESSION_TTL = 7 * 24 * 3600  # 7 days

REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/auth/google/callback"
)


def _sign(payload: str) -> str:
    return hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _make_session(user_id: int) -> str:
    payload = json.dumps({"uid": user_id, "exp": int(time.time()) + SESSION_TTL})
    return payload + "." + _sign(payload)


def _read_session(token: str):
    try:
        payload, sig = token.rsplit(".", 1)
        if not hmac.compare_digest(sig, _sign(payload)):
            return None
        data = json.loads(payload)
        if data.get("exp", 0) < time.time():
            return None
        return data.get("uid")
    except Exception:
        return None


def current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    uid = _read_session(token)
    if not uid:
        return None
    return get_user_by_id(uid)


def require_admin(request: Request):
    """Dependency: requires admin role."""
    user = current_user(request)
    if not user or user.get("role") != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/google")
def google_login():
    if not GOOGLE_CLIENT_ID:
        return {"error": "GOOGLE_CLIENT_ID not set in .env"}
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
    }
    return RedirectResponse(
        "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    )


@router.get("/google/callback")
def google_callback(code: str, response: Response):
    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    if token_resp.status_code != 200:
        return {"error": "token exchange failed", "detail": token_resp.text[:300]}

    access_token = token_resp.json()["access_token"]
    info = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    ).json()

    user = upsert_user(
        email=info.get("email", ""),
        name=info.get("name", info.get("email", "user")),
        provider="google",
    )
    if not user:
        return {"error": "could not create user"}

    response.set_cookie(
        SESSION_COOKIE,
        _make_session(user["id"]),
        max_age=SESSION_TTL,
        httponly=True,
        samesite="lax",
    )
    return RedirectResponse("http://localhost:5173/?login=ok")


@router.post("/dev-login")
def dev_login(body: dict, response: Response):
    """Development-only login so the app works before Google OAuth is set up."""
    if os.environ.get("DEV_AUTH", "true").lower() != "true":
        return {"error": "dev login disabled"}
    name = str(body.get("name", "developer"))[:50]
    email = f"{name.lower().replace(' ', '.')}@dev.local"
    user = upsert_user(email=email, name=name, provider="dev")
    response.set_cookie(
        SESSION_COOKIE,
        _make_session(user["id"]),
        max_age=SESSION_TTL,
        httponly=True,
        samesite="lax",
    )
    return {"ok": True, "user": user}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@router.get("/me")
def me(request: Request):
    return {"user": current_user(request)}
