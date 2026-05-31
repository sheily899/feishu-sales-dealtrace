"""Build a prioritized 'what to improve' inbox by aggregating many call coaching
reports — at the rep, team, or company level.

This is deterministic (no LLM): it rolls up the structured signals already in each
report (criterion scores + flagged improvements), so it's cheap enough to run every
morning. The Claude `inbox-builder` subagent can wrap this with a written narrative.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .models import CoachingReport, FocusArea, Inbox, InboxMember, InboxWin
from .registry import Registry

# A criterion is a "focus" for a report if flagged as an improvement OR scored below
# this. Tune in config if you like.
WEAK_SCORE = 60


@dataclass
class _Acc:
    name: str
    scores: list[float] = field(default_factory=list)
    improvement_count: int = 0
    reports: set[str] = field(default_factory=set)
    reps: set[str] = field(default_factory=set)
    better_moves: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)


def _criterion_name(reg: Registry, cid: str, fallback: str) -> str:
    for sc in reg.scorecards.values():
        for crit in sc.criteria:
            if crit.id == cid:
                return crit.name
    return fallback or cid


def build_inbox(
    reports: list[tuple[dict[str, Any], CoachingReport]],
    scope: str,
    generated_for: str,
    period: str,
    reg: Registry,
    top_n: int = 6,
) -> Inbox:
    """Aggregate reports into an Inbox.

    Args:
        reports: list of ``(meta, CoachingReport)`` where meta may include
            ``{"rep": name, "call_id": id, "title": str}``.
        scope: 'rep' | 'team' | 'company'.
    """
    acc: dict[str, _Acc] = {}
    win_acc: dict[str, _Acc] = {}
    per_rep: dict[str, dict[str, Any]] = defaultdict(lambda: {"scores": [], "calls": 0, "focus": defaultdict(int)})
    by_call_type: dict[str, int] = defaultdict(int)
    overalls: list[float] = []

    for meta, r in reports:
        rep = meta.get("rep") or generated_for or "unknown"
        call_id = meta.get("call_id") or meta.get("title") or r.call_id or "call"
        by_call_type[r.classification.call_type] += 1
        if r.overall_score is not None:
            overalls.append(r.overall_score)
            per_rep[rep]["scores"].append(r.overall_score)
        per_rep[rep]["calls"] += 1

        # Map criterion_id -> score for this report.
        score_by_cid = {s.criterion_id: s.score for s in r.scores}

        # Focus areas: flagged improvements, or weak criterion scores.
        # Track both the accumulator key AND any criterion_id we touched, so the
        # weak-score pass below never double-counts a criterion already flagged.
        flagged: set[str] = set()
        for imp in r.coaching.improvements:
            cid = imp.criterion_id or imp.title
            flagged.add(cid)
            if imp.criterion_id:
                flagged.add(imp.criterion_id)
            a = acc.setdefault(cid, _Acc(name=_criterion_name(reg, cid, imp.title)))
            a.improvement_count += 1
            a.reports.add(call_id)
            a.reps.add(rep)
            if imp.better_move:
                a.better_moves.append(imp.better_move)
            if imp.detail:
                a.details.append(imp.detail)
            if cid in score_by_cid:
                a.scores.append(score_by_cid[cid])
            per_rep[rep]["focus"][a.name] += 1
        for s in r.scores:
            if s.score < WEAK_SCORE and s.criterion_id not in flagged:
                a = acc.setdefault(s.criterion_id, _Acc(name=s.criterion_name))
                a.reports.add(call_id)
                a.reps.add(rep)
                a.scores.append(s.score)
                per_rep[rep]["focus"][a.name] += 1

        # Wins: strengths.
        for st in r.coaching.strengths:
            cid = st.criterion_id or st.title
            w = win_acc.setdefault(cid, _Acc(name=_criterion_name(reg, cid, st.title)))
            w.improvement_count += 1
            w.reports.add(call_id)

    # Rank focus areas: more reports + lower avg score => higher priority.
    def rank_key(a: _Acc) -> float:
        avg = statistics.mean(a.scores) if a.scores else 50.0
        return len(a.reports) * (100 - avg)

    ranked = sorted(acc.values(), key=rank_key, reverse=True)[:top_n]
    focus_areas = []
    for a in ranked:
        avg = round(statistics.mean(a.scores), 1) if a.scores else None
        n = len(a.reports)
        priority = "high" if (n >= 3 or (avg is not None and avg < 45)) else "medium" if n >= 2 else "low"
        fa = FocusArea(
            title=a.name,
            detail=a.details[0] if a.details else None,
            priority=priority,
            evidence_count=n,
            avg_score=avg,
            example_calls=sorted(a.reports)[:5],
            drill=a.better_moves[0] if a.better_moves else None,
            affected_reps=sorted(a.reps) if scope != "rep" else [],
        )
        focus_areas.append(fa)

    wins = [
        InboxWin(title=w.name, evidence_count=len(w.reports))
        for w in sorted(win_acc.values(), key=lambda x: len(x.reports), reverse=True)[:3]
    ]

    members = []
    if scope in ("team", "company"):
        for rep, d in sorted(per_rep.items()):
            top_focus = max(d["focus"].items(), key=lambda kv: kv[1])[0] if d["focus"] else None
            members.append(
                InboxMember(
                    name=rep,
                    calls_analyzed=d["calls"],
                    avg_overall_score=round(statistics.mean(d["scores"]), 1) if d["scores"] else None,
                    top_focus=top_focus,
                )
            )

    return Inbox(
        scope=scope,  # type: ignore[arg-type]
        generated_for=generated_for,
        period=period,
        stats={
            "calls_analyzed": len(reports),
            "avg_overall_score": round(statistics.mean(overalls), 1) if overalls else None,
            "by_call_type": dict(by_call_type),
        },
        focus_areas=focus_areas,
        wins=wins,
        members=members,
    )
