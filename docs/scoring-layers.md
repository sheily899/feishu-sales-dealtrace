# Three layers of scoring

GTM Superintelligence produces scores at three levels of granularity. They are designed to
feed each other: per-call coaching is the raw material; deal and account health
are the aggregations.

```
 individual calls
      │
      ▼
 call coaching reports  ─────────────────┐
      │                                  │
      ├──► deal health report (sales)    ├──► rep / team / company inbox
      │                                  │
      └──► account health report (CSM)  ─┘
```

---

## Layer 1 — Call scoring (per conversation)

Each call runs through the four-stage pipeline (classify → infer outcomes →
score → coach) and produces a **coaching report**: per-criterion scores,
strengths, prioritized improvements with better-moves, and a next-call focus.

Call scoring is the foundation. Deal health and account health both consume
coaching reports as their inputs, so the quality of call coaching directly
determines the quality of the aggregate scores.

For the full anatomy of a coaching report and how scorecards work, see
[scorecards.md](./scorecards.md).

---

## Layer 2 — Deal / opportunity health (sales)

**What it answers:** How healthy is this deal, and what is most likely to kill it?

Deal health aggregates every coaching report filed against one opportunity and
scores it against `rubrics/deal-health.yaml` — a MEDDPICC- and SPICED-grounded
rubric that evaluates qualification coverage, momentum, and risk.

### Dimensions

| Dimension | Weight | What it measures |
|---|---:|---|
| Pain & Quantified Impact | 2 | Is a ranked, quantified pain owned by the buyer? |
| Economic Buyer Engagement | 2 | Is the economic buyer identified and directly engaged? |
| Champion Strength | 1.5 | Does the champion advocate internally and grant access to power? |
| Decision Process & Criteria | 1.5 | Are the steps, criteria, and approvers mapped? |
| Compelling Event & Timeline | 1.5 | Is there a dated forcing function that anchors the close? |
| Multithreading | 1.5 | Are multiple stakeholders across functions engaged? |
| Next-Step Hygiene | 1.5 | Do most calls end on a specific, dated, mutually-owned next step? |
| Paper / Procurement Process | 1 | Is the legal/security/procurement path understood and started? |
| Competition & Alternatives | 1 | Are alternatives (including status quo) known and positioned against? |
| Momentum | 1 | Is there regular, meaningful progress between calls? |

### Score bands and risk

| Band | Min score | Meaning |
|---|---:|---|
| strong | 75 | Well-qualified, multi-threaded, moving. Forecastable. |
| promising | 55 | Real, but with named gaps to close. |
| at-risk | 35 | Material gaps; needs intervention to survive. |
| long-shot | 0 | Poorly qualified or stalled. Inspect or disqualify. |

| Risk label | Score range | Meaning |
|---|---|---|
| low | 65–100 | Low risk if execution continues. |
| medium | 35–64 | Moderate risk; specific gaps to close. |
| high | 0–34 | High risk of slip or loss. |

The `band` comes from `scoring.bands` (highest matching `min` wins). The `risk`
label comes from `scoring.risk_bands` (scores evaluated ascending against `max`).
Both are editable in `rubrics/deal-health.yaml`, which conforms to
`schemas/rubric.schema.json`.

### CLI

```bash
gtmsi deal <folder> --name "Acme — Platform" --owner Jordan \
  --stage Discovery --amount 80000 --date 2026-09-30
```

`<folder>` holds the raw transcripts for **one** opportunity (any supported format);
the command coaches each call, then scores the deal across them. The `--name`,
`--owner`, `--stage`, `--amount`, and `--date` flags attach CRM metadata the model
uses as extra context and that flows into the report's `subject`.

### Example output

From `examples/reports/deal_acme.md`:

```markdown
# Deal health — Acme Corp — Northstar Platform

**Score:** 49/100  ·  **Band:** at-risk  ·  **Risk:** medium  ·  **Trend:** improving

**Owner:** Jordan  ·  **Stage:** Discovery  ·  **Calls:** 1

> Early but real: strong, quantified pain and a genuine Series-B compelling
> event give this deal a spine. It is fragile where it counts — single-threaded
> on Sam, economic buyer unconfirmed, decision and paper process unmapped, and
> no calendared next step.

| Dimension                   | Score | Why                                              |
|-----------------------------|------:|--------------------------------------------------|
| Pain & Quantified Impact    |    74 | Top priority named in the buyer's words; dollar  |
|                             |       | impact is still a gut estimate, not a model.     |
| Economic Buyer Engagement   |    35 | Finance must sign off but EB not yet identified. |
| Multithreading              |    28 | Entirely single-threaded on Sam.                 |
| Next-Step Hygiene           |    35 | Call closed on 'send me a summary' — no date.   |
| Compelling Event & Timeline |    78 | Series B close at end of Q3 is a real deadline.  |
```

The full report also includes a prioritized risk list and recommended actions
with owners.

---

## Layer 3 — Account health (CSM)

**What it answers:** Is this customer healthy, likely to renew, and ready to expand?

Account health is the Customer Success Manager (CSM) counterpart to deal health.
It aggregates post-sales coaching reports (onboarding, check-in, renewal, QBR)
against `rubrics/account-health.yaml` to produce a health score, a churn-risk
label, and recommended plays.

### Dimensions

| Dimension | Weight | What it measures |
|---|---:|---|
| Adoption & Usage | 2 | Is usage active, broad, and growing? |
| Value Realized (ROI) | 2 | Can the customer name concrete outcomes tied to original goals? |
| Sentiment & Satisfaction | 1.5 | Is the tone positive and proactive? |
| Engagement & Cadence | 1.5 | Is there regular, two-way participation? |
| Relationship Depth & Multithreading | 1.5 | Are multiple stakeholders engaged, including a senior sponsor? |
| Risk Signals | 1.5 | Are churn precursors (budget, reorg, competitor eval) present? |
| Renewal Readiness | 1.5 | Is the renewal process known, with budget owner engaged? |
| Champion Health | 1 | Is the champion engaged, influential, and stable? |
| Expansion Potential | 1 | Is there a credible, warm expansion use case? |

### Score bands and risk

| Band | Min score | Meaning |
|---|---:|---|
| healthy | 75 | Adopting, getting value, multi-threaded. Renewal + expansion likely. |
| stable | 55 | Fine but not a fan; watch for drift. |
| at-risk | 35 | Leading indicators are flashing; intervene now. |
| critical | 0 | Likely to churn without urgent action. |

| Risk label | Score range | Meaning |
|---|---|---|
| low | 65–100 | Low churn risk. |
| medium | 35–64 | Elevated churn risk; specific gaps to close. |
| high | 0–34 | High churn risk. |

### CLI

```bash
gtmsi account <folder> --name "Initech"
```

As with deal health, the folder can contain transcripts, existing coaching-report
JSONs, or both.

### Example output

From `examples/reports/account_initech.md`:

```markdown
# Account health — Initech

**Score:** 66/100  ·  **Band:** stable  ·  **Risk:** low  ·  **Trend:** flat

**Owner:** Taylor (CSM)  ·  **Amount:** 90,000  ·  **Date:** renewal in ~1 quarter

> A genuinely happy, well-adopted account with quantified value — but two things
> keep it out of 'healthy': a live budget concern from the budget owner, and a
> renewal that has no committed path.

| Dimension            | Score | Why                                                  |
|----------------------|------:|------------------------------------------------------|
| Adoption & Usage     |    80 | Broad, active usage; real daily work in the product. |
| Value Realized (ROI) |    78 | Concrete, quantified outcomes confirmed by customer. |
| Risk Signals         |    45 | Budget pressure from the budget owner, unresolved.   |
| Renewal Readiness    |    48 | Renewal in ~1 quarter; no commitment secured.        |
```

---

## How call coaching feeds deal / account health

The `score_rubric` engine (in `src/gtmsi/scoring/__init__.py`) takes a list
of `(call_id, CoachingReport)` pairs and sends a compact summary of each to the
model — overall score, call type, outcomes, low-scoring criteria, top
improvements, and key evidence quotes. This keeps token usage low while
preserving the signal the rubric needs.

Call coaching therefore feeds deal and account scoring automatically: run
`gtmsi coach` on each call in a deal, then run `gtmsi deal` on the same
folder. No separate data pipeline is required.

### Customizing rubrics

Both rubrics are editable YAML. To adjust dimensions, weights, or scoring bands,
edit `rubrics/deal-health.yaml` or `rubrics/account-health.yaml` directly.
The schema at `schemas/rubric.schema.json` documents every field and is
enforced on load.

---

## Cross-references

- Per-call scoring and scorecards: [scorecards.md](./scorecards.md)
- Coaching inbox (what to do with the reports): [inbox.md](./inbox.md)
- CRM auto-fill from deal/account reports: [crm.md](./crm.md)
- Core concepts: [concepts.md](./concepts.md)
- Schema reference: `schemas/rubric.schema.json`, `schemas/rubric_report.schema.json`
