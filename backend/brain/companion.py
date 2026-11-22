import os
import time


class Companion:
    """ASTRA's emotional/proactive layer: mood tracking, check-ins,
    and self-issue reporting so she feels like a friend, not software."""

    def __init__(self, llm=None, memory_file="memory.json"):
        self.llm = llm
        self.memory_file = memory_file
        self.mood = "normal"          # happy / sad / angry / normal
        self.last_user_activity = time.time()
        self.last_checkin = 0.0
        self.checkin_interval = 15 * 60  # seconds between proactive check-ins
        self.quiet_hours = (0, 7)     # no check-ins 00:00-07:00

    # ---------------------------------------------------------
    # Mood
    # ---------------------------------------------------------

    def record_exchange(self, user_message: str, mood: str):
        self.mood = mood or "normal"
        self.last_user_activity = time.time()

    def tone_hint(self) -> str:
        hints = {
            "happy": "The user seems happy — match their energy, be warm.",
            "sad": "The user seems down — be extra gentle and supportive.",
            "angry": "The user seems frustrated — stay calm and helpful.",
            "normal": "",
        }
        return hints.get(self.mood, "")

    # ---------------------------------------------------------
    # Proactive check-ins
    # ---------------------------------------------------------

    def checkin_due(self) -> bool:
        now = time.time()
        hour = time.localtime().tm_hour
        if hour < self.quiet_hours[1] or hour >= 24 - self.quiet_hours[0]:
            return False
        idle = now - self.last_user_activity
        return idle > self.checkin_interval and (now - self.last_checkin) > self.checkin_interval

    def checkin_message(self, issues: list | None = None) -> str:
        self.last_checkin = time.time()

        if issues:
            problem = issues[0]
            return (
                f"Hey, quick heads up — {problem} "
                "I fixed what I could, but you should know."
            )

        if self.llm and self.llm.provider:
            prompt = (
                "You are ASTRA, the user's personal AI friend. "
                "The user has been quiet for a while. "
                "Send ONE short, warm, proactive message — ask how their day is going "
                "or mention something useful. Max 2 sentences. No questions stacked."
            )
            reply = self.llm.think(prompt, [])
            if reply:
                return reply.strip()

        return "Hey! Just checking in — how's your day going?"
