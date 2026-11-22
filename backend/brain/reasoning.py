from memory.memory import Memory


class ReasoningEngine:

    def __init__(self):
        self.memory = Memory()

    def learn(self, question: str, answer: str):
        self.memory.remember(question.lower(), answer)

    def think(self, message: str):

        text = message.lower().strip()

        # Check saved memory first
        saved = self.memory.recall(text)

        if saved:
            return saved

        # Built-in knowledge
        if "how are you" in text:
            return "I'm doing great! How can I help you today?"

        if "who are you" in text:
            return "I am ASTRA AI, created by Roshan."

        if "your name" in text or "what is your name" in text:
            return "My name is ASTRA."

        return None