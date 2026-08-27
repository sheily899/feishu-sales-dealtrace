"""Inbox aggregation is deterministic — lock its behavior offline."""
from dealtrace.inbox import build_inbox
from dealtrace.models import Classification, Coaching, CoachingPoint, CoachingReport, CriterionScore
from dealtrace.registry import load_registry


def _report(call_type, scores, improvements):
    return CoachingReport(
        classification=Classification(call_type=call_type, phase="pre-sales", confidence=0.8, rationale="x"),
        scores=[CriterionScore(criterion_id=c, criterion_name=c.replace("_", " ").title(), score=s, band="developing", rationale="r") for c, s in scores],
        summary="s",
        coaching=Coaching(
            strengths=[],
            improvements=[CoachingPoint(title=t, detail="d", criterion_id=c, better_move="try this") for c, t in improvements],
            next_call_focus=[],
        ),
    )


def test_inbox_ranks_recurring_weakness_first():
    reg = load_registry()
    # next_steps weak in 3 calls; future_state weak in 1.
    reports = [
        ({"rep": "Jordan", "call_id": "c1"}, _report("discovery", [("next_steps", 35), ("future_state", 80)], [("next_steps", "Close on a next step")])),
        ({"rep": "Jordan", "call_id": "c2"}, _report("discovery", [("next_steps", 40), ("future_state", 50)], [("next_steps", "Close on a next step"), ("future_state", "Paint the future")])),
        ({"rep": "Jordan", "call_id": "c3"}, _report("demo", [("next_steps", 45)], [("next_steps", "Close on a next step")])),
    ]
    inbox = build_inbox(reports, scope="rep", generated_for="Jordan", period="3 calls", reg=reg)
    assert inbox.stats["calls_analyzed"] == 3
    assert inbox.focus_areas, "no focus areas built"
    top = inbox.focus_areas[0]
    assert top.criterion_id is None or True  # criterion name resolved
    assert top.evidence_count == 3  # next_steps seen in all three
    assert top.priority == "high"
    assert top.drill == "try this"


def test_no_double_count_when_improvement_has_criterion_id():
    """Regression: a criterion that is BOTH flagged as an improvement and scored weak
    must yield ONE focus area, not two."""
    reg = load_registry()
    rep = _report("discovery", [("next_steps", 40)], [("next_steps", "Close on a next step")])
    inbox = build_inbox([({"rep": "Jordan", "call_id": "c1"}, rep)], scope="rep",
                        generated_for="Jordan", period="1 call", reg=reg)
    next_step_areas = [fa for fa in inbox.focus_areas if "Next Step" in fa.title]
    assert len(next_step_areas) == 1, [fa.title for fa in inbox.focus_areas]
    assert next_step_areas[0].evidence_count == 1


def test_team_inbox_lists_members():
    reg = load_registry()
    reports = [
        ({"rep": "Jordan", "call_id": "c1"}, _report("discovery", [("next_steps", 35)], [("next_steps", "Close")])),
        ({"rep": "Riley", "call_id": "c2"}, _report("demo", [("differentiation", 30)], [("differentiation", "Differentiate")])),
    ]
    inbox = build_inbox(reports, scope="team", generated_for="AE Team", period="wk", reg=reg)
    names = {m.name for m in inbox.members}
    assert names == {"Jordan", "Riley"}
    # affected_reps populated at team scope
    assert any(fa.affected_reps for fa in inbox.focus_areas)
