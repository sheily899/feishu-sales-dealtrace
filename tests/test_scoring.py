"""Cross-call rubric scoring (deal/account) with a stub LLM — offline."""
from dealtrace.models import Classification, Coaching, CoachingReport, CriterionScore
from dealtrace.registry import load_registry
from dealtrace.scoring import score_account, score_deal


class FakeLLM:
    def __init__(self, response):
        self._response = response

    def complete_json(self, system, cached_blocks, user_text, max_tokens=None):
        return self._response


def _call_report(call_type="discovery"):
    return CoachingReport(
        classification=Classification(call_type=call_type, phase="pre-sales", confidence=0.8, rationale="x"),
        scores=[CriterionScore(criterion_id="next_steps", criterion_name="Next Steps", score=40, band="developing", rationale="r")],
        summary="s",
        coaching=Coaching(strengths=[], improvements=[], next_call_focus=[]),
    )


def test_score_deal_backfills_band_risk_and_weights():
    reg = load_registry()
    # LLM omits band/risk and dimension weight -> engine must backfill from the rubric.
    llm_resp = {
        "overall_score": 51,
        "dimensions": [
            {"dimension_id": "pain_and_impact", "dimension_name": "Pain & Quantified Impact",
             "score": 74, "rationale": "quantified"}
        ],
        "risks": [{"title": "Single-threaded", "severity": "high"}],
        "recommended_actions": [{"action": "Multi-thread"}],
        "summary": "Early but real.",
    }
    reports = [("c1", _call_report()), ("c2", _call_report("demo"))]
    rep = score_deal(reports, reg, FakeLLM(llm_resp), subject={"name": "Acme"})
    assert rep.kind == "deal-health"
    assert rep.band == "at-risk"   # 51 -> at-risk per deal-health bands
    assert rep.risk == "medium"    # 51 -> medium per risk_bands
    assert rep.subject.call_count == 2
    # weight back-filled from the rubric dimension
    assert rep.dimensions[0].weight == 2


def test_score_account_kind_and_risk():
    reg = load_registry()
    llm_resp = {
        "overall_score": 30,
        "dimensions": [
            {"dimension_id": "adoption_usage", "dimension_name": "Adoption & Usage",
             "score": 25, "rationale": "low usage"}
        ],
        "summary": "Churning.",
    }
    rep = score_account([("c1", _call_report("renewal"))], reg, FakeLLM(llm_resp), subject={"name": "Initech"})
    assert rep.kind == "account-health"
    assert rep.band == "critical"  # 30 -> critical
    assert rep.risk == "high"      # 30 -> high churn risk
