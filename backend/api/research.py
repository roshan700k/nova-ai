import re

import requests
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from api.auth import current_user
from database.database import get_user_settings, set_user_settings

router = APIRouter(prefix="/research", tags=["research"])


def _ddg(query: str) -> dict:
    """DuckDuckGo Instant Answer API — free, no key."""
    try:
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=10,
            headers={"User-Agent": "NOVA-AI/1.0"},
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def _sources_from_ddg(data: dict) -> list:
    sources = []
    if data.get("AbstractURL"):
        sources.append({"title": data.get("Heading") or "Source", "url": data["AbstractURL"]})
    for t in (data.get("RelatedTopics") or [])[:5]:
        if isinstance(t, dict) and t.get("FirstURL"):
            sources.append({"title": t.get("Text", "")[:80], "url": t["FirstURL"]})
    return sources[:6]


class ResearchIn(BaseModel):
    query: str = Field(min_length=2, max_length=500)


def do_research(query: str, llm=None) -> dict:
    """Core research logic — usable from API and chat commands."""
    query = query.strip()
    ddg = _ddg(query)

    answer = ddg.get("AbstractText") or ""
    heading = ddg.get("Heading") or query

    if not answer and llm is not None:
        try:
            answer = llm.think(
                f"Research and briefly explain: {query}. "
                "Mention this is from model knowledge, not live web.",
                None,
                tone_hint="Be factual, concise, and note uncertainty.",
            ) or "No information found."
        except Exception:
            answer = "Research service unavailable right now."

    return {
        "query": query,
        "heading": heading,
        "answer": answer or "No information found.",
        "sources": _sources_from_ddg(ddg),
    }


def _save_note(user_id: int, query: str, result: dict):
    try:
        from memory.memory import Memory
        import os
        mem = Memory(file=os.environ.get("MEMORY_FILE_PATH", "memory.json"))
        key = f"research:{query[:60]}"
        mem.remember(key, f"{result['heading']}: {result['answer'][:500]}", ns=f"u{user_id}")
        return key
    except Exception:
        return None


@router.post("")
def research(data: ResearchIn, request: Request):
    user = current_user(request)
    result = do_research(data.query, llm=None)

    # Enrich with LLM if DDG had no instant answer
    if result["answer"] == "No information found.":
        try:
            from main import brain
            enriched = do_research(data.query, llm=brain.llm)
            if enriched["answer"] != "No information found.":
                result = enriched
        except Exception:
            pass

    note_id = _save_note(user["id"], data.query, result) if user else None
    result["note_saved"] = note_id
    return result
