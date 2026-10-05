# Roadmap and support needed

| Priority | Workstream | Next deliverable | Support needed | Evidence of success |
|---|---|---|---|---|
| Now | Reproduction | Another contributor installs from a clean clone | Apple Silicon Mac; installation report | Recorded setup result without copied virtual environments |
| Now | Model adapters | Compare local Qwen with a selected second provider | Model access; fixed dialogue cases | Same inputs, explicit cost/latency and behavior comparison |
| Next | Speech reliability | Improve phrase prosody and abnormal-tail detection | Synthetic evaluation set; expert listening | Fewer failed/elongated outputs without deleting target words |
| Next | Patient behavior | Expert-grounded cue and retrieval state specification | Clinical collaborators; appropriately usable examples | Predefined differences across relevant, irrelevant and incomplete cues |
| Next | Expression integration | Align controlled facial events with speech | GPU experiment access; consented assets | Measured control accuracy and synchronization |
| Next | Shared service | Authenticated, resource-bounded deployment | Hosting, compute and networking support | Multi-session isolation and measured concurrency |
| Explore | Alternative renderers | Ditto / MuseTalk or another justified candidate | Scheduled NVIDIA GPU job | Same input audio, latency, memory and control comparison |

Candidate sources: [Ditto](https://github.com/antgroup/ditto-talkinghead), [MuseTalk](https://github.com/TMElyralab/MuseTalk). These are candidates, not integrated features. School cluster access supports scheduled experiments; a queued job is not automatically an always-on deployment.

Potential technical research includes state-conditioned timing, cue-history-sensitive behavior, speech/expression consistency and interruption recovery. These are hypotheses to evaluate against prior work, not claims of novelty or clinical validity. Scene reconstruction and full-body generation should be added only when the task requires spatial interaction.
