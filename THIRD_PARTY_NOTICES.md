# Third-party code, models and assets

The root MIT license covers project-authored code. It does not grant additional rights in model weights, voices, portraits or upstream dependencies. Setup fetches pinned upstream code and assets instead of committing their full repositories here.

| Component | Source / terms | How used |
|---|---|---|
| DH_live | [Pinned source](https://github.com/kleinlee/DH_live/tree/4467e97cd97194c2c54762043cf121c6d313db12); upstream README declares MIT and separately discusses commercial likeness/logo authorization | Browser engine, WASM and sample assets downloaded by setup; `public/renderer-engine.js` is an adapted upstream rendering script |
| LivePortrait | [Source](https://github.com/KlingAIResearch/LivePortrait); MIT notice reproduced in `licenses/LivePortrait-MIT.txt` | Local expression adapter includes control-offset logic adapted from upstream `gradio_pipeline.py`; core source and weights downloaded separately |
| Qwen2.5 / MLX conversion | [Model card](https://huggingface.co/mlx-community/Qwen2.5-1.5B-Instruct-4bit) | Local dialogue weights; original model and conversion terms apply |
| Qwen3-TTS / MLX conversion | [Original code](https://github.com/QwenLM/Qwen3-TTS), [model card](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-6bit) | Local preset-voice synthesis; no private voice cloning data included |
| MLX / MLX LM / MLX Audio | [MLX](https://github.com/ml-explore/mlx), [MLX LM](https://github.com/ml-explore/mlx-lm), [MLX Audio](https://github.com/Blaizzy/mlx-audio) | Installed Python dependencies |
| faster-whisper / tiny.en | [Code](https://github.com/SYSTRAN/faster-whisper), [weights](https://huggingface.co/Systran/faster-whisper-tiny.en) | Local transcription |
| macOS system voices | Installed macOS services and their applicable terms | Optional runtime speech generation; no macOS voice files redistributed |

Do not remove the upstream avatar marks or infer a right to commercially use a sample likeness from a code license. Generated source/preview portraits remain local and Git-ignored. Obtain suitable rights for your own characters.

`examples/audio/` contains synthetic English phrases generated with the Qwen3-TTS Aiden preset, not human recordings or real-patient data. Its manifest identifies every clip and checksum. `public/counseling-room.png` is a generated environment illustration created for this prototype, not a photograph of a clinical facility.

The source revisions are pinned in `models.lock.json`; review upstream terms when replacing or distributing any component. This repository does not claim to have trained the upstream foundation models.
