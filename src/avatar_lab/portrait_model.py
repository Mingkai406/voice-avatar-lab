"""LivePortrait inference adapter; control offsets adapted from upstream MIT gradio_pipeline.py."""

import os, sys, time, threading, base64, io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
sys.path.insert(0, str(ROOT / "vendor/LivePortrait"))
_LOCK = threading.Lock()
_ENGINE = None


def render(data):
    global _ENGINE
    with _LOCK:
        from PIL import Image
        import numpy as np
        from src.live_portrait_wrapper import LivePortraitWrapper
        from src.config.inference_config import InferenceConfig

        if _ENGINE is None:
            w = LivePortraitWrapper(InferenceConfig(flag_use_half_precision=False))
            image = np.array(Image.open(ROOT / "public/source-crop.jpg").convert("RGB"))
            x = w.prepare_source(image)
            info = w.get_kp_info(x)
            _ENGINE = (w, info, w.extract_feature_3d(x), w.transform_keypoint(info))
        w, info, f, xs = _ENGINE
        t = time.perf_counter()

        def val(name, lo, hi):
            return max(lo, min(hi, float(data.get(name, 0))))

        smile = val("smile", -0.5, 1.5)
        brow = val("brow", -10, 10)
        gaze = val("gaze", -10, 10)
        yaw = val("yaw", -15, 15)
        k = {a: b.clone() for a, b in info.items()}
        e = k["exp"]
        for i, j, v in [
            (20, 1, -0.01),
            (14, 1, -0.02),
            (17, 1, 0.0065),
            (17, 2, 0.003),
            (13, 1, -0.00275),
            (16, 1, -0.00275),
            (3, 1, -0.0035),
            (7, 1, -0.0035),
        ]:
            e[0, i, j] += smile * v
        if brow > 0:
            e[0, 1, 1] += 0.001 * brow
            e[0, 2, 1] -= 0.001 * brow
        else:
            e[0, 1, 0] -= 0.001 * brow
            e[0, 2, 0] += 0.001 * brow
            e[0, 1, 1] += 0.0003 * brow
            e[0, 2, 1] -= 0.0003 * brow
        e[0, 11, 0] += (0.0007 if gaze > 0 else 0.001) * gaze
        e[0, 15, 0] += (0.001 if gaze > 0 else 0.0007) * gaze
        k["yaw"] += yaw
        xd = w.transform_keypoint(k)
        rgb = w.parse_output(w.warp_decode(f, xs, xd)["out"])[0]
        buf = io.BytesIO()
        Image.fromarray(rgb).save(buf, format="JPEG", quality=95)
        return {
            "image": base64.b64encode(buf.getvalue()).decode(),
            "seconds": round(time.perf_counter() - t, 3),
            "device": w.device,
            "controls": {"smile": smile, "brow": brow, "gaze": gaze, "yaw": yaw},
        }
