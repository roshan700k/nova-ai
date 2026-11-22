from brain.personality import Personality
from brain.intent import IntentDetector
from brain.emotion import EmotionDetector
from brain.reasoning import ReasoningEngine
from brain.responses import ResponseEngine
from brain.context import ContextManager
from brain.decision import DecisionEngine
from brain.module_manager import ModuleManager
from memory.memory import Memory

from modules.chat_module import ChatModule
from modules.coding_module import CodingModule
from modules.browser_module import BrowserModule
from modules.pdf_module import PdfModule

from modules.module_loader import ModuleLoader
from modules.youtube_module import YouTubeModule
from modules.computer_module import ComputerModule


class AstraBrain:

    def __init__(self):

        # Core Systems
        self.intent = IntentDetector()
        self.memory = Memory()
        self.personality = Personality()
        self.emotion = EmotionDetector()
        self.reasoning = ReasoningEngine()
        self.response = ResponseEngine()
        self.context = ContextManager()
        self.youtube = YouTubeModule()
        self.computer = ComputerModule()
    

        # Decision + Modules
        self.decision = DecisionEngine()
        self.module_manager = ModuleManager()

        # Register Modules
        self.loader = ModuleLoader()
        self.loader.load_modules()

    def think(self, message: str):

        text = message.lower().strip()
        computer_reply = self.computer.think(message)

        if computer_reply:
          return computer_reply

        # ===== Memory =====

        if text.startswith("remember "):
            content = text.replace("remember ", "")

            if "=" in content:
                key, value = content.split("=", 1)
                self.memory.remember(key.strip(), value.strip())
                return f"✅ I will remember {key.strip()}."

            return "Use: remember key=value"
        youtube_reply = self.youtube.think(message)

        if youtube_reply:
         return youtube_reply

        if text.startswith("what is "):
            key = text.replace("what is ", "").strip()

            value = self.memory.recall(key)

            if value:
                return f"{key} = {value}"

            return "I don't remember that."

        # ===== Teach =====

        if text.startswith("teach:"):

            content = text.replace("teach:", "").strip()

            if "=" in content:
                q, a = content.split("=", 1)
                self.reasoning.learn(q.strip(), a.strip())
                return "✅ Learned."

            return "Use: teach: question = answer"

        # ===== Module Selection =====

        if "python" in text or "code" in text:
            module = self.loader.get("coding_module")

        elif "browser" in text or "website" in text:
            module = self.loader.get("browser_module")

        elif "pdf" in text:
            module = self.loader.get("pdf_module")

        else:
            module = self.loader.get("chat_module")

        reply = module.think(message)

        if reply:
            self.context.update(message, reply)
            return reply

        # ===== Reasoning =====

        reply = self.reasoning.think(message)

        if reply:
            self.context.update(message, reply)
            return reply

        # ===== Intent =====

        intent = self.intent.detect(message)

        if intent == "greeting":
            reply = self.response.greeting(self.personality.owner)

        elif intent == "coding":
            reply = self.response.coding()

        elif intent == "computer":
            reply = self.response.computer()

        elif intent == "memory":
            reply = self.response.memory()

        else:
            reply = self.response.unknown(message)

        self.context.update(message, reply)

        return reply