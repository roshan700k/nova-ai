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
  timeout: 90000, // Render free tier cold start can take ~60s
  withCredentials: true,
});

export async function sendMessage(message, conversationId = null) {
    const response = await api.post(`/chat`, {
        message: message,
        conversation_id: conversationId,
    });

    return response.data;
}

export async function getChats() {
    const response = await api.get(`/chats`);
    return response.data;
}

export async function getChatMessages(convId) {
    const response = await api.get(`/chats/${convId}/messages`);
    return response.data.messages || [];
}

export async function pinChat(convId, pinned) {
    await api.put(`/chats/${convId}/pin`, { pinned });
}

export async function deleteChat(convId) {
    await api.delete(`/chats/${convId}`);
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

// Admin API
export async function getAdminUsers() {
    const response = await api.get(`/admin/users`);
    return response.data.users;
}

export async function updateAdminUser(userId, data) {
    const response = await api.put(`/admin/users/${userId}`, data);
    return response.data;
}

export async function getAdminFeatures() {
    const response = await api.get(`/admin/features`);
    return response.data.features;
}

export async function updateAdminFeature(name, data) {
    const response = await api.put(`/admin/features/${name}`, data);
    return response.data;
}

export async function getAdminStats() {
    const response = await api.get(`/admin/stats`);
    return response.data;
}
