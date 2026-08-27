"""Gong adapter (best-effort, dependency-free).

Maps a Gong call-transcript export to the normalized format. Gong's transcript is a
list of *monologues*, each with a ``speakerId`` and ``sentences``. Speaker identity
is resolved from a ``parties`` array if present, with ``affiliation`` ("Internal"/
"External") mapped to rep/prospect.

This handles the common export shapes:
  {"callTranscripts":[{"transcript":[{"speakerId","sentences":[{"start","text"}]}]}]}
  {"transcript":[{"speakerId","sentences":[...]}], "parties":[{"speakerId","name","affiliation"}]}
"""
from __future__ import annotations

import json
from typing import Any

from ..models import Participant, Transcript, Turn
from .base import title_from_path


class GongAdapter:
    name = "gong"

    def sniff(self, path: str, text: str) -> bool:
        if not path.lower().endswith(".json"):
            return False
        try:
            data = json.loads(text)
        except ValueError:
            return False
        blob = json.dumps(data)[:20000]
        return "callTranscripts" in blob or ("speakerId" in blob and "sentences" in blob)

    def parse(self, path: str, text: str) -> Transcript:
        data = json.loads(text)
        parties = self._parties(data)
        monologues = self._monologues(data)

        turns: list[Turn] = []
        for m in monologues:
            sid = str(m.get("speakerId", m.get("speaker", "")))
            party = parties.get(sid, {})
            name = party.get("name") or sid or "Speaker"
            side = party.get("side", "unknown")
            sentences = m.get("sentences", [])
            txt = " ".join(s.get("text", "") for s in sentences).strip()
            if not txt:
                continue
            start = None
            if sentences and sentences[0].get("start") is not None:
                start = float(sentences[0]["start"]) / 1000.0
            turns.append(Turn(speaker=name, side=side, text=txt, start_seconds=start))

        participants = [
            Participant(id=sid, name=p.get("name", sid), side=p.get("side", "unknown"))
            for sid, p in parties.items()
        ] or None
        return Transcript(
            title=title_from_path(path),
            source={"recorder": "gong", "adapter": self.name},
            participants=participants or [],
            turns=turns,
        )

    def _parties(self, data: Any) -> dict[str, dict]:
        parties = []
        if isinstance(data, dict):
            parties = data.get("parties") or data.get("speakers") or []
            if not parties and isinstance(data.get("callTranscripts"), list):
                for ct in data["callTranscripts"]:
                    parties = ct.get("parties") or parties
        out: dict[str, dict] = {}
        for p in parties:
            sid = str(p.get("speakerId", p.get("id", p.get("name", ""))))
            aff = (p.get("affiliation") or "").lower()
            side = "rep" if aff == "internal" else "prospect" if aff == "external" else "unknown"
            out[sid] = {"name": p.get("name", sid), "side": side}
        return out

    def _monologues(self, data: Any) -> list[dict]:
        if isinstance(data, dict):
            if isinstance(data.get("transcript"), list):
                return data["transcript"]
            if isinstance(data.get("callTranscripts"), list):
                rows: list[dict] = []
                for ct in data["callTranscripts"]:
                    rows.extend(ct.get("transcript", []))
                return rows
        return []

