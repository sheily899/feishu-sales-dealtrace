"""Fireflies.ai adapter (best-effort).

Fireflies' GraphQL transcript export exposes ``sentences`` with ``speaker_name``,
``text``, and ``start_time`` (seconds). Shapes handled:
  {"sentences":[{"speaker_name","text","start_time"}]}
  {"transcript":{"sentences":[...]}}
  {"data":{"transcript":{"sentences":[...]}}}
"""
from __future__ import annotations

import json
from typing import Any

from ..models import Transcript, Turn
from .base import build_participants, guess_side, title_from_path


class FirefliesAdapter:
    name = "fireflies"

    def sniff(self, path: str, text: str) -> bool:
        if not path.lower().endswith(".json"):
            return False
        try:
            data = json.loads(text)
        except ValueError:
            return False
        return "speaker_name" in json.dumps(data)[:20000]

    def parse(self, path: str, text: str) -> Transcript:
        data = json.loads(text)
        sentences = self._sentences(data)
        turns: list[Turn] = []
        for s in sentences:
            name = s.get("speaker_name") or s.get("speaker") or "Speaker"
            txt = (s.get("text") or "").strip()
            if not txt:
                continue
            start = s.get("start_time")
            turns.append(
                Turn(speaker=name, side=guess_side(str(name)), text=txt,
                     start_seconds=float(start) if start is not None else None)
            )
        return Transcript(
            title=title_from_path(path),
            source={"recorder": "fireflies", "adapter": self.name},
            participants=build_participants(turns),
            turns=turns,
        )

    def _sentences(self, data: Any) -> list[dict]:
        node = data
        for key in ("data", "transcript"):
            if isinstance(node, dict) and key in node:
                node = node[key]
        if isinstance(node, dict) and isinstance(node.get("sentences"), list):
            return node["sentences"]
        if isinstance(data, dict) and isinstance(data.get("sentences"), list):
            return data["sentences"]
        return []

