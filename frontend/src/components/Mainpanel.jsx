import { useState } from "react";
import { sendMessage } from "../api/chatApi";

export default function MainPanel() {
  const [input, setInput] = useState("");

  const [messages, setMessages] = useState([
    {
      sender: "ASTRA",
      text: "Hello Roshan! I am ASTRA AI.",
    },
  ]);

  const speak = (text) => {
    if (!("speechSynthesis" in window)) {
      console.log("Speech synthesis is not supported.");
      return;
    }

    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(text);

    speech.lang = "en-IN";
    speech.rate = 0.95;
    speech.pitch = 1.0;
    speech.volume = 1.0;

    window.speechSynthesis.speak(speech);
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input.trim();

    setMessages((prev) => [
      ...prev,
      {
        sender: "You",
        text: userMessage,
      },
    ]);

    setInput("");

    try {
      const reply = await sendMessage(userMessage);

      setMessages((prev) => [
        ...prev,
        {
          sender: "ASTRA",
          text: reply,
        },
      ]);

      // 🔊 ASTRA speaks the reply
      speak(reply);
    } catch (error) {
      console.error("Backend connection error:", error);

      const errorMessage = "Sorry, I could not connect to my brain.";

      setMessages((prev) => [
        ...prev,
        {
          sender: "ASTRA",
          text: errorMessage,
        },
      ]);

      speak(errorMessage);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      handleSend();
    }
  };

  return (
    <div
      style={{
        flex: 1,
        background: "#111827",
        color: "white",
        display: "flex",
        flexDirection: "column",
        padding: "20px",
      }}
    >
      <h1>ASTRA AI</h1>

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          border: "1px solid #333",
          padding: "15px",
          borderRadius: "10px",
          marginBottom: "20px",
        }}
      >
        {messages.map((msg, index) => (
          <p key={index}>
            <strong>{msg.sender}:</strong> {msg.text}
          </p>
        ))}
      </div>

      <div
        style={{
          display: "flex",
          gap: "10px",
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          style={{
            flex: 1,
            padding: "12px",
            borderRadius: "8px",
            border: "none",
            outline: "none",
          }}
        />

        <button
          onClick={handleSend}
          style={{
            padding: "12px 20px",
            background: "#2563EB",
            color: "white",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}