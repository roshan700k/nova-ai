import { useEffect, useRef, useState } from "react";
import {
  sendMessage,
  getNotifications,
  devLogin,
  getMe,
  logout,
  getSystemStatus,
  getMemories,
} from "../api/chatApi";
import AdminPanel from "./AdminPanel";

const MENU = [
  ["◆", "HOME"],
  ["▣", "MEMORY"],
  ["◇", "TASKS"],
  ["◈", "AI TOOLS"],
  ["▧", "MEDIA"],
  ["□", "CALENDAR"],
  ["▤", "NOTES"],
  ["◎", "SETTINGS"],
  ["⬡", "ADMIN"],
];

export default function Dashboard() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { sender: "NOVA", text: "Hello. I am NOVA — your personal AI. How can I help?" },
  ]);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [activePage, setActivePage] = useState("HOME");
  const [time, setTime] = useState(new Date());
  const [voices, setVoices] = useState([]);
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState(null);
  const [memories, setMemories] = useState({});
  const [toasts, setToasts] = useState([]);
  const [chatHistory, setChatHistory] = useState(["Plan my day", "Write code", "Research topic"]);
  const [pinnedChats, setPinnedChats] = useState(["Daily brief", "Project ideas"]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loading, setLoading] = useState(false);
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
    pollStatus();
    const t1 = setInterval(pollStatus, 15000);
    return () => { clearInterval(t1); };
  }, []);

  useEffect(() => {
    if (activePage === "MEMORY") {
      getMemories().then((d) => setMemories(d.memories || {})).catch(() => {});
    }
  }, [activePage]);

  const pushToast = (text) => {
    const id = Date.now();
    setToasts((p) => [...p, { id, text }]);
    setTimeout(() => setToasts((p) => p.filter((x) => x.id !== id)), 8000);
  };

  // ---------- proactive notifications ----------
  useEffect(() => {
    const poll = async () => {
      try {
        const notes = await getNotifications();
        notes.forEach((text) => {
          setMessages((p) => [...p, { sender: "NOVA", text }]);
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
    if (!message || loading) return;
    setMessages((p) => [...p, { sender: "You", text: message }]);
    setInput("");
    setLoading(true);
    setActivePage("CHAT");
    try {
      const reply = await sendMessage(message);
      setMessages((p) => [...p, { sender: "NOVA", text: reply }]);
      speak(reply);
    } catch {
      const err = "I lost connection to my backend — is it running?";
      setMessages((p) => [...p, { sender: "NOVA", text: err }]);
      speak(err);
    } finally {
      setLoading(false);
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

  const newChat = () => {
    setMessages([{ sender: "NOVA", text: "Ready when you are." }]);
    setActivePage("HOME");
  };

  const selectChat = (title) => {
    setMessages([{ sender: "NOVA", text: `Resuming: ${title}` }]);
    setActivePage("CHAT");
  };

  const unpinChat = (title) => {
    setPinnedChats(pinnedChats.filter((t) => t !== title));
    pushToast(`Unpinned: ${title}`);
  };

  const deleteChat = (title) => {
    setChatHistory(chatHistory.filter((t) => t !== title));
    pushToast(`Deleted: ${title}`);
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
    ADMIN: "Admin Panel",
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
      MEMORY: "Everything NOVA remembers for you.",
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
      <div className="home-full">
        <div className="home-hero">
          <div className="avatar-orb-large">
            <div className="avatar-face-large">
              <div className="avatar-ring-outer"></div>
              <div className="avatar-ring-inner"></div>
              <div className="avatar-dot"></div>
            </div>
          </div>
          <div className="home-status">
            {listening ? "LISTENING" : speaking ? "SPEAKING" : online ? "READY" : "OFFLINE"}
          </div>
          <div className={`voice-state ${listening || speaking ? "active" : ""}`}>
            {listening ? "Listening..." : speaking ? "Speaking..." : "◆ Voice assistant ready"}
          </div>
        </div>
        <div className="home-quick">
          <button className="quick-chip" onClick={() => runQuickAction("Tell me something interesting")}>◆ Ask NOVA</button>
          <button className="quick-chip" onClick={() => runQuickAction("Give me today's tasks")}>◇ Tasks</button>
          <button className="quick-chip" onClick={() => runQuickAction("Open my calendar")}>□ Calendar</button>
          <button className="quick-chip" onClick={() => runQuickAction("Help me with coding")}>⌘ Coding</button>
        </div>
      </div>
    );
  }

  function renderChat() {
    const isEmpty = messages.length <= 1;
    return (
      <section className="panel chat-page">
        {isEmpty ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">◆</div>
            <div className="chat-empty-title">Ready when you are.</div>
          </div>
        ) : (
          <div className="chat-history">
            {messages.map((m, i) => (
              <div className={`chat-msg ${m.sender === "You" ? "user" : "nova"}`} key={i}>
                <span className="msg-sender">{m.sender === "You" ? "You" : "NOVA"}</span>
                <span className="msg-text">{m.text}</span>
              </div>
            ))}
            {loading && (
              <div className="chat-msg nova">
                <span className="msg-sender">NOVA</span>
                <span className="msg-text"><div className="loading-spinner" style={{ width: 20, height: 20, borderWidth: 2 }} /></span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
        )}
      </section>
    );
  }

  function renderMemory() {
    const entries = Object.entries(memories);
    return (
      <section className="panel page-panel">
        <div className="section-title"><span>NOVA'S MEMORY</span><span>{entries.length} items</span></div>
        {entries.length === 0 && <div className="empty-note">Nothing remembered yet. Tell NOVA: "remember wifi password is ..."</div>}
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
          {(status?.issues ?? []).length === 0 && <div className="empty-note">All systems nominal</div>}
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
          <div className="cs-text">This module is on the roadmap. For now, just ask NOVA — e.g. "remind me tomorrow at 9am" or "make a video about cricket".</div>
        </div>
      </section>
    );
  }




  // ---------- render ----------
  return (
    <div className="astra-app">
      <style>{CSS}</style>

      {/* toasts */}
      <div className="toasts">
        {toasts.map((t) => (
          <div className="toast" key={t.id}>◆ {t.text}</div>
        ))}
      </div>

      {/* topbar */}
      <header className="topbar">
        <div className="brand">
          <button className="sidebar-toggle" onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
            {sidebarCollapsed ? "→" : "←"}
          </button>
          <div className="brand-logo">◆</div>
          <div>
            <div className="brand-title">NOVA</div>
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

      <div className={`layout ${sidebarCollapsed ? "collapsed" : ""}`}>
        {/* sidebar */}
        <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
          <button className="new-chat-btn" onClick={newChat}>
            <span className="new-chat-icon">＋</span>
            {!sidebarCollapsed && <span>New chat</span>}
          </button>

          {!sidebarCollapsed && (
            <>
              <div className="sidebar-section">
                <div className="sidebar-header">
                  <span>◆ Pinned</span>
                </div>
                {pinnedChats.length === 0 && <div className="sidebar-empty">No pinned chats</div>}
                {pinnedChats.map((t) => (
                  <div key={t} className="sidebar-item" onClick={() => selectChat(t)}>
                    <span className="sidebar-item-icon">◆</span>
                    <span className="sidebar-item-text">{t}</span>
                    <button className="sidebar-item-action" onClick={(e) => { e.stopPropagation(); unpinChat(t); }}>×</button>
                  </div>
                ))}
              </div>

              <div className="sidebar-section">
                <div className="sidebar-header">
                  <span>● Recents</span>
                </div>
                {chatHistory.length === 0 && <div className="sidebar-empty">No recent chats</div>}
                {chatHistory.map((t) => (
                  <div key={t} className="sidebar-item" onClick={() => selectChat(t)}>
                    <span className="sidebar-item-icon">●</span>
                    <span className="sidebar-item-text">{t}</span>
                    <button className="sidebar-item-action" onClick={(e) => { e.stopPropagation(); deleteChat(t); }}>×</button>
                  </div>
                ))}
              </div>

              <div className="sidebar-divider" />
            </>
          )}

          {MENU.map(([icon, label]) => (
            <div
              key={label}
              className={"nav-item " + ((activePage === label || (label === "HOME" && activePage === "CHAT")) ? "active" : "")}
              onClick={() => setActivePage(label)}
              title={label}
            >
              <span className="nav-icon">{icon}</span>
              {!sidebarCollapsed && <span className="nav-label">{label}</span>}
            </div>
          ))}

          <div className="profile">
            <div className="profile-avatar">{user ? user.name[0].toUpperCase() : "◆"}</div>
            {!sidebarCollapsed && (
              <>
                <div className="profile-name">{user ? user.name : "Guest"}</div>
                <div className="profile-plan">Free</div>
                <div className="profile-status">● {online ? "NOVA READY" : "NOVA OFFLINE"}</div>
              </>
            )}
          </div>
        </aside>

        {/* main */}
        <main className="main" key={activePage}>
          <div className="welcome">
            <h1>{greeting()}</h1>
            <p>{pageTitle} — {subtitle()}</p>
          </div>

          {activePage === "HOME" && renderHome()}
          {activePage === "CHAT" && renderChat()}
          {activePage === "MEMORY" && renderMemory()}
          {activePage === "SETTINGS" && renderSettings()}
          {activePage === "ADMIN" && <AdminPanel />}
          {["TASKS", "CALENDAR", "NOTES", "MEDIA", "AI TOOLS"].includes(activePage) && renderComingSoon()}
        </main>
      </div>

      {/* quick actions only on non-home pages */}
      {activePage !== "CHAT" && activePage !== "HOME" && (
        <div className="quick-actions">
          <button className="quick-button" onClick={() => runQuickAction("Tell me something interesting")}>◉ Ask NOVA</button>
          <button className="quick-button" onClick={() => runQuickAction("Give me today's tasks")}>◇ Tasks</button>
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
          placeholder={listening ? "Listening..." : "Ask NOVA..."}
        />
        <button
          className={"voice-button " + (listening ? "listening" : speaking ? "speaking" : "")}
          onClick={startVoice}
          title={listening ? "Stop" : "Voice"}
        >
          {listening ? "◼" : speaking ? "◉" : "◯"}
        </button>
        <button className="send-button" onClick={handleSend} title="Send">▶</button>
      </div>

      {!input && activePage === "CHAT" && (
        <div className="suggestions">
          <button className="suggestion" onClick={() => runQuickAction("Learn something interesting")}>◆ Learn something</button>
          <button className="suggestion" onClick={() => runQuickAction("Help me write and edit")}>◇ Write or edit</button>
          <button className="suggestion" onClick={() => runQuickAction("Search the web for me")}>◈ Search the web</button>
        </div>
      )}
    </div>
  );

}

// ================= CSS =================
const CSS = `
* { box-sizing: border-box; }
html, body, #root { margin: 0; width: 100%; min-height: 100%; }
body {
  font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
  background: #0a0a0f;
  color: #e8e6f0;
  -webkit-font-smoothing: antialiased;
}
button, input { font-family: inherit; }
button { outline: none; }
::selection { background: rgba(139,92,246,.35); }

.astra-app {
  min-height: 100vh;
  position: relative;
  background:
    radial-gradient(1200px 600px at 70% -10%, rgba(124,58,237,.12), transparent 60%),
    radial-gradient(900px 500px at 10% 110%, rgba(56,189,248,.06), transparent 60%),
    #0a0a0f;
  overflow-x: hidden;
}
.astra-app::before {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(139,92,246,.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(56,189,248,.05) 0%, transparent 50%);
  animation: bgshift 20s ease-in-out infinite alternate;
}
.astra-app::after {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image: radial-gradient(rgba(139,92,246,.25) 1px, transparent 1px);
  background-size: 40px 40px; opacity: .2;
  animation: dotgrid 15s linear infinite;
}
@keyframes bgshift { from { transform: scale(1); } to { transform: scale(1.05); } }
@keyframes dotgrid { from { background-position: 0 0; } to { background-position: 40px 40px; } }

/* ---------- toasts ---------- */
.toasts { position: fixed; top: 84px; right: 24px; z-index: 100; display: flex; flex-direction: column; gap: 8px; }
.toast {
  background: rgba(20,20,28,.92); border: 1px solid rgba(139,92,246,.45);
  border-radius: 12px; padding: 11px 16px; font-size: 13px; color: #ddd6fe;
  box-shadow: 0 8px 30px rgba(0,0,0,.5), 0 0 20px rgba(139,92,246,.15);
  backdrop-filter: blur(12px); animation: slidein .3s cubic-bezier(.2,.9,.3,1.2);
  max-width: 340px; position: relative; overflow: hidden;
}
.toast::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(180deg, #a78bfa, #7c3aed);
}
@keyframes slidein { from { transform: translateX(40px); opacity: 0; } to { transform: none; opacity: 1; } }

/* ---------- topbar ---------- */
.topbar {
  height: 60px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; border-bottom: 1px solid rgba(255,255,255,.06);
  background: rgba(10,10,15,.7); backdrop-filter: blur(16px);
  position: sticky; top: 0; z-index: 50; transition: box-shadow .2s;
}
.topbar:hover { box-shadow: 0 4px 20px rgba(0,0,0,.3); }
.brand { display: flex; align-items: center; gap: 11px; }
.brand-logo {
  width: 34px; height: 34px; display: grid; place-items: center;
  border-radius: 10px; font-size: 18px; color: #fff;
  background: linear-gradient(135deg, #4c1d95, #7c3aed);
  box-shadow: 0 0 18px rgba(124,58,237,.5);
  position: relative; transition: transform .2s, box-shadow .2s;
}
.brand-logo:hover { transform: scale(1.05); box-shadow: 0 0 25px rgba(124,58,237,.7); }
.brand-logo::before {
  content: ""; position: absolute; inset: -2px; border-radius: 12px;
  border: 1px solid rgba(139,92,246,.3);
}
.brand-title { font-size: 15px; font-weight: 700; letter-spacing: 2.5px; }
.brand-subtitle { font-size: 9px; color: #6b7280; letter-spacing: 2px; margin-top: 1px; }
.top-center { text-align: center; }
.clock { font-size: 14px; letter-spacing: 1px; color: #c4b5fd; font-variant-numeric: tabular-nums; }
.date { font-size: 10px; color: #6b7280; margin-top: 1px; }
.top-right { display: flex; align-items: center; gap: 12px; }
.online { color: #34d399; font-size: 11px; letter-spacing: 1.5px; display: flex; align-items: center; gap: 6px; }
.online.offline { color: #f87171; }
.online-dot { width: 7px; height: 7px; border-radius: 50%; background: #34d399; box-shadow: 0 0 8px #34d399; animation: pulse-online 2s ease-in-out infinite; }
.online.offline .online-dot { background: #f87171; box-shadow: 0 0 8px #f87171; animation: none; }
@keyframes pulse-online { 0%,100% { opacity: 1; } 50% { opacity: .5; } }
.user-chip {
  font-size: 12px; color: #d1d5db; border: 1px solid rgba(255,255,255,.12);
  border-radius: 999px; padding: 6px 14px; cursor: pointer; background: rgba(255,255,255,.04);
  transition: .15s;
}
.user-chip:hover { background: rgba(139,92,246,.2); border-color: rgba(139,92,246,.5); }

/* ---------- layout ---------- */
.layout { display: grid; grid-template-columns: 260px minmax(0,1fr); min-height: calc(100vh - 60px); transition: grid-template-columns .3s ease; }
.layout.collapsed { grid-template-columns: 64px minmax(0,1fr); }
.sidebar {
  border-right: 1px solid rgba(255,255,255,.06);
  background: rgba(13,13,18,.6); padding: 16px 12px;
  display: flex; flex-direction: column; overflow-y: auto;
  backdrop-filter: blur(10px); transition: width .3s ease;
}
.sidebar.collapsed { padding: 16px 8px; }
.sidebar-toggle {
  width: 32px; height: 32px; border-radius: 8px; border: 1px solid rgba(255,255,255,.1);
  background: rgba(255,255,255,.04); color: #9ca3af; cursor: pointer; font-size: 14px;
  display: grid; place-items: center; transition: .15s; margin-right: 8px;
}
.sidebar-toggle:hover { background: rgba(255,255,255,.08); color: #fff; }
.sidebar.collapsed .new-chat-btn { justify-content: center; padding: 10px; }
.sidebar.collapsed .new-chat-btn span:not(.new-chat-icon) { display: none; }
.sidebar.collapsed .sidebar-section, .sidebar.collapsed .sidebar-divider { display: none; }
.sidebar.collapsed .nav-item { justify-content: center; padding: 0; }
.sidebar.collapsed .nav-label { display: none; }
.sidebar.collapsed .profile { padding: 10px; text-align: center; }
.sidebar.collapsed .profile-name, .sidebar.collapsed .profile-plan, .sidebar.collapsed .profile-status { display: none; }
.new-chat-btn {
  display: flex; align-items: center; gap: 10px; width: 100%;
  padding: 10px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,.12);
  background: rgba(255,255,255,.04); color: #e5e7eb; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: .15s; margin-bottom: 20px; position: relative; overflow: hidden;
}
.new-chat-btn::before {
  content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(139,92,246,.2), transparent);
  transform: translateX(-100%); transition: transform .4s;
}
.new-chat-btn:hover::before { transform: translateX(100%); }
.new-chat-btn:hover { background: rgba(255,255,255,.08); border-color: rgba(139,92,246,.4); }
.new-chat-icon { font-size: 16px; }
.sidebar-section { margin-bottom: 18px; }
.sidebar-header {
  display: flex; justify-content: space-between; align-items: center;
  color: #6b7280; font-size: 11px; font-weight: 600; letter-spacing: 1px;
  margin-bottom: 8px; text-transform: uppercase;
}
.sidebar-empty { color: #4b5563; font-size: 12px; padding: 6px 0; }
.sidebar-item {
  display: flex; align-items: center; gap: 10px; padding: 8px 12px;
  border-radius: 8px; color: #9ca3af; font-size: 13px; cursor: pointer;
  transition: .15s; border: 1px solid transparent; position: relative;
}
.sidebar-item:hover { background: rgba(255,255,255,.05); color: #e5e7eb; transform: translateX(2px); }
.sidebar-item-icon { font-size: 13px; opacity: .7; }
.sidebar-item-text { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sidebar-item-action {
  opacity: 0; background: none; border: none; color: #6b7280; cursor: pointer;
  font-size: 12px; padding: 2px 6px; border-radius: 4px; transition: .15s;
}
.sidebar-item:hover .sidebar-item-action { opacity: 1; }
.sidebar-item-action:hover { background: rgba(255,255,255,.1); color: #ef4444; }
.sidebar-divider { height: 1px; background: rgba(255,255,255,.06); margin: 12px 0; }
.nav-item {
  height: 38px; display: flex; align-items: center; gap: 12px;
  padding: 0 14px; margin-bottom: 2px; border-radius: 10px;
  color: #9ca3af; cursor: pointer; font-size: 13px; font-weight: 500;
  transition: .15s; border: 1px solid transparent; position: relative;
}
.nav-item:hover { color: #fff; background: rgba(255,255,255,.05); }
.nav-item.active {
  color: #fff; background: rgba(139,92,246,.15);
  border-color: rgba(139,92,246,.3);
  box-shadow: 0 0 15px rgba(139,92,246,.2);
}
.nav-icon { font-size: 15px; width: 20px; text-align: center; opacity: .8; }
.nav-item.active .nav-icon { opacity: 1; color: #a78bfa; }
.profile {
  margin-top: auto; padding: 14px;
  border: 1px solid rgba(255,255,255,.08); border-radius: 14px;
  background: rgba(255,255,255,.03); transition: transform .2s, box-shadow .2s;
}
.profile:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,.3); }
.profile-avatar {
  width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center;
  margin-bottom: 10px; font-size: 16px; font-weight: 600; color: #fff;
  background: linear-gradient(135deg, #7c3aed, #ec4899);
}
.profile-name { font-weight: 600; font-size: 13px; }
.profile-plan { color: #6b7280; font-size: 11px; margin-top: 2px; }
.profile-status { color: #34d399; font-size: 11px; margin-top: 3px; display: flex; align-items: center; gap: 5px; }
.profile-status::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: #34d399; }

.main { padding: 32px 36px 200px; min-width: 0; overflow-y: auto; max-width: 1400px; position: relative; z-index: 1; animation: fade-in-page .3s ease-out; }
@keyframes fade-in-page { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
.welcome h1 { margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -.5px; background: linear-gradient(135deg, #fff, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.welcome p { margin: 6px 0 0; color: #6b7280; font-size: 14px; }

/* ---------- home full screen ---------- */
.home-full {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: calc(100vh - 140px); padding: 20px; gap: 40px;
}
.home-hero {
  display: flex; flex-direction: column; align-items: center; gap: 24px;
}
.avatar-orb-large {
  width: 320px; height: 320px; border-radius: 50%; display: grid; place-items: center;
  position: relative;
  background: radial-gradient(circle at 50% 50%, #1e1b4b 0%, #0a0a0f 100%);
  box-shadow: 0 30px 80px rgba(124,58,237,.4), inset 0 0 80px rgba(124,58,237,.15);
  transition: transform .3s, box-shadow .3s;
}
.avatar-orb-large:hover { transform: scale(1.05); box-shadow: 0 40px 100px rgba(124,58,237,.6), inset 0 0 100px rgba(124,58,237,.25); }
.avatar-face-large {
  position: relative; width: 220px; height: 220px;
}
.avatar-ring-outer {
  position: absolute; inset: 0; border-radius: 50%;
  border: 2px solid rgba(139,92,246,.4);
  animation: spin 12s linear infinite;
}
.avatar-ring-outer::before, .avatar-ring-outer::after {
  content: ""; position: absolute; top: -4px; left: 50%; width: 8px; height: 8px;
  border-radius: 50%; background: #a78bfa; transform: translateX(-50%);
}
.avatar-ring-outer::after { top: auto; bottom: -4px; }
.avatar-ring-inner {
  position: absolute; inset: 35px; border-radius: 50%;
  border: 1px solid rgba(139,92,246,.25);
  animation: spin-reverse 8s linear infinite;
}
.avatar-ring-inner::before {
  content: ""; position: absolute; top: -3px; left: 50%; width: 6px; height: 6px;
  border-radius: 50%; background: #c4b5fd; transform: translateX(-50%);
}
.avatar-dot {
  position: absolute; inset: 0; margin: auto; width: 12px; height: 12px;
  border-radius: 50%; background: #a78bfa;
  box-shadow: 0 0 20px #a78bfa, 0 0 40px rgba(139,92,246,.6);
  animation: pulse-dot 2s ease-in-out infinite;
}
.home-status {
  font-size: 16px; color: #a78bfa; letter-spacing: 6px; font-weight: 600;
}
.voice-state {
  padding: 10px 24px; border-radius: 999px;
  border: 1px solid rgba(255,255,255,.1); background: rgba(255,255,255,.04);
  color: #9ca3af; font-size: 13px; transition: .3s;
}
.voice-state.active { color: #e9d5ff; border-color: rgba(139,92,246,.5); box-shadow: 0 0 20px rgba(139,92,246,.2); }
.home-quick {
  display: flex; gap: 12px; flex-wrap: wrap; justify-content: center;
}
.quick-chip {
  padding: 12px 24px; border-radius: 12px; font-size: 14px;
  color: #d1d5db; background: rgba(17,17,24,.8); border: 1px solid rgba(255,255,255,.12);
  cursor: pointer; backdrop-filter: blur(10px); transition: .15s; position: relative; overflow: hidden;
}
.quick-chip::before {
  content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(139,92,246,.2), transparent);
  transform: translateX(-100%); transition: transform .3s;
}
.quick-chip:hover::before { transform: translateX(100%); }
.quick-chip:hover { color: #fff; border-color: rgba(139,92,246,.5); background: rgba(139,92,246,.15); transform: translateY(-2px); box-shadow: 0 8px 20px rgba(124,58,237,.3); }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes spin-reverse { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
@keyframes pulse-dot { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.3); opacity: .6; } }

.section-title {
  display: flex; justify-content: space-between; align-items: center;
  color: #9ca3af; font-size: 11px; font-weight: 600; letter-spacing: 1.5px;
  margin-bottom: 16px; text-transform: uppercase;
}
.section-title .live { color: #34d399; animation: blink-live 2s ease-in-out infinite; }
.section-title .off { color: #f87171; }
@keyframes blink-live { 0%,100% { opacity: 1; } 50% { opacity: .6; } }

/* tools + activity */
.tool {
  display: flex; gap: 12px; padding: 12px; margin-bottom: 6px;
  border: 1px solid rgba(255,255,255,.06); border-radius: 12px;
  cursor: pointer; transition: .15s; position: relative; overflow: hidden;
}
.tool::before {
  content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(139,92,246,.1), transparent);
  transform: translateX(-100%); transition: transform .4s;
}
.tool:hover::before { transform: translateX(100%); }
.tool:hover { border-color: rgba(139,92,246,.4); background: rgba(139,92,246,.08); transform: translateX(-2px); }
.tool-icon {
  width: 34px; height: 34px; display: grid; place-items: center; flex-shrink: 0;
  border-radius: 9px; background: rgba(139,92,246,.15); color: #c4b5fd; font-size: 15px;
}
.tool-name { font-size: 13px; color: #e5e7eb; font-weight: 500; }
.tool-desc { color: #6b7280; font-size: 11px; margin-top: 2px; }
.activity { margin-top: 22px; }
.activity-item {
  display: flex; gap: 10px; align-items: center; padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,.05); transition: background .15s;
}
.activity-item:hover { background: rgba(255,255,255,.02); padding-left: 8px; border-radius: 6px; }
.activity-icon { color: #a78bfa; font-size: 13px; width: 18px; text-align: center; }
.activity-text { flex: 1; font-size: 12px; color: #9ca3af; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.activity-time { color: #4b5563; font-size: 10px; flex-shrink: 0; }
.empty-note { color: #4b5563; font-size: 12px; padding: 12px 0; }

/* ---------- chat bar ---------- */
.chat-bar {
  position: fixed; left: 280px; right: 36px; bottom: 24px; z-index: 10;
  display: flex; gap: 8px; padding: 8px;
  border: 1px solid rgba(255,255,255,.1); border-radius: 18px;
  background: rgba(17,17,24,.85); backdrop-filter: blur(20px);
  box-shadow: 0 12px 40px rgba(0,0,0,.5), 0 0 30px rgba(139,92,246,.08);
  max-width: 1100px; transition: transform .2s, box-shadow .2s, left .3s ease;
}
.layout.collapsed .chat-bar { left: 84px; }
.chat-bar:focus-within {
  transform: translateY(-2px);
  box-shadow: 0 16px 50px rgba(0,0,0,.6), 0 0 40px rgba(139,92,246,.15);
}
.chat-input {
  flex: 1; min-width: 0; border: 0; outline: 0; color: #fff;
  background: transparent; padding: 12px 16px; font-size: 14px;
}
.chat-input::placeholder { color: #4b5563; }
.voice-button, .send-button {
  width: 44px; height: 44px; border: 0; border-radius: 12px;
  color: white; cursor: pointer; font-size: 17px; transition: .15s; flex-shrink: 0;
  position: relative; overflow: hidden;
}
.voice-button { background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); }
.voice-button:hover { background: rgba(255,255,255,.1); transform: scale(1.05); }
.voice-button.listening { background: #7c3aed; box-shadow: 0 0 20px rgba(124,58,237,.6); animation: pulse 1.2s infinite; }
.voice-button.speaking { background: rgba(236,72,153,.6); box-shadow: 0 0 20px rgba(236,72,153,.5); }
.send-button { background: linear-gradient(135deg, #7c3aed, #a855f7); box-shadow: 0 4px 16px rgba(124,58,237,.4); }
.send-button:hover { filter: brightness(1.1); transform: scale(1.05); }
@keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.08); } }

.quick-actions {
  position: fixed; left: 280px; right: 36px; bottom: 96px; z-index: 9;
  display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; max-width: 1100px;
  transition: left .3s ease;
}
.layout.collapsed .quick-actions { left: 84px; }
.quick-button {
  padding: 8px 14px; border-radius: 999px; font-size: 12px;
  color: #9ca3af; background: rgba(17,17,24,.8); border: 1px solid rgba(255,255,255,.09);
  cursor: pointer; backdrop-filter: blur(10px); transition: .15s; position: relative; overflow: hidden;
}
.quick-button::before {
  content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(139,92,246,.2), transparent);
  transform: translateX(-100%); transition: transform .3s;
}
.quick-button:hover::before { transform: translateX(100%); }
.quick-button:hover { color: #fff; border-color: rgba(139,92,246,.5); background: rgba(139,92,246,.12); transform: translateY(-1px); }

.suggestions {
  position: fixed; left: 290px; right: 36px; bottom: 96px; z-index: 9;
  display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; max-width: 1100px;
  transition: left .3s ease;
}
.layout.collapsed .suggestions { left: 94px; }
.suggestion {
  padding: 10px 18px; border-radius: 12px; font-size: 13px;
  color: #9ca3af; background: rgba(17,17,24,.8); border: 1px solid rgba(255,255,255,.09);
  cursor: pointer; backdrop-filter: blur(10px); transition: .15s; display: flex; align-items: center; gap: 8px;
  position: relative; overflow: hidden;
}
.suggestion::before {
  content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(139,92,246,.2), transparent);
  transform: translateX(-100%); transition: transform .3s;
}
.suggestion:hover::before { transform: translateX(100%); }
.suggestion:hover { color: #fff; border-color: rgba(139,92,246,.5); background: rgba(139,92,246,.12); transform: translateY(-1px); }

/* ---------- chat page ---------- */
.chat-page { min-height: 60vh; display: flex; flex-direction: column; }
.chat-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 40vh; color: #6b7280;
}
.chat-empty-icon { font-size: 48px; color: #374151; margin-bottom: 16px; }
.chat-empty-title { font-size: 20px; color: #d1d5db; font-weight: 500; }
.chat-history { flex: 1; overflow-y: auto; padding: 16px 4px; max-height: calc(100vh - 300px); }
.chat-msg { margin-bottom: 18px; font-size: 14px; line-height: 1.6; display: flex; gap: 12px; animation: fadeup .3s ease-out; }
@keyframes fadeup { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
.msg-sender { font-weight: 600; min-width: 56px; font-size: 12px; padding-top: 2px; }
.chat-msg.nova .msg-sender { color: #a78bfa; }
.chat-msg.user .msg-sender { color: #38bdf8; }
.msg-text { flex: 1; color: #d1d5db; white-space: pre-wrap; }

/* ---------- pages ---------- */
.page-panel { padding: 28px; max-width: 760px; margin-top: 8px; }
.memory-item {
  display: flex; justify-content: space-between; gap: 16px;
  padding: 13px 0; border-bottom: 1px solid rgba(255,255,255,.05); transition: background .15s;
}
.memory-item:hover { background: rgba(255,255,255,.02); padding-left: 8px; border-radius: 6px; }
.mem-key { color: #a78bfa; font-weight: 600; font-size: 13px; }
.mem-val { color: #9ca3af; text-align: right; word-break: break-word; font-size: 13px; }
.settings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 8px; }
.kv {
  display: flex; justify-content: space-between; padding: 11px 0;
  border-bottom: 1px solid rgba(255,255,255,.05); color: #9ca3af; font-size: 13px;
  transition: background .15s;
}
.kv:hover { background: rgba(255,255,255,.02); padding-left: 8px; border-radius: 6px; }
.kv b { color: #e5e7eb; font-weight: 600; }
.kv b.ok { color: #34d399; }
.kv b.bad { color: #f87171; }
.btn {
  margin-top: 16px; padding: 10px 22px; border-radius: 10px; font-size: 13px;
  border: 1px solid rgba(139,92,246,.5); background: rgba(139,92,246,.15);
  color: #ede9fe; cursor: pointer; transition: .15s; position: relative; overflow: hidden;
}
.btn::before {
  content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,.2), transparent);
  transform: translateX(-100%); transition: transform .4s;
}
.btn:hover::before { transform: translateX(100%); }
.btn:hover { background: rgba(139,92,246,.3); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(124,58,237,.3); }
.hint { margin-top: 12px; font-size: 11px; color: #4b5563; line-height: 1.5; }

.coming-soon {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 320px; color: #6b7280;
}
.cs-icon { font-size: 40px; color: #374151; margin-bottom: 14px; }
.cs-title { font-size: 18px; color: #d1d5db; margin-bottom: 8px; font-weight: 600; }
.cs-text { font-size: 13px; max-width: 400px; text-align: center; line-height: 1.6; }

/* ---------- admin panel ---------- */
.admin-panel { padding: 24px; max-width: 800px; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 24px; }
.stat-card {
  padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,.08);
  background: rgba(255,255,255,.03); text-align: center;
}
.stat-number { font-size: 32px; font-weight: 700; color: #a78bfa; }
.stat-label { font-size: 12px; color: #6b7280; margin-top: 4px; }
.admin-section { margin-bottom: 32px; }
.feature-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,.06);
  background: rgba(255,255,255,.02); margin-bottom: 8px;
}
.feature-info { flex: 1; }
.feature-name { font-weight: 600; color: #e5e7eb; font-size: 14px; }
.feature-desc { color: #6b7280; font-size: 12px; margin-top: 4px; }
.feature-toggle {
  padding: 8px 16px; border-radius: 8px; border: none; cursor: pointer;
  font-size: 12px; font-weight: 600; transition: .15s;
}
.feature-toggle.enabled { background: rgba(52,211,153,.2); color: #34d399; border: 1px solid rgba(52,211,153,.4); }
.feature-toggle.disabled { background: rgba(248,113,113,.2); color: #f87171; border: 1px solid rgba(248,113,113,.4); }
.feature-toggle:hover { transform: scale(1.05); }
.user-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,.06);
  background: rgba(255,255,255,.02); margin-bottom: 8px;
}
.user-info { flex: 1; }
.user-name { font-weight: 600; color: #e5e7eb; font-size: 14px; }
.user-email { color: #6b7280; font-size: 12px; margin-top: 4px; }
.user-actions { display: flex; align-items: center; gap: 12px; }
.role-select {
  padding: 6px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,.1);
  background: rgba(255,255,255,.05); color: #e5e7eb; font-size: 12px; cursor: pointer;
}
.user-status { font-size: 11px; font-weight: 600; }
.user-status.active { color: #34d399; }
.user-status.inactive { color: #f87171; }

/* ---------- performance optimizations ---------- */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Loading state */
.loading-spinner {
  width: 40px; height: 40px; border: 3px solid rgba(139,92,246,.2);
  border-top-color: #a78bfa; border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Error boundary fallback */
.error-fallback {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 100vh; color: #9ca3af; padding: 20px; text-align: center;
}
.error-fallback h2 { color: #f87171; margin-bottom: 10px; }
.error-fallback button {
  margin-top: 20px; padding: 10px 20px; border-radius: 8px;
  background: rgba(139,92,246,.2); border: 1px solid rgba(139,92,246,.5);
  color: #ede9fe; cursor: pointer;
}

/* ---------- touch & mobile optimizations ---------- */
@media (hover: none) and (pointer: coarse) {
  .tool:hover::before, .quick-button:hover::before, .suggestion:hover::before, .btn:hover::before, .new-chat-btn:hover::before {
    display: none;
  }
  .panel:hover, .avatar-orb:hover, .avatar-orb-large:hover, .brand-logo:hover, .profile:hover {
    transform: none;
  }
  .sidebar-item:hover { transform: none; }
  .nav-item:hover { background: rgba(255,255,255,.05); }
}

@media (max-width: 1100px) {
  .layout { grid-template-columns: 64px minmax(0,1fr); }
  .layout.collapsed { grid-template-columns: 64px minmax(0,1fr); }
  .sidebar { padding: 12px 8px; }
  .new-chat-btn, .sidebar-section, .sidebar-divider { display: none; }
  .nav-label, .profile { display: none; }
  .nav-item { justify-content: center; padding: 0; height: 44px; }
  .chat-bar, .quick-actions, .suggestions { left: 88px; right: 20px; }
  .home-full { min-height: calc(100vh - 120px); }
  .avatar-orb-large { width: 240px; height: 240px; }
  .avatar-face-large { width: 160px; height: 160px; }
  .quick-chip { padding: 14px 28px; font-size: 15px; }
}
@media (max-width: 700px) {
  .topbar { height: 52px; padding: 0 14px; }
  .brand-subtitle, .top-center { display: none; }
  .clock { font-size: 12px; }
  .layout { grid-template-columns: 52px 1fr; }
  .layout.collapsed { grid-template-columns: 52px 1fr; }
  .main { padding: 20px 16px 200px; }
  .home-full { min-height: calc(100vh - 100px); gap: 24px; }
  .avatar-orb-large { width: 180px; height: 180px; }
  .avatar-face-large { width: 120px; height: 120px; }
  .home-status { font-size: 12px; letter-spacing: 4px; }
  .chat-bar { left: 62px; right: 10px; bottom: 12px; padding: 6px; }
  .chat-input { padding: 12px 12px; font-size: 16px; }
  .voice-button, .send-button { width: 44px; height: 44px; font-size: 16px; }
  .quick-actions, .suggestions { left: 62px; right: 10px; bottom: 84px; }
  .quick-button, .suggestion { padding: 10px 14px; font-size: 13px; }
  .quick-chip { padding: 12px 20px; font-size: 14px; }
}
@media (max-width: 400px) {
  .avatar-orb-large { width: 140px; height: 140px; }
  .avatar-face-large { width: 90px; height: 90px; }
  .home-status { font-size: 10px; letter-spacing: 3px; }
  .chat-bar { left: 52px; right: 8px; bottom: 8px; }
  .quick-actions, .suggestions { left: 52px; right: 8px; bottom: 76px; }
}
`;
