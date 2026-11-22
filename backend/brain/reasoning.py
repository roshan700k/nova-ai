from memory.memory import Memory


QUESTION_PREFIXES = (
    "what is ", "what's ", "whats ", "who is ", "who's ",
    "tell me ", "do you know ", "do you remember ",
)


class ReasoningEngine:

    def __init__(self, memory: Memory | None = None):
        self.memory = memory or Memory()

    def learn(self, question: str, answer: str, ns: str | None = None):
        self.memory.remember(self._normalize(question), answer, ns=ns)

    def think(self, message: str, ns: str | None = None):

        text = message.lower().strip()

        # Exact match first, then normalized question form
        saved = (
            self.memory.recall(text, ns=ns)
            or self.memory.recall(self._normalize(text), ns=ns)
        )

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

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = text.strip("? ")
        for prefix in QUESTION_PREFIXES:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip("? ")
                break
        # Drop leading articles so "the capital of france" -> "capital of france"
        changed = True
        while changed:
            changed = False
            for article in ("the ", "a ", "an "):
                if normalized.startswith(article):
                    normalized = normalized[len(article):].strip()
                    changed = True
        return normalized
