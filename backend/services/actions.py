"""Permission gate for anything NOVA does on the machine.

Every action (open app, write file, run command, upload) must be
approved by the user before it executes. Nothing runs silently.
"""

import json
import os
import subprocess
import time
import uuid
import webbrowser
from urllib.parse import quote


class ActionBroker:
    def __init__(self):
        self.pending = {}   # id -> {description, kind, payload, created_at}
        self.history = []   # executed/denied log

    # ---------------------------------------------------------
    # Request / approve / deny
    # ---------------------------------------------------------

    def request(self, kind: str, description: str, payload: dict) -> str:
        action_id = uuid.uuid4().hex[:8]
        self.pending[action_id] = {
            "id": action_id,
            "kind": kind,
            "description": description,
            "payload": payload,
            "created_at": time.time(),
        }
        return action_id

    def list_pending(self):
        return list(self.pending.values())

    def approve(self, action_id: str):
        action = self.pending.pop(action_id, None)
        if not action:
            return {"ok": False, "error": "unknown or expired action"}
        try:
            result = self._execute(action["kind"], action["payload"])
            self.history.append({**action, "status": "done", "result": str(result)[:500]})
            return {"ok": True, "result": str(result)[:500]}
        except Exception as exc:
            self.history.append({**action, "status": "failed", "result": str(exc)})
            return {"ok": False, "error": str(exc)}

    def deny(self, action_id: str):
        action = self.pending.pop(action_id, None)
        if action:
            self.history.append({**action, "status": "denied"})
        return {"ok": True}

    # ---------------------------------------------------------
    # Executors — each kind is a small, explicit function
    # ---------------------------------------------------------

    def _execute(self, kind: str, payload: dict):
        if kind == "open_url":
            url = payload["url"]
            if not url.startswith(("http://", "https://")):
                raise ValueError("only http(s) URLs allowed")
            webbrowser.open(url)
            return f"opened {url}"

        if kind == "launch_app":
            exe = payload["exe"]
            # Allowlist of known-safe Windows executables
            allowed = {
                "notepad.exe", "calc.exe", "explorer.exe", "taskmgr.exe",
                "chrome", "code", "msedge",
            }
            name = os.path.basename(exe).lower()
            if name not in allowed and exe not in allowed:
                raise ValueError(f"app not in allowlist: {exe}")
            subprocess.Popen([exe] if ".exe" in name or exe in allowed else [exe])
            return f"launched {exe}"

        if kind == "write_file":
            path = os.path.abspath(payload["path"])
            root = os.path.abspath(".")
            if not path.startswith(root):
                raise ValueError("path outside workspace")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(payload["content"])
            return f"wrote {path}"

        if kind == "upload_video":
            from modules import youtube_manager
            meta = payload.get("metadata") or {}
            return youtube_manager.upload_video(
                video_path=payload["video"],
                title=payload.get("title", "NOVA video"),
                description=meta.get("description", ""),
                tags=meta.get("tags", []),
                privacy="private",  # never public without explicit second approval
            )

        if kind == "run_command":
            cmd = payload["cmd"]
            # No shell=True; commands must be explicit arg lists
            if isinstance(cmd, str):
                cmd = cmd.split()
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, cwd=payload.get("cwd")
            )
            return (proc.stdout or "") + (proc.stderr or "")

        raise ValueError(f"unknown action kind: {kind}")


broker = ActionBroker()
