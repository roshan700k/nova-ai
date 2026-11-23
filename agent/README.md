# NOVA Local Agent

Runs on YOUR computer so NOVA can perform permitted actions locally
(open apps, websites, list/read files in your home folder).

The cloud backend can never reach your PC directly — this agent polls
it every few seconds for queued commands and reports results back.

## Setup (one time)

1. Open NOVA in your browser and **sign in**.
2. Chat menu **(+)** → **PC Agent** → copy the token shown.
3. Paste the token into `agent/config.json` → `"token": "..."`
4. Run:

   ```
   python nova_agent.py
   ```

   Keep the window open while you want NOVA to control this PC.

## Commands you can give NOVA in chat

- `pc open notepad` / `pc open chrome` / `pc open spotify`
- `pc open youtube lofi study` / `pc google best laptops`
- `pc open https://example.com`
- `pc files in downloads` / `pc files in documents`
- `pc read myfile.txt` (text files in your home folder only)
- `pc status`

## Safety

- No shell/exec action exists — commands cannot be injected.
- File access is limited to your user folder; only common text
  extensions can be read; files over 200 KB are refused.
- The token only lets the agent poll *your* command queue.
  Re-registering (＋ → PC Agent) rotates it instantly.
