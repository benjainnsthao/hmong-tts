.PHONY: bootstrap check test privacy config env

bootstrap:
	bash scripts/bootstrap.sh

check: privacy config
	uv run ruff check .
	uv run mypy src
	uv run pytest

test:
	uv run pytest

privacy:
	uv run hmong-tts-privacy-scan

config:
	uv run hmong-tts-config-check

env:
	uv run hmong-tts-env
