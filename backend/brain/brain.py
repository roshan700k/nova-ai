import re

from brain.personality import Personality
from brain.intent import IntentDetector
from brain.emotion import EmotionDetector
from brain.reasoning import ReasoningEngine
from brain.responses import ResponseEngine
from brain.context import ContextManager
from brain.decision import DecisionEngine
from brain.module_manager import ModuleManager
from brain.llm import LLMBrain
from brain.companion import Companion
from brain.self_check import SelfCheck
from builder.builder import BuilderAgent
from creator.engine import CreatorEngine
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
        self.reasoning = ReasoningEngine(self.memory)
        self.response = ResponseEngine()
        self.context = ContextManager()
        self.youtube = YouTubeModule()
        self.computer = ComputerModule()
        self.llm = LLMBrain()
        self.companion = Companion(self.llm)
        self.self_check = SelfCheck(self.llm)
        self.builder = BuilderAgent(self.llm)
        self.creator = CreatorEngine(self.llm)
        self.outbox = []
    

        # Decision + Modules
        self.decision = DecisionEngine()
        self.module_manager = ModuleManager()

        # Register Modules
        self.loader = ModuleLoader()
        self.loader.load_modules()

    def think(self, message: str, user_id: int | None = None):
        ns = f"u{user_id}" if user_id else None
        reply = self._think(message, ns)
        self.companion.record_exchange(message, self.emotion.detect(message))
        return reply

    def _think(self, message: str, ns: str | None = None):

        if not message or not message.strip():
            return "I'm here. What would you like to do?"

        text = message.lower().strip()
        computer_reply = self.computer.think(message)

        if computer_reply:
          return computer_reply

        # ===== Memory =====

        if text.startswith("remember "):
            content = text.replace("remember ", "")

            if "=" in content:
                key, value = content.split("=", 1)
                self.memory.remember(key.strip(), value.strip(), ns=ns)
                return f"✅ I will remember {key.strip()}."

            return "Use: remember key=value"
        youtube_reply = self.youtube.think(message)

        if youtube_reply:
         return youtube_reply

        if text.startswith("what is ") or text.startswith("what's "):
            key = text.replace("what is ", "", 1).replace("what's ", "", 1).strip()

            candidates = {key, self.reasoning._normalize(key)}

            for candidate in candidates:
                value = self.memory.recall(candidate, ns=ns)
                if value:
                    return f"{candidate} = {value}"

            saved = self.reasoning.think(message, ns=ns)
            if saved:
                self.context.update(message, saved)
                return saved

            return "I don't remember that."

        # ===== Teach =====

        if text.startswith("teach:"):

            content = text.replace("teach:", "").strip()

            if "=" in content:
                q, a = content.split("=", 1)
                self.reasoning.learn(q.strip(), a.strip(), ns=ns)
                return "✅ Learned."

            return "Use: teach: question = answer"

        # ===== Creator mode: "make a video about X" =====

        if text.startswith("make") and "video" in text:
            topic = text.replace("make", "", 1).replace("video", "", 1).strip(" about")
            reply = self._creator_reply(topic or message)
            self.context.update(message, reply)
            return reply

        # ===== Builder mode: "build me X" / "create an app" =====

        if text.startswith(("build ", "create an app", "create a app", "make an app", "make a app")):
            reply = self.builder.handle(message)
            self.context.update(message, reply)
            return reply

        # ===== Real AI brain (Gemini -> Ollama -> keyword fallback) =====

        llm_reply = self.llm.think(
            message,
            self.context.get_history(),
            tone_hint=self.companion.tone_hint(),
        )

        if llm_reply:
            self.context.update(message, llm_reply)
            return llm_reply

        # ===== Module Selection =====

        if "python" in text or "code" in text:
            module = self.loader.get("coding_module")

        elif "browser" in text or "website" in text:
            module = self.loader.get("browser_module")

        elif "pdf" in text:
            module = self.loader.get("pdf_module")

        else:
            module = self.loader.get("chat_module")

        if module is not None:
            reply = module.think(message)

            if reply:
                self.context.update(message, reply)
                return reply

        # ===== Reasoning =====

        reply = self.reasoning.think(message, ns=ns)

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

    def _creator_reply(self, topic: str) -> str:
        # "make 5 videos about X" -> batch of scripts+ideas
        match = re.match(r"(\d+)\s*(?:videos?|videos?)?\s*(?:about|on|for)?\s*(.*)", topic)
        count = 1
        clean_topic = topic
        m = re.match(r"(\d+)\s+", topic)
        if m:
            count = min(int(m.group(1)), 5)
            clean_topic = topic[m.end():].strip(" about")

        if count > 1 or "idea" in topic or "script" in topic:
            ideas = self.creator.ideas(clean_topic or topic, count=count)
            if not ideas:
                return "My AI brain is offline — connect Gemini or start Ollama and I'll generate video ideas."
            lines = [f"Here are {len(ideas)} video ideas for '{clean_topic or topic}':\n"]
            for i, idea in enumerate(ideas, 1):
                lines.append(f"{i}. **{idea.get('title','?')}** (score {idea.get('score','?')}/10) — {idea.get('hook','')}")
            lines.append("\nSay 'make video: <title>' to produce one, or 'script: <title>' for just the script.")
            return "\n".join(lines)

        result = self.creator.make_video(clean_topic or topic)
        if result.get("error"):
            return result["error"]
        steps = ", ".join(result.get("steps", []))
        video = result.get("video", "")
        return (
            f"Done — video pipeline ran: {steps}.\n"
            f"Video file: {video or 'not rendered (moviepy missing?)'}\n"
            f"Upload queued for your approval (action id: {result.get('upload_action_id','-')}). "
            "Approve it via /actions/{id}/approve — it will upload as PRIVATE."
        )