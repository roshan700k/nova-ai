# ASTRA AI — Phase-by-Phase Command Sheet

Run these in order. Each phase lists: **what you run now**, **what gets built**, **how to verify**.

> Convention: `ASTRA` = repo root `C:\Users\user\ASTRA-AI`
> Backend commands run from `backend\`, frontend from `frontend\`.

---

## PHASE 0 — Startup, encoding & security hygiene (do first, ~1 session)

**Goal:** backend starts on a normal Windows console, repo is safe to commit.

Commands you run:
```bat
cd /d C:\Users\user\ASTRA-AI

:: 1. Create root .gitignore (venv, node_modules, *.db, memory.json, logs, .env)
:: 2. Re-save requirements.txt as UTF-8
cd backend
..\venv\Scripts\python.exe -m pip install -r ..\requirements.txt --force-reinstall

:: 3. First commit
cd /d C:\Users\user\ASTRA-AI
git add -A
git commit -m "Initial commit: ASTRA AI audit-clean baseline"
```

Code fixes needed (Devin does these):
- Fix `backend/modules/module_loader.py` emoji print crash + `YouTubeModule` name bug
- Restrict CORS in `backend/main.py` to `http://localhost:5173`
- Add `.gitignore`, delete stray root `package-lock.json`

Verify:
```bat
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --port 8000
:: (no PYTHONIOENCODING needed anymore)
curl http://127.0.0.1:8000/
```

---

## PHASE 1 — Reliable chat & unified memory

**Goal:** one memory store, `teach:` actually works, no 500s on bad input.

Commands:
```bat
cd /d C:\Users\user\ASTRA-AI\backend
..\venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload
```

Test commands (PowerShell):
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method Post -ContentType "application/json" -Body '{"message":"remember favcolor=purple"}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method Post -ContentType "application/json" -Body '{"message":"what is favcolor"}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method Post -ContentType "application/json" -Body '{"message":"teach: capital of france = paris"}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method Post -ContentType "application/json" -Body '{"message":"what is the capital of france"}'
```

Verify: last call must return `paris`, and `memory.json` must keep BOTH keys (no data loss).

---

## PHASE 2 — Connect a real AI model

**Goal:** ASTRA actually answers questions instead of "I understood: ...".

You need an API key (pick one): Google Gemini (free tier: `https://aistudio.google.com`), Groq (free: `https://console.groq.com`), or OpenAI.

Commands:
```bat
cd /d C:\Users\user\ASTRA-AI
:: add key to .env — NEVER commit .env
notepad .env

cd backend
..\venv\Scripts\python.exe -m pip install httpx
..\venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload
```

`.env` gets: `GEMINI_API_KEY=your_key_here` (or `GROQ_API_KEY` / `OPENAI_API_KEY`).

Verify: ask "what is the capital of Australia?" → real answer, not a keyword stub.

---

## PHASE 2B — Companion Core: emotion, proactivity, self-awareness

**Goal:** ASTRA stops feeling like software and starts feeling like a friend. This is the soul of the project — everything else is plumbing.

### What gets built

- **Emotional companion mode** — ASTRA remembers your moods (from chat + Phase 4B face reading), adapts its tone, asks how your day was, celebrates your wins, notices when you're quiet or sad. Goal: "I feel I'm talking to my friend, not an AI."
- **Proactive behavior** — ASTRA makes its own decisions and speaks first: morning briefing ("good morning, you have 2 tasks today"), reminds without being asked, warns about problems, suggests things ("you seem stuck on X — want help?"). Not just reactive replies.
- **Self-awareness / internal issue reporting** — ASTRA monitors its own health: "my memory file is getting full", "the YouTube API quota is almost over", "I couldn't reach the AI model — running on backup brain". It tells YOU when something is wrong inside itself, in plain language.
- **Transparent builder** — when ASTRA writes code (Phase 5 builder), it shows its work: "I'll create 3 files — app.py for the logic, style.css, index.html — want to see them before I run it?" Code visible in dashboard, step-by-step narration.

### How it's implemented

- `brain/proactive.py` — scheduler + decision rules for when ASTRA initiates conversation
- `brain/self_check.py` — health checks (API keys valid, memory size, quota, disk space, services running) run periodically; issues pushed to chat as ASTRA-initiated messages
- `brain/companion.py` — emotional state model: tracks your mood over time, picks tone/personality mode (Friendly / Professional / Concerned / Celebrating — already half-built in `personality.py`)
- Dashboard: "ASTRA is thinking..." presence indicator + notification toasts for proactive messages

### Commands once built

```bat
cd /d C:\Users\user\ASTRA-AI\backend
..\venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload
```

### Self-modifying UI (ASTRA redesigns itself)

ASTRA can edit its own dashboard code — the frontend is just files it can read/write:

- You say: *"change my dashboard to minimal dark mode"* or *"make the avatar bigger"* or *"add a weather widget"*
- ASTRA's builder edits `frontend/src/components/*.jsx` + CSS → Vite hot-reloads → new UI live in seconds
- It shows you a diff/preview first and asks before applying big changes

**Safety rails (mandatory):**
- Every self-edit auto-commits to git first → one-command rollback ("ASTRA, undo that")
- Cosmetic changes (colors, layout, sizes) → auto-apply; structural changes (new pages, deleting features) → always ask first
- ASTRA narrates what it changed in plain words: "I made the sidebar collapsible and switched to dark purple"

Verify:
- Don't message ASTRA for a while → it sends a check-in on its own
- Temporarily break the Gemini key → ASTRA messages you: "I can't reach my AI brain right now, using offline mode"
- Ask it to build something → it narrates each step and shows the code before running

---

## PHASE 3 — Multi-user Google login & private data

**Goal:** accounts, per-user memory, privacy.

Setup (one time, Google Cloud Console `https://console.cloud.google.com`):
1. Create project → enable "Google Identity Services" / OAuth client ID (Web)
2. Authorized redirect URI: `http://localhost:8000/auth/google/callback`
3. Put `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` in `.env`

Commands:
```bat
cd /d C:\Users\user\ASTRA-AI\backend
..\venv\Scripts\python.exe -m pip install itsdangerous httpx
..\venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload
```

Frontend:
```bat
cd /d C:\Users\user\ASTRA-AI\frontend
npm run dev
```

Verify: log in with Google → send "remember my bike = hornet" → log out, log in as a second account → ask "what is my bike" → must say it doesn't know.

---

## PHASE 4 — Voice assistant

**Goal:** push-to-talk voice in, natural voice out (upgrade from browser Web Speech).

Option A (free, fast): keep browser SpeechRecognition + add backend TTS.
```bat
cd /d C:\Users\user\ASTRA-AI\backend
..\venv\Scripts\python.exe -m pip install gtts
```

Option B (better): Groq Whisper (free STT) + ElevenLabs/Gemini TTS.
```bat
..\venv\Scripts\python.exe -m pip install groq
```

Frontend stays `npm run dev`. Verify: hold mic button → speak → ASTRA answers aloud.

---

## PHASE 4B — Eyes, Ears & Gesture (camera + presence)

**Goal:** ASTRA sees you, senses your mood, and you control the PC with finger gestures — Minority Report style, but free and local.

### What gets built

- **Face/presence detection** — webcam detects you, knows when you sit down/leave, greets you by name
- **Emotion sensing** — reads your facial expression (happy/sad/focused) → ASTRA adapts tone ("you look tired — want a break summary?")
- **Finger/gesture control** — MediaPipe hand tracking: point to move cursor, pinch to click, swipe for volume/scroll, peace-sign to push-to-talk
- **Gesture commands** — custom poses mapped to ASTRA commands (e.g., OK sign → "summarize this page")

### Stack (all free, runs locally)

```bat
cd /d C:\Users\user\ASTRA-AI\backend
..\venv\Scripts\python.exe -m pip install opencv-python mediapipe
```

- `opencv-python` — webcam capture
- `mediapipe` — hand landmarks + face mesh (Google's free library, runs on CPU)
- Optional later: eye-gaze tracking for "look at what you want ASTRA to see"

### Privacy rules (built in)

- Camera feeds processed **locally only** — frames never uploaded anywhere
- Physical shutter rule: ASTRA only watches when you explicitly enable "presence mode" (dashboard toggle)
- No recording/storage of video — only transient landmark data (coordinates), discarded each frame

### Commands once built

```bat
cd /d C:\Users\user\ASTRA-AI\backend
..\venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload
:: plus the camera service:
..\venv\Scripts\python.exe -m vision.camera_service
```

Verify: enable presence mode → wave at camera → ASTRA greets; smile → mood logged; point-and-pinch → cursor moves and clicks.

---

## PHASE 5 — Browser & computer actions (with permission)

**Goal:** ASTRA can act on your PC only after you approve each action.

Commands:
```bat
cd /d C:\Users\user\ASTRA-AI\backend
..\venv\Scripts\python.exe -m pip install playwright pyautogui
..\venv\Scripts\python.exe -m playwright install chromium
```

Flow: user says "open youtube and find lo-fi" → ASTRA shows approval card in dashboard → you click Allow → action runs → logged.

Verify: ask ASTRA to open a site → dashboard shows permission prompt → only executes on approve.

---

## PHASE 6 — YouTube Channel Manager & Creator Engine

**Goal:** ASTRA runs your YouTube channel end-to-end — research, ideas, scripts, video creation, upload, scheduling, analytics. You just say "make me a video about X" or "how is my channel doing".

### 6a. Channel connection (one-time setup)

1. Google Cloud Console → enable **YouTube Data API v3**
2. OAuth consent screen → add scope `youtube.upload` + `yt-analytics.readonly`
3. OAuth client (Desktop app type) → download `client_secret.json` into `backend/`
4. First run opens browser → you approve once → token saved locally

Commands:
```bat
cd /d C:\Users\user\ASTRA-AI\backend
..\venv\Scripts\python.exe -m pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib moviepy
```

`.env` additions: `YT_CLIENT_SECRET_FILE=client_secret.json`

### 6b. What ASTRA can then do on command

| You say | What ASTRA does |
|---|---|
| "make a video about cricket highlights" | researches topic → writes script → generates video → returns preview for approval |
| "make 5 videos about space tech" | batch pipeline: 5 scripts → 5 videos → drafts all metadata |
| "upload the cricket video" | uploads to your channel (private by default → you flip to public) |
| "schedule it for Friday 6pm" | sets publishAt via API |
| "how are my videos performing" | pulls Analytics API: views, watch time, CTR, subs |
| "what should I make next" | analyzes your top videos + trending → recommends topics |

### 6c. Video generation — pick your engine

- **Free/template engine (MoviePy):** script → AI voiceover (gTTS/Edge-TTS) → stock footage (Pexels API, free) → subtitles → 1080p MP4. Good for: commentary, listicles, slideshows, shorts. Cost: ~₹0.
- **AI video engine (paid APIs):** text-to-video via Runway / Pika / Veo / Kling APIs for cinematic b-roll. Cost: ~₹5–50 per video depending on length/quality.
- **Avatar/talking-head (HeyGen/Synthesia API):** realistic presenter videos. Cost: subscription (~$30+/mo).
- **Remotion (code-based):** React-based programmatic videos — great for data viz, captions, branded templates. Free, needs Node render step.

Recommended start: **MoviePy + Pexels + Edge-TTS** (free), add a paid AI-video API later for premium content.

### 6d. Safety rules built in

- Videos upload as **private**; nothing goes public without your explicit approval in chat/dashboard.
- Channel actions (upload, delete, schedule) require a confirmation step every time.
- API quota tracked; batch jobs queue instead of hitting limits.

### 6e. Commands once built

```bat
cd /d C:\Users\user\ASTRA-AI\backend
..\venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload
```

Then just talk to ASTRA:
- "ASTRA, research today's trending AI news and make a 60-second short about it"
- "ASTRA, make 5 video ideas about space tech, score them, make the top 2"
- "ASTRA, upload video 2 as private and schedule it Friday 6pm"
- "ASTRA, show my channel analytics for last 28 days"

Honest limit: ASTRA handles the production pipeline — topic research, scripts, voiceover, editing, metadata, upload, scheduling, analytics. Virality and revenue still depend on niche, consistency, and content quality; no tool can guarantee either.

---

## PHASE 7 — Testing & deployment

**Goal:** tests exist, app deployable.

Commands:
```bat
cd /d C:\Users\user\ASTRA-AI\backend
..\venv\Scripts\python.exe -m pip install pytest httpx
..\venv\Scripts\python.exe -m pytest

cd /d C:\Users\user\ASTRA-AI\frontend
npm run build
npm run lint
```

Deploy options:
- Backend → Render/Railway/Fly.io (`Dockerfile` or `uvicorn main:app`)
- Frontend → Vercel/Netlify (`npm run build` → `dist/`)
- DB → Supabase/Neon Postgres when moving off SQLite

Verify: `pytest` green, `npm run build` clean, deployed URL loads and chats.

---

## Daily run commands (after setup)

```bat
:: Terminal 1 — backend
cd /d C:\Users\user\ASTRA-AI\backend
..\venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload

:: Terminal 2 — frontend
cd /d C:\Users\user\ASTRA-AI\frontend
npm run dev
```

Open `http://localhost:5173`. Say "ASTRA, ..." or type — everything routes through `POST /chat`.

## Example "commands" ASTRA will understand (by phase)

| You say | Phase | What happens |
|---|---|---|
| "remember wifi password is X" | 1 | saved to your private memory |
| "what is my birthday" | 1 | recalled |
| "summarize today's AI news" | 2+6 | real web research + LLM summary |
| "remind me tomorrow at 9am to call mom" | 6 | task/reminder created |
| "ASTRA can you see me" | 4B | presence mode: face + mood detection |
| "control my PC with gestures" | 4B | finger tracking → mouse/commands |
| "open youtube and play lofi" | 5 | permission prompt → opens |
| "make 5 video scripts about cricket" | 6 | research + scripts + metadata |
| "make a video about X and upload it" | 6 | full pipeline → private upload, you approve publish |
| "how are my videos performing" | 6 | channel analytics report |
| "how are you feeling ASTRA" | 2B | real mood check — it answers from its own state |
| "what's wrong with you" | 2B | self-diagnostic report in plain language |
| "build me a to-do app" | 5+2B | narrates steps, shows code, asks before running |
| "change your dashboard to dark mode" | 5+2B | ASTRA edits its own UI files, hot-reloads, shows diff |
| "ASTRA undo that" | 5+2B | git rollback of its own last self-edit |
| "log me out" / "show my data" | 3 | account control |

**Never supported:** bypassing passwords/locks on devices you don't own, or any "crack this passcode" request — ASTRA will refuse and offer legit recovery steps instead.
