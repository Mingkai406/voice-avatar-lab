#!/usr/bin/env python3
"""Run from any directory; configuration stays on the server."""

import argparse, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_env():
    path = ROOT / ".env"
    allowed = {
        "AVATAR_LLM_PROVIDER",
        "AVATAR_LLM_MODEL",
        "AVATAR_LLM_BASE_URL",
        "AVATAR_LLM_API_KEY",
        "AVATAR_LLM_TIMEOUT",
    }
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, sep, value = line.partition("=")
            if sep and name.strip() in allowed:
                os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VOICE Avatar Lab local development server")
    parser.add_argument("--sample", action="store_true", help="Recorded replies and audio; no Python ML dependencies")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    load_env()
    if args.sample:
        os.environ["AVATAR_SAMPLE_MODE"] = "1"
    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
    sys.path.insert(0, str(ROOT / "src"))
    from avatar_lab.server import serve

    serve(args.port)
