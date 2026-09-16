"""Content identity for retained fixtures; custom text is never audited by association."""

import hashlib
from typing import Literal

ENGLISH_REFERENCE = "builtin:project-synthetic-eng-smoke-v1"
ENGLISH_EXAMPLE = "this is a synthetic inference test"
VIETNAMESE_REFERENCE = "external:vietnam-constitution-2013-article-1"
VIETNAMESE_SHA256 = "b6919cd1f33ec808355462bfa29e8444f8525560f8223d0486e67b35f29854c5"
PromptProvenance = Literal[
    "builtin_fixture", "retained_external_fixture", "user_supplied_unreviewed"
]


def classify_prompt(reference: str, text: str) -> PromptProvenance:
    if reference == ENGLISH_REFERENCE and text == ENGLISH_EXAMPLE:
        return "builtin_fixture"
    if reference == VIETNAMESE_REFERENCE and (
        hashlib.sha256(text.encode("utf-8")).hexdigest() == VIETNAMESE_SHA256
    ):
        return "retained_external_fixture"
    return "user_supplied_unreviewed"
