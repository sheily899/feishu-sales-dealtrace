"""Plain-text transcript adapter.

Handles the most common human/LLM-readable shapes:

    Rep (Jordan): Thanks for making the time...
    Prospect (Sam): Of course.
    Jordan: Sure, let me walk you through it.
    [00:03] Sam: That makes sense.

Blank lines separate turns; a wrapped line without a new speaker label continues
the previous turn.
"""
from __future__ import annotations

import re

from ..models import Transcript, Turn
from .base import build_participants, guess_side, looks_like_speaker, split_role_name, title_from_path

# "Speaker label:" at line start. Label may include "(role)" and a leading [mm:ss].
_TS = re.compile(r"^\s*\[?(\d{1,2}):(\d{2})(?::(\d{2}))?\]?\s+")
_SPEAKER = re.compile(r"^\s*([A-Za-z0-9 ._'\-/]+(?:\([^)]*\))?)\s*:\s+(.*)$")


class PlaintextAdapter:
    name = "plaintext"

    def sniff(self, path: str, text: str) -> bool:
        if path.lower().endswith((".txt", ".md", ".log")):
            return True
        # Looks like "Name: text" lines.
        hits = sum(1 for ln in text.splitlines()[:30] if _SPEAKER.match(ln))
        return hits >= 3

    def parse(self, path: str, text: str) -> Transcript:
        turns: list[Turn] = []
        cur: Turn | None = None
        for raw in text.splitlines():
            line = raw.rstrip()
            if not line.strip():
                continue
            start = None
            ts = _TS.match(line)
            body = line
            if ts:
                a, b, c = ts.groups()
                # Two parts -> MM:SS; three parts -> HH:MM:SS.
                if c is not None:
                    start = int(a) * 3600 + int(b) * 60 + int(c)
                else:
                    start = int(a) * 60 + int(b)
                body = line[ts.end():]
            m = _SPEAKER.match(body)
            if m and looks_like_speaker(m.group(1)):
                label, content = m.group(1).strip(), m.group(2).strip()
                name, role = split_role_name(label)
                side = guess_side(role or name)
                cur = Turn(speaker=name, side=side, text=content, start_seconds=start)
                turns.append(cur)
            elif cur is not None:
                cur.text += " " + line.strip()
        turns = [t for t in turns if t.text.strip()]
        return Transcript(
            title=title_from_path(path),
            source={"recorder": "plaintext", "adapter": self.name},
            participants=build_participants(turns),
            turns=turns,
        )

