"""File uploads for chat — images, PDFs and text files that NOVA can
analyze (vision via Gemini). Stored per-user in SQLite."""

from fastapi import APIRouter, Request, UploadFile, File, HTTPException

from api.auth import current_user
from database.database import create_upload, get_upload, delete_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_SIZE = 15 * 1024 * 1024  # 15 MB — Gemini inline limit is ~20 MB
ALLOWED_PREFIXES = ("image/", "text/")
ALLOWED_MIMES = {"application/pdf"}


def _uid(request: Request):
    user = current_user(request)
    return user["id"] if user else None


@router.post("")
async def upload(request: Request, file: UploadFile = File(...)):
    mime = (file.content_type or "").lower()
    ok = mime.startswith(ALLOWED_PREFIXES) or mime in ALLOWED_MIMES
    if not ok:
        raise HTTPException(
            status_code=415,
            detail="Supported: images, PDF, and text files")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 15 MB)")
    uid = create_upload(_uid(request), file.filename or "file", mime, data)
    return {"id": uid, "name": file.filename, "mime": mime, "size": len(data)}


@router.get("/{upload_id}")
def meta(upload_id: int, request: Request):
    up = get_upload(upload_id, _uid(request))
    if not up:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": up["id"], "name": up["name"], "mime": up["mime"]}


@router.delete("/{upload_id}")
def remove(upload_id: int, request: Request):
    delete_upload(upload_id, _uid(request))
    return {"ok": True}
