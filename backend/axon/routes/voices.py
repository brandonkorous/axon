"""Voice model management routes — list, download, and manage Piper voices."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from axon.logging import get_logger
from axon.voice_catalog import (
    download_voice,
    fetch_catalog,
    installed_voices,
    list_voices_summary,
)

logger = get_logger("axon.voices")

router = APIRouter()


def _parse_voice_key(key: str) -> dict:
    """Parse metadata from a voice key like 'en_US-lessac-medium'."""
    parts = key.split("-")
    lang_parts = parts[0].split("_") if parts else []
    return {
        "key": key,
        "name": key,
        "language": lang_parts[0] if lang_parts else "",
        "language_name": "",
        "country": lang_parts[1] if len(lang_parts) > 1 else "",
        "quality": parts[2] if len(parts) > 2 else "",
        "size_mb": 0,
        "installed": True,
    }


@router.get("")
async def list_voices():
    """List all available Piper voices with install status."""
    try:
        catalog = await fetch_catalog()
        voices = list_voices_summary(catalog)
    except Exception:
        logger.exception("Failed to fetch voice catalog, returning installed only")
        voices = [_parse_voice_key(k) for k in installed_voices()]
    return {"voices": voices}


@router.get("/installed")
async def list_installed():
    """List only locally installed voice IDs."""
    return {"voices": installed_voices()}


class DownloadRequest(BaseModel):
    voice_key: str


@router.post("/download")
async def download(req: DownloadRequest):
    """Download a Piper voice model from Hugging Face."""
    try:
        path = await download_voice(req.voice_key)
        return {"status": "ok", "voice_key": req.voice_key, "path": str(path)}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Voice not found: {req.voice_key}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
