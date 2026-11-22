import os


class SelfCheck:
    """NOVA monitors her own health and reports issues in plain language."""

    def __init__(self, llm=None, memory_file="memory.json"):
        self.llm = llm
        self.memory_file = memory_file
        self._reported = set()

    def run(self) -> list:
        issues = []

        # 1. AI brain reachable?
        if self.llm is not None:
            provider = self.llm.provider
            if provider is None:
                issues.append(
                    "my AI brain is offline — no Gemini key and Ollama isn't running, "
                    "so I'm running on basic keyword mode"
                )

        # 2. Memory file size sanity (>5MB of key-values is a lot for JSON)
        try:
            if os.path.exists(self.memory_file) and os.path.getsize(self.memory_file) > 5 * 1024 * 1024:
                issues.append("my memory file has grown quite large — we may want to move to a real database soon")
        except OSError:
            pass

        # 3. .env present?
        if not os.path.exists(".env") and not os.path.exists(os.path.join("..", ".env")):
            issues.append("I don't see a .env file — API keys may not be loading")

        return issues

    def new_issues(self) -> list:
        """Return only issues not reported before."""
        fresh = []
        for issue in self.run():
            key = issue[:60]
            if key not in self._reported:
                self._reported.add(key)
                fresh.append(issue)
        return fresh
