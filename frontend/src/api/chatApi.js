import axios from "axios";

// API URL: use env var if set, else auto-detect local IP for phone access
const API = import.meta.env.VITE_API_URL || (() => {
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") {
      return "http://localhost:8000";
    }
    return `http://${host}:8000`;
  }
  return "http://localhost:8000";
})();

export async function sendMessage(message) {
    const response = await axios.post(`${API}/chat`, {
        message: message,
    });

    return response.data.reply;
}

export async function getNotifications() {
    const response = await axios.get(`${API}/notifications`);
    return response.data.messages || [];
}

export async function devLogin(name) {
    const response = await axios.post(`${API}/auth/dev-login`, { name });
    return response.data;
}

export async function getMe() {
    const response = await axios.get(`${API}/auth/me`);
    return response.data.user;
}

export async function logout() {
    await axios.post(`${API}/auth/logout`);
}

export async function getSystemStatus() {
    const response = await axios.get(`${API}/system-status`);
    return response.data;
}

export async function getActivity() {
    const response = await axios.get(`${API}/activity`);
    return response.data.activity || [];
}

export async function getMemories() {
    const response = await axios.get(`${API}/memory`);
    return response.data;
}
