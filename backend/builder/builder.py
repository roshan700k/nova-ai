"""ASTRA Builder: turns 'build me X' into real files on disk.

Flow: LLM produces a file plan -> each write_file goes through the
ActionBroker permission gate -> user approves -> files written.
"""

import json
import os
import re

from services.actions import broker

PROJECTS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "projects")


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:40] or "project"


class BuilderAgent:

    def __init__(self, llm=None):
        self.llm = llm

    def handle(self, message: str) -> str:
        if not self.llm or not self.llm.provider:
            return (
                "I can build things for you, but my AI brain is offline right now — "
                "connect a Gemini API key or start Ollama and I'll write the code myself."
            )

        prompt = (
            "You are ASTRA's builder. The user asked: "
            f"\"{message}\"\n\n"
            "Respond with ONLY a JSON object, no markdown:\n"
            '{"name": "short-project-name", "files": [{"path": "relative/path", '
            '"content": "full file content"}], "run": "optional command to run"}\n'
            "Keep it minimal but working. Use Python/Flask or plain HTML+JS unless asked otherwise."
        )

        raw = self.llm.think(prompt, [])
        if not raw:
            return "My AI brain didn't respond — try again in a moment."

        plan = self._parse_plan(raw)
        if not plan:
            return "I drafted a plan but couldn't parse it — ask me to try again."

        project_dir = os.path.join(PROJECTS_ROOT, _slug(plan.get("name", "project")))

        # Queue every file write through the permission gate
        queued = 0
        for f in plan.get("files", []):
            path = os.path.join(project_dir, f["path"].lstrip("/").lstrip("\\"))
            aid = broker.request(
                kind="write_file",
                description=f"ASTRA wants to create {f['path']} in {project_dir}",
                payload={"path": path, "content": f["content"]},
            )
            queued += 1
            print(f"[builder] queued {aid}: {path}")

        return (
            f"I've drafted {queued} files for \"{plan.get('name','project')}\" in "
            f"{project_dir}. I've queued them for your approval — check pending actions "
            f"(GET /actions/pending) and approve each one, or tell me to auto-approve."
        )

    @staticmethod
    def _parse_plan(raw: str):
        # Strip markdown fences if the model added them
        cleaned = re.sub(r"```(?:json)?", "", raw).strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            return None
        try:
            plan = json.loads(match.group(0))
            if isinstance(plan, dict) and plan.get("files"):
                return plan
        except json.JSONDecodeError:
            return None
        return None
