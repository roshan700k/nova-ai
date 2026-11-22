class ResponseEngine:

    def greeting(self, owner):
        return f"👋 Hello {owner}! Nice to see you."

    def coding(self):
        return "👨‍💻 Coding module is coming soon."

    def computer(self):
        return "💻 Computer Control module is coming soon."

    def memory(self):
        return "🧠 Memory command detected."

    def unknown(self, message):
        return f"I understood: {message}"