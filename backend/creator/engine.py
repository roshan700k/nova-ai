"""NOVA Creator Engine: idea -> script -> voiceover -> video -> metadata.

Pipeline:
  1. research/ideas  (LLM + optional YouTube/Data API trends)
  2. script           (LLM writes narration script)
  3. voiceover        (edge-tts or gTTS -> mp3)
  4. video assembly   (moviepy: stock clips or slides + subtitles -> mp4)
  5. metadata         (title, description, tags, thumbnail prompt)

Everything queues through ActionBroker before upload/publish.
"""

import json
import os
import re
import subprocess

from services.actions import broker

try:
    # moviepy 2.x API
    from moviepy import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, ColorClip
    MOVIEPY = True
except Exception:
    try:
        # moviepy 1.x API
        from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, ColorClip
        MOVIEPY = True
    except Exception:
        MOVIEPY = False


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50] or "video"


class CreatorEngine:

    def __init__(self, llm=None):
        self.llm = llm
        self.out_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "projects", "videos"
        )
        os.makedirs(self.out_dir, exist_ok=True)

    # ---------------------------------------------------------
    # 1+2. Ideas and scripts
    # ---------------------------------------------------------

    def ideas(self, topic: str, count: int = 5) -> list:
        prompt = (
            f"You are a YouTube strategist. Topic: {topic}. "
            f"Give {count} video ideas that could perform well. "
            "Reply ONLY with JSON: {\"ideas\": [{\"title\": ..., \"hook\": ..., "
            "\"angle\": ..., \"score\": 1-10}]}. No markdown."
        )
        raw = self.llm.think(prompt, []) if self.llm and self.llm.provider else None
        if not raw:
            return []
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        try:
            return json.loads(match.group(0)).get("ideas", []) if match else []
        except Exception:
            return []

    def script(self, title: str, angle: str = "", length_seconds: int = 60) -> str:
        words = int(length_seconds / 2.5)  # ~150wpm
        prompt = (
            f"Write a YouTube video script titled '{title}'"
            + (f" with angle: {angle}" if angle else "")
            + f". Target ~{words} words ({length_seconds}s narration). "
            "Hook in first 5 seconds. Conversational tone. No stage directions."
        )
        return self.llm.think(prompt, []) if self.llm and self.llm.provider else ""

    # ---------------------------------------------------------
    # 3. Voiceover (free: edge-tts -> mp3, fallback gTTS)
    # ---------------------------------------------------------

    def voiceover(self, text: str, out_path: str) -> str | None:
        # Try edge-tts first (better voices, free)
        try:
            import sys
            proc = subprocess.run(
                [sys.executable, "-m", "edge_tts",
                 "--voice", "en-IN-NeerjaNeural",
                 "--text", text[:3000], "--write-media", out_path],
                capture_output=True, text=True, timeout=120,
            )
            if proc.returncode == 0 and os.path.exists(out_path):
                return out_path
        except FileNotFoundError:
            pass
        # Fallback: gTTS
        try:
            from gtts import gTTS
            gTTS(text=text[:3000], lang="en").save(out_path)
            return out_path
        except Exception as exc:
            print(f"[creator] voiceover failed: {exc}")
            return None

    # ---------------------------------------------------------
    # 4. Video assembly (moviepy)
    # ---------------------------------------------------------

    def assemble(self, audio_path: str, title: str, out_name: str | None = None) -> str | None:
        if not MOVIEPY:
            print("[creator] moviepy not installed")
            return None
        try:
            audio = AudioFileClip(audio_path)
            duration = audio.duration

            # Title card rendered with PIL (no ImageMagick needed)
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (1280, 720), (10, 5, 20))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arialbd.ttf", 64)
            except Exception:
                font = ImageFont.load_default()
            text = title[:60]
            bbox = draw.textbbox((0, 0), text, font=font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((1280 - w) / 2, (720 - h) / 2), text, fill=(230, 200, 255), font=font)
            card_path = os.path.join(self.out_dir, f"{_slug(out_name or title)}_card.png")
            img.save(card_path)

            clip = ColorClip((1280, 720), color=(10, 5, 20)).with_duration(duration)
            txt = ImageClip(card_path).with_duration(duration)
            video = CompositeVideoClip([clip, txt]).with_audio(audio)
            out = os.path.join(self.out_dir, f"{_slug(out_name or title)}.mp4")
            video.write_videofile(out, fps=24, codec="libx264", audio_codec="aac")
            return out
        except Exception as exc:
            print(f"[creator] assemble failed: {exc}")
            return None

    # ---------------------------------------------------------
    # 5. Metadata
    # ---------------------------------------------------------

    def metadata(self, title: str, script_text: str) -> dict:
        prompt = (
            f"YouTube video titled '{title}'. Script excerpt: {script_text[:800]}. "
            "Reply ONLY JSON: {\"description\": ..., \"tags\": [...], "
            "\"thumbnail_concept\": ...}. No markdown."
        )
        raw = self.llm.think(prompt, []) if self.llm and self.llm.provider else ""
        match = re.search(r"\{.*\}", raw or "", re.DOTALL)
        try:
            return json.loads(match.group(0)) if match else {"description": "", "tags": []}
        except Exception:
            return {"description": "", "tags": []}

    # ---------------------------------------------------------
    # Full pipeline
    # ---------------------------------------------------------

    def make_video(self, topic: str, title: str | None = None,
                   length_seconds: int = 60) -> dict:
        result = {"topic": topic, "steps": []}

        script_text = self.script(title or topic, length_seconds=length_seconds)
        if not script_text:
            result["error"] = "no script generated (AI brain offline?)"
            return result
        result["script"] = script_text
        result["steps"].append("script")

        slug = _slug(title or topic)
        audio_path = os.path.join(self.out_dir, f"{slug}.mp3")
        if self.voiceover(script_text, audio_path):
            result["voiceover"] = audio_path
            result["steps"].append("voiceover")

        video_path = self.assemble(audio_path, title or topic) if os.path.exists(audio_path) else None
        if video_path:
            result["video"] = video_path
            result["steps"].append("video")

        result["metadata"] = self.metadata(title or topic, script_text)
        result["steps"].append("metadata")

        # Queue upload for approval (never auto-publish)
        if video_path:
            aid = broker.request(
                kind="upload_video",
                description=f"NOVA wants to upload '{title or topic}' to YouTube (private)",
                payload={"video": video_path, "title": title or topic,
                         "metadata": result["metadata"]},
            )
            result["upload_action_id"] = aid
            result["steps"].append("upload_queued")

        return result
