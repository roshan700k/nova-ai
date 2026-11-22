import webbrowser
from urllib.parse import quote


class YouTubeModule:

    def think(self, message: str):

        text = message.lower().strip()

        if "arijit singh" in text:
            query = "Arijit Singh top songs"
        elif "youtube" in text and ("play" in text or "open" in text):
            query = text.replace("open", "").replace("play", "").replace("youtube", "").strip()
        else:
            return None

        if not query:
            query = "Arijit Singh top songs"

        url = "https://www.youtube.com/results?search_query=" + quote(query)

        webbrowser.open(url)

        return f"Opening YouTube and searching for {query}."