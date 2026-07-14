# Contributing

This project is not yet accepting public contributions. Never open an issue or
commit containing recordings, speaker identities, completed consent records,
private evaluations, credentials, or language rules that lack native approval.

Local changes must pass:

```bash
uv run hmong-tts-privacy-scan
uv run hmong-tts-config-check
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

Native-language changes require a decision ID from
`docs/native_validation_register.md`.
