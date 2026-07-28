$ErrorActionPreference = "Stop"
$UvVersion = "0.11.28"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is required."
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    python -m pip install --user "uv==$UvVersion"
    $UserScripts = python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"
    $env:PATH = "$UserScripts;$env:PATH"
}

$ActualUv = (uv --version).Split()[1]
if ($ActualUv -ne $UvVersion) {
    throw "Expected uv $UvVersion; found $ActualUv."
}

uv sync --frozen
uv run pre-commit install
uv run tts-workbench-config
uv run tts-workbench-models validate
uv run tts-workbench-privacy-scan
uv run pytest
