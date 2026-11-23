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

export async function sendMessage(message, conversationId = null, signal = null) {
    const response = await api.post(`/chat`, {
        message: message,
        conversation_id: conversationId,
    }, signal ? { signal } : {});

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

export const API_URL = API;

export async function getSettings() {
    const response = await api.get(`/settings`);
    return response.data.settings || {};
}

export async function updateSettings(settings) {
    await api.put(`/settings`, { settings });
}

export async function clearMemoryApi() {
    await api.delete(`/memory`);
}

export async function clearAllChatsApi() {
    await api.delete(`/chats`);
}

// Monitor / Tasks / Research
export async function getSystemMonitor() {
    const response = await api.get(`/system-monitor`);
    return response.data;
}

export async function getTasks() {
    const response = await api.get(`/tasks`);
    return response.data.tasks || [];
}

export async function addTask(title, notes = "", due = "") {
    const response = await api.post(`/tasks`, { title, notes, due });
    return response.data;
}

export async function updateTask(taskId, fields) {
    const response = await api.put(`/tasks/${taskId}`, fields);
    return response.data;
}

export async function deleteTask(taskId) {
    await api.delete(`/tasks/${taskId}`);
}

export async function runResearch(query) {
    const response = await api.post(`/research`, { query });
    return response.data;
}

// PC Agent
export async function getAgentStatus() {
    const response = await api.get(`/agent/status`);
    return response.data;
}

export async function registerAgent(name = "My PC") {
    const response = await api.post(`/agent/register`, { name });
    return response.data;
}
