# Contributing

Start with sample mode and a small issue. Public contributors can fork the repository; no invitation is needed to propose a pull request.

## Workflow

1. Check existing Issues and agree on the behavior or interface being changed.
2. Fork and create a descriptive branch, such as `speech/pause-boundaries`.
3. Keep changes focused; preserve the default local Qwen path unless the issue explicitly changes it.
4. Run `python3 -m unittest discover -s tests -v` and `python3 scripts/check_repository.py`.
5. For browser changes, test an actual conversation/replay/stop cycle. For model changes, record hardware, model revision, latency and representative failures.
6. Open a PR using the template. Explain the user-visible behavior and evidence.
7. Address review; a maintainer merges after required checks and review.

Do not commit `.env`, API keys, model weights, virtual environments, upstream checkouts, private paths, participant data or unapproved likenesses. Use synthetic examples for tests. Do not silently turn local inference into a remote call or swap voices after a failure.

## Module boundaries

- Dialogue adapters return text; speech adapters return canonical PCM WAV.
- Phrase plans preserve the intended words and expose timing changes.
- Renderer controls distinguish low-level mouth weights from semantic expressions.
- Clinical claims require appropriate evidence; synthetic behavior tests establish software behavior only.

For a new model, add configuration documentation, a mocked contract test, explicit failure handling and a manual integration report. CI should not require credentials or download multi-GB weights.

Incoming PRs use the MIT license for project-authored contributions unless explicitly stated and reviewed. Third-party code retains upstream notices and terms.
