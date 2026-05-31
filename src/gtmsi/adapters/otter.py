"""Otter.ai adapter (best-effort — Otter's API is Enterprise-gated and its JSON
schema is not publicly documented).

Handles the documented/observed Otter shapes: an array under ``utterances``,
``transcripts``, or ``speeches``, where each item has text (``transcript``/``text``/
``words``), a speaker (``speaker``/``speaker_name``, or ``speaker_id`` resolved
against a top-level ``speakers[]`` list), and a timestamp (``start_offset`` in
**milliseconds**, or ``start_time``/``start`` in seconds).

For most users the reliable path is Otter's **SRT or TXT export**, handled by the
srt / plaintext adapters. This adapter covers the JSON case.
"""
from __future__ import annotations

import json
from typing import Any

from ..models import Transcript, Turn
from .base import build_participants, guess_side, title_from_path

# Keys we will READ a transcript array from (includes the generic-sounding
# "transcripts"); but we only SNIFF on the Otter-distinctive ones so we don't steal a
# generic {"transcripts": [...]} export (that falls through to json-generic).
_ARRAY_KEYS = ("utterances", "transcripts", "speeches")
_SNIFF_KEYS = ("utterances", "speeches", "start_offset")


class OtterAdapter:
    name = "otter"

    def sniff(self, path: str, text: str) -> bool:
        if not path.lower().endswith(".json"):
            return False
        try:
            data = json.loads(text)
        except ValueError:
            return False
        blob = json.dumps(data)[:20000]
        return any(k in blob for k in _SNIFF_KEYS) or "otter" in blob.lower()

    def parse(self, path: str, text: str) -> Transcript:
        data = json.loads(text)
        rows = self._rows(data)
        speakers = self._speaker_map(data)
        turns: list[Turn] = []
        for sp in rows:
            if not isinstance(sp, dict):
                continue
            name = (
                sp.get("speaker")
                or sp.get("speaker_name")
                or speakers.get(str(sp.get("speaker_id")))
                or "Speaker"
            )
            txt = sp.get("transcript") or sp.get("text")
            if not txt and isinstance(sp.get("words"), list):
                txt = " ".join(
                    (w.get("word") or w.get("text") or "") if isinstance(w, dict) else str(w)
                    for w in sp["words"]
                )
            txt = (txt or "").strip()
            if not txt:
                continue
            start = self._start_seconds(sp)
            turns.append(
                Turn(speaker=str(name), side=guess_side(str(name)), text=txt, start_seconds=start)
            )
        return Transcript(
            title=title_from_path(path),
            source={"recorder": "otter", "adapter": self.name},
            participants=build_participants(turns),
            turns=turns,
        )

    def _rows(self, data: Any) -> list:
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for k in _ARRAY_KEYS:
                if isinstance(data.get(k), list):
                    return data[k]
            for v in data.values():
                if isinstance(v, dict):
                    for k in _ARRAY_KEYS:
                        if isinstance(v.get(k), list):
                            return v[k]
        return []

    def _speaker_map(self, data: Any) -> dict[str, str]:
        out: dict[str, str] = {}
        spk = data.get("speakers") if isinstance(data, dict) else None
        if isinstance(spk, list):
            for s in spk:
                if isinstance(s, dict) and s.get("id") is not None and s.get("name"):
                    out[str(s["id"])] = s["name"]
        return out

    def _start_seconds(self, sp: dict) -> float | None:
        # start_offset / end_offset are milliseconds; start_time / start are seconds.
        if sp.get("start_offset") is not None:
            try:
                return float(sp["start_offset"]) / 1000.0
            except (TypeError, ValueError):
                return None
        v = sp.get("start_time", sp.get("start"))
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

