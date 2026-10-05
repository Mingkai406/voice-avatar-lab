"""Recorded synthetic examples for contributor work without ML dependencies."""

import base64, io, json, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def synthesize(data):
    text = str(data.get("text", "")).strip()
    manifest = json.loads((ROOT / "examples/audio/index.json").read_text())
    entry = manifest["clips"].get(text)
    if entry is None:
        raise ValueError("Sample mode supports the provided example replies only. Use full mode for new speech.")
    raw = (ROOT / "examples/audio" / entry["file"]).read_bytes()
    with wave.open(io.BytesIO(raw)) as w:
        duration = w.getnframes() / w.getframerate()
    return {
        "audio": base64.b64encode(raw).decode(),
        "duration": duration,
        "voice": "Recorded Aiden example",
        "rate": 160,
        "pause": 0,
    }
