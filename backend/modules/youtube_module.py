import re
import webbrowser
from urllib.parse import quote


class YouTubeModule:

    YT_RE = re.compile(r"\b(yt|youtube|you\s*tube)\b")
    ACTION_RE = re.compile(
        r"\b(play|open|search|find|watch|latest|khol|chalao|bajao|chala|"
        r"play me|khol do|gaana|gana)\b"
    )
    MEDIA_WORDS = ("song", "music", "video", "movie", "hindi", "hits",
                   "gana", "gaana", "film", "cricket", "lofi", "lo-fi")

    def think(self, message: str):

        text = message.lower().strip()

        has_youtube = bool(self.YT_RE.search(text))
        has_action = bool(self.ACTION_RE.search(text))
        # Long sentences that merely mention YouTube mid-thought are
        # questions for the brain, not media commands.
        short = len(text.split()) <= 12

        # Explicit YouTube request, or media-ish request without the word
        if "arijit singh" in text and short:
            query = "Arijit Singh top songs"
            url = "https://www.youtube.com/results?search_query=" + quote(query)
            self._open_local(url)
            return f'Opening YouTube for "{query}" — [click here]({url})'
        elif has_youtube and has_action and short:
            query = self._extract_query(text)
        elif has_action and short and any(w in text for w in self.MEDIA_WORDS):
            # "play latest hindi hits" style — assume YouTube
            query = self._extract_query(text)
        else:
            return None

        if not query:
            query = "trending"

        url = "https://www.youtube.com/results?search_query=" + quote(query)
        self._open_local(url)

        return f'Opening YouTube for "{query}" — [click here]({url})'

    @staticmethod
    def _open_local(url: str):
        # Only meaningful on the user's own machine; on a server it's a no-op
        try:
            webbrowser.open(url)
        except Exception:
            pass

    @staticmethod
    def _extract_query(text: str) -> str:
        # Remove command words and "on youtube" style tails
        q = text
        q = re.sub(r"\b(on|from|via)\s+(youtube|you\s*tube|yt)\b", " ", q)
        q = re.sub(r"\b(youtube|you\s*tube|yt)\b", " ", q)
        for w in ("play me", "khol do", "search for", "please",
                  "play", "open", "khol", "chalao", "chala", "bajao",
                  "search", "find", "watch", "karo", "kar do", "me", "for"):
            q = re.sub(rf"\b{re.escape(w)}\b", " ", q)
        q = re.sub(r"\s+", " ", q).strip(" ?.!")
        q = re.sub(r"^(to|the|a|an)\s+", "", q)
        # Cut trailing clauses: "lofi or something", "music but hindi"
        q = re.split(r"\s+(?:or|but|because|if|when)\s+", q)[0]
        return q.strip(" ?!.")
