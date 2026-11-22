import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from gtts import gTTS
from pydantic import BaseModel, Field

router = APIRouter(prefix="/voice", tags=["voice"])


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    lang: str = Field(default="en", max_length=8)


@router.post("/tts")
def tts(req: TTSRequest):
    "returns mp3 audio of ASTRA speaking"""
    buf = io.BytesIO()
    gTTS(text=req.text, lang=req.lang).write_to_fp(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="audio/mpeg")
