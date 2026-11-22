class EmotionDetector:

    def detect(self, message: str):

        text = message.lower()

        if any(word in text for word in [
            "happy", "great", "awesome", "good"
        ]):
            return "happy"

        if any(word in text for word in [
            "sad", "cry", "depressed", "upset"
        ]):
            return "sad"

        if any(word in text for word in [
            "angry", "mad", "hate"
        ]):
            return "angry"

        return "normal"