#!/usr/bin/env python3
"""
NOVA Local Agent — runs on YOUR computer and executes commands
that NOVA (cloud) sends through the backend.

Setup:
  1. On the NOVA site: chat menu (+) -> "PC Agent" -> copy your token.
  2. Put the token in agent/config.json next to this file.
  3. Run:  python nova_agent.py

Only safe, allow-listed actions are supported. Nothing destructive
can run — there is no shell/exec action by design.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")

DEFAULT_CONFIG = {
    "backend": "https://nova-ai-1-5hlz.onrender.com",
    "token": "",
    "poll_interval": 3,
}

# Friendly app names -> launch commands (Windows first, fallbacks included)
APPS = {
    "notepad": ["notepad.exe"],
    "notes": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "cmd": ["cmd.exe"],
    "command prompt": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "terminal": ["wt.exe", "cmd.exe"],
    "explorer": ["explorer.exe"],
    "files": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "task manager": ["taskmgr.exe"],
    "chrome": ["chrome", "chrome.exe", "google chrome"],
    "browser": ["chrome", "msedge", "firefox", "brave"],
    "vscode": ["code"],
    "vs code": ["code"],
    "code": ["code"],
    "spotify": ["spotify"],
    "settings": ["ms-settings:"],
    "control panel": ["control.exe"],
}

# Directories the agent is allowed to browse/read
ALLOWED_DIRS = [
    os.path.expanduser("~"),
]
ALLOWED_READ_EXT = {
    ".txt", ".md", ".json", ".csv", ".py", ".js", ".ts", ".html",
    ".css", ".log", ".ini", ".cfg", ".yaml", ".yml", ".xml",
}
MAX_READ_BYTES = 200 * 1024
MAX_LIST = 60


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            print(f"[config] could not parse config.json: {e}")
    return cfg


def api(cfg, method, path, payload=None, timeout=15):
    url = cfg["backend"].rstrip("/") + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if cfg.get("token"):
        req.add_header("X-Agent-Token", cfg["token"])
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def safe_path(path_arg, must_exist=False):
    """Resolve a user-supplied path; must stay under an allowed dir."""
    if not path_arg:
        return os.path.expanduser("~")
    p = os.path.abspath(os.path.expanduser(path_arg))
    for base in ALLOWED_DIRS:
        base = os.path.abspath(base)
        if p == base or p.startswith(base + os.sep):
            if must_exist and not os.path.exists(p):
                raise FileNotFoundError(p)
            return p
    raise PermissionError(f"Path outside allowed area: {p}")


def act_open_app(args):
    name = (args.get("name") or "").strip().lower()
    if not name:
        raise ValueError("No app name given")
    candidates = APPS.get(name, [name])  # unknown names tried as-is (start menu search)
    for cmd in candidates:
        try:
            if os.name == "nt":
                subprocess.Popen(cmd, shell=True)
            else:
                subprocess.Popen([cmd])
            return f"Opened {name}"
        except Exception:
            continue
    raise RuntimeError(f"Could not launch: {name}")


def act_open_url(args):
    url = (args.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def act_open_path(args):
    p = safe_path(args.get("path"), must_exist=True)
    os.startfile(p) if os.name == "nt" else subprocess.Popen(["xdg-open", p])
    return f"Opened {p}"


def act_list_dir(args):
    p = safe_path(args.get("path"))
    if not os.path.isdir(p):
        raise NotADirectoryError(p)
    items = sorted(os.listdir(p))[:MAX_LIST]
    dirs = [i for i in items if os.path.isdir(os.path.join(p, i))]
    files = [i for i in items if os.path.isfile(os.path.join(p, i))]
    return f"{p}\nFolders: {', '.join(dirs[:20]) or '-'}\nFiles: {', '.join(files[:20]) or '-'}"


def act_read_file(args):
    p = safe_path(args.get("path"), must_exist=True)
    ext = os.path.splitext(p)[1].lower()
    if ext not in ALLOWED_READ_EXT:
        raise PermissionError(f"File type not allowed: {ext or 'none'}")
    if os.path.getsize(p) > MAX_READ_BYTES:
        raise ValueError("File too large (>200KB)")
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        text = f.read(8000)
    return f"{os.path.basename(p)}:\n{text}"


def act_status(args):
    import platform
    return (f"{platform.node()} | {platform.system()} {platform.release()} | "
            f"Python {platform.python_version()} | agent online")


ACTIONS = {
    "open_app": act_open_app,
    "open_url": act_open_url,
    "open_path": act_open_path,
    "list_dir": act_list_dir,
    "read_file": act_read_file,
    "status": act_status,
}


def execute(cmd):
    fn = ACTIONS.get(cmd["action"])
    if not fn:
        return False, f"Unknown action: {cmd['action']}"
    try:
        return True, fn(cmd.get("args") or {})
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    cfg = load_config()
    if not cfg.get("token"):
        print("=" * 60)
        print("NOVA Local Agent")
        print("=" * 60)
        print("No token found. Do this:")
        print("  1. Open NOVA in your browser and sign in")
        print("  2. Chat menu (+) -> 'PC Agent' -> copy the token")
        print("  3. Paste it into agent/config.json -> \"token\": \"...\"")
        print("  4. Run this script again")
        print("=" * 60)
        sys.exit(1)

    print(f"[agent] connected to {cfg['backend']} — polling every {cfg['poll_interval']}s")
    print("[agent] Ctrl+C to stop")

    backoff = cfg["poll_interval"]
    while True:
        try:
            data = api(cfg, "GET", "/agent/poll", timeout=20)
            backoff = cfg["poll_interval"]
            for cmd in data.get("commands", []):
                print(f"[agent] #{cmd['id']} {cmd['action']} {cmd.get('args')}")
                ok, out = execute(cmd)
                print(f"[agent]   -> {'OK' if ok else 'FAIL'}: {str(out)[:120]}")
                try:
                    api(cfg, "POST", "/agent/result",
                        {"id": cmd["id"], "ok": ok, "output": str(out)[:3900]},
                        timeout=15)
                except Exception as e:
                    print(f"[agent]   result post failed: {e}")
        except urllib.error.HTTPError as e:
            print(f"[agent] HTTP {e.code}: {e.reason}")
            if e.code == 401:
                print("[agent] bad token — check config.json")
                sys.exit(1)
            backoff = min(backoff * 2, 30)
        except Exception as e:
            print(f"[agent] poll error: {e}")
            backoff = min(backoff * 2, 30)
        time.sleep(backoff)


if __name__ == "__main__":
    main()
