"""Optional, lightweight PII redaction for transcripts.

This is a *best-effort* convenience for users who want to scrub obvious identifiers
before sending text to a model. It is regex-based and not a compliance guarantee —
see ``docs/privacy-and-pii.md``. Disabled by default; enable with ``--redact``.
"""
from __future__ import annotations

import re

from .models import Transcript

# Order matters: patterns are applied top-to-bottom, so the more specific
# identifiers (SSN, CARD) must run BEFORE the broad PHONE digit-run, or a 16-digit
# card / SSN would be mislabeled "[PHONE]".
_PATTERNS = {
    "EMAIL": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "URL": re.compile(r"https?://\S+"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    # Phone-like only: an international +number, a ddd-ddd-dddd group, or a 10+ digit run.
    # Crucially this does NOT match space-separated number groups like "1 200 000" or
    # "2024 01 02" or "10 hours" — those quantified values are exactly what coaching needs.
    "PHONE": re.compile(r"\+\d[\d\s().-]{6,}\d|\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}|\b\d{10,}\b"),
}


def redact_text(text: str) -> str:
    for tag, pat in _PATTERNS.items():
        text = pat.sub(f"[{tag}]", text)
    return text


def redact_transcript(t: Transcript) -> Transcript:
    """Return a copy of the transcript with obvious PII masked in turn text."""
    redacted = t.model_copy(deep=True)
    for turn in redacted.turns:
        turn.text = redact_text(turn.text)
    redacted.metadata = {**redacted.metadata, "redacted": True}
    return redacted
