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

// Axios instance with timeout
const api = axios.create({
  baseURL: API,
  timeout: 10000,
});

export async function sendMessage(message) {
    const response = await api.post(`/chat`, {
        message: message,
    });

    return response.data.reply;
}

export async function getNotifications() {
    const response = await api.get(`/notifications`);
    return response.data.messages || [];
}

export async function devLogin(name) {
    const response = await api.post(`/auth/dev-login`, { name });
    return response.data;
}

export async function getMe() {
    const response = await api.get(`/auth/me`);
    return response.data.user;
}

export async function logout() {
    await api.post(`/auth/logout`);
}

export async function getSystemStatus() {
    const response = await api.get(`/system-status`);
    return response.data;
}

export async function getActivity() {
    const response = await api.get(`/activity`);
    return response.data.activity || [];
}

export async function getMemories() {
    const response = await api.get(`/memory`);
    return response.data;
}
