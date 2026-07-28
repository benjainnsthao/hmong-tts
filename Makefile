.PHONY: bootstrap check test privacy config models env

bootstrap:
	bash scripts/bootstrap.sh

check: privacy config models
	uv run ruff check .
	uv run mypy src
	uv run pytest

test:
	uv run pytest

privacy:
	uv run hmong-tts-privacy-scan

config:
	uv run hmong-tts-config-check

models:
	uv run tts-workbench-models validate

env:
	uv run hmong-tts-env
