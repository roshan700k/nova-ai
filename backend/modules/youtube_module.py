import re
import webbrowser
from urllib.parse import quote


class YouTubeModule:

    YT_WORDS = ("youtube", "you tube", "yt")
    ACTION_WORDS = ("play", "open", "search", "find", "watch", "latest",
                    "play me", "khol", "chalao", "bajao", "chala")
    MEDIA_WORDS = ("song", "music", "video", "movie", "hindi", "hits",
                   "gana", "gaana", "film")

    def think(self, message: str):

        text = message.lower().strip()

        has_youtube = any(w in text for w in self.YT_WORDS)
        has_action = any(w in text for w in self.ACTION_WORDS)

        # Explicit YouTube request, or media-ish request without the word
        if "arijit singh" in text:
            query = "Arijit Singh top songs"
            url = "https://www.youtube.com/results?search_query=" + quote(query)
            self._open_local(url)
            return f'Opening YouTube for "{query}" — [click here]({url})'
        elif has_youtube and has_action:
            query = self._extract_query(text)
        elif has_action and any(w in text for w in self.MEDIA_WORDS):
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
        for w in ("on youtube", "you tube", "youtube", "yt",
                  "play me", "play", "open", "khol do", "khol",
                  "chalao", "chala", "bajao", "search for", "search",
                  "find", "watch", "karo", "kar do"):
            q = q.replace(w, " ")
        q = re.sub(r"\s+", " ", q).strip(" ?.!")
        q = re.sub(r"^(for|to|me|please)\s+", "", q)
        return q
