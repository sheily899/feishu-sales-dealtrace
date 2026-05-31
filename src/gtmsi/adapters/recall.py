"""Recall.ai adapter.

Recall.ai's transcript download is a JSON array of speaker turns; each turn has a
``participant`` object and a word-level ``words[]`` array. Verified shape:

    [
      {
        "participant": {"id": 1, "name": "Alice", "is_host": true, "email": null},
        "words": [
          {"text": "Hello", "start_timestamp": {"relative": 153.12, "absolute": "..."}},
          ...
        ]
      }
    ]

We join the words into one turn per element. Timestamps are seconds (``relative``).
``is_host`` is the only native rep/buyer hint, so we map host -> rep, others ->
prospect (a heuristic; override with ``--participants`` for exact roles).
"""
from __future__ import annotations

import json
from typing import Any

from ..models import Participant, Transcript, Turn
from .base import title_from_path


class RecallAdapter:
    name = "recall"

    def sniff(self, path: str, text: str) -> bool:
        if not path.lower().endswith(".json"):
            return False
        try:
            data = json.loads(text)
        except ValueError:
            return False
        rows = self._rows(data)
        return bool(rows) and isinstance(rows[0], dict) and "participant" in rows[0] and "words" in rows[0]

    def parse(self, path: str, text: str) -> Transcript:
        data = json.loads(text)
        rows = self._rows(data)
        turns: list[Turn] = []
        sides: dict[str, str] = {}
        for seg in rows:
            if not isinstance(seg, dict):
                continue
            p = seg.get("participant")
            p = p if isinstance(p, dict) else {}
            name = p.get("name") or "Speaker"
            side = "rep" if p.get("is_host") else "prospect"
            sides[name] = side
            words = seg.get("words") or []
            txt = " ".join(
                (w.get("text") or "") if isinstance(w, dict) else str(w) for w in words
            ).strip()
            if not txt:
                continue
            start = None
            if words and isinstance(words[0], dict):
                ts = words[0].get("start_timestamp") or {}
                start = ts.get("relative") if isinstance(ts, dict) else None
            turns.append(
                Turn(speaker=str(name), side=side, text=txt,
                     start_seconds=float(start) if start is not None else None)
            )
        participants = [
            Participant(id=n, name=n, side=s,
                        organization=None)
            for n, s in sides.items()
        ]
        return Transcript(
            title=title_from_path(path),
            source={"recorder": "recall", "adapter": self.name},
            participants=participants,
            turns=turns,
        )

    def _rows(self, data: Any) -> list:
        if isinstance(data, list):
            return data
        # tolerate {"transcript": [...]} or a single real-time {"data": {...}} wrapper
        if isinstance(data, dict):
            for k in ("transcript", "segments", "data"):
                v = data.get(k)
                if isinstance(v, list):
                    return v
                if isinstance(v, dict) and isinstance(v.get("data"), dict) and "words" in v["data"]:
                    return [v["data"]]
        return []

