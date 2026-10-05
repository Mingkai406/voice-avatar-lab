# Initial release verification

Date: 2026-10-05. Reference machine: Apple M4 Pro, 24 GB unified memory.

| Check | Result | Scope |
|---|---|---|
| Source setup | Passed | Pinned upstream renderer and expression repositories fetched into an independent checkout |
| Dependency setup | Passed | Two fresh Python 3.12 environments installed from committed version lists |
| Model downloads | Passed | All four pinned Hugging Face revisions downloaded independently |
| Sample browser | Passed | Chrome renderer, scripted speech, stop and editable 1.2 s pause |
| Core/API tests | 16 passed locally | Actual silence, phrase preservation, cue history, synthetic clip hashes, sample API and mocked dialogue-provider contract |
| Default dialogue | Passed | MLX Qwen returned a phrase-level reply in the standalone package |
| Neural speech | Passed, experimental | One cold 1.36 s utterance took about 21.5 s to prepare; not a throughput benchmark |
| Expression inference | Passed | Independent MPS frame generation; about 2.3 s for the tested inference call, excluding initial model loading |
| Repository checks | Passed | Public-source scan, local documentation links and syntax checks |

GitHub Actions separately reports the committed revision's automated checks. It does not load the full models. Fresh installation on a second physical Mac, microphone behavior in a real meeting, concurrent sessions, model-specific external APIs and GPU-cluster integration are still unverified.

One observed local warning concerns duplicate AVFoundation receiver classes in the installed PyAV/OpenCV libraries. The tested expression call succeeded, but model-environment cleanup is a useful follow-up if it causes instability on another machine.
