"""GTM Superintelligence — open-source, Claude-native sales coaching for any call transcript."""
from __future__ import annotations

__version__ = "0.1.0"

from .models import CoachingReport, Scorecard, Transcript
from .pipeline import classify, coach, coach_transcript
from .registry import Registry, load_registry

__all__ = [
    "__version__",
    "load_registry",
    "Registry",
    "Transcript",
    "Scorecard",
    "CoachingReport",
    "classify",
    "coach",
    "coach_transcript",
]
