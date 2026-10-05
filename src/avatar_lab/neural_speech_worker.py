"""Isolated, persistent MLX speech process. Requests and results stay on this Mac."""

import os, sys, json, io, wave, base64, time, contextlib, re
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
ROOT = Path(__file__).resolve().parents[2]
model = None
for line in sys.stdin:
    try:
        request = json.loads(line)
        start = time.perf_counter()
        with contextlib.redirect_stdout(sys.stderr):
            import numpy as np
            from scipy.signal import resample_poly
            from mlx_audio.tts.utils import load_model

            if model is None:
                model = load_model(str(ROOT / "models/qwen3-tts"))
            articulation = "Use a normal speaking pace and clear, brief word endings."
            styles = {
                "neutral": "Speak clearly in a conversational tone. ",
                "hesitant": "Use a slightly uncertain conversational tone. ",
                "warm": "Use a friendly conversational tone. ",
            }
            requested_style = request.get("delivery", "neutral")
            # Guard the native audio BEFORE user-requested slowing. This heuristic
            # rejects abnormal tails; it never truncates or silently speeds up speech.
            words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", request["text"])
            limit = (
                max(2.0, 0.09 * sum(map(len, words)) + 0.6 + 0.2 * len(words))
                if len(words) <= 2
                else 0.65 * len(words) + 0.025 * sum(map(len, words)) + 1
            )
            # Tone instructions are unreliable for isolated words; keep articulation
            # clear there and express hesitation through the explicit pause plan.
            style_used = "neutral" if len(words) <= 2 else requested_style
            attempts = []
            adjusted = False
            for attempt in range(2):
                instruction = styles.get(style_used, styles["neutral"]) if attempt == 0 else styles["neutral"]
                results = list(
                    model.generate_custom_voice(
                        text=request["text"].strip()
                        if re.search(r"[.!?]$", request["text"].strip())
                        else request["text"].strip() + ".",
                        speaker=request.get("speaker", "Aiden"),
                        language="English",
                        instruct="Speak clearly at a normal conversational pace."
                        if len(words) <= 2
                        else instruction + articulation,
                        temperature=0.4 if attempt == 0 else 0.2,
                        max_tokens=600,
                        verbose=False,
                    )
                )
                samples = np.concatenate([np.array(r.audio).reshape(-1) for r in results])
                sr = results[0].sample_rate
                native_duration = len(samples) / sr
                attempts.append(round(native_duration, 3))
                if native_duration <= limit:
                    adjusted = attempt > 0
                    break
            else:
                raise ValueError(
                    "Generated speech had an abnormally long ending. "
                    "Please retry or choose System voice. No audio was played."
                )
            from math import gcd

            divisor = gcd(sr, 16000)
            samples = resample_poly(samples, 16000 // divisor, sr // divisor)
            pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes()
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(16000)
                w.writeframes(pcm)
        result = {
            "audio": base64.b64encode(buffer.getvalue()).decode(),
            "duration": len(pcm) / 32000,
            "generation_s": round(time.perf_counter() - start, 3),
            "backend": "qwen3",
            "voice": request.get("speaker", "Aiden"),
            "native_duration": round(native_duration, 3),
            "quality_retry": adjusted,
            "delivery_used": "neutral" if adjusted else style_used,
            "short_fragment_delivery": len(words) <= 2 and requested_style != "neutral",
            "attempt_durations": attempts,
        }
    except Exception as exc:
        result = {"error": str(exc)}
    print(json.dumps(result), flush=True)
