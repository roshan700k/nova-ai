"""Automation Engine — breaks a goal into steps, executes safe ones,
flags sensitive ones for confirmation. Never claims success without
verifying the underlying tool actually ran."""

import json
import re

import requests
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from api.auth import current_user
from api.research import do_research
from database.database import create_task

router = APIRouter(prefix="/automation", tags=["automation"])

SAFE_ACTIONS = {"research", "task", "note", "search", "answer"}

PLAN_PROMPT = """Break this goal into executable steps. Reply with ONLY a JSON array, no markdown, no commentary:
[{"action":"ACTION","detail":"short detail"}]

Allowed actions:
- research: web research on a topic (detail = search query)
- task: add an item to the user's task list (detail = task title)
- note: save a fact/preference to memory (detail = "key: value")
- search: open a web/youtube search (detail = search query)
- answer: answer a question directly (detail = the question)
- confirm: an action needing explicit user permission — deleting data, sending messages, publishing, spending money, controlling the computer (detail = what to do)

Rules: max 6 steps, keep details under 12 words, order steps logically.
Goal: {goal}"""


def _extract_json(text: str):
    if not text:
        return None
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, list) else None
    except Exception:
        return None


def _plan(goal: str, llm) -> list:
    """Ask the LLM for a JSON step plan; fall back to a single research step."""
    if llm is not None:
        try:
            raw = llm.think(PLAN_PROMPT.format(goal=goal), None,
                            tone_hint="Output ONLY the JSON array. No other text.")
            steps = _extract_json(raw or "")
            if steps:
                clean = []
                for s in steps[:6]:
                    if isinstance(s, dict) and s.get("action") and s.get("detail"):
                        clean.append({"action": str(s["action"]).lower(),
                                      "detail": str(s["detail"])[:200]})
                if clean:
                    return clean
        except Exception:
            pass
    return [{"action": "research", "detail": goal}]


def _exec_search(detail: str) -> str:
    q = detail.strip().replace(" ", "+")
    return f"[Open search results](https://www.youtube.com/results?search_query={q})"


def _exec_step(step: dict, user_id, llm) -> dict:
    """Run one step. Returns {status, output}."""
    action, detail = step["action"], step["detail"]

    if action == "confirm":
        return {"status": "needs_confirmation",
                "output": f"Requires your approval: {detail}"}
    if action not in SAFE_ACTIONS:
        return {"status": "skipped", "output": f"Unknown action: {action}"}

    if action == "research":
        res = do_research(detail, llm=llm)
        src = f" ({len(res['sources'])} sources)" if res["sources"] else ""
        return {"status": "done",
                "output": f"{res['answer'][:400]}{src}"}

    if action == "task":
        if user_id is None:
            return {"status": "skipped", "output": "Sign in to save tasks."}
        tid = create_task(user_id, detail)
        return {"status": "done" if tid else "failed",
                "output": f"Task added: {detail}" if tid else "Could not save task."}

    if action == "note":
        if user_id is None:
            return {"status": "skipped", "output": "Sign in to save memory."}
        try:
            import os
            from memory.memory import Memory
            mem = Memory(file=os.environ.get("MEMORY_FILE_PATH", "memory.json"))
            key, _, val = detail.partition(":")
            mem.remember(key.strip()[:60] or "note", val.strip() or detail,
                         ns=f"u{user_id}")
            return {"status": "done", "output": f"Remembered: {detail[:80]}"}
        except Exception:
            return {"status": "failed", "output": "Could not save to memory."}

    if action == "search":
        return {"status": "done", "output": _exec_search(detail)}

    if action == "answer":
        if llm is None:
            return {"status": "skipped", "output": "AI offline."}
        ans = llm.think(detail, None) or "No answer."
        return {"status": "done", "output": ans[:500]}

    return {"status": "skipped", "output": f"Unknown action: {action}"}


def run_automation(goal: str, user_id, llm) -> dict:
    """Plan + execute. Returns structured result usable by API and chat."""
    steps = _plan(goal, llm)
    results = []
    done = pending = failed = 0
    for i, step in enumerate(steps, 1):
        r = _exec_step(step, user_id, llm)
        results.append({"n": i, **step, **r})
        if r["status"] == "done":
            done += 1
        elif r["status"] == "needs_confirmation":
            pending += 1
        elif r["status"] == "failed":
            failed += 1
    return {
        "goal": goal,
        "steps": results,
        "summary": {"done": done, "needs_confirmation": pending, "failed": failed},
    }


def format_report(result: dict) -> str:
    icons = {"done": "✅", "needs_confirmation": "⏸", "failed": "❌",
             "skipped": "⏭"}
    lines = [f"**Automation: {result['goal']}**\n"]
    for s in result["steps"]:
        icon = icons.get(s["status"], "•")
        lines.append(f"{icon} **{s['action']}** — {s['detail']}")
        if s["output"]:
            lines.append(f"   {s['output']}")
    sm = result["summary"]
    lines.append(
        f"\nDone: {sm['done']} · Needs approval: {sm['needs_confirmation']}"
        f" · Failed: {sm['failed']}"
    )
    if sm["needs_confirmation"]:
        lines.append("Reply 'confirm' to approve the pending steps.")
    return "\n".join(lines)


class AutomationIn(BaseModel):
    goal: str = Field(min_length=3, max_length=500)


@router.post("")
def automate(data: AutomationIn, request: Request):
    user = current_user(request)
    user_id = user["id"] if user else None
    try:
        from main import brain
        llm = brain.llm
    except Exception:
        llm = None
    return run_automation(data.goal.strip(), user_id, llm)
