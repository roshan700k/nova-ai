class ChartModule:

    def think(self, message: str):

        text = message.lower()

        if "hello" in text:
            return "Hello! I'm NOVA."

        if "how are you" in text:
            return "I'm doing great. How can I help you?"

        return None