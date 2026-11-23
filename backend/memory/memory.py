import json
import os


class Memory:

    def __init__(self, file=None):
        # Use env var for memory file path (for deployment), fallback to local
        self.file = file or os.environ.get("MEMORY_FILE_PATH", "memory.json")
        self.file = file

        if os.path.exists(self.file):
            with open(self.file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {}

    @staticmethod
    def _key(key: str, ns: str | None) -> str:
        return f"{ns}:{key}" if ns else key

    def save(self):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def remember(self, key, value, ns: str | None = None):
        self.data[self._key(key, ns)] = value
        self.save()

    def recall(self, key, ns: str | None = None):
        return self.data.get(self._key(key, ns))

    def forget(self, key, ns: str | None = None):
        k = self._key(key, ns)
        if k in self.data:
            del self.data[k]
            self.save()

    def all(self, ns: str | None = None):
        if not ns:
            return self.data
        prefix = f"{ns}:"
        return {k[len(prefix):]: v for k, v in self.data.items() if k.startswith(prefix)}

    def clear_ns(self, ns: str | None):
        if not ns:
            return
        prefix = f"{ns}:"
        for k in [k for k in self.data if k.startswith(prefix)]:
            del self.data[k]
        self.save()
