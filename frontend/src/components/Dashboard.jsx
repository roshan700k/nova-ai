import { useEffect, useRef, useState } from "react";
import {
  sendMessage,
  getNotifications,
  devLogin,
  getMe,
  logout,
  getSystemStatus,
  getActivity,
  getMemories,
} from "../api/chatApi";

const MENU = [
  ["⌂", "HOME"],
  ["◉", "CHAT"],
  ["◇", "MEMORY"],
  ["✓", "TASKS"],
  ["✦", "AI TOOLS"],
  ["▧", "MEDIA"],
  ["□", "CALENDAR"],
  ["▤", "NOTES"],
  ["⚙", "SETTINGS"],
];

const TOOLS = [
  ["✎", "AI Writer", "Write anything with AI"],
  ["▣", "Image Generator", "Generate images"],
  ["⌘", "Code Assistant", "Write and debug code"],
  ["♩", "Voice Assistant", "Talk with ASTRA"],
  ["◈", "Research Helper", "Get information and insights"],
];

export default function Dashboard() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { sender: "ASTRA", text: "Hello. I am ASTRA — your personal AI. How can I help?" },
  ]);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [activePage, setActivePage] = useState("HOME");
  const [time, setTime] = useState(new Date());
  const [voices, setVoices] = useState([]);
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState(null);
  const [activity, setActivity] = useState([]);
  const [memories, setMemories] = useState({});
  const [toasts, setToasts] = useState([]);
  const recognitionRef = useRef(null);
  const chatEndRef = useRef(null);

  // ---------- clock ----------
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  // ---------- voices ----------
  useEffect(() => {
    if (!("speechSynthesis" in window)) return;
    const load = () => setVoices(window.speechSynthesis.getVoices());
    load();
    window.speechSynthesis.onvoiceschanged = load;
    return () => (window.speechSynthesis.onvoiceschanged = null);
  }, []);

  // ---------- session + live data ----------
  useEffect(() => {
    getMe().then(setUser).catch(() => {});
    const pollStatus = () => getSystemStatus().then(setStatus).catch(() => setStatus({ status: "offline" }));
    const pollActivity = () => getActivity().then((a) => setActivity(a)).catch(() => {});
    pollStatus();
    pollActivity();
    const t1 = setInterval(pollStatus, 15000);
    const t2 = setInterval(pollActivity, 15000);
    return () => { clearInterval(t1); clearInterval(t2); };
  }, []);

  useEffect(() => {
    if (activePage === "MEMORY") {
      getMemories().then((d) => setMemories(d.memories || {})).catch(() => {});
    }
  }, [activePage]);

  // ---------- proactive notifications ----------
  useEffect(() => {
    const poll = async () => {
      try {
        const notes = await getNotifications();
        notes.forEach((text) => {
          setMessages((p) => [...p, { sender: "ASTRA", text }]);
          pushToast(text);
        });
      } catch { /* backend offline */ }
    };
    const t = setInterval(poll, 30000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activePage]);

  const pushToast = (text) => {
    const id = Date.now();
    setToasts((p) => [...p, { id, text }]);
    setTimeout(() => setToasts((p) => p.filter((x) => x.id !== id)), 8000);
  };

  // ---------- voice ----------
  const getAstraVoice = () => {
    if (!voices.length) return null;
    return (
      voices.find((v) => v.lang.toLowerCase().includes("en-in")) ||
      voices.find((v) => v.lang.toLowerCase().startsWith("en")) ||
      voices[0]
    );
  };

  const speak = (text) => {
    if (!("speechSynthesis" in window) || !text) return;
    window.speechSynthesis.cancel();
    const clean = String(text).replace(/[*#_`]/g, "").replace(/\n+/g, " ").replace(/\s+/g, " ").trim();
    if (!clean) return;
    const u = new SpeechSynthesisUtterance(clean);
    const v = getAstraVoice();
    if (v) u.voice = v;
    u.lang = "en-IN";
    u.rate = 1.05;
    u.pitch = 1.15;
    u.volume = 1;
    u.onstart = () => setSpeaking(true);
    u.onend = () => setSpeaking(false);
    u.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(u);
  };

  const startVoice = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      alert("Voice recognition needs Chrome or Edge.");
      return;
    }
    if (listening) {
      recognitionRef.current?.stop();
      return;
    }
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
    }
    const rec = new SR();
    rec.lang = "en-IN";
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (e) => {
      const result = e.results[0][0].transcript;
      setInput(result);
      handleSend(result);
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    recognitionRef.current = rec;
    rec.start();
    setListening(true);
  };

  useEffect(() => () => {
    recognitionRef.current?.stop?.();
    window.speechSynthesis?.cancel();
  }, []);

  // ---------- chat ----------
  const handleSend = async (textOverride = null) => {
    const message = (textOverride ?? input).trim();
    if (!message) return;
    setMessages((p) => [...p, { sender: "You", text: message }]);
    setInput("");
    try {
      const reply = await sendMessage(message);
      setMessages((p) => [...p, { sender: "ASTRA", text: reply }]);
      speak(reply);
    } catch {
      const err = "I lost connection to my backend — is it running?";
      setMessages((p) => [...p, { sender: "ASTRA", text: err }]);
      speak(err);
    }
  };

  const runQuickAction = (text) => {
    setInput(text);
    handleSend(text);
  };

  const handleLogin = async () => {
    const name = prompt("Your name (dev login):", user?.name || "Roshan");
    if (!name) return;
    try {
      await devLogin(name);
      setUser(await getMe());
      pushToast(`Logged in as ${name}`);
    } catch {
      pushToast("Login failed");
    }
  };

  const handleLogout = async () => {
    await logout();
    setUser(null);
    pushToast("Logged out");
  };

  // ---------- derived ----------
  const fmtTime = (d) =>
    d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const fmtDate = (d) =>
    d.toLocaleDateString([], { weekday: "long", month: "long", day: "numeric", year: "numeric" });
  const uptime = status?.uptime_seconds
    ? `${Math.floor(status.uptime_seconds / 60)}m`
    : "—";
  const online = status && status.status === "online";

  const pageTitle = {
    HOME: "Dashboard",
    CHAT: "Chat",
    MEMORY: "Memory",
    TASKS: "Tasks",
    "AI TOOLS": "AI Tools",
    MEDIA: "Media",
    CALENDAR: "Calendar",
    NOTES: "Notes",
    SETTINGS: "Settings",
  }[activePage];

  // ================= page renderers =================

  function greeting() {
    const h = time.getHours();
    const part = h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
    return `${part}${user ? `, ${user.name}` : ""}.`;
  }

  function subtitle() {
    return {
      HOME: "Your AI assistant is online and ready.",
      CHAT: "Full conversation view.",
      MEMORY: "Everything ASTRA remembers for you.",
      TASKS: "Reminders and to-dos — coming soon.",
      "AI TOOLS": "Quick tools — coming soon.",
      MEDIA: "Videos and media — coming soon.",
      CALENDAR: "Schedule view — coming soon.",
      NOTES: "Quick notes — coming soon.",
      SETTINGS: "System health and account.",
    }[activePage];
  }

  function renderHome() {
    return (
      <div className="dashboard-grid">
        {/* system status — REAL data */}
        <section className="panel stats-panel">
          <div className="section-title"><span>SYSTEM STATUS</span><span className={online ? "live" : "off"}>{online ? "LIVE" : "OFFLINE"}</span></div>
          <div className="status-ring">
            <div className="status-ring-inner">
              <div className="status-small">ASTRA</div>
              <div className="status-number">{online ? "100%" : "—"}</div>
              <div className="status-good">{online ? "SYSTEM GOOD" : "OFFLINE"}</div>
            </div>
          </div>
          <StatusBar label="AI BRAIN" value={status?.llm_provider ? status.llm_provider.toUpperCase() : "OFFLINE"} pct={status?.llm_provider ? 100 : 0} />
          <StatusBar label="MEMORY" value={`${status?.memory_entries ?? 0} entries`} pct={Math.min(100, (status?.memory_entries ?? 0) * 2)} />
          <StatusBar label="UPTIME" value={uptime} pct={Math.min(100, (status?.uptime_seconds ?? 0) / 60)} />
          {status?.issues?.length > 0 && (
            <div className="issue-box">⚠ {status.issues[0]}</div>
          )}
        </section>

        {/* avatar */}
        <section className="panel avatar-panel">
          <div className="avatar-orb"><div className="avatar-face">✦</div></div>
          <div className="avatar-status">
            {listening ? "LISTENING" : speaking ? "SPEAKING" : online ? "READY" : "OFFLINE"}
          </div>
          <div className={`voice-state ${listening || speaking ? "active" : ""}`}>
            {listening ? "🎙 Listening..." : speaking ? "🔊 Speaking..." : "✨ Voice assistant ready"}
          </div>
        </section>

        {/* tools + activity — REAL */}
        <section className="right-panel">
          <div className="section-title"><span>AI TOOLS</span><span>→</span></div>
          {TOOLS.map(([icon, name, desc]) => (
            <div className="tool" key={name} onClick={() => name === "Voice Assistant" ? startVoice() : runQuickAction(`Help me with ${name.toLowerCase()}`)}>
              <div className="tool-icon">{icon}</div>
              <div>
                <div className="tool-name">{name}</div>
                <div className="tool-desc">{desc}</div>
              </div>
            </div>
          ))}

          <div className="activity">
            <div className="section-title"><span>RECENT ACTIVITY</span></div>
            {activity.length === 0 && <div className="empty-note">No activity yet — start chatting.</div>}
            {activity.map((a, i) => (
              <div className="activity-item" key={i}>
                <div className="activity-icon">{iconFor(a.kind)}</div>
                <div className="activity-text">{a.text}</div>
                <div className="activity-time">{a.ago}</div>
              </div>
            ))}
          </div>
        </section>
      </div>
    );
  }

  function renderChat() {
    return (
      <section className="panel chat-page">
        <div className="chat-history">
          {messages.map((m, i) => (
            <div className={`chat-msg ${m.sender === "You" ? "user" : "astra"}`} key={i}>
              <span className="msg-sender">{m.sender === "You" ? "You" : "ASTRA"}</span>
              <span className="msg-text">{m.text}</span>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
      </section>
    );
  }

  function renderMemory() {
    const entries = Object.entries(memories);
    return (
      <section className="panel page-panel">
        <div className="section-title"><span>ASTRA'S MEMORY</span><span>{entries.length} items</span></div>
        {entries.length === 0 && <div className="empty-note">Nothing remembered yet. Tell ASTRA: "remember wifi password is ..."</div>}
        {entries.map(([k, v]) => (
          <div className="memory-item" key={k}>
            <span className="mem-key">{k}</span>
            <span className="mem-val">{String(v)}</span>
          </div>
        ))}
      </section>
    );
  }

  function renderSettings() {
    return (
      <div className="settings-grid">
        <section className="panel page-panel">
          <div className="section-title"><span>SYSTEM</span></div>
          <div className="kv"><span>Status</span><b className={online ? "ok" : "bad"}>{status?.status ?? "unknown"}</b></div>
          <div className="kv"><span>AI Brain</span><b>{status?.llm_provider ?? "offline"} {status?.llm_model ? `(${status.llm_model})` : ""}</b></div>
          <div className="kv"><span>Uptime</span><b>{uptime}</b></div>
          <div className="kv"><span>Memory</span><b>{status?.memory_entries ?? 0} entries / {status?.memory_size_kb ?? 0} KB</b></div>
          <div className="kv"><span>Version</span><b>{status?.version ?? "—"}</b></div>
        </section>
        <section className="panel page-panel">
          <div className="section-title"><span>ACCOUNT</span></div>
          <div className="kv"><span>User</span><b>{user ? `${user.name} (${user.provider})` : "Guest"}</b></div>
          <button className="btn" onClick={user ? handleLogout : handleLogin}>
            {user ? "Log out" : "Dev login"}
          </button>
          <div className="hint">Google OAuth: set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET in .env, then use /auth/google</div>
        </section>
        <section className="panel page-panel">
          <div className="section-title"><span>SELF-CHECK</span></div>
          {(status?.issues ?? []).length === 0 && <div className="empty-note">All systems nominal ✓</div>}
          {(status?.issues ?? []).map((i, k) => <div className="issue-box" key={k}>⚠ {i}</div>)}
        </section>
      </div>
    );
  }

  function renderComingSoon() {
    return (
      <section className="panel page-panel">
        <div className="coming-soon">
          <div className="cs-icon">◌</div>
          <div className="cs-title">{pageTitle}</div>
          <div className="cs-text">This module is on the roadmap. For now, just ask ASTRA — e.g. "remind me tomorrow at 9am" or "make a video about cricket".</div>
        </div>
      </section>
    );
  }

  function iconFor(kind) {
    return { chat: "◉", memory: "◇", build: "⌘", video: "▧" }[kind] || "✦";
  }

  function StatusBar({ label, value, pct }) {
    return (
      <div className="metric">
        <div className="metric-head"><span>{label}</span><span>{value}</span></div>
        <div className="bar"><div className="bar-fill" style={{ width: `${Math.min(100, pct)}%` }} /></div>
      </div>
    );
  }


  // ---------- render ----------
  return (
    <div className="astra-app">
      <style>{CSS}</style>

      {/* toasts */}
      <div className="toasts">
        {toasts.map((t) => (
          <div className="toast" key={t.id}>✦ {t.text}</div>
        ))}
      </div>

      {/* topbar */}
      <header className="topbar">
        <div className="brand">
          <div className="brand-logo">✦</div>
          <div>
            <div className="brand-title">ASTRA</div>
            <div className="brand-subtitle">PERSONAL AI ASSISTANT</div>
          </div>
        </div>
        <div className="top-center">
          <div className="clock">{fmtTime(time)}</div>
          <div className="date">{fmtDate(time)}</div>
        </div>
        <div className="top-right">
          <div className={`online ${online ? "" : "offline"}`}>
            <span className="online-dot"></span>
            {online ? "ONLINE" : "OFFLINE"}
          </div>
          <div className="user-chip" onClick={user ? handleLogout : handleLogin} title={user ? "Click to logout" : "Click to login"}>
            {user ? user.name : "Sign in"}
          </div>
        </div>
      </header>

      <div className="layout">
        {/* sidebar */}
        <aside className="sidebar">
          {MENU.map(([icon, label]) => (
            <div
              key={label}
              className={"nav-item " + (activePage === label ? "active" : "")}
              onClick={() => setActivePage(label)}
            >
              <span className="nav-icon">{icon}</span>
              <span className="nav-label">{label}</span>
            </div>
          ))}
          <div className="profile">
            <div className="profile-avatar">{user ? user.name[0].toUpperCase() : "✦"}</div>
            <div className="profile-name">{user ? user.name : "Guest"}</div>
            <div className="profile-status">● {online ? "ASTRA READY" : "ASTRA OFFLINE"}</div>
          </div>
        </aside>

        {/* main */}
        <main className="main">
          <div className="welcome">
            <h1>{greeting()}</h1>
            <p>{pageTitle} — {subtitle()}</p>
          </div>

          {activePage === "HOME" && renderHome()}
          {activePage === "CHAT" && renderChat()}
          {activePage === "MEMORY" && renderMemory()}
          {activePage === "SETTINGS" && renderSettings()}
          {["TASKS", "CALENDAR", "NOTES", "MEDIA", "AI TOOLS"].includes(activePage) && renderComingSoon()}
        </main>
      </div>

      {/* quick actions + chat bar */}
      {activePage !== "CHAT" && (
        <div className="quick-actions">
          <button className="quick-button" onClick={() => runQuickAction("Tell me something interesting")}>✦ Ask ASTRA</button>
          <button className="quick-button" onClick={() => runQuickAction("Give me today's tasks")}>✓ Tasks</button>
          <button className="quick-button" onClick={() => runQuickAction("Open my calendar")}>□ Calendar</button>
          <button className="quick-button" onClick={() => runQuickAction("Help me with coding")}>⌘ Coding</button>
        </div>
      )}

      <div className="chat-bar">
        <input
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder={listening ? "Listening..." : "Talk to ASTRA..."}
        />
        <button
          className={"voice-button " + (listening ? "listening" : speaking ? "speaking" : "")}
          onClick={startVoice}
          title={listening ? "Stop" : "Voice"}
        >
          {listening ? "⏹" : speaking ? "🔊" : "🎙"}
        </button>
        <button className="send-button" onClick={handleSend} title="Send">➤</button>
      </div>
    </div>
  );

}

// ================= CSS =================
const CSS = `
* { box-sizing: border-box; }
html, body, #root { margin: 0; width: 100%; min-height: 100%; background: #03010b; }
body { font-family: Arial, Helvetica, sans-serif; }
button, input { font-family: inherit; }
button { outline: none; }

.astra-app { min-height: 100vh; color: #f8f5ff; position: relative; overflow: hidden;
  background:
    radial-gradient(circle at 50% 42%, rgba(132,0,255,0.18), transparent 30%),
    radial-gradient(circle at 82% 20%, rgba(0,120,255,0.10), transparent 25%),
    linear-gradient(135deg, #03010b 0%, #090314 45%, #020107 100%); }
.astra-app::before { content:""; position:absolute; inset:0; pointer-events:none; opacity:.18;
  background-image: linear-gradient(rgba(180,70,255,.12) 1px, transparent 1px), linear-gradient(90deg, rgba(180,70,255,.12) 1px, transparent 1px);
  background-size: 50px 50px; }

/* toasts */
.toasts { position: fixed; top: 90px; right: 20px; z-index: 100; display: flex; flex-direction: column; gap: 8px; }
.toast { background: rgba(30,10,55,.95); border: 1px solid rgba(200,100,255,.5); border-radius: 12px;
  padding: 10px 16px; font-size: 13px; color: #e8d5ff; box-shadow: 0 0 20px rgba(160,50,255,.3);
  animation: slidein .3s ease; max-width: 320px; }
@keyframes slidein { from { transform: translateX(30px); opacity: 0; } to { transform: none; opacity: 1; } }

.topbar { height: 82px; display: flex; align-items: center; justify-content: space-between; padding: 0 28px;
  border-bottom: 1px solid rgba(180,80,255,.28); background: rgba(5,2,14,.82); backdrop-filter: blur(16px); position: relative; z-index: 5; }
.brand { display: flex; align-items: center; gap: 14px; }
.brand-logo { width: 48px; height: 48px; display: grid; place-items: center; border: 1px solid #b55cff; color: #d995ff; font-size: 27px; border-radius: 14px; box-shadow: 0 0 25px rgba(183,80,255,.45); }
.brand-title { font-size: 25px; font-weight: 700; letter-spacing: 2px; color: #f2d8ff; }
.brand-subtitle { font-size: 10px; color: #9b8ba9; letter-spacing: 1.5px; margin-top: 3px; }
.top-center { text-align: center; }
.clock { font-size: 22px; letter-spacing: 2px; color: #d9c5e7; }
.date { font-size: 11px; color: #81758e; margin-top: 3px; }
.top-right { display: flex; align-items: center; gap: 14px; }
.online { color: #67ff9a; font-size: 12px; letter-spacing: 1px; }
.online.offline { color: #ff6b6b; }
.online-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #48ff89; box-shadow: 0 0 12px #48ff89; margin-right: 6px; }
.online.offline .online-dot { background: #ff6b6b; box-shadow: 0 0 12px #ff6b6b; }
.user-chip { font-size: 12px; color: #cbb8e0; border: 1px solid rgba(180,80,255,.35); border-radius: 16px; padding: 6px 14px; cursor: pointer; }
.user-chip:hover { background: rgba(160,55,255,.15); }

.layout { display: grid; grid-template-columns: 220px minmax(0,1fr); min-height: calc(100vh - 82px); position: relative; z-index: 2; }
.sidebar { border-right: 1px solid rgba(180,80,255,.22); background: rgba(5,2,13,.72); padding: 22px 12px; }
.nav-item { height: 52px; display: flex; align-items: center; gap: 15px; padding: 0 18px; margin-bottom: 8px; border-radius: 12px; color: #aaa0b6; cursor: pointer; transition: .2s; }
.nav-item:hover { color: white; background: rgba(160,55,255,.12); }
.nav-item.active { color: white; background: linear-gradient(90deg, rgba(158,55,255,.35), rgba(72,21,100,.15)); border: 1px solid rgba(196,92,255,.5); box-shadow: 0 0 25px rgba(180,70,255,.18); }
.nav-icon { font-size: 21px; width: 24px; text-align: center; }
.profile { margin-top: 28px; padding: 18px; border: 1px solid rgba(180,80,255,.3); border-radius: 18px; background: rgba(30,10,50,.5); }
.profile-avatar { width: 54px; height: 54px; border-radius: 50%; display: grid; place-items: center; margin-bottom: 10px; background: radial-gradient(circle, #ff9bf8, #7524c9 60%, #18042b); box-shadow: 0 0 25px rgba(211,74,255,.55); font-size: 24px; font-weight: 700; }
.profile-name { font-weight: 700; }
.profile-status { color: #6dff9a; font-size: 12px; margin-top: 5px; }

.main { padding: 25px; min-width: 0; overflow-y: auto; padding-bottom: 190px; }
.welcome { margin-bottom: 20px; }
.welcome h1 { margin: 0; font-size: 23px; color: #f3d9ff; }
.welcome p { margin: 7px 0 0; color: #887c98; }

.dashboard-grid { display: grid; grid-template-columns: 1fr 1.35fr 1fr; gap: 18px; align-items: stretch; }
.panel { border: 1px solid rgba(178,70,255,.27); border-radius: 18px; background: rgba(13,6,26,.7); box-shadow: inset 0 0 30px rgba(140,45,255,.04), 0 0 25px rgba(130,40,255,.06); }
.section-title { display: flex; justify-content: space-between; color: #e6d7ed; font-size: 13px; letter-spacing: 1px; margin-bottom: 12px; }
.section-title .live { color: #6dff9a; }
.section-title .off { color: #ff6b6b; }

.stats-panel { padding: 20px; }
.status-ring { width: 160px; height: 160px; border-radius: 50%; margin: 10px auto 25px; display: grid; place-items: center; border: 2px solid #8d42ff; box-shadow: 0 0 20px rgba(132,51,255,.8), inset 0 0 30px rgba(132,51,255,.25); }
.status-ring-inner { text-align: center; }
.status-small { color: #8f82a1; font-size: 10px; letter-spacing: 1px; }
.status-number { font-size: 30px; font-weight: 700; color: #dcb8ff; margin: 7px 0; }
.status-good { color: #63ffae; font-size: 11px; }
.metric { margin: 15px 0; }
.metric-head { display: flex; justify-content: space-between; color: #9c91a7; font-size: 12px; margin-bottom: 7px; }
.bar { height: 5px; background: #21182b; border-radius: 5px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 5px; background: linear-gradient(90deg, #633cff, #e74cff); box-shadow: 0 0 12px #a73fff; transition: width .6s; }
.issue-box { margin-top: 14px; padding: 10px 12px; border: 1px solid rgba(255,180,80,.4); border-radius: 10px; color: #ffcf9e; font-size: 12px; background: rgba(255,140,0,.08); }

.avatar-panel { min-height: 570px; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; overflow: hidden; }
.avatar-orb { width: 280px; height: 280px; border-radius: 50%; display: grid; place-items: center; position: relative; border: 2px solid rgba(206,96,255,.7); background: radial-gradient(circle at 50% 45%, #ff78ed 0%, #9a27dd 35%, #25053d 70%, #09020f 100%); box-shadow: 0 0 35px rgba(229,63,255,.9), 0 0 90px rgba(120,35,255,.5), inset 0 0 50px rgba(255,100,255,.35); animation: breathe 3s ease-in-out infinite; }
.avatar-face { font-size: 92px; filter: drop-shadow(0 0 20px rgba(255,255,255,.5)); }
.avatar-status { position: absolute; bottom: 90px; color: #f0cfff; letter-spacing: 5px; font-size: 13px; }
.voice-state { margin-top: 28px; padding: 10px 20px; border-radius: 20px; border: 1px solid rgba(208,87,255,.35); background: rgba(26,8,44,.75); color: #bfaec9; font-size: 12px; }
.voice-state.active { color: #ff8fff; box-shadow: 0 0 25px rgba(255,60,255,.35); }
@keyframes breathe { 0%,100% { transform: scale(1); } 50% { transform: scale(1.035); } }

.right-panel { padding: 20px; border-left: 1px solid rgba(180,80,255,.22); background: rgba(5,2,13,.72); overflow-y: auto; }
.tool { display: flex; gap: 13px; padding: 13px; margin-bottom: 8px; border: 1px solid rgba(180,80,255,.16); border-radius: 12px; cursor: pointer; transition: .2s; }
.tool:hover { border-color: rgba(210,90,255,.5); background: rgba(180,60,255,.1); transform: translateX(-3px); }
.tool-icon { width: 36px; height: 36px; display: grid; place-items: center; border-radius: 10px; background: rgba(126,47,255,.2); color: #d49aff; font-size: 18px; }
.tool-name { font-size: 13px; color: #d7cbdc; }
.tool-desc { color: #756a7e; font-size: 10px; margin-top: 4px; }
.activity { margin-top: 25px; }
.activity-item { display: flex; gap: 10px; align-items: center; padding: 11px 0; border-bottom: 1px solid rgba(255,255,255,.05); }
.activity-icon { color: #b568ff; }
.activity-text { flex: 1; font-size: 11px; color: #b7adbd; }
.activity-time { color: #665d6c; font-size: 9px; }
.empty-note { color: #665d6c; font-size: 12px; padding: 12px 0; }

.chat-bar { position: fixed; left: 250px; right: 30px; bottom: 20px; z-index: 10; display: flex; gap: 10px; padding: 8px; border: 1px solid rgba(201,78,255,.5); border-radius: 18px; background: rgba(12,4,23,.92); box-shadow: 0 0 35px rgba(166,55,255,.22); backdrop-filter: blur(15px); }
.chat-input { flex: 1; min-width: 0; border: 0; outline: 0; color: white; background: transparent; padding: 14px; font-size: 14px; }
.chat-input::placeholder { color: #756a7e; }
.voice-button, .send-button { width: 48px; height: 48px; border: 0; border-radius: 50%; color: white; cursor: pointer; font-size: 20px; }
.voice-button { background: rgba(115,38,200,.5); border: 1px solid rgba(205,92,255,.4); }
.voice-button.listening { background: #df36db; box-shadow: 0 0 25px rgba(255,55,225,.8); animation: pulse 1s infinite; }
.voice-button.speaking { background: rgba(255,65,205,.65); box-shadow: 0 0 25px rgba(255,60,220,.7); }
.send-button { background: linear-gradient(135deg, #8e35ff, #d02fff); box-shadow: 0 0 20px rgba(206,48,255,.5); }
@keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.1); } }

.quick-actions { position: fixed; left: 250px; right: 30px; bottom: 92px; z-index: 9; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
.quick-button { padding: 11px 18px; border-radius: 10px; color: #bbaec5; background: rgba(23,8,37,.82); border: 1px solid rgba(166,71,255,.24); cursor: pointer; transition: .2s; }
.quick-button:hover { color: white; border-color: rgba(210,90,255,.55); background: rgba(180,60,255,.15); }

.chat-page { min-height: 60vh; display: flex; flex-direction: column; }
.chat-history { flex: 1; overflow-y: auto; padding: 10px 4px; max-height: calc(100vh - 320px); }
.chat-msg { margin-bottom: 14px; font-size: 14px; line-height: 1.5; display: flex; gap: 10px; }
.msg-sender { font-weight: 700; min-width: 52px; }
.chat-msg.astra .msg-sender { color: #d37aff; }
.chat-msg.user .msg-sender { color: #8fd0ff; }
.msg-text { flex: 1; color: #e8e0f0; white-space: pre-wrap; }

.page-panel { padding: 22px; max-width: 720px; }
.memory-item { display: flex; justify-content: space-between; gap: 16px; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,.05); }
.mem-key { color: #d49aff; font-weight: 600; }
.mem-val { color: #b7adbd; text-align: right; word-break: break-word; }

.settings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; }
.kv { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,.05); color: #9c91a7; font-size: 13px; }
.kv b { color: #e8d5ff; font-weight: 600; }
.kv b.ok { color: #63ffae; }
.kv b.bad { color: #ff6b6b; }
.btn { margin-top: 14px; padding: 10px 20px; border-radius: 10px; border: 1px solid rgba(200,100,255,.5); background: rgba(140,50,255,.2); color: #f0d8ff; cursor: pointer; }
.btn:hover { background: rgba(160,60,255,.35); }
.hint { margin-top: 12px; font-size: 11px; color: #665d6c; }

.coming-soon { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; color: #887c98; }
.cs-icon { font-size: 48px; color: #5a3a7a; margin-bottom: 14px; }
.cs-title { font-size: 20px; color: #d9c5e7; margin-bottom: 8px; }
.cs-text { font-size: 13px; max-width: 380px; text-align: center; line-height: 1.6; }

@media (max-width: 1100px) {
  .layout { grid-template-columns: 75px minmax(0,1fr); }
  .right-panel { display: none; }
  .nav-item { justify-content: center; padding: 0; }
  .nav-label, .profile { display: none; }
  .chat-bar, .quick-actions { left: 100px; right: 20px; }
}
@media (max-width: 700px) {
  .topbar { height: 65px; padding: 0 12px; }
  .brand-title { font-size: 18px; }
  .brand-subtitle, .top-center { display: none; }
  .layout { grid-template-columns: 55px 1fr; }
  .main { padding: 15px; padding-bottom: 190px; }
  .dashboard-grid { grid-template-columns: 1fr; }
  .avatar-panel { min-height: 380px; }
  .avatar-orb { width: 200px; height: 200px; }
  .avatar-face { font-size: 64px; }
  .chat-bar { left: 65px; right: 10px; bottom: 10px; }
  .quick-actions { left: 65px; right: 10px; bottom: 80px; }
  .quick-button { padding: 8px 10px; font-size: 11px; }
  .dashboard-grid { grid-template-columns: 1fr; }
}
`;
