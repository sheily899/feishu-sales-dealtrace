"""Generic JSON adapter.

Handles three cases, in order:
  1. Already a normalized GTM Superintelligence transcript (``schema_version`` + ``turns``).
  2. A bare list of turn-like objects: ``[{"speaker": .., "text": ..}, ..]``.
  3. A dict with a ``turns``/``segments``/``sentences``/``monologues`` array.

Vendor-specific JSON (Gong, Fireflies, Otter) has dedicated adapters that run
before this one; this is the catch-all for "some JSON with speakers and text".
"""
from __future__ import annotations

import json
from typing import Any

from ..models import Transcript, Turn
from .base import build_participants, guess_side, title_from_path

_ARRAY_KEYS = ("turns", "segments", "sentences", "monologues", "entries", "utterances", "transcripts")
_SPEAKER_KEYS = ("speaker", "speaker_name", "name", "speakerName", "from")
_TEXT_KEYS = ("text", "sentence", "content", "transcript", "words")
_START_KEYS = ("start_seconds", "start", "startTime", "start_time", "offset")


def _first(d: dict, keys) -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def _to_seconds(v: Any) -> float | None:
    # Generic JSON is assumed to be in SECONDS (the common case: Fireflies, Recall
    # `relative`, Otter `start_time`). Recorders that emit milliseconds (Gong, Grain,
    # Otter `start_offset`) have dedicated adapters that convert explicitly — we do NOT
    # guess units here, because a ms/seconds heuristic is wrong in both directions.
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class JSONGenericAdapter:
    name = "json-generic"

    def sniff(self, path: str, text: str) -> bool:
        if not path.lower().endswith(".json"):
            return False
        try:
            json.loads(text)
            return True
        except ValueError:
            return False

    def parse(self, path: str, text: str) -> Transcript:
        data = json.loads(text)

        # Case 1: already normalized.
        if isinstance(data, dict) and "turns" in data and "schema_version" in data:
            return Transcript(**data)

        rows = self._extract_rows(data)
        turns: list[Turn] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            speaker = _first(r, _SPEAKER_KEYS) or "Speaker"
            txt = _first(r, _TEXT_KEYS)
            if isinstance(txt, list):  # e.g. list of word objects
                txt = " ".join(w.get("word", w.get("text", "")) if isinstance(w, dict) else str(w) for w in txt)
            if not txt:
                continue
            turns.append(
                Turn(
                    speaker=str(speaker),
                    side=guess_side(str(speaker)),
                    text=str(txt).strip(),
                    start_seconds=_to_seconds(_first(r, _START_KEYS)),
                )
            )
        return Transcript(
            title=title_from_path(path),
            source={"recorder": "json", "adapter": self.name},
            participants=build_participants(turns),
            turns=turns,
        )

    def _extract_rows(self, data: Any) -> list:
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for k in _ARRAY_KEYS:
                if isinstance(data.get(k), list):
                    return data[k]
            # nested e.g. {"transcript": {"sentences": [...]}}
            for v in data.values():
                if isinstance(v, dict):
                    for k in _ARRAY_KEYS:
                        if isinstance(v.get(k), list):
                            return v[k]
        return []

