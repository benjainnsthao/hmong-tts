# Contributing

This project is not yet accepting public contributions. Never open an issue or
commit containing audio, model weights, caches, credentials, private material,
unlicensed prompts, or unsupported language-capability claims.

Local changes must pass:

```bash
uv run hmong-tts-privacy-scan
uv run hmong-tts-config-check
uv run tts-workbench-models validate
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

White Hmong implementation is outside the active scope. NV-001 through NV-008
remain deferred in `docs/deferred/white_hmong_native_validation.md`.
