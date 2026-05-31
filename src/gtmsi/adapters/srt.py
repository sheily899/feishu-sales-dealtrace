"""SubRip (.srt) adapter. Speaker is taken from a leading ``Name:`` inside the cue
text when present; otherwise cues are attributed to a generic speaker and merged.
"""
from __future__ import annotations

import re

from ..models import Transcript, Turn
from .base import build_participants, guess_side, looks_like_speaker, title_from_path
from .vtt import _merge_consecutive

# Hours 1–2 digits (some exporters emit single-digit hours); comma millisecond sep.
_TIME = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2}),\d{3}\s*-->\s*(\d{1,2}):(\d{2}):(\d{2}),\d{3}"
)
_SPEAKER = re.compile(r"^\s*([A-Za-z0-9 ._'\-]+):\s+(.*)$")


def _secs(h: str, m: str, s: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s)


class SRTAdapter:
    name = "srt"

    def sniff(self, path: str, text: str) -> bool:
        if path.lower().endswith(".srt"):
            return True
        return "-->" in text and "," in text and bool(re.search(r"\d+\n\d{2}:\d{2}:\d{2},", text))

    def parse(self, path: str, text: str) -> Transcript:
        blocks = re.split(r"\n\s*\n", text)
        raw: list[Turn] = []
        for block in blocks:
            lines = [ln for ln in block.splitlines() if ln.strip()]
            if not lines:
                continue
            start = end = None
            seen_ts = False
            body: list[str] = []
            for ln in lines:
                tm = _TIME.search(ln)
                if tm:
                    start = _secs(tm.group(1), tm.group(2), tm.group(3))
                    end = _secs(tm.group(4), tm.group(5), tm.group(6))
                    seen_ts = True
                    continue
                if not seen_ts and re.match(r"^\d+$", ln.strip()):  # cue index (before timestamp)
                    continue
                body.append(ln.strip())
            if not seen_ts:
                continue
            content = " ".join(body).strip()
            if not content:
                continue
            speaker = "Speaker"
            m = _SPEAKER.match(content)
            if m and looks_like_speaker(m.group(1)):
                speaker, content = m.group(1).strip(), m.group(2).strip()
            raw.append(Turn(speaker=speaker, side=guess_side(speaker), text=content, start_seconds=start, end_seconds=end))
        turns = _merge_consecutive(raw)
        return Transcript(
            title=title_from_path(path),
            source={"recorder": "srt", "adapter": self.name},
            participants=build_participants(turns),
            turns=turns,
        )

