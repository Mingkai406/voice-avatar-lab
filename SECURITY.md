# Security

This is a loopback-only development prototype, not a hardened multi-user service. Supported security fixes target the current `main` branch.

For vulnerabilities, use GitHub's **Security → Report a vulnerability** private reporting feature. Do not post credentials, personal data or exploit details in a public Issue. If private reporting is unavailable, open a minimal Issue requesting a private contact channel without sensitive details.

Provider credentials stay on the server in environment variables or the ignored `.env`. A selected external provider receives dialogue content. The default model runtime loads local weights offline after setup. No automatic clinical-record ingestion is implemented.

The browser retains session history in memory and exports it only on request. Audio processing uses temporary local files or memory. Users should still treat downloaded software, configured endpoints and model assets according to their own requirements.
