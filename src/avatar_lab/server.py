"""Loopback development server. External dialogue calls occur only with an explicitly configured API provider."""

import base64
import io
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
import uuid
import wave
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[2]
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HOME"] = str(ROOT / ".hf-cache")
PUBLIC = ROOT / "public"
ENGINE = ROOT / "vendor/DH_live/web_demo/static"
RUNTIME = ROOT / "runtime"
RUNTIME.mkdir(exist_ok=True)
LOCK = threading.Lock()
ASR_LOCK = threading.Lock()
READY = {"llm": False, "asr": False, "error": None}
PROVIDER = ASR = None
SAMPLE = os.environ.get("AVATAR_SAMPLE_MODE") == "1"
CASE = (
    "You are Alex, a fictional adult in a communication-training demonstration. "
    "You live with your partner Sam, enjoy gardening and tea, and previously worked in a library. "
    "Stay in the patient role. Speak English only. Answer the student directly in 1 or 2 short sentences, "
    "under 35 words. Never write stage directions, labels or medical advice. "
    "Do not invent medical history. You are practicing communication, not asking the student to act as a patient. "
)


def initialize():
    global PROVIDER, ASR
    try:
        from .providers import create_provider

        PROVIDER = create_provider(ROOT, SAMPLE)
        READY["llm"] = True
        if not SAMPLE:
            from faster_whisper import WhisperModel

            ASR = WhisperModel(str(ROOT / "models/whisper"), device="cpu", compute_type="int8", cpu_threads=4)
            READY["asr"] = True
    except Exception as exc:
        READY["error"] = str(exc)
        print("Initialization failed:", exc, flush=True)


def number(value, low, high, default):
    try:
        return max(low, min(high, float(value)))
    except (TypeError, ValueError):
        return default


def chat(data):
    prompt = str(data.get("prompt", "")).strip()[:1000]
    if not prompt:
        raise ValueError("Please enter a question.")
    mode = data.get("mode", "chat")
    stage = data.get("stage", 0)
    before = time.perf_counter()
    if mode == "cue":
        from .behavior_plan import retrieval_turn

        text, patient_state, reason = retrieval_turn(prompt, data.get("patient_state", {"stage": stage}))
        stage = patient_state["stage"]
        provider = "Explicit cue rules (illustrative)"
    else:
        if not READY["llm"]:
            raise ValueError("Local language model is still loading. Try again shortly.")
        profile = data.get("profile", "conversational")
        instruction = CASE + (
            "Use a short reply of about 5 to 18 words. Preserve natural multiword phrases. "
            "Show occasional word-finding difficulty with one or two ... boundaries. "
            "Do not put ... after every word. Mix fluent phrases with a difficult retrieval. "
            "An occasional um or a restart is allowed, but not in every reply. "
            "Style examples: I enjoy gardening... and... um... drinking tea. "
            "I would like... some tea, please. I live with my... my partner Sam. "
            "Answer the actual question using Alex facts, not an unrelated example. "
            "Do not add stage directions or a diagnosis. "
            if profile == "wordfinding"
            else "Speak naturally and conversationally."
        )
        messages = [{"role": "system", "content": instruction}]
        history = data.get("history", [])
        if not isinstance(history, list):
            raise ValueError("Invalid conversation history.")
        for msg in history[-8:]:
            if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": str(msg.get("content", ""))[:1000]})
        messages.append({"role": "user", "content": prompt})
        text = PROVIDER.generate(messages, max_tokens=100, temperature=0.35)
        text = re.sub(r"<[^>]+>|\*[^*]*\*", "", text).strip()[:600]
        if not text:
            raise ValueError("The local model returned an empty response. Please retry.")
        reason = "Configured dialogue provider response; no clinical validity claim"
        if profile == "wordfinding":
            from .behavior_plan import phrase_text

            marked = phrase_text(text)
            if marked != text:
                text = marked
                reason = "Local model words; dense markers consolidated into phrases by the demo"
        provider = PROVIDER.name + " · " + PROVIDER.model_id
    elapsed = round(time.perf_counter() - before, 3)
    from .behavior_plan import make_plan

    state = patient_state if mode == "cue" else None
    return {
        "text": text,
        "stage": stage,
        "reason": reason,
        "provider": provider,
        "generation_s": elapsed,
        "patient_state": state,
        "plan": make_plan(text, state["last_cue"] if state else None),
    }


def synthesize_continuous(data):
    text = str(data.get("text", "")).strip()[:1000]
    if not text:
        raise ValueError("Nothing to speak.")
    # Strip embedded macOS speech commands before inserting only our own timing controls.
    text = re.sub(r"\[.*?\]", "", text)
    rate = int(number(data.get("rate"), 20, 220, 150))
    pause = int(number(data.get("pause"), 0, 1800, 350))
    voice = data.get("voice", "Daniel")
    if voice not in ["Samantha", "Daniel", "Karen"]:
        voice = "Daniel"
    native_rate = max(80, rate)
    tempo = min(1.0, rate / 80)
    # Compensate explicit pauses before slowing the whole waveform.
    inserted_pause = round(pause * tempo)
    speech = re.sub(r"(\.{2,}|[.!?])\s*", lambda m: m.group(1) + f" [[slnc {inserted_pause}]] ", text)
    tag = uuid.uuid4().hex
    aiff, wav = RUNTIME / f"{tag}.aiff", RUNTIME / f"{tag}.wav"
    slowed = RUNTIME / f"{tag}-slow.wav"
    try:
        subprocess.run(
            ["/usr/bin/say", "-v", voice, "-r", str(native_rate), "-o", str(aiff), speech],
            check=True,
            capture_output=True,
            timeout=35,
        )
        subprocess.run(
            ["/usr/bin/afconvert", str(aiff), str(wav), "-f", "WAVE", "-d", "LEI16@16000", "-c", "1"],
            check=True,
            capture_output=True,
            timeout=15,
        )
        if tempo < 1:
            import imageio_ffmpeg

            # atempo preserves pitch; use chained factors in the supported >=0.5 range.
            remaining = tempo
            factors = []
            while remaining < 0.5:
                factors.append("atempo=0.5")
                remaining /= 0.5
            factors.append(f"atempo={remaining:.6f}")
            subprocess.run(
                [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-nostdin",
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(wav),
                    "-af",
                    ",".join(factors),
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s16le",
                    str(slowed),
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )
            slowed.replace(wav)
        # Repack afconvert output: it includes a 4044-byte FLLR chunk.
        # Keep the browser decoder and the WASM model on identical canonical PCM WAV.
        with wave.open(str(wav), "rb") as w:
            duration = w.getnframes() / w.getframerate()
            pcm = w.readframes(w.getnframes())
        packed = io.BytesIO()
        with wave.open(packed, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(pcm)
        audio = packed.getvalue()
        return {
            "audio": base64.b64encode(audio).decode(),
            "duration": round(duration, 3),
            "rate": rate,
            "pause": pause,
            "voice": voice,
            "tempo": tempo,
            "native_rate": native_rate,
        }
    finally:
        aiff.unlink(missing_ok=True)
        wav.unlink(missing_ok=True)
        slowed.unlink(missing_ok=True)


def synthesize(data):
    from .speech_timing import segmented_speech
    from .behavior_plan import make_plan
    from .neural_speech import synthesize as neural_synthesize

    backend = data.get("backend", "system")
    if SAMPLE:
        from .sample_runtime import synthesize as synth
    else:
        synth = neural_synthesize if backend == "qwen3" else synthesize_continuous
    rhythm = data.get("rhythm", "planned")
    text = str(data.get("text", ""))
    before = time.perf_counter()
    if rhythm == "planned":
        plan = data.get("plan") or make_plan(text)
        result = segmented_speech({**data, "plan": plan}, synth)
    elif rhythm == "words" or (rhythm == "marked" and re.search(r"\.{2,}|…+", text)):
        result = segmented_speech(data, synth)
    else:
        result = {**synth(data), "rhythm": rhythm, "segments": []}
    return {**result, "backend": backend, "preparation_s": round(time.perf_counter() - before, 3)}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Do not persist conversation contents or recordings.

    def translate_path(self, path):
        p = unquote(urlparse(path).path)
        if p.startswith("/engine/"):
            base, rel = ENGINE, p[len("/engine/") :]
        else:
            base, rel = PUBLIC, p.lstrip("/") or "index.html"
        resolved = (base / rel).resolve()
        return str(resolved if resolved.is_relative_to(base.resolve()) else PUBLIC / "404")

    def reply(self, data, status=200):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/status":
            from .neural_speech import available

            return self.reply(
                {
                    **READY,
                    "tts": "macOS / Qwen3-TTS",
                    "neural_available": not SAMPLE and available(),
                    "sample_mode": SAMPLE,
                    "dialogue_provider": PROVIDER.name if PROVIDER else None,
                    "avatar": "DH_live WebAssembly",
                    "version": 2,
                }
            )
        return super().do_GET()

    def do_POST(self):
        expected = f"http://{self.headers.get('Host')}"
        if self.headers.get("Origin") not in (None, expected):
            return self.reply({"error": "Cross-origin requests are not allowed."}, 403)
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 < length <= 12_000_000:
                raise ValueError("Request is empty or too large.")
            raw = self.rfile.read(length)
            if self.path == "/api/transcribe":
                if not READY["asr"]:
                    raise ValueError("Local speech recognition is still loading.")
                with ASR_LOCK:
                    segments, info = ASR.transcribe(io.BytesIO(raw), language="en", beam_size=1, vad_filter=True)
                    transcript = " ".join(seg.text.strip() for seg in segments).strip()
                return self.reply({"text": transcript})
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object.")
            if self.path == "/api/chat":
                return self.reply(chat(data))
            if self.path == "/api/voice-turn":
                from .voice_adapter import normalize_turn

                return self.reply(normalize_turn(data))
            if self.path == "/api/portrait":
                if SAMPLE:
                    raise ValueError("Expression generation requires the full installation.")
                from .portrait_model import render

                return self.reply(render(data))
            if self.path == "/api/say":
                return self.reply(synthesize(data))
            self.reply({"error": "Not found"}, 404)
        except Exception as exc:
            self.reply({"error": str(exc)}, 400)


def serve(port=8765):
    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535.")
    threading.Thread(target=initialize, daemon=True).start()
    print(f"VOICE Avatar Lab: http://127.0.0.1:{port}", flush=True)
    print("Mode: recorded examples" if SAMPLE else "Mode: configured AI provider", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
