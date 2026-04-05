"""Voice engine — speech-to-text (Whisper) and text-to-speech (Piper).

Optional feature: install with `pip install axon[voice]`.
"""

from __future__ import annotations

import io
import tempfile
import wave
from pathlib import Path
from typing import TYPE_CHECKING

from axon.logging import get_logger

logger = get_logger("axon.voice")

# Lazy imports — only loaded when voice is actually used
_whisper_model = None
_vad_model = None
_piper_voices: dict[str, object] = {}


class VoiceUnavailableError(Exception):
    """Raised when voice dependencies are not installed."""


def _check_voice_deps() -> None:
    """Check that voice dependencies are importable."""
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        raise VoiceUnavailableError(
            "Voice features require: pip install axon[voice]"
        )


# ── Speech-to-Text ───────────────────────────────────────────────────


def get_whisper_model(model_size: str = "base"):
    """Get or create the Whisper model (lazy singleton)."""
    global _whisper_model
    if _whisper_model is None:
        _check_voice_deps()
        from faster_whisper import WhisperModel

        logger.info(f"Loading Whisper model: {model_size}")
        _whisper_model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
        )
        logger.info("Whisper model ready")
    return _whisper_model


def transcribe(
    audio_bytes: bytes,
    sample_rate: int = 16000,
    audio_format: str = "pcm",
) -> str:
    """Transcribe audio bytes to text.

    Args:
        audio_bytes: Audio data — raw 16-bit PCM, or an encoded format (webm, etc.).
        sample_rate: Sample rate (only used for raw PCM).
        audio_format: Format hint — "pcm" for raw PCM, "webm/opus", "webm", etc.

    Returns:
        Transcribed text string.
    """
    model = get_whisper_model()

    # Determine file extension and whether to wrap in WAV
    if audio_format in ("pcm", "raw"):
        suffix = ".wav"
        # Wrap raw PCM in a WAV container
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            with wave.open(tmp, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(audio_bytes)
    else:
        # Encoded format — write as-is, faster-whisper uses ffmpeg to decode
        suffix = ".webm" if "webm" in audio_format else f".{audio_format.split('/')[0]}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(audio_bytes)

    try:
        segments, info = model.transcribe(
            tmp_path,
            beam_size=5,
            language="en",
            vad_filter=True,
        )
        text = " ".join(segment.text.strip() for segment in segments)
        return text.strip()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ── Text-to-Speech ───────────────────────────────────────────────────


def _find_voice_model(voice_id: str) -> Path:
    """Locate a Piper voice model ONNX file.

    Searches:
      1. models/piper/ directory relative to this package
      2. Current working directory
      3. Bare voice_id as-is (absolute path or cwd fallback)
    """
    candidates = [
        Path(__file__).parent.parent / "models" / "piper" / f"{voice_id}.onnx",
        Path.cwd() / "models" / "piper" / f"{voice_id}.onnx",
        Path(f"{voice_id}.onnx"),
        Path(voice_id),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        f"Piper voice model not found for '{voice_id}'. "
        f"Searched: {[str(c) for c in candidates]}"
    )


def get_piper_voice(voice_id: str = "en_US-lessac-medium"):
    """Get or create a Piper TTS voice (lazy cache)."""
    global _piper_voices
    if voice_id not in _piper_voices:
        _check_voice_deps()
        from piper import PiperVoice

        model_path = _find_voice_model(voice_id)
        logger.info(f"Loading Piper voice: {voice_id} from {model_path}")
        _piper_voices[voice_id] = PiperVoice.load(str(model_path))
        logger.info(f"Piper voice ready: {voice_id}")
    return _piper_voices[voice_id]


def synthesize(
    text: str,
    voice_id: str = "en_US-lessac-medium",
    speed: float = 1.0,
) -> bytes:
    """Synthesize text to WAV audio bytes.

    Args:
        text: The text to speak.
        voice_id: Piper voice model ID.
        speed: Speaking speed multiplier.

    Returns:
        WAV file bytes (16-bit mono PCM with header).
    """
    from piper.config import SynthesisConfig

    voice = get_piper_voice(voice_id)

    syn_config = SynthesisConfig(length_scale=1.0 / speed)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(voice.config.sample_rate)

        for audio_chunk in voice.synthesize(text, syn_config=syn_config):
            wf.writeframes(audio_chunk.audio_int16_bytes)

    return buf.getvalue()


# ── Voice availability check ─────────────────────────────────────────


def is_available() -> bool:
    """Check if voice dependencies are installed."""
    try:
        _check_voice_deps()
        return True
    except VoiceUnavailableError:
        return False
