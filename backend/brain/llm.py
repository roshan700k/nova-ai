import os
import time

import requests
from dotenv import load_dotenv

# .env lives at repo root; backend runs with backend/ as cwd
for candidate in (".env", os.path.join("..", ".env")):
    load_dotenv(candidate)

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
# Tried in order when the primary model errors (deprecated/overloaded/quota)
GEMINI_FALLBACKS = ["gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-2.5-flash-lite"]
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

NOVA_PERSONA = (
    "You are NOVA, Roshan's personal AI assistant. "
    "You are friendly, concise and a little futuristic. "
    "You remember context from the conversation. "
    "Keep replies short unless a detailed answer is needed."
)


class LLMBrain:
    """Real AI backend with provider fallback: Gemini -> Ollama -> None."""

    def __init__(self):
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self._ollama_ok_at = 0.0
        self._ollama_ok = False

    # ---------------------------------------------------------
    # Provider detection
    # ---------------------------------------------------------

    @property
    def provider(self):
        if self.gemini_key:
            return "gemini"
        if self._ollama_available():
            return "ollama"
        return None

    def _ollama_available(self):
        # Cache the check for 60s so we don't ping Ollama every message
        if time.time() - self._ollama_ok_at < 60:
            return self._ollama_ok
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            self._ollama_ok = r.status_code == 200
        except Exception:
            self._ollama_ok = False
        self._ollama_ok_at = time.time()
        return self._ollama_ok

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def think(self, message: str, history: list | None = None, tone_hint: str = "") -> str | None:
        provider = self.provider
        if provider == "gemini":
            return self._gemini(message, history, tone_hint)
        if provider == "ollama":
            return self._ollama(message, history, tone_hint)
        return None

    # ---------------------------------------------------------
    # Gemini
    # ---------------------------------------------------------

    def _gemini(self, message: str, history: list | None, tone_hint: str = ""):
        contents = self._build_contents(message, history)
        persona = NOVA_PERSONA + (("\n" + tone_hint) if tone_hint else "")
        payload = {
            "system_instruction": {"parts": [{"text": persona}]},
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512},
        }

        last_exc = None
        for model in [GEMINI_MODEL] + [m for m in GEMINI_FALLBACKS if m != GEMINI_MODEL]:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={self.gemini_key}"
            )
            try:
                r = requests.post(url, json=payload, timeout=30)
                if r.status_code in (404, 429, 500, 502, 503):
                    last_exc = f"{model}: {r.status_code}"
                    continue
                r.raise_for_status()
                parts = r.json()["candidates"][0]["content"]["parts"]
                text = "".join(p.get("text", "") for p in parts).strip()
                return text or None
            except requests.RequestException as exc:
                last_exc = f"{model}: {exc}"
                continue

        print(f"[llm] gemini error: {last_exc}")
        return None

    # ---------------------------------------------------------
    # Ollama (local, free, private)
    # ---------------------------------------------------------

    def _ollama(self, message: str, history: list | None, tone_hint: str = ""):
        prompt = self._build_prompt(message, history, tone_hint)
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 512},
                },
                timeout=60,
            )
            r.raise_for_status()
            text = r.json().get("response", "").strip()
            return text or None
        except Exception as exc:
            print(f"[llm] ollama error: {exc}")
            self._ollama_ok = False
            self._ollama_ok_at = time.time()
            return None

    # ---------------------------------------------------------
    # Prompt building (shared shape for both providers)
    # ---------------------------------------------------------

    @staticmethod
    def _build_contents(message: str, history: list | None):
        contents = []
        for turn in (history or [])[-4:]:
            contents.append({"role": "user", "parts": [{"text": turn["user"]}]})
            contents.append({"role": "model", "parts": [{"text": turn["astra"]}]})
        contents.append({"role": "user", "parts": [{"text": message}]})
        return contents

    @staticmethod
    def _build_prompt(message: str, history: list | None, tone_hint: str = ""):
        lines = [NOVA_PERSONA + (("\n" + tone_hint) if tone_hint else ""), ""]
        for turn in (history or [])[-4:]:
            lines.append(f"User: {turn['user']}")
            lines.append(f"NOVA: {turn['astra']}")
        lines.append(f"User: {message}")
        lines.append("NOVA:")
        return "\n".join(lines)
