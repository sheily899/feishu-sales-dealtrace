"""Render a CoachingReport as Markdown (for files, PRs, Slack, CRM notes) or a
compact terminal summary.
"""
from __future__ import annotations

from .models import CoachingReport, Quote

_BAND_EMOJI = {"great": "🟢", "good": "🟢", "developing": "🟡", "poor": "🔴"}
_RISK_EMOJI = {"low": "🟢", "medium": "🟡", "high": "🔴"}
_PRIO_EMOJI = {"high": "🔴", "medium": "🟡", "low": "⚪"}


def _quotes(qs: list[Quote]) -> str:
    if not qs:
        return ""
    return "\n".join(f"  > **{q.speaker}:** {q.text}" for q in qs)


def to_markdown(r: CoachingReport, title: str | None = None) -> str:
    L: list[str] = []
    head = title or (r.call_id or "Call")
    L.append(f"# Coaching report — {head}\n")

    c = r.classification
    score = f"{round(r.overall_score)}/100" if r.overall_score is not None else "n/a"
    L.append(
        f"**Call type:** {c.call_type}  ·  **Phase:** {c.phase}  ·  "
        f"**Classifier confidence:** {c.confidence:.0%}  ·  **Overall:** {score}\n"
    )
    L.append(f"> {r.summary}\n")

    # Outcomes
    if r.outcomes:
        L.append("## Desired outcomes\n")
        icon = {"achieved": "✅", "partial": "🟡", "missed": "❌", "unknown": "❔"}
        for o in r.outcomes:
            L.append(f"- {icon.get(o.status, '❔')} **{o.status.title()}** — {o.statement}")
            ev = _quotes(o.evidence)
            if ev:
                L.append(ev)
        L.append("")

    # Scores table
    if r.scores:
        L.append("## Scorecard\n")
        L.append("| Criterion | Score | Band | Why |")
        L.append("|---|---:|:---:|---|")
        for s in r.scores:
            emoji = _BAND_EMOJI.get(s.band, "")
            why = s.rationale.replace("|", "\\|")
            L.append(f"| {s.criterion_name} | {round(s.score)} | {emoji} {s.band} | {why} |")
        L.append("")

    # Coaching
    co = r.coaching
    if co.strengths:
        L.append("## What worked\n")
        for p in co.strengths:
            L.append(f"### ✅ {p.title}")
            L.append(p.detail)
            ev = _quotes(p.evidence)
            if ev:
                L.append(ev)
            L.append("")

    if co.improvements:
        L.append("## What to improve\n")
        order = {"high": 0, "medium": 1, "low": 2}
        for p in sorted(co.improvements, key=lambda x: order.get(x.priority or "medium", 1)):
            pr = f" _(priority: {p.priority})_" if p.priority else ""
            L.append(f"### 🎯 {p.title}{pr}")
            L.append(p.detail)
            ev = _quotes(p.evidence)
            if ev:
                L.append(ev)
            if p.better_move:
                L.append(f"\n  **Try instead:** _{p.better_move}_")
            L.append("")

    if co.next_call_focus:
        L.append("## Focus for the next call\n")
        for n in co.next_call_focus:
            L.append(f"- [ ] {n}")
        L.append("")

    if r.manager_notes:
        L.append("---\n")
        L.append(f"_Manager notes:_ {r.manager_notes}")

    return "\n".join(L).rstrip() + "\n"


def to_terminal(r: CoachingReport) -> str:
    """A compact, color-free one-screen summary for CLI output."""
    c = r.classification
    score = f"{round(r.overall_score)}/100" if r.overall_score is not None else "n/a"
    lines = [
        f"{c.call_type} ({c.phase}) · confidence {c.confidence:.0%} · overall {score}",
        f"  {r.summary}",
    ]
    if r.scores:
        lines.append("  scores: " + ", ".join(f"{s.criterion_name} {round(s.score)}" for s in r.scores))
    if r.coaching.improvements:
        lines.append("  top fix: " + r.coaching.improvements[0].title)
    return "\n".join(lines)


def to_share_card(r, title: str | None = None) -> str:
    """A short, paste-ready card for a coaching report."""
    L: list[str] = []
    if isinstance(r, CoachingReport):
        score = f"{round(r.overall_score)}/100" if r.overall_score is not None else "n/a"
        L.append(f"🎯 {title or 'My sales call'} — {r.classification.call_type} call scored {score}")
        if r.coaching.strengths:
            L.append(f"✅ Did well: {r.coaching.strengths[0].title}")
        if r.coaching.improvements:
            L.append(f"🎯 Biggest lever: {r.coaching.improvements[0].title}")
    else:
        raise TypeError("to_share_card expects a CoachingReport")

    L.append("")
    return "\n".join(L) + "\n"


