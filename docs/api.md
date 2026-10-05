# Local API contracts

The development server binds to `127.0.0.1`. Cross-origin POST requests are rejected; browser and API should share an origin. API responses use JSON unless the endpoint explicitly receives recording bytes.

| Endpoint | Input | Output |
|---|---|---|
| `GET /api/status` | — | Model readiness, provider name, sample mode, neural availability; no credentials |
| `POST /api/chat` | `prompt`, `mode`, `profile`, `history`, `patient_state` | `text`, provider, generation time, state and speech `plan` |
| `POST /api/say` | `text`, `backend`, voice/rate settings, `rhythm`, `hesitation`, optional `plan` | Base64 WAV, duration, preparation time and timed `segments` |
| `POST /api/transcribe` | Raw browser recording bytes | Reviewed-before-send text; full mode only |
| `POST /api/portrait` | `smile`, `brow`, `gaze`, `yaw` | Base64 JPEG, measured time and controls; full mode only |
| `POST /api/voice-turn` | Normalized raw PCM turn | Canonical WAV and unmapped control metadata |

## Example pause plan

```json
[
  {"kind": "speech", "text": "I enjoy gardening", "label": "Speaking"},
  {"kind": "pause", "label": "Phrase pause", "scale": 0.55},
  {"kind": "speech", "text": "and drinking tea.", "label": "Speaking"}
]
```

A pause's `scale` multiplies base `hesitation` in milliseconds. Optional `duration_ms` overrides the scale for that gap, bounded to 0–5000 ms. The actual response timeline uses seconds: `start`, `duration`, `kind`, `text` or `label`. Exact pause duration is inserted in the WAV; it is not merely a UI animation.

The portrait bridge receives `{type: "speak", audio, id, segments}`. It emits `speech-started`, `segment-started`, `speech-progress`, `speech-ended` and renderer errors. The parent checks both origin and iframe source.

## VOICE audio import

```json
{"responseText":"Example response","audioBase64":"BASE64_RAW_PCM","format":"pcm_16000","turnIndex":1}
```

Audio is signed 16-bit little-endian, mono, 16 kHz, without a WAV header. The adapter adds the header. `emotionCode` and `motionCode` are retained as metadata, not interpreted as face controls. See `examples/voice-turn.schema.json`.
