import { useEffect, useRef, useState } from "react";
import { sendMessage } from "../api/chatApi";

export default function Dashboard() {
  // ============================================================
  // STATE
  // ============================================================

  const [input, setInput] = useState("");

  const [messages, setMessages] = useState([
    {
      sender: "ASTRA",
      text: "Hello Roshan. I am ASTRA AI. How can I assist you today?",
    },
  ]);

  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  const [activePage, setActivePage] = useState("HOME");

  const [time, setTime] = useState(new Date());

  const [voices, setVoices] = useState([]);

  const recognitionRef = useRef(null);

  // ============================================================
  // CLOCK
  // ============================================================

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => {
      clearInterval(timer);
    };
  }, []);

  // ============================================================
  // LOAD BROWSER VOICES
  // ============================================================

  useEffect(() => {
    if (!("speechSynthesis" in window)) {
      return;
    }

    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();

      setVoices(availableVoices);

      console.log(
        "ASTRA available voices:",
        availableVoices.map((voice) => ({
          name: voice.name,
          language: voice.lang,
        }))
      );
    };

    loadVoices();

    window.speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, []);

  // ============================================================
  // FIND BEST ASTRA FEMALE VOICE
  // ============================================================

  const getAstraVoice = () => {
    if (!voices || voices.length === 0) {
      return null;
    }

    // ----------------------------------------------------------
    // Priority 1:
    // Microsoft natural Indian female voice
    // ----------------------------------------------------------

    const naturalIndianVoice = voices.find((voice) => {
      const name = voice.name.toLowerCase();
      const lang = voice.lang.toLowerCase();

      return (
        lang.includes("en-in") &&
        (
          name.includes("neerja") ||
          name.includes("heera")
        ) &&
        (
          name.includes("natural") ||
          name.includes("online")
        )
      );
    });

    if (naturalIndianVoice) {
      return naturalIndianVoice;
    }

    // ----------------------------------------------------------
    // Priority 2:
    // Any Indian English female voice
    // ----------------------------------------------------------

    const indianFemaleVoice = voices.find((voice) => {
      const name = voice.name.toLowerCase();
      const lang = voice.lang.toLowerCase();

      return (
        lang.includes("en-in") &&
        (
          name.includes("female") ||
          name.includes("neerja") ||
          name.includes("heera")
        )
      );
    });

    if (indianFemaleVoice) {
      return indianFemaleVoice;
    }

    // ----------------------------------------------------------
    // Priority 3:
    // Any Indian English voice
    // ----------------------------------------------------------

    const indianEnglishVoice = voices.find((voice) => {
      const name = voice.name.toLowerCase();
      const lang = voice.lang.toLowerCase();

      return (
        lang.includes("en-in") ||
        name.includes("india")
      );
    });

    if (indianEnglishVoice) {
      return indianEnglishVoice;
    }

    // ----------------------------------------------------------
    // Priority 4:
    // Common female English voices
    // ----------------------------------------------------------

    const femaleVoice = voices.find((voice) => {
      const name = voice.name.toLowerCase();

      return (
        name.includes("female") ||
        name.includes("samantha") ||
        name.includes("zira") ||
        name.includes("susan") ||
        name.includes("karen")
      );
    });

    if (femaleVoice) {
      return femaleVoice;
    }

    // ----------------------------------------------------------
    // Priority 5:
    // Any English voice
    // ----------------------------------------------------------

    const englishVoice = voices.find((voice) => {
      const lang = voice.lang.toLowerCase();

      return lang.startsWith("en");
    });

    if (englishVoice) {
      return englishVoice;
    }

    // ----------------------------------------------------------
    // Final fallback
    // ----------------------------------------------------------

    return voices[0] || null;
  };

  // ============================================================
  // ASTRA SPEAK
  // ============================================================

  const speak = (text) => {
    if (!("speechSynthesis" in window)) {
      console.log("Speech synthesis is not supported.");
      return;
    }

    if (!text) {
      return;
    }

    // Stop previous speech
    window.speechSynthesis.cancel();

    // Clean AI response
    const cleanText = String(text)
      .replace(/[*#_`]/g, "")
      .replace(/\n+/g, " ")
      .replace(/\s+/g, " ")
      .trim();

    if (!cleanText) {
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);

    const astraVoice = getAstraVoice();

    if (astraVoice) {
      utterance.voice = astraVoice;

      console.log(
        "ASTRA is speaking with:",
        astraVoice.name,
        astraVoice.lang
      );
    }

    // ----------------------------------------------------------
    // ASTRA VOICE PERSONALITY
    // ----------------------------------------------------------

    // Indian English
    utterance.lang = "en-IN";

    // Slightly conversational speed
    utterance.rate = 1.08;

    // Slightly warm/friendly pitch
    utterance.pitch = 1.18;

    // Full volume
    utterance.volume = 1.0;

    utterance.onstart = () => {
      setSpeaking(true);
    };

    utterance.onend = () => {
      setSpeaking(false);
    };

    utterance.onerror = (event) => {
      console.error("ASTRA speech error:", event);

      setSpeaking(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  // ============================================================
  // SEND MESSAGE TO BACKEND
  // ============================================================

  const handleSend = async (textOverride = null) => {
    const message =
      textOverride !== null
        ? textOverride
        : input;

    if (!message || !message.trim()) {
      return;
    }

    const userMessage = message.trim();

    // Add user message
    setMessages((previousMessages) => [
      ...previousMessages,
      {
        sender: "You",
        text: userMessage,
      },
    ]);

    setInput("");

    try {
      // Send message to ASTRA backend
      const reply = await sendMessage(userMessage);

      // Add ASTRA response
      setMessages((previousMessages) => [
        ...previousMessages,
        {
          sender: "ASTRA",
          text: reply,
        },
      ]);

      // Speak response
      speak(reply);
    } catch (error) {
      console.error("Backend error:", error);

      const errorMessage =
        "I could not connect to my backend. Please check that the ASTRA backend is running.";

      setMessages((previousMessages) => [
        ...previousMessages,
        {
          sender: "ASTRA",
          text: errorMessage,
        },
      ]);

      speak(errorMessage);
    }
  };

  // ============================================================
  // START / STOP VOICE INPUT
  // ============================================================

  const startVoice = () => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert(
        "Voice recognition is not supported in this browser. Please use Google Chrome."
      );

      return;
    }

    // If already listening, stop it
    if (listening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }

      return;
    }

    // Stop ASTRA speaking before listening
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
    }

    const recognition = new SpeechRecognition();

    // Indian English
    recognition.lang = "en-IN";

    // Only one request at a time
    recognition.continuous = false;

    // We only need final result
    recognition.interimResults = false;

    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.log("ASTRA voice recognition started.");

      setListening(true);
    };

    recognition.onresult = (event) => {
      const result =
        event.results[0][0].transcript;

      console.log(
        "You said:",
        result
      );

      setInput(result);

      // Automatically send voice message
      handleSend(result);
    };

    recognition.onerror = (event) => {
      console.error(
        "Speech recognition error:",
        event.error
      );

      setListening(false);
    };

    recognition.onend = () => {
      console.log(
        "ASTRA voice recognition ended."
      );

      setListening(false);
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
    } catch (error) {
      console.error(
        "Could not start voice recognition:",
        error
      );

      setListening(false);
    }
  };

  // ============================================================
  // CLEANUP
  // ============================================================

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (error) {
          console.log(error);
        }
      }

      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // ============================================================
  // NAVIGATION
  // ============================================================

  const menuItems = [
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

  // ============================================================
  // AI TOOLS
  // ============================================================

  const tools = [
    [
      "✎",
      "AI Writer",
      "Write anything with AI",
    ],
    [
      "▣",
      "Image Generator",
      "Generate images",
    ],
    [
      "⌘",
      "Code Assistant",
      "Write and debug code",
    ],
    [
      "♩",
      "Voice Assistant",
      "Talk with ASTRA",
    ],
    [
      "◈",
      "Research Helper",
      "Get information and insights",
    ],
  ];

  // ============================================================
  // ACTIVITY
  // ============================================================

  const activities = [
    [
      "✓",
      "Created a project plan",
      "2h ago",
    ],
    [
      "▧",
      "Generated an image",
      "5h ago",
    ],
    [
      "◉",
      "AI Chat Summary",
      "1d ago",
    ],
    [
      "✓",
      "Set a reminder",
      "2d ago",
    ],
    [
      "⌘",
      "Code file debugged",
      "2d ago",
    ],
  ];

  // ============================================================
  // TIME FORMAT
  // ============================================================

  const formatTime = (date) => {
    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  // ============================================================
  // DATE FORMAT
  // ============================================================

  const formatDate = (date) => {
    return date.toLocaleDateString([], {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  // ============================================================
  // QUICK ACTION
  // ============================================================

  const runQuickAction = (text) => {
    setInput(text);

    handleSend(text);
  };

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="astra-app">

      {/* ======================================================
          GLOBAL CSS
      ====================================================== */}

      <style>{`

        * {
          box-sizing: border-box;
        }

        html,
        body,
        #root {
          margin: 0;
          width: 100%;
          min-height: 100%;
          background: #03010b;
        }

        body {
          font-family:
            Arial,
            Helvetica,
            sans-serif;
        }

        button,
        input {
          font-family: inherit;
        }

        button {
          outline: none;
        }

        /* =====================================================
           MAIN APP
        ===================================================== */

        .astra-app {
          min-height: 100vh;

          color: #f8f5ff;

          background:
            radial-gradient(
              circle at 50% 42%,
              rgba(132, 0, 255, 0.18),
              transparent 30%
            ),

            radial-gradient(
              circle at 82% 20%,
              rgba(0, 120, 255, 0.10),
              transparent 25%
            ),

            linear-gradient(
              135deg,
              #03010b 0%,
              #090314 45%,
              #020107 100%
            );

          overflow: hidden;

          position: relative;
        }

        .astra-app::before {
          content: "";

          position: absolute;

          inset: 0;

          pointer-events: none;

          opacity: 0.18;

          background-image:
            linear-gradient(
              rgba(180, 70, 255, 0.12) 1px,
              transparent 1px
            ),
            linear-gradient(
              90deg,
              rgba(180, 70, 255, 0.12) 1px,
              transparent 1px
            );

          background-size: 50px 50px;
        }

        /* =====================================================
           TOP BAR
        ===================================================== */

        .topbar {
          height: 82px;

          display: flex;

          align-items: center;

          justify-content: space-between;

          padding: 0 28px;

          border-bottom:
            1px solid
            rgba(180, 80, 255, 0.28);

          background:
            rgba(5, 2, 14, 0.82);

          backdrop-filter: blur(16px);

          position: relative;

          z-index: 5;
        }

        .brand {
          display: flex;

          align-items: center;

          gap: 14px;
        }

        .brand-logo {
          width: 48px;

          height: 48px;

          display: grid;

          place-items: center;

          border:
            1px solid
            #b55cff;

          color: #d995ff;

          font-size: 27px;

          border-radius: 14px;

          box-shadow:
            0 0 25px
            rgba(183, 80, 255, 0.45);
        }

        .brand-title {
          font-size: 25px;

          font-weight: 700;

          letter-spacing: 2px;

          color: #f2d8ff;
        }

        .brand-subtitle {
          font-size: 10px;

          color: #9b8ba9;

          letter-spacing: 1.5px;

          margin-top: 3px;
        }

        .top-center {
          text-align: center;
        }

        .clock {
          font-size: 22px;

          letter-spacing: 2px;

          color: #d9c5e7;
        }

        .date {
          font-size: 11px;

          color: #81758e;

          margin-top: 3px;
        }

        .online {
          color: #67ff9a;

          font-size: 12px;

          letter-spacing: 1px;
        }

        .online-dot {
          display: inline-block;

          width: 7px;

          height: 7px;

          border-radius: 50%;

          background: #48ff89;

          box-shadow:
            0 0 12px
            #48ff89;

          margin-right: 6px;
        }

        .search {
          width: 250px;

          height: 42px;

          border-radius: 24px;

          border:
            1px solid
            rgba(200, 100, 255, 0.3);

          background:
            rgba(40, 20, 60, 0.55);

          color: white;

          padding: 0 18px;

          outline: none;
        }

        /* =====================================================
           LAYOUT
        ===================================================== */

        .layout {
          display: grid;

          grid-template-columns:
            220px
            minmax(0, 1fr)
            300px;

          min-height:
            calc(100vh - 82px);

          position: relative;

          z-index: 2;
        }

        /* =====================================================
           SIDEBAR
        ===================================================== */

        .sidebar {
          border-right:
            1px solid
            rgba(180, 80, 255, 0.22);

          background:
            rgba(5, 2, 13, 0.72);

          padding: 22px 12px;
        }

        .nav-item {
          height: 52px;

          display: flex;

          align-items: center;

          gap: 15px;

          padding: 0 18px;

          margin-bottom: 8px;

          border-radius: 12px;

          color: #aaa0b6;

          cursor: pointer;

          transition: 0.2s;
        }

        .nav-item:hover {
          color: white;

          background:
            rgba(160, 55, 255, 0.12);
        }

        .nav-item.active {
          color: white;

          background:
            linear-gradient(
              90deg,
              rgba(158, 55, 255, 0.35),
              rgba(72, 21, 100, 0.15)
            );

          border:
            1px solid
            rgba(196, 92, 255, 0.5);

          box-shadow:
            0 0 25px
            rgba(180, 70, 255, 0.18);
        }

        .nav-icon {
          font-size: 21px;

          width: 24px;

          text-align: center;
        }

        .profile {
          margin-top: 28px;

          padding: 18px;

          border:
            1px solid
            rgba(180, 80, 255, 0.3);

          border-radius: 18px;

          background:
            rgba(30, 10, 50, 0.5);
        }

        .profile-avatar {
          width: 54px;

          height: 54px;

          border-radius: 50%;

          display: grid;

          place-items: center;

          margin-bottom: 10px;

          background:
            radial-gradient(
              circle,
              #ff9bf8,
              #7524c9 60%,
              #18042b
            );

          box-shadow:
            0 0 25px
            rgba(211, 74, 255, 0.55);

          font-size: 27px;
        }

        .profile-name {
          font-weight: 700;
        }

        .profile-status {
          color: #6dff9a;

          font-size: 12px;

          margin-top: 5px;
        }

        /* =====================================================
           MAIN
        ===================================================== */

        .main {
          padding: 25px;

          min-width: 0;

          overflow-y: auto;

          padding-bottom: 180px;
        }

        .welcome {
          margin-bottom: 20px;
        }

        .welcome h1 {
          margin: 0;

          font-size: 23px;

          color: #f3d9ff;
        }

        .welcome p {
          margin: 7px 0 0;

          color: #887c98;
        }

        /* =====================================================
           DASHBOARD GRID
        ===================================================== */

        .dashboard-grid {
          display: grid;

          grid-template-columns:
            1fr
            1.35fr
            1fr;

          gap: 18px;

          align-items: stretch;
        }

        .panel {
          border:
            1px solid
            rgba(178, 70, 255, 0.27);

          border-radius: 18px;

          background:
            rgba(13, 6, 26, 0.7);

          box-shadow:
            inset 0 0 30px
            rgba(140, 45, 255, 0.04),

            0 0 25px
            rgba(130, 40, 255, 0.06);
        }

        /* =====================================================
           STATUS
        ===================================================== */

        .stats-panel {
          padding: 20px;
        }

        .status-ring {
          width: 160px;

          height: 160px;

          border-radius: 50%;

          margin:
            10px auto 25px;

          display: grid;

          place-items: center;

          border:
            2px solid
            #8d42ff;

          box-shadow:
            0 0 20px
            rgba(132, 51, 255, 0.8),

            inset 0 0 30px
            rgba(132, 51, 255, 0.25);
        }

        .status-ring-inner {
          text-align: center;
        }

        .status-small {
          color: #8f82a1;

          font-size: 10px;

          letter-spacing: 1px;
        }

        .status-number {
          font-size: 30px;

          font-weight: 700;

          color: #dcb8ff;

          margin: 7px 0;
        }

        .status-good {
          color: #63ffae;

          font-size: 11px;
        }

        .metric {
          margin: 15px 0;
        }

        .metric-head {
          display: flex;

          justify-content: space-between;

          color: #9c91a7;

          font-size: 12px;

          margin-bottom: 7px;
        }

        .bar {
          height: 5px;

          background: #21182b;

          border-radius: 5px;

          overflow: hidden;
        }

        .bar-fill {
          height: 100%;

          border-radius: 5px;

          background:
            linear-gradient(
              90deg,
              #633cff,
              #e74cff
            );

          box-shadow:
            0 0 12px
            #a73fff;
        }

        /* =====================================================
           ASTRA AVATAR
        ===================================================== */

        .avatar-panel {
          min-height: 570px;

          display: flex;

          flex-direction: column;

          align-items: center;

          justify-content: center;

          position: relative;

          overflow: hidden;
        }

        .avatar-panel::before {
          content: "";

          position: absolute;

          width: 390px;

          height: 390px;

          border-radius: 50%;

          background:
            radial-gradient(
              circle,
              rgba(212, 50, 255, 0.42),
              rgba(89, 27, 255, 0.14),
              transparent 70%
            );

          filter: blur(10px);
        }

        .avatar-orb {
          width: 280px;

          height: 280px;

          border-radius: 50%;

          display: grid;

          place-items: center;

          position: relative;

          border:
            2px solid
            rgba(206, 96, 255, 0.7);

          background:
            radial-gradient(
              circle at 50% 45%,
              #ff78ed 0%,
              #9a27dd 35%,
              #25053d 70%,
              #09020f 100%
            );

          box-shadow:
            0 0 35px
            rgba(229, 63, 255, 0.9),

            0 0 90px
            rgba(120, 35, 255, 0.5),

            inset 0 0 50px
            rgba(255, 100, 255, 0.35);

          animation:
            breathe 3s ease-in-out infinite;
        }

        .avatar-face {
          font-size: 92px;

          filter:
            drop-shadow(
              0 0 20px
              rgba(255,255,255,0.5)
            );
        }

        .avatar-status {
          position: absolute;

          bottom: 90px;

          color: #f0cfff;

          letter-spacing: 5px;

          font-size: 13px;
        }

        .voice-state {
          margin-top: 28px;

          padding: 10px 20px;

          border-radius: 20px;

          border:
            1px solid
            rgba(208, 87, 255, 0.35);

          background:
            rgba(26, 8, 44, 0.75);

          color: #bfaec9;

          font-size: 12px;
        }

        .voice-state.active {
          color: #ff8fff;

          box-shadow:
            0 0 25px
            rgba(255, 60, 255, 0.35);
        }

        /* =====================================================
           RIGHT PANEL
        ===================================================== */

        .right-panel {
          padding: 20px;

          border-left:
            1px solid
            rgba(180, 80, 255, 0.22);

          background:
            rgba(5, 2, 13, 0.72);

          overflow-y: auto;
        }

        .section-title {
          display: flex;

          justify-content: space-between;

          color: #e6d7ed;

          font-size: 13px;

          letter-spacing: 1px;

          margin-bottom: 12px;
        }

        .tool {
          display: flex;

          gap: 13px;

          padding: 13px;

          margin-bottom: 8px;

          border:
            1px solid
            rgba(180, 80, 255, 0.16);

          border-radius: 12px;

          cursor: pointer;

          transition: 0.2s;
        }

        .tool:hover {
          border-color:
            rgba(210, 90, 255, 0.5);

          background:
            rgba(180, 60, 255, 0.1);

          transform:
            translateX(-3px);
        }

        .tool-icon {
          width: 36px;

          height: 36px;

          display: grid;

          place-items: center;

          border-radius: 10px;

          background:
            rgba(126, 47, 255, 0.2);

          color: #d49aff;

          font-size: 18px;
        }

        .tool-name {
          font-size: 13px;

          color: #d7cbdc;
        }

        .tool-desc {
          color: #756a7e;

          font-size: 10px;

          margin-top: 4px;
        }

        /* =====================================================
           ACTIVITY
        ===================================================== */

        .activity {
          margin-top: 25px;
        }

        .activity-item {
          display: flex;

          gap: 10px;

          align-items: center;

          padding: 11px 0;

          border-bottom:
            1px solid
            rgba(255,255,255,0.05);
        }

        .activity-icon {
          color: #b568ff;
        }

        .activity-text {
          flex: 1;

          font-size: 11px;

          color: #b7adbd;
        }

        .activity-time {
          color: #665d6c;

          font-size: 9px;
        }

        /* =====================================================
           CHAT BAR
        ===================================================== */

        .chat-bar {
          position: fixed;

          left: 250px;

          right: 330px;

          bottom: 20px;

          z-index: 10;

          display: flex;

          gap: 10px;

          padding: 8px;

          border:
            1px solid
            rgba(201, 78, 255, 0.5);

          border-radius: 18px;

          background:
            rgba(12, 4, 23, 0.92);

          box-shadow:
            0 0 35px
            rgba(166, 55, 255, 0.22);

          backdrop-filter: blur(15px);
        }

        .chat-input {
          flex: 1;

          min-width: 0;

          border: 0;

          outline: 0;

          color: white;

          background: transparent;

          padding: 14px;

          font-size: 14px;
        }

        .chat-input::placeholder {
          color: #756a7e;
        }

        .voice-button,
        .send-button {
          width: 48px;

          height: 48px;

          border: 0;

          border-radius: 50%;

          color: white;

          cursor: pointer;

          font-size: 20px;
        }

        .voice-button {
          background:
            rgba(115, 38, 200, 0.5);

          border:
            1px solid
            rgba(205, 92, 255, 0.4);
        }

        .voice-button.listening {
          background: #df36db;

          box-shadow:
            0 0 25px
            rgba(255, 55, 225, 0.8);

          animation:
            pulse 1s infinite;
        }

        .voice-button.speaking {
          background:
            rgba(255, 65, 205, 0.65);

          box-shadow:
            0 0 25px
            rgba(255, 60, 220, 0.7);
        }

        .send-button {
          background:
            linear-gradient(
              135deg,
              #8e35ff,
              #d02fff
            );

          box-shadow:
            0 0 20px
            rgba(206, 48, 255, 0.5);
        }

        /* =====================================================
           QUICK ACTIONS
        ===================================================== */

        .quick-actions {
          position: fixed;

          left: 250px;

          right: 330px;

          bottom: 92px;

          z-index: 9;

          display: flex;

          gap: 10px;

          justify-content: center;

          flex-wrap: wrap;
        }

        .quick-button {
          padding: 11px 18px;

          border-radius: 10px;

          color: #bbaec5;

          background:
            rgba(23, 8, 37, 0.82);

          border:
            1px solid
            rgba(166, 71, 255, 0.24);

          cursor: pointer;

          transition: 0.2s;
        }

        .quick-button:hover {
          color: white;

          border-color:
            rgba(210, 90, 255, 0.55);

          background:
            rgba(180, 60, 255, 0.15);
        }

        /* =====================================================
           CHAT WINDOW
        ===================================================== */

        .chat-window {
          position: fixed;

          right: 25px;

          bottom: 90px;

          width: 320px;

          max-height: 360px;

          overflow-y: auto;

          z-index: 20;

          padding: 15px;

          border:
            1px solid
            rgba(196, 74, 255, 0.35);

          border-radius: 15px;

          background:
            rgba(8, 3, 16, 0.96);
        }

        .message {
          margin-bottom: 12px;

          font-size: 12px;

          line-height: 1.5;
        }

        .message strong {
          color: #d37aff;
        }

        /* =====================================================
           ANIMATIONS
        ===================================================== */

        @keyframes breathe {
          0%,
          100% {
            transform: scale(1);
          }

          50% {
            transform: scale(1.035);
          }
        }

        @keyframes pulse {
          0%,
          100% {
            transform: scale(1);
          }

          50% {
            transform: scale(1.1);
          }
        }

        /* =====================================================
           TABLET
        ===================================================== */

        @media (max-width: 1100px) {

          .layout {
            grid-template-columns:
              75px
              minmax(0, 1fr);
          }

          .right-panel {
            display: none;
          }

          .nav-item {
            justify-content: center;

            padding: 0;
          }

          .nav-label,
          .profile {
            display: none;
          }

          .chat-bar,
          .quick-actions {
            left: 100px;

            right: 20px;
          }

        }

        /* =====================================================
           MOBILE
        ===================================================== */

        @media (max-width: 700px) {

          .topbar {
            height: 65px;

            padding: 0 12px;
          }

          .brand-title {
            font-size: 18px;
          }

          .brand-subtitle,
          .top-center,
          .search {
            display: none;
          }

          .layout {
            grid-template-columns:
              55px
              1fr;
          }

          .main {
            padding: 15px;

            padding-bottom: 190px;
          }

          .dashboard-grid {
            grid-template-columns: 1fr;
          }

          .avatar-panel {
            min-height: 450px;
          }

          .avatar-orb {
            width: 220px;

            height: 220px;
          }

          .avatar-face {
            font-size: 70px;
          }

          .chat-bar {
            left: 65px;

            right: 10px;

            bottom: 10px;
          }

          .quick-actions {
            left: 65px;

            right: 10px;

            bottom: 80px;
          }

          .quick-button {
            padding: 8px 10px;

            font-size: 11px;
          }

          .chat-window {
            left: 65px;

            right: 10px;

            width: auto;
          }

        }

      `}</style>

      {/* ======================================================
          TOP BAR
      ====================================================== */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-logo">
            ✦
          </div>

          <div>

            <div className="brand-title">
              ASTRA
            </div>

            <div className="brand-subtitle">
              PERSONAL AI ASSISTANT
            </div>

          </div>

        </div>

        <div className="top-center">

          <div className="clock">
            {formatTime(time)}
          </div>

          <div className="date">
            {formatDate(time)}
          </div>

        </div>

        <div>

          <div className="online">

            <span className="online-dot"></span>

            ONLINE

          </div>

        </div>

      </header>

      {/* ======================================================
          MAIN LAYOUT
      ====================================================== */}

      <div className="layout">

        {/* ====================================================
            SIDEBAR
        ==================================================== */}

        <aside className="sidebar">

          {menuItems.map(
            ([icon, label]) => (

              <div
                key={label}
                className={
                  "nav-item " +
                  (
                    activePage === label
                      ? "active"
                      : ""
                  )
                }
                onClick={() =>
                  setActivePage(label)
                }
              >

                <span className="nav-icon">
                  {icon}
                </span>

                <span className="nav-label">
                  {label}
                </span>

              </div>

            )
          )}

          <div className="profile">

            <div className="profile-avatar">
              👤
            </div>

            <div className="profile-name">
              Roshan
            </div>

            <div className="profile-status">
              ● ASTRA READY
            </div>

          </div>

        </aside>

        {/* ====================================================
            MAIN PANEL
        ==================================================== */}

        <main className="main">

          <div className="welcome">

            <h1>
              Good day, Roshan.
            </h1>

            <p>
              Your AI assistant is ready.
            </p>

          </div>

          <div className="dashboard-grid">

            {/* ==================================================
                SYSTEM STATUS
            ================================================== */}

            <section className="panel stats-panel">

              <div className="section-title">
                <span>
                  SYSTEM STATUS
                </span>

                <span>
                  LIVE
                </span>
              </div>

              <div className="status-ring">

                <div className="status-ring-inner">

                  <div className="status-small">
                    ASTRA
                  </div>

                  <div className="status-number">
                    98%
                  </div>

                  <div className="status-good">
                    SYSTEM GOOD
                  </div>

                </div>

              </div>

              <div className="metric">

                <div className="metric-head">
                  <span>
                    CPU
                  </span>

                  <span>
                    34%
                  </span>
                </div>

                <div className="bar">
                  <div
                    className="bar-fill"
                    style={{
                      width: "34%",
                    }}
                  />
                </div>

              </div>

              <div className="metric">

                <div className="metric-head">
                  <span>
                    MEMORY
                  </span>

                  <span>
                    62%
                  </span>
                </div>

                <div className="bar">
                  <div
                    className="bar-fill"
                    style={{
                      width: "62%",
                    }}
                  />
                </div>

              </div>

              <div className="metric">

                <div className="metric-head">
                  <span>
                    AI CORE
                  </span>

                  <span>
                    91%
                  </span>
                </div>

                <div className="bar">
                  <div
                    className="bar-fill"
                    style={{
                      width: "91%",
                    }}
                  />
                </div>

              </div>

            </section>

            {/* ==================================================
                ASTRA AVATAR
            ================================================== */}

            <section className="panel avatar-panel">

              <div className="avatar-orb">

                <div className="avatar-face">
                  ✦
                </div>

              </div>

              <div className="avatar-status">

                {listening
                  ? "LISTENING"
                  : speaking
                  ? "SPEAKING"
                  : "READY"}

              </div>

              <div
                className={
                  "voice-state " +
                  (
                    listening || speaking
                      ? "active"
                      : ""
                  )
                }
              >

                {listening
                  ? "🎙 Listening to you..."
                  : speaking
                  ? "🔊 ASTRA is speaking..."
                  : "✨ Voice assistant ready"}

              </div>

            </section>

            {/* ==================================================
                AI TOOLS
            ================================================== */}

            <section className="right-panel">

              <div className="section-title">
                <span>
                  AI TOOLS
                </span>

                <span>
                  →
                </span>
              </div>

              {tools.map(
                ([icon, name, description]) => (

                  <div
                    className="tool"
                    key={name}
                    onClick={() => {

                      if (
                        name ===
                        "Voice Assistant"
                      ) {
                        startVoice();

                        return;
                      }

                      runQuickAction(
                        `Open ${name}`
                      );

                    }}
                  >

                    <div className="tool-icon">
                      {icon}
                    </div>

                    <div>

                      <div className="tool-name">
                        {name}
                      </div>

                      <div className="tool-desc">
                        {description}
                      </div>

                    </div>

                  </div>

                )
              )}

              <div className="activity">

                <div className="section-title">
                  <span>
                    RECENT ACTIVITY
                  </span>
                </div>

                {activities.map(
                  ([icon, text, activityTime]) => (

                    <div
                      className="activity-item"
                      key={text}
                    >

                      <div className="activity-icon">
                        {icon}
                      </div>

                      <div className="activity-text">
                        {text}
                      </div>

                      <div className="activity-time">
                        {activityTime}
                      </div>

                    </div>

                  )
                )}

              </div>

            </section>

          </div>

        </main>

      </div>

      {/* ======================================================
          CHAT HISTORY
      ====================================================== */}

      {messages.length > 1 && (

        <div className="chat-window">

          {messages.map(
            (message, index) => (

              <div
                className="message"
                key={index}
              >

                <strong>
                  {message.sender}:
                </strong>{" "}

                {message.text}

              </div>

            )
          )}

        </div>

      )}

      {/* ======================================================
          QUICK ACTIONS
      ====================================================== */}

      <div className="quick-actions">

        <button
          className="quick-button"
          onClick={() =>
            runQuickAction(
              "Tell me something interesting"
            )
          }
        >
          ✦ Ask ASTRA
        </button>

        <button
          className="quick-button"
          onClick={() =>
            runQuickAction(
              "Give me today's tasks"
            )
          }
        >
          ✓ Tasks
        </button>

        <button
          className="quick-button"
          onClick={() =>
            runQuickAction(
              "Open my calendar"
            )
          }
        >
          □ Calendar
        </button>

        <button
          className="quick-button"
          onClick={() =>
            runQuickAction(
              "Help me with coding"
            )
          }
        >
          ⌘ Coding
        </button>

      </div>

      {/* ======================================================
          CHAT INPUT
      ====================================================== */}

      <div className="chat-bar">

        <input
          className="chat-input"
          value={input}
          onChange={(event) =>
            setInput(event.target.value)
          }
          onKeyDown={(event) => {

            if (event.key === "Enter") {
              handleSend();
            }

          }}
          placeholder={
            listening
              ? "Listening..."
              : "Talk to ASTRA..."
          }
        />

        {/* VOICE BUTTON */}

        <button
          className={
            "voice-button " +
            (
              listening
                ? "listening"
                : speaking
                ? "speaking"
                : ""
            )
          }
          onClick={startVoice}
          title={
            listening
              ? "Stop listening"
              : "Talk to ASTRA"
          }
        >

          {listening
            ? "⏹"
            : speaking
            ? "🔊"
            : "🎙"}

        </button>

        {/* SEND BUTTON */}

        <button
          className="send-button"
          onClick={() =>
            handleSend()
          }
          title="Send"
        >
          ➤
        </button>

      </div>

    </div>
  );
}