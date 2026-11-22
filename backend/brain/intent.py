import re


class IntentDetector:

    def detect(self, message: str):

        text = message.lower()

        def has(words):
            return any(re.search(rf"\b{re.escape(w)}\b", text) for w in words)

        if has(["hi", "hello", "hey"]):
            return "greeting"

        if has(["remember", "save"]):
            return "memory"

        if has(["open", "start", "launch"]):
            return "computer"

        if has(["code", "python", "javascript"]):
            return "coding"

        return "chat"
