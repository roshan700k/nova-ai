import axios from "axios";

const API = "http://127.0.0.1:8000";

export async function sendMessage(message) {
    const response = await axios.post(`${API}/chat`, {
        message: message,
    });

    return response.data.reply;
}