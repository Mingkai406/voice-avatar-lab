import base64, hashlib, io, json, sys, unittest, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from avatar_lab.behavior_plan import make_plan, phrase_text, retrieval_turn
from avatar_lab.speech_timing import segmented_speech
from avatar_lab.voice_adapter import normalize_turn
from avatar_lab.sample_runtime import synthesize


class BehaviorTests(unittest.TestCase):
    def test_cues_retain_history_without_false_retrieval(self):
        state = {}
        for prompt, expected in [
            ("What is this?", 0),
            ("It starts with", 0),
            ("Take your time", 0),
            ("It starts with ba", 0),
            ("rain", 1),
            ("It starts with um", 3),
            ("Take your time", 3),
        ]:
            _, state, _ = retrieval_turn(prompt, state)
            self.assertEqual(state["stage"], expected)
        self.assertEqual(len(state["cue_history"]), 7)

    def test_phrase_words_preserved(self):
        self.assertEqual(
            phrase_text("I... enjoy... gardening... and... drinking... tea."), "I enjoy gardening... and drinking tea."
        )
        self.assertEqual(phrase_text("I enjoy gardening."), "I enjoy gardening.")

    def test_manual_gap_is_actual_silence(self):
        plan = make_plan("I enjoy gardening... and drinking tea.")
        plan[1]["duration_ms"] = 1350
        result = segmented_speech({"text": "example", "rhythm": "planned", "plan": plan, "hesitation": 100}, synthesize)
        pause = result["segments"][1]
        self.assertEqual(pause["duration"], 1.35)
        with wave.open(io.BytesIO(base64.b64decode(result["audio"]))) as w:
            pcm = w.readframes(w.getnframes())
        a = round(pause["start"] * 16000) * 2
        b = round((pause["start"] + pause["duration"]) * 16000) * 2
        self.assertFalse(any(pcm[a + 8 : b - 8]))
        self.assertAlmostEqual(sum(s["duration"] for s in result["segments"]), result["duration"], places=2)

    def test_plan_bounds_and_empty_rejection(self):
        with self.assertRaises(ValueError):
            segmented_speech({"rhythm": "planned", "plan": []}, synthesize)
        p = make_plan("I enjoy gardening... and drinking tea.")
        p[1]["duration_ms"] = 99999
        self.assertEqual(segmented_speech({"rhythm": "planned", "plan": p}, synthesize)["segments"][1]["duration"], 5)

    def test_voice_adapter_canonical(self):
        raw = b"\0\0" * 160
        d = normalize_turn({"format": "pcm_16000", "audioBase64": base64.b64encode(raw).decode()})
        self.assertAlmostEqual(d["duration"], 0.01)
        with self.assertRaises(ValueError):
            normalize_turn({"format": "mp3"})

    def test_fixture_hashes(self):
        manifest = json.loads((ROOT / "examples/audio/index.json").read_text())
        for text, e in manifest["clips"].items():
            raw = (ROOT / "examples/audio" / e["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), e["sha256"])
            with wave.open(io.BytesIO(raw)) as w:
                self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, 16000))

    def test_sample_cue_audio_coverage(self):
        for prompt, state in [
            ("name", {}),
            ("name", {"attempts": 1}),
            ("rain", {}),
            ("It starts with", {}),
            ("Take your time", {}),
            ("It starts with um", {}),
            ("umbrella", {}),
            ("name", {"stage": 3}),
        ]:
            text, _, _ = retrieval_turn(prompt, state)
            for e in make_plan(text):
                if e["kind"] == "speech":
                    self.assertGreater(synthesize({"text": e["text"]})["duration"], 0)


if __name__ == "__main__":
    unittest.main()
