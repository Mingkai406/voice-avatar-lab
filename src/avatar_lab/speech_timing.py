"""Build a measured audio timeline from explicit, bounded speech and pause events."""

import base64, io, re, wave


def segmented_speech(data, synthesize_continuous):
    text = re.sub(r"\[.*?\]", "", str(data.get("text", "")).strip()[:1000])
    rhythm = data.get("rhythm", "marked")
    try:
        gap = max(0, min(3000, int(float(data.get("hesitation", 700)))))
    except (TypeError, ValueError):
        gap = 700
    if rhythm == "planned":
        plan = data.get("plan", [])
        if not isinstance(plan, list) or len(plan) > 200:
            raise ValueError("Invalid speech plan.")
        planned = []
        total_text = 0
        for event in plan:
            if not isinstance(event, dict):
                raise ValueError("Invalid speech event.")
            if event.get("kind") == "speech":
                fragment = re.sub(r"\[.*?\]", "", str(event.get("text", ""))).strip()
                total_text += len(fragment)
                if total_text > 1000:
                    raise ValueError("Speech plan is too long.")
                if fragment:
                    planned.append({"kind": "speech", "text": fragment, "label": "Speaking"})
            elif event.get("kind") == "pause":
                scale = max(0, min(2, float(event.get("scale", 1))))
                milliseconds = (
                    max(0, min(5000, round(float(event["duration_ms"]))))
                    if "duration_ms" in event
                    else min(5000, round(gap * scale))
                )
                labels = ["Restart pause", "Word-finding pause", "Hesitation pause", "Phrase pause"]
                planned.append(
                    {
                        "kind": "pause",
                        "milliseconds": milliseconds,
                        "label": event.get("label") if event.get("label") in labels else "Word-finding pause",
                    }
                )
    else:
        parts = (
            re.findall(r"[^\s.…]+", text)
            if rhythm == "words"
            else [p.strip() for p in re.split(r"\.{2,}|…+", text) if p.strip()]
        )
        planned = []
        for i, part in enumerate(parts):
            planned.append({"kind": "speech", "text": part, "label": "Speaking"})
            if i < len(parts) - 1:
                planned.append({"kind": "pause", "milliseconds": gap, "label": "Fragment pause"})
    if not any(x["kind"] == "speech" for x in planned):
        raise ValueError("Nothing to speak.")
    if len(planned) > 200:
        raise ValueError("Please use a shorter response.")
    chunks = []
    timeline = []
    position = 0
    cache = {}
    meta = {}
    quality_retries = []
    for event in planned:
        if event["kind"] == "pause":
            pcm = bytes(event["milliseconds"] * 32)
        else:
            part = event["text"]
            if part not in cache:
                d = synthesize_continuous({**data, "text": part, "pause": 0})
                with wave.open(io.BytesIO(base64.b64decode(d["audio"]))) as w:
                    pcm = w.readframes(w.getnframes())
                from array import array
                import sys

                samples = array("h")
                samples.frombytes(pcm)
                if sys.byteorder != "little":
                    samples.byteswap()
                active = [i for i, v in enumerate(samples) if abs(v) > 60]
                if active:
                    lo = max(0, active[0] - 640)
                    hi = min(len(samples), active[-1] + 641)
                    pcm = pcm[lo * 2 : hi * 2]
                cache[part] = (pcm, d)
                if d.get("quality_retry"):
                    quality_retries.append(part)
            pcm, meta = cache[part]
        chunks.append(pcm)
        duration = len(pcm) / 32000
        timeline.append(
            {k: v for k, v in event.items() if k != "milliseconds"}
            | {"start": round(position, 4), "duration": round(duration, 4)}
        )
        position += duration
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"".join(chunks))
    return {
        **{k: v for k, v in meta.items() if k not in ["audio", "duration"]},
        "audio": base64.b64encode(buf.getvalue()).decode(),
        "quality_retries": quality_retries,
        "duration": round(position, 3),
        "rhythm": rhythm,
        "hesitation": gap,
        "segments": timeline,
        "pause": data.get("pause", 150),
    }
