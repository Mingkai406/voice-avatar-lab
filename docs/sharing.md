# Sharing and team development

A public repository lets anyone download or fork code without an invitation. It does not provide a running AI endpoint. GitHub Pages could host static documentation, but cannot run this Python/MLX inference service.

| Goal | Use |
|---|---|
| Explore interface/timing | Clone, install sample assets, run sample mode |
| Reproduce the Mac prototype | Full setup on Apple Silicon; download pinned models |
| Contribute without write permission | Fork, feature branch, pull request |
| Collaborate with write permission | Branch in this repository and open a pull request |
| Let others try one running instance | Build an authenticated shared service separately |
| Compare GPU models | Run scheduled experiments behind the same documented interfaces |

`main` is the reviewed baseline. Releases identify known versions. Avoid editing each other's environments or sharing virtual-environment folders. Model weights are downloaded from upstream and remain outside Git.

Before shared hosting, add authentication, TLS, request limits, per-session isolation, inference queuing and cancellation/resource policies, then test concurrency and cost. A public tunnel alone does not add those capabilities. The provided server binds to loopback intentionally.
