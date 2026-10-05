# Dialogue providers and model experiments

The browser sends input to `/api/chat`. The server builds patient instructions and history, calls a provider, then turns the returned **text** into a speech plan. Changing the LLM does not change the speech backend or portrait renderer.

| Provider | Configure | Scope |
|---|---|---|
| `mlx` | Default; optional `AVATAR_LLM_MODEL=/absolute/path/to/model` | Local MLX-compatible text model; tokenizer must have a chat template |
| `openai_compatible` | Base URL, installed/provider model ID, optional server-side API key | Non-streaming text Chat Completions contract |
| `fixtures` | `python3 run.py --sample` | Fixed examples; no model reasoning |

Qwen2.5 is the **dialogue model**. Qwen3-TTS is the **speech model**. They are independent. Switching `AVATAR_LLM_MODEL` does not switch TTS.

## Local default

No `.env` file is required. The pinned Qwen2.5-1.5B-Instruct model in `models/qwen` is loaded on MLX. To experiment with another local model, obtain compatible weights separately, point `AVATAR_LLM_MODEL` to their directory and restart. Memory requirements depend on the replacement model.

## API-backed dialogue

Copy `.env.example` to `.env`. Configure an endpoint whose base includes its API prefix (often `/v1`); the adapter appends `/chat/completions` exactly once. It sends `model`, `messages`, `max_tokens`, `temperature`, and `stream: false`.

The response must contain `choices[0].message.content` as a nonempty string. Compatibility is an API contract, not a guarantee that every service supports every parameter. Adapt the request for services requiring different token parameters, structured content, Responses API, tools, audio or streaming. Credentials never appear in browser settings or status responses. Errors omit server response bodies to avoid exposing credentials or request details.

The included tests use a local mock HTTP service. No paid API request is part of CI. A remote provider receives dialogue text and may charge for usage. Select only endpoints suitable for the data you intend to use.

## Add your own adapter

```python
class MyProvider:
    name = "my_provider"
    def __init__(self, root):
        self.model_id = "your-model-id"
        # Load once; read credentials from the server environment.
    def generate(self, messages, *, max_tokens=100, temperature=.35):
        # Return text only; raise a clear error on failure.
        return "Your generated response"
```

Register it in `PROVIDERS` in `src/avatar_lab/providers.py`, select `AVATAR_LLM_PROVIDER=my_provider`, and add tests. Do not accept arbitrary provider URLs or Python import paths from browser requests. A stateful model should protect inference with a lock.

Preserve the shared patient prompt and case facts when comparing models. Record model ID/revision, provider, generation settings, prompt, hardware, latency and failure cases. Evaluate content, timing and behavior separately; an attractive portrait is not evidence of patient fidelity.

## Speech backend extension

`synthesize(data)` returns base64 canonical mono PCM16 WAV at 16 kHz and its duration. `speech_timing.py` inserts measured silence and returns timed segments. New speech backends must preserve repetitions, avoid reading stage directions and report failures instead of silently changing providers. The current Qwen3 worker is isolated in `.venv-tts`.
