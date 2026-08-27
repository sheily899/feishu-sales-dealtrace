"""GTM Superintelligence — open-source, Claude-native sales coaching for any call transcript."""
from __future__ import annotations

__version__ = "0.1.0"

from .adapters import load_transcript
from .inbox import build_inbox
from .models import CoachingReport, Inbox, RubricReport, Scorecard, Transcript
from .pipeline import classify, coach, coach_transcript
from .registry import Registry, load_registry
from .render import inbox_to_markdown, rubric_report_to_markdown, to_markdown, to_share_card
from .scoring import score_account, score_deal

__all__ = [
    "__version__",
    "load_transcript",
    "load_registry",
    "Registry",
    "Transcript",
    "Scorecard",
    "CoachingReport",
    "RubricReport",
    "Inbox",
    "classify",
    "coach",
    "coach_transcript",
    "score_deal",
    "score_account",
    "build_inbox",
    "to_markdown",
    "rubric_report_to_markdown",
    "inbox_to_markdown",
    "to_share_card",
]
