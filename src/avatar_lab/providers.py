"""Dialogue provider boundary. Audio, portrait and timing do not depend on the LLM."""

import json, os, threading, urllib.request, urllib.error
from pathlib import Path


class MLXProvider:
    name = "mlx"

    def __init__(self, root):
        from mlx_lm import load

        model_path = os.environ.get("AVATAR_LLM_MODEL") or str(root / "models/qwen")
        self.model_id = (
            (Path(model_path).name if os.path.isabs(model_path) else model_path)
            if os.environ.get("AVATAR_LLM_MODEL")
            else "mlx-community/Qwen2.5-1.5B-Instruct-4bit"
        )
        self.model, self.tokenizer = load(model_path)
        self.lock = threading.Lock()

    def generate(self, messages, *, max_tokens=100, temperature=0.35):
        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler

        with self.lock:
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            return generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=max_tokens,
                sampler=make_sampler(temp=temperature),
                verbose=False,
            )


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(self, root=None):
        self.model_id = os.environ.get("AVATAR_LLM_MODEL", "").strip()
        self.base_url = os.environ.get("AVATAR_LLM_BASE_URL", "").rstrip("/")
        self.api_key = os.environ.get("AVATAR_LLM_API_KEY", "")
        if not self.model_id or not self.base_url.startswith(("http://", "https://")):
            raise ValueError("Set AVATAR_LLM_MODEL and AVATAR_LLM_BASE_URL for the API provider.")
        self.timeout = max(1, min(180, float(os.environ.get("AVATAR_LLM_TIMEOUT", "60"))))

    def generate(self, messages, *, max_tokens=100, temperature=0.35):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        req = urllib.request.Request(
            self.base_url + "/chat/completions", data=json.dumps(payload).encode(), headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = json.load(response)
        except urllib.error.HTTPError as e:
            raise ValueError(
                f"Dialogue API returned HTTP {e.code}. Check the model, endpoint and credentials."
            ) from None
        except (urllib.error.URLError, TimeoutError):
            raise ValueError("Dialogue API unavailable or timed out. Check the configured endpoint.") from None
        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ValueError("Dialogue API must return choices[0].message.content.") from None
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Dialogue API returned no text.")
        return text


class FixtureProvider:
    name = "fixtures"
    model_id = "recorded-examples"

    def generate(self, messages, **kwargs):
        prompt = messages[-1]["content"].lower()
        if any(x in prompt for x in ["drink", "tea", "thirst"]):
            return "I would like... some tea, please."
        if any(x in prompt for x in ["live", "partner", "family"]):
            return "I live with my partner Sam."
        if any(x in prompt for x in ["time", "rush", "okay"]):
            return "Thank you... give me a moment."
        return "I enjoy gardening... and drinking tea."


PROVIDERS = {
    "mlx": MLXProvider,
    "openai_compatible": OpenAICompatibleProvider,
    "fixtures": lambda root: FixtureProvider(),
}


def create_provider(root, sample=False):
    name = "fixtures" if sample else os.environ.get("AVATAR_LLM_PROVIDER", "mlx")
    if name not in PROVIDERS:
        raise ValueError("Unknown dialogue provider. Register an adapter in providers.py.")
    return PROVIDERS[name](root)
