import axios from "axios";

const API = "http://localhost:8000";

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