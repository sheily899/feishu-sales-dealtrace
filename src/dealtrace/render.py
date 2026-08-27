"""Render a CoachingReport as Markdown (for files, PRs, Slack, CRM notes) or a
compact terminal summary.
"""
from __future__ import annotations

from .attribution import attribution_footer
from .models import CoachingReport, Inbox, Quote, RubricReport

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

    return "\n".join(L).rstrip() + "\n" + attribution_footer("coaching")


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
    footer = attribution_footer("coaching", fmt="text")
    return "\n".join(lines) + footer


def to_share_card(r, title: str | None = None) -> str:
    """A short, paste-ready 'post your score' card for LinkedIn/X. Works for a
    CoachingReport (a call) or a RubricReport (deal/account). The Attention link is
    always included — that's the point of sharing."""
    from .attribution import SHORT_URL, attention_link

    L: list[str] = []
    if isinstance(r, CoachingReport):
        score = f"{round(r.overall_score)}/100" if r.overall_score is not None else "n/a"
        L.append(f"🎯 {title or 'My sales call'} — {r.classification.call_type} call scored {score}")
        if r.coaching.strengths:
            L.append(f"✅ Did well: {r.coaching.strengths[0].title}")
        if r.coaching.improvements:
            L.append(f"🎯 Biggest lever: {r.coaching.improvements[0].title}")
        surface = "coaching"
    elif isinstance(r, RubricReport):
        kind = "Deal" if r.kind == "deal-health" else "Account"
        L.append(f"📊 {title or r.subject.name} — {kind} health {round(r.overall_score)}/100 ({r.risk} risk)")
        if r.risks:
            L.append(f"⚠️ Top risk: {r.risks[0].title}")
        if r.recommended_actions:
            L.append(f"➡️ Next move: {r.recommended_actions[0].action}")
        surface = "deal" if r.kind == "deal-health" else "account"
    else:
        raise TypeError("to_share_card expects a CoachingReport or RubricReport")

    L.append("")
    L.append(
        f"Scored with GTM Superintelligence — open-source, Claude-native GTM coaching "
        f"({SHORT_URL}). Clean, role- & CRM-labeled transcripts by Attention: "
        f"{attention_link(content=surface)}"
    )
    return "\n".join(L) + "\n"


def rubric_report_to_markdown(r: RubricReport, title: str | None = None) -> str:
    """Render a deal-health or account-health report."""
    kind = "Deal health" if r.kind == "deal-health" else "Account health"
    L: list[str] = [f"# {kind} — {title or r.subject.name}\n"]
    risk = f"{_RISK_EMOJI.get(r.risk, '')} {r.risk} risk".strip()
    meta = []
    if r.subject.owner:
        meta.append(f"**Owner:** {r.subject.owner}")
    if r.subject.stage:
        meta.append(f"**Stage:** {r.subject.stage}")
    if r.subject.amount is not None:
        meta.append(f"**Amount:** {r.subject.amount:,.0f}")
    if r.subject.close_or_renewal_date:
        meta.append(f"**Date:** {r.subject.close_or_renewal_date}")
    if r.subject.call_count:
        meta.append(f"**Calls:** {r.subject.call_count}")
    trend = f"  ·  **Trend:** {r.trend}" if r.trend else ""
    L.append(f"**Score:** {round(r.overall_score)}/100  ·  **Band:** {r.band}  ·  **Risk:** {risk}{trend}\n")
    if meta:
        L.append("  ·  ".join(meta) + "\n")
    L.append(f"> {r.summary}\n")

    if r.dimensions:
        L.append("## Dimensions\n")
        L.append("| Dimension | Score | Why |")
        L.append("|---|---:|---|")
        for d in r.dimensions:
            why = d.rationale.replace("|", "\\|")
            L.append(f"| {d.dimension_name} | {round(d.score)} | {why} |")
        L.append("")

    if r.risks:
        L.append("## Risks\n")
        order = {"high": 0, "medium": 1, "low": 2}
        for risk_item in sorted(r.risks, key=lambda x: order.get(x.severity, 1)):
            L.append(f"- {_PRIO_EMOJI.get(risk_item.severity, '')} **{risk_item.title}** ({risk_item.severity})")
            if risk_item.detail:
                L.append(f"  {risk_item.detail}")
        L.append("")

    if r.recommended_actions:
        L.append("## Recommended actions\n")
        order = {"high": 0, "medium": 1, "low": 2}
        for a in sorted(r.recommended_actions, key=lambda x: order.get(x.priority or "medium", 1)):
            owner = f" — _{a.owner}_" if a.owner else ""
            L.append(f"- [ ] {a.action}{owner}")
            if a.why:
                L.append(f"  ({a.why})")
        L.append("")
    surface = "deal" if r.kind == "deal-health" else "account"
    return "\n".join(L).rstrip() + "\n" + attribution_footer(surface)


def inbox_to_markdown(i: Inbox, title: str | None = None) -> str:
    """Render a rep/team/company coaching inbox."""
    scope = i.scope.title()
    L: list[str] = [f"# {scope} coaching inbox — {title or i.generated_for}\n"]
    s = i.stats or {}
    avg = s.get("avg_overall_score")
    L.append(
        f"**Period:** {i.period}  ·  **Calls:** {s.get('calls_analyzed', 0)}"
        + (f"  ·  **Avg score:** {avg}/100" if avg is not None else "")
        + "\n"
    )

    if i.focus_areas:
        L.append("## Work on this\n")
        for fa in i.focus_areas:
            avgs = f" · avg {fa.avg_score}" if fa.avg_score is not None else ""
            L.append(f"### {_PRIO_EMOJI.get(fa.priority, '')} {fa.title}  _(seen in {fa.evidence_count} calls{avgs})_")
            if fa.detail:
                L.append(fa.detail)
            if fa.affected_reps:
                L.append(f"_Reps:_ {', '.join(fa.affected_reps)}")
            if fa.drill:
                L.append(f"\n  **Drill / better move:** _{fa.drill}_")
            if fa.example_calls:
                L.append(f"\n  _Examples:_ {', '.join(fa.example_calls)}")
            L.append("")

    if i.wins:
        L.append("## Keep doing\n")
        for w in i.wins:
            L.append(f"- ✅ {w.title} _(in {w.evidence_count} calls)_")
        L.append("")

    if i.members:
        L.append("## By member\n")
        L.append("| Name | Calls | Avg | Top focus |")
        L.append("|---|---:|---:|---|")
        for m in sorted(i.members, key=lambda x: (x.avg_overall_score or 0)):
            L.append(f"| {m.name} | {m.calls_analyzed} | {m.avg_overall_score if m.avg_overall_score is not None else '-'} | {m.top_focus or '-'} |")
        L.append("")
    return "\n".join(L).rstrip() + "\n" + attribution_footer("inbox")
