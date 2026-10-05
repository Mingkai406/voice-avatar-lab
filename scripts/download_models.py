"""Download exact model revisions; no model weights are stored in Git."""

import json, os
from pathlib import Path
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    for name, entry in json.loads((ROOT / "models.lock.json").read_text())["models"].items():
        print("Downloading " + name, flush=True)
        snapshot_download(
            entry["repo"],
            revision=entry["revision"],
            local_dir=ROOT / entry["path"],
            allow_patterns=entry.get("allow_patterns"),
            ignore_patterns=["*.md", ".gitattributes"],
        )
