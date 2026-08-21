"""Pipeline tests with a stub LLM — no API key required.

We inject a fake ``llm`` whose ``complete_json`` returns canned, schema-shaped
responses, so we can test orchestration, merging, weight back-fill, banding, and
rendering deterministically.
"""
from gtmsi.models import Transcript, Turn
from gtmsi.pipeline import classify, coach, coach_transcript
from gtmsi.registry import load_registry
from gtmsi.render import to_markdown


class FakeLLM:
    """Returns queued responses in order, one per complete_json call."""

    def __init__(self, *responses):
        self._queue = list(responses)
        self.calls = 0

    def complete_json(self, system, cached_blocks, user_text, max_tokens=None):
        self.calls += 1
        return self._queue.pop(0)


def _transcript():
    return Transcript(
        title="Acme Discovery",
        turns=[
            Turn(speaker="Jordan", side="rep", text="What's your top priority this quarter?"),
            Turn(speaker="Sam", side="prospect", text="Cutting reporting time, it's ~10 hours a week."),
        ],
    )


def test_classify_uses_taxonomy_phase():
    reg = load_registry()
    # Model returns a wrong phase; pipeline should correct it from the taxonomy.
    fake = FakeLLM(
        {"call_type": "discovery", "phase": "post-sales", "confidence": 0.9, "rationale": "questions"},
    )
    c = classify(_transcript(), reg, fake)
    assert c.call_type == "discovery"
    assert c.phase == "pre-sales"  # corrected


def test_coach_merges_and_backfills():
    reg = load_registry()
    classification = {"call_type": "discovery", "phase": "pre-sales", "confidence": 0.8, "rationale": "x"}
    report = {
        "schema_version": "1.0",
        "outcomes": [
            {"id": "quantify-priority", "statement": "Quantify reporting cost", "status": "partial",
             "evidence": [{"speaker": "Sam", "text": "10 hours a week"}]}
        ],
        "scores": [
            # Note: no weight and no band provided -> pipeline back-fills both.
            {"criterion_id": "priority_quantified",
             "score": 72, "band": "", "rationale": "named hours not dollars",
             "evidence": [{"speaker": "Sam", "text": "10 hours a week"}]}
        ],
        "summary": "Solid discovery; quantify in dollars next time.",
        "coaching": {
            "strengths": [{"title": "Asked for the priority", "detail": "Good open question."}],
            "improvements": [{"title": "Quantify in dollars", "detail": "Hours isn't CFO-ready.",
                               "criterion_id": "priority_quantified", "better_move": "What's an hour of that team's time worth?",
                               "priority": "high"}],
            "next_call_focus": ["Bring an ROI estimate"],
        },
    }
    from gtmsi.models import Classification

    fake = FakeLLM(report)
    r = coach(_transcript(), Classification(**classification), reg, fake)

    # weight back-filled from the scorecard, band derived from score.
    s = r.scores[0]
    assert s.criterion_name == "Top Priority Identified & Quantified"
    assert s.weight is not None and s.weight > 0
    assert s.band == "good"  # 72 -> good
    # overall score computed
    assert r.overall_score is not None
    # markdown renders without error and includes the better move
    md = to_markdown(r, title="Acme Discovery")
    assert "Quantify in dollars" in md
    assert "Try instead" in md


def test_coach_handles_null_score_gracefully():
    """Regression: a null/missing score must not crash band backfill or construction."""
    reg = load_registry()
    classification = {"call_type": "discovery", "phase": "pre-sales", "confidence": 0.8, "rationale": "x"}
    report = {
        "scores": [
            {"criterion_id": "next_steps", "criterion_name": "Clear Next Steps with the Right People",
             "score": None, "rationale": "no evidence"}
        ],
        "summary": "s",
        "coaching": {"strengths": [], "improvements": [], "next_call_focus": []},
    }
    from gtmsi.models import Classification

    r = coach(_transcript(), Classification(**classification), reg, FakeLLM(report))
    assert r.scores[0].score == 0
    assert r.scores[0].band == "poor"  # 0 -> lowest band


def test_coach_transcript_end_to_end_with_injected_llm():
    """Top-level entry point: classify + coach with an injected llm and a model set.
    Regression for the llm-construction ternary precedence (must NOT build AnthropicCoach)."""
    reg = load_registry()
    classification = {"call_type": "discovery", "phase": "pre-sales", "confidence": 0.8, "rationale": "x"}
    report = {
        "scores": [{"criterion_id": "next_steps", "criterion_name": "Clear Next Steps with the Right People",
                    "score": 50, "rationale": "ok"}],
        "summary": "s",
        "coaching": {"strengths": [], "improvements": [], "next_call_focus": []},
    }
    fake = FakeLLM(classification, report)
    # model="x" + injected llm must not attempt to construct AnthropicCoach (no API key here).
    r = coach_transcript(_transcript(), reg=reg, llm=fake, model="x")
    assert r.classification.call_type == "discovery"
    assert r.overall_score is not None
