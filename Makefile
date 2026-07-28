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
	uv run tts-workbench-privacy-scan

config:
	uv run tts-workbench-config

models:
	uv run tts-workbench-models validate

env:
	uv run tts-workbench-env
