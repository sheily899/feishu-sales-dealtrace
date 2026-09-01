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
    message_id: str | None = None
    occurred_at: str | None = None


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


class GroupChatResponse(BaseModel):
    title: str
    detail: str
    status: Literal["addressed", "partially_addressed", "unaddressed"]
    evidence: list[Quote] = Field(default_factory=list)


class GroupChatAnalysis(BaseModel):
    customer_needs: list[CoachingPoint] = Field(default_factory=list)
    customer_concerns: list[CoachingPoint] = Field(default_factory=list)
    response_coverage: list[GroupChatResponse] = Field(default_factory=list)
    sales_commitments: list[CoachingPoint] = Field(default_factory=list)
    todos: list[CoachingPoint] = Field(default_factory=list)
    next_steps: list[CoachingPoint] = Field(default_factory=list)


class StateItem(BaseModel):
    """An evidence-bound item retained in a customer's current sales state."""

    issue_id: str | None = None
    title: str
    detail: str | None = None
    evidence: list[Quote] = Field(default_factory=list)


class StateTodo(StateItem):
    status: Literal["pending", "completed"] = "pending"


class StateChangeItem(StateItem):
    category: Literal["need", "concern", "commitment", "todo", "stakeholder", "risk", "next_step"]


IssueCategory = Literal[
    "need",
    "concern",
    "commitment",
    "todo",
    "stakeholder",
    "risk",
    "next_step",
]
IssueStatus = Literal["open", "accepted_workaround", "resolved"]
IssueOperationKind = Literal["create", "update", "resolve", "reopen", "accept_workaround"]


class CustomerIssue(BaseModel):
    """Canonical, program-owned lifecycle record for one customer matter."""

    issue_id: str
    category: IssueCategory
    business_object: str
    status: IssueStatus = "open"
    title: str
    detail: str | None = None
    evidence_history: list[Quote] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    created_message_id: str
    updated_message_id: str


class IssueOperation(BaseModel):
    """A model proposal. The application validates it before mutating state."""

    operation: IssueOperationKind
    issue_id: str | None = None
    category: IssueCategory
    business_object: str
    title: str
    detail: str | None = None
    evidence: list[Quote] = Field(default_factory=list)
    executor: str | None = None
    action: str | None = None
    temporal_status: str | None = None
    source_type: str | None = None


class AppliedIssueOperation(IssueOperation):
    """An accepted operation with the stable identity assigned by the application."""

    issue_id: str


class StateTransition(BaseModel):
    """A material business-object state change, distinct from item resolution."""

    category: Literal["opportunity", "customer_intent", "solution"]
    title: str
    from_status: str
    to_status: str
    evidence: list[Quote] = Field(default_factory=list)


class StateChange(BaseModel):
    """The evidence-bound delta between two append-only customer state versions."""

    added: list[StateChangeItem] = Field(default_factory=list)
    resolved: list[StateChangeItem] = Field(default_factory=list)
    status_transitions: list[StateTransition] = Field(default_factory=list)
    operations: list[AppliedIssueOperation] = Field(default_factory=list)
    current_focus: str | None = None
    evidence: list[Quote] = Field(default_factory=list)


class CustomerState(BaseModel):
    """A versioned, per-chat customer state snapshot.

    ``version=0`` represents an unsaved model candidate. The SQLite store assigns
    persisted snapshots a monotonically increasing version starting at 1.
    """

    version: int = Field(default=0, ge=0)
    stage: str = "unknown"
    issues: list[CustomerIssue] = Field(default_factory=list)
    needs: list[StateItem] = Field(default_factory=list)
    unresolved_concerns: list[StateItem] = Field(default_factory=list)
    commitments: list[StateItem] = Field(default_factory=list)
    todos: list[StateTodo] = Field(default_factory=list)
    stakeholders: list[StateItem] = Field(default_factory=list)
    risks: list[StateItem] = Field(default_factory=list)
    scheduled_next_steps: list[StateItem] = Field(default_factory=list)
    updated_at: str | None = None
    analyzed_message_ids: list[str] = Field(default_factory=list)


class CoachingReport(BaseModel):
    schema_version: str = "1.0"
    call_id: str | None = None
    classification: Classification
    outcomes: list[OutcomeResult] = Field(default_factory=list)
    scores: list[CriterionScore] = Field(default_factory=list)
    overall_score: float | None = None
    summary: str
    coaching: Coaching
    group_chat: GroupChatAnalysis | None = None
    manager_notes: str | None = None

    @model_validator(mode="after")
    def _compute_overall(self) -> CoachingReport:
        if self.overall_score is None and self.scores:
            wsum = sum((s.weight or 1) for s in self.scores) or 1
            self.overall_score = round(
                sum(s.score * (s.weight or 1) for s in self.scores) / wsum
            )
        return self


