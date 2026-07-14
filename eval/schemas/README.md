# Evaluation schemas

Typed evaluation configuration is defined in
`src/hmong_tts/config/schema.py` and can be exported as JSON Schema without
duplicating the source of truth:

```bash
uv run hmong-tts-config-check --schema eval
```

Manifest and linguistic-inventory schemas are Phase 1 work and must not encode
unreviewed White Hmong rules.
