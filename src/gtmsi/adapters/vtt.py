"""WebVTT adapter. Supports both speaker conventions seen in the wild:

- the ``<v Speaker>text`` voice-span tag, and
- an inline ``Speaker: text`` prefix inside the cue text (this is what **Zoom**
  cloud-recording transcripts and **Avoma** VTT exports emit — confirmed against
  their formats).

Consecutive cues from the same speaker are merged.
"""
from __future__ import annotations

import re

from ..models import Transcript, Turn
from .base import build_participants, guess_side, looks_like_speaker, title_from_path

# Timestamps: hours are optional (WebVTT allows MM:SS.mmm) and 1–2 digits.
_TIME = re.compile(
    r"(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\.\d{3}\s*-->\s*(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\.\d{3}"
)
# <v Speaker> or <v.class Speaker>; speaker may contain spaces.
_VOICE = re.compile(r"<v(?:\.[^\s>]+)?\s+([^>]+?)>(.*?)(?:</v>)?$", re.S)
# Inline "Name: text" prefix (Zoom/Avoma).
_INLINE_SPEAKER = re.compile(r"^([A-Za-z0-9][\w .'\-]{0,38}):\s+(\S.*)$", re.S)
# Block types that are NOT cues.
_NON_CUE = ("WEBVTT", "NOTE", "STYLE", "REGION")


def _secs(h: str | None, m: str, s: str) -> float:
    return (int(h) if h else 0) * 3600 + int(m) * 60 + int(s)


class VTTAdapter:
    name = "vtt"

    def sniff(self, path: str, text: str) -> bool:
        return path.lower().endswith(".vtt") or text.lstrip().upper().startswith("WEBVTT")

    def parse(self, path: str, text: str) -> Transcript:
        blocks = re.split(r"\n\s*\n", text)
        raw_turns: list[Turn] = []
        for block in blocks:
            lines = [ln for ln in block.splitlines() if ln.strip()]
            if not lines or lines[0].upper().startswith(_NON_CUE):
                continue
            start = end = None
            content_lines = []
            speaker = None
            seen_ts = False
            for ln in lines:
                tm = _TIME.search(ln)
                if tm:
                    start = _secs(tm.group(1), tm.group(2), tm.group(3))
                    end = _secs(tm.group(4), tm.group(5), tm.group(6))
                    seen_ts = True
                    continue
                if not seen_ts and re.match(r"^\d+$", ln.strip()):  # cue index (before the timestamp)
                    continue
                v = _VOICE.match(ln.strip())
                if v:
                    speaker = v.group(1).strip()
                    content_lines.append(v.group(2).strip())
                else:
                    content_lines.append(ln.strip())
            if not seen_ts:  # a block with no timestamp line isn't a cue
                continue
            content = " ".join(c for c in content_lines if c).strip()
            if not content:
                continue
            # No <v> tag? Try the inline "Name: text" prefix (Zoom/Avoma).
            if speaker is None:
                m = _INLINE_SPEAKER.match(content)
                if m and looks_like_speaker(m.group(1)):
                    speaker, content = m.group(1).strip(), m.group(2).strip()
            if speaker is None:
                speaker = "Speaker"
            raw_turns.append(
                Turn(speaker=speaker, side=guess_side(speaker), text=content, start_seconds=start, end_seconds=end)
            )

        turns = _merge_consecutive(raw_turns)
        return Transcript(
            title=title_from_path(path),
            source={"recorder": "vtt", "adapter": self.name},
            participants=build_participants(turns),
            turns=turns,
        )


def _merge_consecutive(turns: list[Turn]) -> list[Turn]:
    out: list[Turn] = []
    for t in turns:
        if out and out[-1].speaker == t.speaker:
            out[-1].text += " " + t.text
            out[-1].end_seconds = t.end_seconds or out[-1].end_seconds
        else:
            out.append(t)
    return out

