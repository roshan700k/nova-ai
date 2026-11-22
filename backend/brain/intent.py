class IntentDetector:

    def detect(self, message: str):

        text = message.lower()

        if any(word in text for word in ["hi", "hello", "hey"]):
            return "greeting"

        if any(word in text for word in ["remember", "save"]):
            return "memory"

        if any(word in text for word in ["open", "start", "launch"]):
            return "computer"

        if any(word in text for word in ["code", "python", "javascript"]):
            return "coding"

        return "chat"