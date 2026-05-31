"""Cross-call scoring: roll a set of per-call coaching reports up into a deal/
opportunity health score (sales) or an account health score (CSM).

Both share one engine — :func:`score_rubric` — because a deal report and an account
report have the same shape; only the rubric differs.
"""
from __future__ import annotations

import json
from typing import Any

from ..llm import CachedBlock
from ..models import CoachingReport, Rubric, RubricReport
from ..registry import Registry


def _compact_report(r: CoachingReport, call_id: str | None = None) -> dict[str, Any]:
    """A compact view of a per-call report for cross-call reasoning (keeps tokens low
    while preserving the signal the rubric needs)."""
    return {
        "call_id": call_id or r.call_id,
        "call_type": r.classification.call_type,
        "phase": r.classification.phase,
        "overall_score": r.overall_score,
        "summary": r.summary,
        "outcomes": [{"statement": o.statement, "status": o.status} for o in r.outcomes],
        "low_scores": [
            {"criterion": s.criterion_name, "score": s.score}
            for s in sorted(r.scores, key=lambda x: x.score)[:3]
        ],
        "top_improvements": [p.title for p in r.coaching.improvements[:3]],
        "key_evidence": [
            {"speaker": q.speaker, "text": q.text}
            for s in r.scores
            for q in s.evidence[:1]
        ][:6],
    }


def score_rubric(
    reports: list[tuple[str, CoachingReport]],
    rubric: Rubric,
    reg: Registry,
    llm,
    subject: dict[str, Any],
    extra_context: str | None = None,
) -> RubricReport:
    """Score a deal or account.

    Args:
        reports: list of ``(call_id_or_title, CoachingReport)`` in chronological order.
        rubric: the deal-health or account-health rubric.
        subject: metadata dict (name, id, owner, amount, stage, dates...).
    """

    def _read(*parts: str) -> str:
        return reg.root.joinpath(*parts).read_text(encoding="utf-8")

    system = _read("prompts", "system.md")
    template = _read("prompts", "rubric_scoring.md")
    rubric_yaml = (reg.root / "rubrics" / f"{rubric.id}.yaml").read_text(encoding="utf-8")
    frameworks_yaml = "\n---\n".join(
        (reg.root / "frameworks" / f"{fw.id}.yaml").read_text(encoding="utf-8")
        for fw in reg.frameworks_for_rubric(rubric)
    )

    subject = {**subject, "call_count": len(reports)}
    compact = [_compact_report(r, cid) for cid, r in reports]
    call_reports_json = json.dumps(compact, indent=2)
    if extra_context:
        call_reports_json += f"\n\n## Additional signals\n{extra_context}"

    subject_noun = "deal" if rubric.kind == "deal-health" else "account"
    user = (
        template.replace("{{KIND}}", rubric.kind)
        .replace("{{SUBJECT_NOUN}}", subject_noun)
        .replace("{{SUBJECT}}", json.dumps(subject, indent=2))
        .replace("{{RUBRIC_YAML}}", "(provided above as cached context)")
        .replace("{{FRAMEWORKS_YAML}}", "(provided above as cached context)")
        .replace("{{CALL_REPORTS}}", call_reports_json)
    )

    data = llm.complete_json(
        system=system,
        cached_blocks=[
            CachedBlock(f"Rubric: {rubric.name}", rubric_yaml),
            CachedBlock("Frameworks", frameworks_yaml or "(none)"),
        ],
        user_text=user,
        max_tokens=4096,
    )

    # Defensive back-fill of weights/band/risk from the rubric.
    data.setdefault("kind", rubric.kind)
    data.setdefault("subject", subject)
    dims = data.get("dimensions", [])
    for d in dims:
        dim = next((x for x in rubric.dimensions if x.id == d.get("dimension_id")), None)
        if dim and d.get("weight") is None:
            d["weight"] = dim.weight
    # If the model omitted overall_score, compute it from the weighted dimension mean
    # so a recoverable response degrades gracefully instead of crashing construction.
    if data.get("overall_score") is None and dims:
        wsum = sum((d.get("weight") or 1) for d in dims) or 1
        data["overall_score"] = round(sum((d.get("score") or 0) * (d.get("weight") or 1) for d in dims) / wsum)
    if data.get("overall_score") is not None:
        data["band"] = data.get("band") or rubric.band_for(data["overall_score"])
        data["risk"] = data.get("risk") or rubric.risk_for(data["overall_score"])
    return RubricReport(**data)


def score_deal(reports, reg: Registry, llm, subject: dict[str, Any], extra_context=None) -> RubricReport:
    rubric = reg.rubric_of_kind("deal-health")
    if rubric is None:
        raise ValueError("No deal-health rubric found in rubrics/")
    return score_rubric(reports, rubric, reg, llm, subject, extra_context)


def score_account(reports, reg: Registry, llm, subject: dict[str, Any], extra_context=None) -> RubricReport:
    rubric = reg.rubric_of_kind("account-health")
    if rubric is None:
        raise ValueError("No account-health rubric found in rubrics/")
    return score_rubric(reports, rubric, reg, llm, subject, extra_context)
