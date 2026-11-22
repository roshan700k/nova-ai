# ASTRA AI — Initial Repository Audit

**Date:** 2026-11-22
**Auditor:** Devin
**Scope:** Full repository audit — structure, backend, frontend, dependencies, security. Audit only; no source changes were made.

---

## 1. Repository Structure

```
ASTRA-AI/
├── .env                  # 4 vars, no secrets (APP_NAME, VERSION, OWNER, DEBUG)
├── README.md             # 5 lines, minimal
├── requirements.txt      # UTF-16LE encoded — see Dependency Problems
├── package-lock.json     # EMPTY stub ("packages": {}) — stray file, not a real project
├── venv/                 # Python 3.12.10 venv with fastapi/uvicorn installed
├── backend/              # Real backend code (see §2)
├── frontend/             # Real frontend code (React + Vite)
├── assets/               # EMPTY
├── databade/             # EMPTY (note: misspelled "database")
├── desktop/              # EMPTY
├── docs/                 # EMPTY
├── memory/               # EMPTY (real memory lives in backend/memory/)
├── mobile/               # EMPTY
├── plugins/              # EMPTY (real plugin code is backend/plugins/)
├── vision/               # EMPTY
└── voice/                # EMPTY
```

**Key fact:** 8 of the 9 top-level feature directories are completely empty placeholders. All actual code lives in `backend/` and `frontend/`. The project is much earlier-stage than the directory layout suggests.

Inside `backend/`, these directories are also empty: `api/`, `services/`, `models/`, `data/`, `skills/`. `plugins/plugin_manager.py` is an empty file.

Git: repo initialized (`master` branch) with **zero commits** and **no root `.gitignore`** — `venv/`, `frontend/node_modules/`, `backend/astra.db`, `backend/memory.json`, and `logs/` are all untracked and would be committed accidentally.

---

## 2. Entry Points

- **Backend:** `backend/main.py` — FastAPI app, single `POST /chat` endpoint + `GET /`. Must be run with `backend/` as the working directory because imports are absolute-from-backend (`from database.database import ...`, `from brain.brain import ...`).
- **Frontend:** `frontend/src/main.jsx` → `App.jsx` → `Dashboard.jsx` (~2,300 lines, all CSS inlined in a `<style>` block). `chatApi.js` calls `http://127.0.0.1:8000/chat`.

---

## 3. What Was Actually Tested

### Backend — RUNNING (with one required workaround)

Started with:
```
cd backend
set PYTHONIOENCODING=utf-8
..\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Verified live via `curl`:

| Input | Result | Verdict |
|---|---|---|
| `GET /` | `{"message":"ASTRA AI Backend Running"}` | Works |
| `hello` | `👋 Hello Roshan! Nice to see you.` | Works |
| `remember city=bangalore` → `what is city` | `city = bangalore` | Works |
| `how are you` / `who are you` | canned replies | Works |
| `teach: capital of france = paris` → `what is capital of france` | `I don't remember that.` | **BROKEN** (see B2) |
| `remember tempkey=abc` then `teach: q2=a2` | `tempkey` silently deleted from `memory.json` | **BROKEN — data loss** (see B3) |
| `write some python code` | `👨‍💻 Coding module is coming soon.` | Stub |
| `open the pdf` | `📄 PDF Reader module is under development.` | Stub |
| `tell me a joke` | `I understood: tell me a joke` | No real chat/LLM |
| `open notepad` | `Opening Notepad.` (app actually launched) | Works |
| `{"message":123}` | HTTP 500 Internal Server Error | **BROKEN** (see B4) |
| `{}` (no message) | `I understood: ` | Silent acceptance of empty input |
| `GET /docs` | Swagger UI loads | Exposed (see S3) |

### Frontend — RUNNING

- `npm run lint` → **passes clean** (0 errors/warnings)
- `npm run build` → **succeeds** (267 kB JS bundle)
- `npm run dev` → serves on `http://localhost:5173`
- Dashboard renders the purple holographic UI; chat input, voice button (Web Speech API), TTS (`speechSynthesis`), quick-action buttons, and fake activity feed are all present in code.
- Voice input uses `webkitSpeechRecognition` — **Chrome/Edge only**; other browsers get an alert. TTS auto-reads every reply.
- Not browser-tested end-to-end beyond serving; chat depends on backend at `127.0.0.1:8000`.

---

## 4. Existing Working Features

1. **Chat round-trip** frontend → `POST /chat` → reply displayed and spoken. Verified.
2. **Key-value memory commands** — `remember key=value` and `what is key`, persisted to `backend/memory.json`. Verified.
3. **Computer control (partial)** — `ComputerModule` (`backend/modules/computer_module.py`) opens websites, Chrome, VS Code, Calculator, Notepad, Explorer, Downloads, Desktop, Settings, Task Manager via `webbrowser`/`subprocess`/`os.startfile`. Windows-only paths hardcoded. Verified (`open notepad` launched Notepad).
4. **YouTube search-open** — `YouTubeModule` opens a YouTube results page for queries containing "youtube" + play/open, or hardcoded "Arijit Singh top songs".
5. **Intent/emotion/personality/context scaffolding** — `brain/` modules exist and are wired, though most are shallow keyword matchers.
6. **Frontend dashboard UI** — polished purple theme, live clock, voice in/out, chat history popup, quick actions. Lint+build clean.

## 5. Broken Features

- **B1 — `ModuleLoader` crashes the backend on Windows consoles.** `backend/modules/module_loader.py:35` prints `⚠️ Class YoutubeModule not found in youtube_module`. On the default Windows `cp1252` console this raises `UnicodeEncodeError` and **the whole app fails to start**. Reproduced: `import main` crashes without `PYTHONIOENCODING=utf-8`.
- **B1b — Class-name generation bug (same file).** `module_name.replace("module", "")` + capitalize produces `YoutubeModule`, but the real class is `YouTubeModule` (`backend/modules/youtube_module.py:5`). `youtube_module` is therefore **never registered** in the loader. It still works only because `brain.py:33` instantiates `YouTubeModule` directly — the loader path is dead for it.
- **B2 — `teach:` answers can never be recalled.** `ReasoningEngine.learn` stores the bare question (`capital of france`), but `think` looks up the **entire raw message** (`what is capital of france`). Exact-match recall therefore fails for any natural phrasing. Verified live.
- **B3 — Memory data loss (two unsynchronized `Memory` instances).** `AstraBrain` creates `self.memory = Memory()` (`brain.py:27`) and `ReasoningEngine.__init__` creates a second `Memory()` (`reasoning.py:7`). Each caches `memory.json` in memory at startup; each `save()` writes its own stale copy. Verified: `remember tempkey=abc` followed by `teach: q2 = a2` **deleted `tempkey` from `memory.json`** — last writer wins, silent data loss.
- **B4 — No input validation.** `main.py:26` accepts `data: dict`; `{"message": 123}` → `AttributeError` → HTTP 500 (verified). Missing `message` silently becomes `""`.
- **B5 — `chart_module.py` is dead code.** Loaded by `ModuleLoader` but `brain.py` has no branch that ever calls `loader.get("chart_module")`. It also duplicates greeting logic.
- **B6 — Module dispatch can `AttributeError`.** `brain.py:95-106` calls `module.think(message)` where `module = self.loader.get(name)`; `get` returns `None` for unregistered names → crash → 500. Currently unreachable only because all hardcoded names happen to exist.
- **B7 — `computer` module shadows `youtube`.** `brain.py:48` runs `computer.think()` before everything. "open youtube" is consumed by `ComputerModule` (opens youtube.com home), so `YouTubeModule`'s search behavior is unreachable for open/play phrasing that overlaps.

## 6. Incomplete Features

- `coding_module.py`, `chat_module.py` — `think()` returns `None` (intent fallthrough produces "coming soon"/"I understood").
- `pdf_module.py`, `browser_module.py` — return "under development" strings.
- `plugins/plugin_manager.py` — empty file; `backend/plugins/` unused.
- `database/database.py` — creates `astra.db` + `memory` table at startup, but **nothing ever reads or writes it**. Dead code; real memory is `memory.json`.
- `config/config_manager.py`, `utils/logger.py` — logger is never imported anywhere; `LOG_FILE`, `MAX_HISTORY`, `MEMORY_FILE` settings are unused (values hardcoded in `Memory`/`ContextManager` instead).
- `decision.py`, `emotion.py`, `module_manager.py` — instantiated but their outputs are never used in `think()` (`decision.decide`, `emotion.detect`, `module_manager` are dead weight).
- `Sidebar.jsx`, `AvatarPanel.jsx`, `Mainpanel.jsx` — exist but are **not imported anywhere**; `App.jsx` renders only `Dashboard`. `Mainpanel.jsx` duplicates the TTS logic.
- Frontend nav: `activePage` state changes highlight only — CHAT/MEMORY/TASKS/etc. all render the same HOME dashboard. Search CSS exists but no search input is rendered.

## 7. Missing Features (vs. stated vision)

| Vision item | Status |
|---|---|
| Natural language chat | Keyword stubs only — **no LLM/AI backend at all** |
| Voice input/output | Browser Web Speech API only (Chrome); no backend voice |
| Personalized memory per user | Single global `memory.json`, no users |
| Google authentication | Absent |
| Multi-user accounts/privacy | Absent — everything is single-user, hardcoded "Roshan" |
| News/research summaries | Absent |
| Computer/browser automation w/ permission | Partial — no permission system at all |
| Tasks & reminders | UI buttons exist; backend absent |
| YouTube research/video creation | Search-open only |
| Purple holographic dashboard | Present (static/fake data) |
| Desktop/mobile apps | Empty directories |

## 8. Dependency Problems

- **`requirements.txt` is UTF-16LE encoded** — `pip install -r requirements.txt` will likely fail or misparse on Windows. Re-save as UTF-8. Contents: fastapi 0.141.1, uvicorn 0.52.1, pydantic, requests, python-dotenv — all installed in `venv/` and importable (verified).
- **Root `package-lock.json` is an empty stub** (`"packages": {}`) — stray artifact, not tied to any package.json.
- **No root `package.json`** — frontend has its own; monorepo tooling absent.
- **No `.gitignore` at repo root** — `venv/`, `node_modules/`, `*.db`, `memory.json`, `logs/` unprotected.
- **No tests** anywhere (no pytest, no test files, no CI).
- Frontend deps are modern and fine (React 19, Vite 8, axios); `axios` is used only in `chatApi.js`.
- `backend/` has no `requirements.txt` of its own and no `pyproject.toml` — dependencies only resolvable from repo root, and only if encoding is fixed.

## 9. Security Problems

- **S1 — CORS wide open:** `main.py:13` `allow_origins=["*"]` combined with `allow_credentials=True` — invalid per spec and maximally permissive. Any website can call the API.
- **S2 — Unauthenticated remote control:** `POST /chat` triggers `ComputerModule` — arbitrary website opens and app launches driven purely by message text. No auth, no confirmation/permission gate (vision requires permission-based automation). Currently bound to `127.0.0.1` by convention only; nothing enforces it.
- **S3 — Swagger `/docs` exposed** in production-facing code; `DEBUG=True` hardcoded in `config/settings.py` (though unused).
- **S4 — No input validation/sanitization** (B4) — also enables trivial 500s.
- **S5 — Secrets:** `.env` contains no secrets today (good), but there is **no `.gitignore`**, so a future key added there would be committed. `.env` is currently untracked-but-unprotected.
- **S6 — `os.startfile`/`subprocess` on user text** — fine for a local single-user toy, dangerous the moment auth/network exposure is added.
- **S7 — `memory.json`/`astra.db` contain personal data**, stored plaintext in repo tree, unencrypted, no per-user isolation.

## 10. Recommended Fixes (ordered)

1. Add root `.gitignore` (`venv/`, `node_modules/`, `dist/`, `*.db`, `memory.json`, `logs/`, `.env`) **before the first commit**.
2. Re-encode `requirements.txt` to UTF-8.
3. Fix `ModuleLoader`: explicit class-name map (or `getattr` fallback scanning module members) and replace emoji `print` with ASCII or guard encoding — backend currently can't start on a stock Windows console.
4. Unify memory: single `Memory` instance shared by brain + reasoning (or a repository layer); fix `teach:` recall to store/lookup normalized question text.
5. Add a Pydantic request model (`message: str`) to `/chat`; strip/validate length.
6. Restrict CORS to the Vite origin (`http://localhost:5173`); remove `allow_credentials` or scope origins.
7. Add a permission/confirmation layer before `ComputerModule` acts (aligns with the stated vision).
8. Decide the real architecture: the empty `api/`, `services/`, `models/` dirs suggest a planned FastAPI router/service split — either implement it or delete the empty dirs to reduce confusion.
9. Remove or wire dead code (`chart_module`, `decision`, `emotion`, `module_manager`, `database.py`, unused frontend components) — pick one, don't leave both.
10. Move frontend API base URL to `import.meta.env.VITE_API_URL` with a localhost default.

## 11. Development Priorities

**P0 — Make it runnable & safe to commit:** `.gitignore`, UTF-8 requirements, loader crash fix, first git commit.
**P1 — Correctness:** memory unification + teach recall, input validation, CORS lockdown.
**P2 — Real chat brain:** integrate an actual LLM API (the current "brain" is keyword matching; every non-command message returns "I understood: ...").
**P3 — Vision alignment:** auth + per-user memory schema (replace `memory.json` with the already-created SQLite `astra.db` or Postgres), permission-gated automation, tasks/reminders backend, real module implementations.
**P4 — Frontend:** wire nav pages, loading states, env-based API URL, remove dead components.

## 12. Phased Development Plan

- **Phase 0 (hygiene):** gitignore, requirements encoding, loader fix, initial commit, delete stray root `package-lock.json`/`nul` artifacts.
- **Phase 1 (stable core):** validated `/chat`, single memory store, fixed teach/recall, CORS lockdown, backend tests (pytest + fastapi TestClient).
- **Phase 2 (real intelligence):** LLM provider integration behind `brain/`, context window from `ContextManager`, streaming responses.
- **Phase 3 (identity):** user accounts (start with Google OAuth), per-user memory/tasks in SQLite→Postgres, auth middleware on all endpoints.
- **Phase 4 (capabilities):** permission-gated computer/browser automation, reminders/tasks API + UI pages, news/research summarization, YouTube research pipeline.
- **Phase 5 (surface):** voice pipeline (STT/TTS backend or keep Web Speech), desktop (Tauri/Electron) and mobile shells, dashboard data wired to real backend metrics.

---

## 13. Commands to Run (Windows)

**Backend** (CMD or PowerShell — the `PYTHONIOENCODING` workaround is required until B1 is fixed):

```bat
cd /d C:\Users\user\ASTRA-AI\backend
set PYTHONIOENCODING=utf-8
..\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

PowerShell equivalent: `$env:PYTHONIOENCODING="utf-8"` before the uvicorn line.

**Frontend** (separate terminal):

```bat
cd /d C:\Users\user\ASTRA-AI\frontend
npm run dev
```

Then open `http://localhost:5173`. The dashboard talks to `http://127.0.0.1:8000/chat` (hardcoded in `frontend/src/api/chatApi.js`).

*Both servers were left running at the time of this audit.*
