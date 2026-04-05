"""Piper voice catalog — browse and download voice models from Hugging Face.

Voices are stored in models/piper/ relative to the backend root.
The catalog is fetched from rhasspy/piper-voices on Hugging Face.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from axon.logging import get_logger

logger = get_logger("axon.voice_catalog")

VOICES_JSON_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/voices.json"
)
HF_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"

MODELS_DIR = Path(__file__).parent.parent / "models" / "piper"

# In-memory cache of the voice catalog (fetched once per process)
_catalog_cache: dict[str, Any] | None = None


def _models_dir() -> Path:
    """Ensure and return the models directory."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR


def installed_voices() -> list[str]:
    """Return voice IDs that have both .onnx and .onnx.json locally."""
    d = _models_dir()
    return sorted(
        p.stem
        for p in d.glob("*.onnx")
        if (d / f"{p.stem}.onnx.json").exists()
    )


async def fetch_catalog(force: bool = False) -> dict[str, Any]:
    """Fetch the Piper voices.json catalog from Hugging Face.

    Results are cached in memory. Use force=True to refresh.
    """
    global _catalog_cache
    if _catalog_cache is not None and not force:
        return _catalog_cache

    import httpx

    logger.info("Fetching Piper voice catalog from Hugging Face...")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(VOICES_JSON_URL)
        resp.raise_for_status()
        _catalog_cache = resp.json()

    logger.info(f"Catalog loaded: {len(_catalog_cache)} voices")
    return _catalog_cache


def _voice_download_urls(catalog: dict[str, Any], voice_key: str) -> tuple[str, str]:
    """Get the .onnx and .onnx.json download URLs for a voice key.

    voice_key is the top-level key in voices.json, e.g. "en_US-lessac-medium".
    """
    voice = catalog.get(voice_key)
    if not voice:
        raise KeyError(f"Voice not found in catalog: {voice_key}")

    files = voice.get("files", {})

    onnx_path = None
    json_path = None
    for file_key in files:
        if file_key.endswith(".onnx") and not file_key.endswith(".onnx.json"):
            onnx_path = file_key
        elif file_key.endswith(".onnx.json"):
            json_path = file_key

    if not onnx_path or not json_path:
        raise ValueError(f"Missing model files in catalog for: {voice_key}")

    return (HF_BASE_URL + onnx_path, HF_BASE_URL + json_path)


async def download_voice(voice_key: str) -> Path:
    """Download a Piper voice model to the local models directory.

    Returns the path to the .onnx file.
    """
    d = _models_dir()
    onnx_dest = d / f"{voice_key}.onnx"
    json_dest = d / f"{voice_key}.onnx.json"

    # Already downloaded?
    if onnx_dest.exists() and json_dest.exists():
        logger.info(f"Voice already downloaded: {voice_key}")
        return onnx_dest

    catalog = await fetch_catalog()
    onnx_url, json_url = _voice_download_urls(catalog, voice_key)

    import httpx

    logger.info(f"Downloading voice: {voice_key}")
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        # Download .onnx
        resp = await client.get(onnx_url)
        resp.raise_for_status()
        onnx_dest.write_bytes(resp.content)
        logger.info(f"  {onnx_dest.name}: {len(resp.content) / 1024 / 1024:.1f} MB")

        # Download .onnx.json
        resp = await client.get(json_url)
        resp.raise_for_status()
        json_dest.write_bytes(resp.content)

    logger.info(f"Voice downloaded: {voice_key}")
    return onnx_dest


def list_voices_summary(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a simplified list of voices from the catalog.

    Returns a list suitable for the frontend voice selector.
    """
    local = set(installed_voices())
    result = []

    for key, voice in catalog.items():
        lang = voice.get("language", {})
        # Estimate size from files
        files = voice.get("files", {})
        size_bytes = sum(f.get("size_bytes", 0) for f in files.values())

        result.append({
            "key": key,
            "name": voice.get("name", key),
            "language": lang.get("code", ""),
            "language_name": lang.get("name_english", ""),
            "country": lang.get("country", ""),
            "quality": voice.get("quality", ""),
            "speakers": len(voice.get("speaker_id_map", {})) or 1,
            "size_mb": round(size_bytes / 1024 / 1024, 1),
            "installed": key in local,
        })

    # Sort: installed first, then by language + name
    result.sort(key=lambda v: (not v["installed"], v["language"], v["key"]))
    return result
