class ContextManager:

    def __init__(self):
        self.history = []

    def update(self, user_message, ai_reply):
        self.history.append({
            "user": user_message,
            "astra": ai_reply
        })

        # Keep only the last 20 conversations
        if len(self.history) > 20:
            self.history.pop(0)

    def last_message(self):
        if self.history:
            return self.history[-1]
        return None

    def get_history(self):
        return self.history

    def clear(self):
        self.history.clear()