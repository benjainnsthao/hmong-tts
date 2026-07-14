"""Repository wrapper for the privacy scanner CLI."""

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from hmong_tts.privacy.scan import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
