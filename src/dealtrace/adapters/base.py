"""Adapter base + shared helpers.

An adapter turns one recorder's export into a :class:`Transcript`. Adapters are
intentionally tiny and dependency-free so contributors can add new recorders in a
few lines. See ``docs/adapters.md``.
"""
from __future__ import annotations

import os
import re
from typing import Protocol

from ..models import Participant, Side, Transcript, Turn


def title_from_path(path: str) -> str:
    """Derive a human-readable call title from a file path: ``acme_demo-call.vtt``
    -> ``Acme Demo Call``. Shared by every adapter."""
    stem = os.path.splitext(os.path.basename(path))[0]
    return stem.replace("_", " ").replace("-", " ").title()

# Heuristics for guessing which side a speaker is on from a role label or name.
_REP_HINTS = re.compile(r"\b(rep|seller|ae|sales|bdr|sdr|csm|am|account exec|host)\b", re.I)
_BUYER_HINTS = re.compile(r"\b(prospect|buyer|customer|client|guest|attendee)\b", re.I)

# Common "X:" line prefixes that are NOT a speaker (so we don't mis-split a sentence
# or a heading like "Note:"/"Action items:"/"Re:" into a fake speaker turn).
_NOT_A_SPEAKER = {
    "note", "notes", "re", "fwd", "fw", "q", "a", "ps", "p.s", "warning", "caution",
    "action items", "action item", "next steps", "next step", "summary", "agenda",
    "topic", "topics", "todo", "to-do", "example", "tip", "tips", "caption", "music",
    "applause", "laughter", "silence", "inaudible", "crosstalk", "transcript", "speaker",
    "subject", "date", "time", "attendees", "participants", "location", "overview",
}


def looks_like_speaker(label: str) -> bool:
    """True if ``label`` (the text before a leading colon) plausibly names a speaker
    rather than being a sentence fragment or a heading. Used by the plaintext, VTT,
    and SRT adapters to avoid splitting on colons inside normal speech."""
    s = (label or "").strip()
    if not s or len(s) > 40:
        return False
    if "." in s.rstrip("."):  # internal period -> sentence, not a name (allow trailing)
        return False
    if len(s.split()) > 4:    # speaker labels are short ("Rep (Jordan)", "VP of Sales")
        return False
    return s.lower().rstrip(".") not in _NOT_A_SPEAKER


class Adapter(Protocol):
    name: str

    def sniff(self, path: str, text: str) -> bool:
        """Return True if this adapter can parse the given file."""

    def parse(self, path: str, text: str) -> Transcript:
        """Parse the file into a normalized Transcript."""


def guess_side(label: str, rep_names: set[str] | None = None) -> Side:
    if rep_names and label.strip() in rep_names:
        return "rep"
    if _REP_HINTS.search(label):
        return "rep"
    if _BUYER_HINTS.search(label):
        return "prospect"
    return "unknown"


def split_role_name(label: str) -> tuple[str, str | None]:
    """'Rep (Jordan)' -> ('Jordan', 'rep'); 'Jordan' -> ('Jordan', None)."""
    m = re.match(r"^\s*([^()]+?)\s*\(([^)]+)\)\s*$", label)
    if m:
        a, b = m.group(1).strip(), m.group(2).strip()
        # Either "Rep (Jordan)" or "Jordan (Rep)" — pick the role-ish token as side.
        if _REP_HINTS.search(a) or _BUYER_HINTS.search(a):
            return b, a.lower()
        return a, b.lower()
    return label.strip(), None


def build_participants(turns: list[Turn], rep_names: set[str] | None = None) -> list[Participant]:
    seen: dict[str, Participant] = {}
    for t in turns:
        if t.speaker not in seen:
            seen[t.speaker] = Participant(
                id=t.speaker, name=t.speaker, side=t.side or guess_side(t.speaker, rep_names)
            )
    return list(seen.values())
