# Installation and recovery

## Requirements

- Git and Python 3.12+ on the command line.
- Chrome with WebGL enabled for the browser renderer.
- Full mode: Apple Silicon macOS; development reference M4 Pro with 24 GB unified memory. This is a tested reference, not a verified minimum specification.
- Allow at least 10 GB free for full setup. Installation time depends on network and wheel availability; there is no guaranteed one-minute installation.

`python3 scripts/setup.py --profile sample` fetches the pinned DH_live browser source. It installs no Python ML dependencies. `python3 run.py --sample` uses committed synthetic clips and scripted dialogue, not a live LLM. Recording, neural voice settings and expression generation are unavailable.

`python3 scripts/setup.py --profile full` creates `.venv` and `.venv-tts` using uv. If uv is absent, it installs uv 0.8.22 into a repository-local `.bootstrap` environment. It installs pinned dependencies, fetches two upstream repositories, downloads pinned weights and creates local-only expression inputs from the upstream sample. Nothing is installed into system Python.

The source/model manifest is `models.lock.json`. Source checkouts under `vendor/` are detached at exact commits. A mismatched existing checkout is not overwritten. Move it aside intentionally, or update the manifest in a reviewed PR.

## Re-run and diagnose

```bash
python3 scripts/doctor.py --profile sample
.venv/bin/python scripts/doctor.py --profile full
```

| Symptom | Action |
|---|---|
| Git missing on macOS | Install Git / Command Line Tools, then rerun setup |
| Download interrupted | Rerun setup; Hugging Face resumes/reuses cached files |
| Port 8765 occupied | Start with `--port 8766`; open the matching address |
| Missing model / loading error | Read the server message; run `.venv/bin/python scripts/download_models.py` |
| System voice missing | Select an installed macOS voice or use Qwen3-TTS; available voices differ by OS |
| Unusually long neural ending | Retry, simplify the phrase or switch to System voice; retries may add latency |
| Microphone unavailable | Use localhost in Chrome, allow microphone access, or type instead |
| Portrait blank | Check renderer assets with doctor and enable WebGL; inspect browser errors |
| Expression page missing input | Run `.venv/bin/python scripts/prepare_portrait.py` after full setup |
| API provider fails | Verify base URL, model ID and credentials; do not paste keys into Issues |

The server defaults to offline model loading. Setup downloads happen in a separate process. An API dialogue provider makes network calls only when you choose it.

## Optional: your own expression input

Use a consented, square, front-facing face crop:

```bash
.venv/bin/python scripts/prepare_portrait.py --image /path/to/face-crop.jpg
```

This changes only the separate expression experiment. It does not create a new talking-avatar asset. Generated crop and preview files are ignored by Git.

## Installation validation status

The release is checked in a separate checkout on the development Mac. Sample API tests also run in Linux CI. This does not establish full inference compatibility on every Apple Silicon model or OS version. Please report fresh-machine results with hardware, OS, Python, commit and exact failing step.
