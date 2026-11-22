import os
import subprocess
import webbrowser
from urllib.parse import quote


class ComputerModule:

    def think(self, message: str):

        text = message.lower().strip()

        # -----------------------------
        # GOOGLE SEARCH
        # -----------------------------
        if "search google for" in text:
            query = text.split("search google for", 1)[1].strip()

            if query:
                url = "https://www.google.com/search?q=" + quote(query)
                webbrowser.open(url)

                return f"Searching Google for {query}."

        # -----------------------------
        # OPEN GOOGLE
        # -----------------------------
        if "open google" in text:
            webbrowser.open("https://www.google.com")
            return "Opening Google."

        # -----------------------------
        # OPEN YOUTUBE
        # -----------------------------
        if "open youtube" in text:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube."

        # -----------------------------
        # OPEN GITHUB
        # -----------------------------
        if "open github" in text:
            webbrowser.open("https://github.com")
            return "Opening GitHub."

        # -----------------------------
        # OPEN CHROME
        # -----------------------------
        if "open chrome" in text:
            try:
                subprocess.Popen(
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                )
                return "Opening Google Chrome."
            except Exception:
                try:
                    subprocess.Popen(
                        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                    )
                    return "Opening Google Chrome."
                except Exception:
                    webbrowser.open("https://www.google.com")
                    return "I could not find Chrome directly, so I opened Google."

        # -----------------------------
        # OPEN VS CODE
        # -----------------------------
        if "open vs code" in text or "open visual studio code" in text:
            try:
                subprocess.Popen(["code"])
                return "Opening Visual Studio Code."
            except Exception:
                return "I could not open Visual Studio Code."

        # -----------------------------
        # OPEN CALCULATOR
        # -----------------------------
        if "open calculator" in text or "open calc" in text:
            try:
                subprocess.Popen(["calc.exe"])
                return "Opening Calculator."
            except Exception:
                return "I could not open Calculator."

        # -----------------------------
        # OPEN NOTEPAD
        # -----------------------------
        if "open notepad" in text:
            try:
                subprocess.Popen(["notepad.exe"])
                return "Opening Notepad."
            except Exception:
                return "I could not open Notepad."

        # -----------------------------
        # OPEN FILE EXPLORER
        # -----------------------------
        if (
            "open file explorer" in text
            or "open explorer" in text
            or "open my files" in text
        ):
            try:
                subprocess.Popen(["explorer.exe"])
                return "Opening File Explorer."
            except Exception:
                return "I could not open File Explorer."

        # -----------------------------
        # OPEN DOWNLOADS
        # -----------------------------
        if "open downloads" in text or "open my downloads" in text:
            try:
                downloads = os.path.join(
                    os.path.expanduser("~"),
                    "Downloads"
                )

                os.startfile(downloads)

                return "Opening your Downloads folder."
            except Exception:
                return "I could not open your Downloads folder."

        # -----------------------------
        # OPEN DESKTOP
        # -----------------------------
        if "open desktop" in text or "open my desktop" in text:
            try:
                desktop = os.path.join(
                    os.path.expanduser("~"),
                    "Desktop"
                )

                os.startfile(desktop)

                return "Opening your Desktop."
            except Exception:
                return "I could not open your Desktop."

        # -----------------------------
        # OPEN SETTINGS
        # -----------------------------
        if "open settings" in text:
            try:
                subprocess.Popen(["start", "ms-settings:"], shell=True)
                return "Opening Windows Settings."
            except Exception:
                return "I could not open Windows Settings."

        # -----------------------------
        # OPEN TASK MANAGER
        # -----------------------------
        if "open task manager" in text:
            try:
                subprocess.Popen(["taskmgr.exe"])
                return "Opening Task Manager."
            except Exception:
                return "I could not open Task Manager."

        # -----------------------------
        # NOTHING DETECTED
        # -----------------------------
        return None