"""Pydantic models mirroring the JSON Schemas in ``schemas/``.

These give us validation, editor autocomplete, and a single source of truth for the
shapes that flow through the pipeline. The JSON Schemas remain the canonical,
language-agnostic contract; these models track them.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

Side = Literal["rep", "prospect", "customer", "partner", "internal", "unknown"]
Phase = Literal["pre-sales", "post-sales", "neither"]


# --------------------------------------------------------------------------- transcript
class Participant(BaseModel):
    id: str
    name: str
    side: Side = "unknown"
    title: str | None = None
    organization: str | None = None
    talk_seconds: float | None = None


class Turn(BaseModel):
    speaker: str
    side: Side = "unknown"
    text: str
    start_seconds: float | None = None
    end_seconds: float | None = None


class Transcript(BaseModel):
    schema_version: str = "1.0"
    call_id: str | None = None
    title: str | None = None
    started_at: str | None = None
    duration_seconds: float | None = None
    source: dict[str, Any] = Field(default_factory=dict)
    participants: list[Participant] = Field(default_factory=list)
    turns: list[Turn]
    metadata: dict[str, Any] = Field(default_factory=dict)

    def as_text(self, max_turns: int | None = None) -> str:
        """Render the transcript as a clean, speaker-labeled text block for the LLM."""
        rows = self.turns[:max_turns] if max_turns else self.turns
        lines = []
        for t in rows:
            label = t.speaker
            side = t.side if t.side != "unknown" else self._side_of(t.speaker)
            tag = f" ({side})" if side and side != "unknown" else ""
            ts = ""
            if t.start_seconds is not None:
                m, s = divmod(int(t.start_seconds), 60)
                ts = f"[{m:02d}:{s:02d}] "
            lines.append(f"{ts}{label}{tag}: {t.text}")
        return "\n".join(lines)

    def _side_of(self, speaker: str) -> Side:
        for p in self.participants:
            if speaker in (p.id, p.name):
                return p.side
        return "unknown"

    def talk_ratio(self) -> dict[str, float]:
        """Rep vs non-rep talk share by word count (cheap proxy when timings absent)."""
        rep, other = 0, 0
        for t in self.turns:
            side = t.side if t.side != "unknown" else self._side_of(t.speaker)
            words = len(t.text.split())
            if side == "rep":
                rep += words
            else:
                other += words
        total = rep + other or 1
        return {"rep": round(rep / total, 3), "other": round(other / total, 3)}


# --------------------------------------------------------------------------- registry shapes
class FrameworkElement(BaseModel):
    id: str
    name: str
    question: str
    why_it_matters: str | None = None
    good_signals: list[str] = Field(default_factory=list)
    missing_signals: list[str] = Field(default_factory=list)
    example_questions: list[str] = Field(default_factory=list)


class Framework(BaseModel):
    id: str
    name: str
    acronym: str | None = None
    origin: str | None = None
    summary: str | None = None
    best_for: list[str] = Field(default_factory=list)
    elements: list[FrameworkElement]
    further_reading: list[dict[str, str]] = Field(default_factory=list)


class ScoringBand(BaseModel):
    label: str
    min: float
    meaning: str | None = None


class Scoring(BaseModel):
    scale_max: float = 100
    bands: list[ScoringBand] = Field(default_factory=list)


class Criterion(BaseModel):
    id: str
    name: str
    weight: float
    intent: str | None = None
    framework_refs: list[str] = Field(default_factory=list)
    what_great_looks_like: list[str]
    what_poor_looks_like: list[str] = Field(default_factory=list)
    evidence_cues: list[str] = Field(default_factory=list)
    coaching_prompts: list[str] = Field(default_factory=list)


class Scorecard(BaseModel):
    id: str
    name: str
    version: str
    description: str | None = None
    applies_to: list[str]
    frameworks: list[str] = Field(default_factory=list)
    scoring: Scoring = Field(default_factory=Scoring)
    criteria: list[Criterion]

    def band_for(self, score: float) -> str:
        bands = sorted(self.scoring.bands, key=lambda b: b.min, reverse=True)
        for b in bands:
            if score >= b.min:
                return b.label
        return bands[-1].label if bands else "unscored"


class CallType(BaseModel):
    id: str
    name: str
    phase: Phase
    definition: str
    positive_signals: list[str] = Field(default_factory=list)
    negative_signals: list[str] = Field(default_factory=list)
    often_confused_with: list[str] = Field(default_factory=list)
    scorecards: list[str]
    default_outcomes: list[str] = Field(default_factory=list)


class Outcome(BaseModel):
    id: str
    phase: Phase
    statement: str
    success_looks_like: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- report shapes
class Quote(BaseModel):
    speaker: str
    text: str
    timestamp_seconds: float | None = None


class Classification(BaseModel):
    call_type: str
    phase: Phase
    confidence: float = Field(ge=0, le=1)
    rationale: str
    alternatives: list[dict[str, Any]] = Field(default_factory=list)


class OutcomeResult(BaseModel):
    id: str
    statement: str
    status: Literal["achieved", "partial", "missed", "unknown"]
    evidence: list[Quote] = Field(default_factory=list)


class CriterionScore(BaseModel):
    criterion_id: str
    criterion_name: str
    score: float = Field(ge=0, le=100)
    band: str
    weight: float | None = None
    rationale: str
    evidence: list[Quote] = Field(default_factory=list)


class CoachingPoint(BaseModel):
    title: str
    detail: str
    criterion_id: str | None = None
    evidence: list[Quote] = Field(default_factory=list)
    better_move: str | None = None
    priority: Literal["high", "medium", "low"] | None = None


class Coaching(BaseModel):
    strengths: list[CoachingPoint] = Field(default_factory=list)
    improvements: list[CoachingPoint] = Field(default_factory=list)
    next_call_focus: list[str] = Field(default_factory=list)


class CoachingReport(BaseModel):
    schema_version: str = "1.0"
    call_id: str | None = None
    classification: Classification
    outcomes: list[OutcomeResult] = Field(default_factory=list)
    scores: list[CriterionScore] = Field(default_factory=list)
    overall_score: float | None = None
    summary: str
    coaching: Coaching
    manager_notes: str | None = None

    @model_validator(mode="after")
    def _compute_overall(self) -> CoachingReport:
        if self.overall_score is None and self.scores:
            wsum = sum((s.weight or 1) for s in self.scores) or 1
            self.overall_score = round(
                sum(s.score * (s.weight or 1) for s in self.scores) / wsum
            )
        return self


# --------------------------------------------------------------------------- rubric shapes
RubricKind = Literal["deal-health", "account-health"]


class RubricBand(BaseModel):
    label: str
    min: float
    meaning: str | None = None


class RubricRiskBand(BaseModel):
    label: str
    max: float
    meaning: str | None = None


class RubricScoring(BaseModel):
    scale_max: float = 100
    bands: list[RubricBand] = Field(default_factory=list)
    risk_bands: list[RubricRiskBand] = Field(default_factory=list)


class RubricDimension(BaseModel):
    id: str
    name: str
    weight: float
    intent: str | None = None
    framework_refs: list[str] = Field(default_factory=list)
    strong_signals: list[str]
    weak_signals: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    evidence_cues: list[str] = Field(default_factory=list)


class Rubric(BaseModel):
    id: str
    name: str
    version: str
    kind: RubricKind
    description: str | None = None
    frameworks: list[str] = Field(default_factory=list)
    scoring: RubricScoring = Field(default_factory=RubricScoring)
    dimensions: list[RubricDimension]

    def band_for(self, score: float) -> str:
        for b in sorted(self.scoring.bands, key=lambda x: x.min, reverse=True):
            if score >= b.min:
                return b.label
        return self.scoring.bands[-1].label if self.scoring.bands else "unscored"

    def risk_for(self, score: float) -> str:
        for b in sorted(self.scoring.risk_bands, key=lambda x: x.max):
            if score <= b.max:
                return b.label
        return self.scoring.risk_bands[-1].label if self.scoring.risk_bands else "unknown"


# --------------------------------------------------------------------------- rubric report
class RubricEvidence(BaseModel):
    call_id: str | None = None
    speaker: str | None = None
    text: str


class DimensionScore(BaseModel):
    dimension_id: str
    dimension_name: str
    score: float = Field(ge=0, le=100)
    weight: float | None = None
    rationale: str
    evidence: list[RubricEvidence] = Field(default_factory=list)


class RubricRisk(BaseModel):
    title: str
    detail: str | None = None
    severity: Literal["high", "medium", "low"]
    dimension_id: str | None = None
    evidence: list[RubricEvidence] = Field(default_factory=list)


class RecommendedAction(BaseModel):
    action: str
    why: str | None = None
    owner: str | None = None
    priority: Literal["high", "medium", "low"] | None = None


class RubricSubject(BaseModel):
    id: str | None = None
    name: str
    owner: str | None = None
    amount: float | None = None
    stage: str | None = None
    close_or_renewal_date: str | None = None
    call_count: int | None = None

    model_config = {"extra": "allow"}


class RubricReport(BaseModel):
    schema_version: str = "1.0"
    kind: RubricKind
    subject: RubricSubject
    overall_score: float = Field(ge=0, le=100)
    band: str
    risk: str
    dimensions: list[DimensionScore] = Field(default_factory=list)
    risks: list[RubricRisk] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    summary: str
    trend: Literal["improving", "flat", "declining"] | None = None


# --------------------------------------------------------------------------- inbox shapes
class FocusArea(BaseModel):
    criterion_id: str | None = None
    title: str
    detail: str | None = None
    priority: Literal["high", "medium", "low"]
    evidence_count: int
    avg_score: float | None = None
    trend: Literal["improving", "flat", "declining"] | None = None
    example_calls: list[str] = Field(default_factory=list)
    drill: str | None = None
    affected_reps: list[str] = Field(default_factory=list)


class InboxWin(BaseModel):
    title: str
    detail: str | None = None
    evidence_count: int = 0


class InboxMember(BaseModel):
    name: str
    calls_analyzed: int = 0
    avg_overall_score: float | None = None
    top_focus: str | None = None


class Inbox(BaseModel):
    schema_version: str = "1.0"
    scope: Literal["rep", "team", "company"]
    generated_for: str
    period: str
    stats: dict[str, Any] = Field(default_factory=dict)
    focus_areas: list[FocusArea] = Field(default_factory=list)
    wins: list[InboxWin] = Field(default_factory=list)
    members: list[InboxMember] = Field(default_factory=list)
