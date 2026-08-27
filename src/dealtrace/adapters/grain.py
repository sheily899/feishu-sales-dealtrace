"""Grain adapter.

Grain's public-API JSON transcript is a flat array of turn-level segments. Verified
shape (timestamps are **milliseconds** from recording start):

    [
      {"start": 8000, "end": 9000, "text": "Hello there.",
       "speaker": "Obi Wan", "participant_id": "uuid-or-null"},
      ...
    ]

``participant_id`` is nullable (unidentified speaker). There is no native
internal/external flag, so side is inferred from the name heuristic (override with
``--participants``). Grain also offers .vtt/.srt/.txt exports handled by those adapters.
"""
from __future__ import annotations

import json

from ..models import Transcript, Turn
from .base import build_participants, guess_side, title_from_path


class GrainAdapter:
    name = "grain"

    def sniff(self, path: str, text: str) -> bool:
        if not path.lower().endswith(".json"):
            return False
        try:
            data = json.loads(text)
        except ValueError:
            return False
        rows = data if isinstance(data, list) else None
        if not rows:
            return False
        # Distinctive Grain signature: speaker + text + participant_id. Check the first
        # few rows (the first speaker may be unidentified, omitting participant_id).
        return any(
            isinstance(r, dict) and "speaker" in r and "text" in r and "participant_id" in r
            for r in rows[:5]
        )

    def parse(self, path: str, text: str) -> Transcript:
        data = json.loads(text)
        turns: list[Turn] = []
        for r in data:
            if not isinstance(r, dict):
                continue
            txt = (r.get("text") or "").strip()
            if not txt:
                continue
            name = r.get("speaker") or "Speaker"
            start = r.get("start")
            end = r.get("end")
            turns.append(
                Turn(
                    speaker=str(name),
                    side=guess_side(str(name)),
                    text=txt,
                    start_seconds=float(start) / 1000.0 if start is not None else None,
                    end_seconds=float(end) / 1000.0 if end is not None else None,
                )
            )
        return Transcript(
            title=title_from_path(path),
            source={"recorder": "grain", "adapter": self.name},
            participants=build_participants(turns),
            turns=turns,
        )

