class DecisionEngine:

    def decide(self, message: str):

        text = message.lower()

        if any(word in text for word in ["python", "code", "program", "bug"]):
            return "coding"

        if any(word in text for word in ["browser", "website", "google"]):
            return "browser"

        if "pdf" in text:
            return "pdf"

        return "chat"