import re
import webbrowser
from urllib.parse import quote


class YouTubeModule:

    ACTION_WORDS = ("play", "open", "search", "find", "watch", "latest", "play me")

    def think(self, message: str):

        text = message.lower().strip()

        has_youtube = "youtube" in text
        has_action = any(w in text for w in self.ACTION_WORDS)

        # Explicit YouTube request, or media-ish request without the word
        if "arijit singh" in text:
            query = "Arijit Singh top songs"
        elif has_youtube and has_action:
            query = self._extract_query(text)
        elif has_action and any(w in text for w in ("song", "music", "video", "movie", "hindi", "hits")):
            # "play latest hindi hits" style — assume YouTube
            query = self._extract_query(text)
        else:
            return None

        if not query:
            query = "trending"

        url = "https://www.youtube.com/results?search_query=" + quote(query)

        webbrowser.open(url)

        return f"Opening YouTube and searching for {query}."

    @staticmethod
    def _extract_query(text: str) -> str:
        # Remove command words and "on youtube" style tails
        q = text
        for w in ("on youtube", "youtube", "play me", "play", "open",
                  "search for", "search", "find", "watch"):
            q = q.replace(w, " ")
        q = re.sub(r"\s+", " ", q).strip(" ?.!")
        q = re.sub(r"^(for|to|me)\s+", "", q)
        return q
