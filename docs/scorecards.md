# Scorecards

A **scorecard** is the coaching rubric for a specific call type. It is a
weighted list of criteria — observable, evidence-grounded behaviors — that the
pipeline scores 0–100 and maps to a band (e.g., poor/developing/good/great).

Scorecards live in `scorecards/*.yaml` and conform to
`schemas/scorecard.schema.json`.

---

## Anatomy of a scorecard

```yaml
id: discovery                    # stable slug; matches call_types.yaml reference
name: Discovery
version: "1.0"
description: >
  Evaluates how well the rep uncovered priorities, quantified impact,
  mapped the decision, avoided premature pitching, and secured next steps.
applies_to: [discovery]          # call-type IDs this scorecard is valid for
frameworks: [spiced, meddpicc]   # frameworks this scorecard draws on

scoring:
  scale_max: 100
  bands:
    - { label: great,     min: 80, meaning: "Textbook execution; use as a teaching example." }
    - { label: good,      min: 60, meaning: "Solid; minor gaps to tighten." }
    - { label: developing, min: 40, meaning: "Partially done; clear room to improve." }
    - { label: poor,      min: 0,  meaning: "Missing or counterproductive." }

criteria:
  - id: priority_quantified
    name: Top Priority Identified & Quantified
    weight: 2                    # relative; normalized to 1.0 across all criteria
    intent: >
      The highest-signal discovery move — a ranked priority with a number on it.
    framework_refs: [spiced.pain, spiced.impact, meddpicc.metrics]
    what_great_looks_like:
      - "The #1 priority is named in the buyer's words."
      - "Impact is quantified (time, money, or risk) and cost of inaction is explored."
    what_poor_looks_like:
      - "Pain stays vague ('it's a headache') with no quantification."
      - "Rep supplies the pain instead of the buyer confirming it."
    evidence_cues:
      - "\"Of everything on your plate, where does this rank?\""
      - "\"What's that costing you per month?\""
    coaching_prompts:
      - "Could you take the impact number from this call to a CFO? If not, what's missing?"
```

---

## Anatomy of a criterion

| Field | Required | Purpose |
|---|---|---|
| `id` | Yes | Stable slug (`^[a-z0-9_]+$`). Referenced in the coaching report. |
| `name` | Yes | Human-readable label. |
| `weight` | Yes | Relative weight. The engine normalizes all weights to sum to 1.0. |
| `intent` | No | One sentence: why this criterion matters to deal outcomes. |
| `framework_refs` | No | Links to framework elements (e.g., `spiced.pain`). |
| `what_great_looks_like` | Yes | Observable behaviors that earn a top score. The LLM's gold standard. |
| `what_poor_looks_like` | No | Common failure modes / anti-patterns. |
| `evidence_cues` | No | Phrases or moves to look for in the transcript. |
| `coaching_prompts` | No | Reflective questions the coach can pose back to the rep. |

---

## How scoring works

### 1. Evidence search

The LLM reads the transcript looking for each criterion's `evidence_cues` — both
positive (the rep did this well) and negative (the rep missed it or did the
opposite). It also looks for behaviors in `what_great_looks_like` and
`what_poor_looks_like`.

### 2. Score assignment (0–100)

The model assigns a score to each criterion using the full 0–100 range:

| Range | Interpretation |
|---|---|
| 80–100 | Great — textbook execution; suitable as a teaching example |
| 60–79 | Good — solid, minor gaps |
| 40–59 | Developing — partially done, clear room to improve |
| 0–39 | Poor — missing or counterproductive |

The system prompt instructs the model not to inflate scores and to reserve 90+
for genuinely exceptional moments. An average call lands 50–65.

### 3. Band assignment

Each score is mapped to a band using the scorecard's `bands` definition. The
default bands are `poor` (0+), `developing` (40+), `good` (60+), `great` (80+).
You can customize band thresholds and labels per scorecard.

### 4. Weighted average

The engine computes `overall_score` as:

```
overall_score = Σ (criterion_score × normalized_weight)
```

Weights are normalized so they sum to 1.0. A scorecard with criteria weights
`[1, 1.5, 2, 1, 1.5, 1, 1, 1.5]` is internally rescaled before the average is
computed.

---

## How to read a coaching report

A coaching report (JSON, conforming to `schemas/coaching_report.schema.json`)
has the following structure:

### `classification`

```json
{
  "call_type": "discovery",
  "phase": "pre-sales",
  "confidence": 0.88,
  "rationale": "…",
  "alternatives": [{"call_type": "demo", "confidence": 0.09}]
}
```

Use `confidence` and `alternatives` to spot calls where the classification is
ambiguous — those are worth a human review.

### `outcomes`

```json
[
  {
    "id": "quantify-priority",
    "statement": "Quantify the cost of manual reporting (~10 hrs/week, not yet in dollars).",
    "status": "partial",
    "evidence": [{"speaker": "Alex", "text": "It's probably ten hours a week across the team."}]
  }
]
```

`status` is one of `achieved` / `partial` / `missed` / `unknown`. Pay attention
to `missed` outcomes — these are the clearest signal of what the rep should fix.

### `scores`

```json
[
  {
    "criterion_id": "priority_quantified",
    "criterion_name": "Top Priority Identified & Quantified",
    "score": 55,
    "band": "developing",
    "weight": 0.22,
    "rationale": "Rep surfaced the priority but never quantified the impact in dollars or time.",
    "evidence": [
      {"speaker": "Rep", "text": "So the biggest pain point is the reporting backlog?"},
      {"speaker": "Buyer", "text": "Yes, it's a real headache every month."}
    ]
  }
]
```

High-weight criteria that score `developing` or `poor` are the highest-leverage
coaching targets.

### `overall_score`

A single number (weighted average). Use it for trending over time per rep, not
as a performance rating in isolation.

### `coaching`

```json
{
  "strengths": [
    {
      "title": "Strong agenda and framing",
      "detail": "Rep opened by proposing a clear agenda and inviting the buyer to add to it.",
      "criterion_id": "agenda_and_framing",
      "evidence": [{"speaker": "Rep", "text": "Here's what I was hoping to cover — what would make this valuable for you?"}]
    }
  ],
  "improvements": [
    {
      "title": "Quantify the cost of inaction",
      "detail": "Pain was named but never given a number. Without a dollar or time figure, the buyer has no ROI anchor.",
      "criterion_id": "priority_quantified",
      "evidence": [{"speaker": "Buyer", "text": "It's a real headache every month."}],
      "better_move": "\"When you say 'headache every month' — how many hours does it cost the team? And if you put a dollar figure to that, what are we talking about?\"",
      "priority": "high"
    }
  ],
  "next_call_focus": [
    "Return to the reporting pain and quantify it in dollars or hours before advancing.",
    "Introduce a second stakeholder — the economic buyer has not been identified."
  ]
}
```

**Strengths** are meant for positive reinforcement — they should be shared with
the rep and used as examples in team settings.

**Improvements** are prioritized (`high` / `medium` / `low`). Focus rep coaching
on `high`-priority items first. Each includes a `better_move` — a concrete,
copy-pasteable example of what the rep could have said instead.

**Next-call focus** is the most actionable section: 1–3 specific things the rep
should do on the very next interaction with this account.

---

## Scorecards shipped with GTM Superintelligence

| File | Call type(s) | Key frameworks |
|---|---|---|
| `scorecards/cold-call.yaml` | `cold-call` | BANT, Next Steps |
| `scorecards/discovery.yaml` | `discovery` | SPICED, MEDDPICC |
| `scorecards/demo.yaml` | `demo` | Command of the Message, SPICED |
| `scorecards/technical-validation.yaml` | `technical-validation` | MEDDPICC |
| `scorecards/go-no-go.yaml` | `go-no-go` | MEDDPICC, Next Steps |
| `scorecards/negotiation.yaml` | `negotiation` | MEDDPICC, Command of the Message |
| `scorecards/closing.yaml` | `closing` | Next Steps, MEDDPICC |
| `scorecards/onboarding-kickoff.yaml` | `onboarding-kickoff` | Next Steps |
| `scorecards/customer-check-in.yaml` | `customer-check-in` | SPICED |
| `scorecards/renewal.yaml` | `renewal` | SPICED, Command of the Message |
| `scorecards/qbr.yaml` | `qbr` | Command of the Message |
| `scorecards/generic-conversation.yaml` | `internal`, `partner`, `vendor` | (none) |

---

## Cross-references

- Core concepts: [concepts.md](./concepts.md)
- Writing your own scorecard: [writing-a-scorecard.md](./writing-a-scorecard.md)
- Framework reference: [frameworks.md](./frameworks.md)
- Call types: [call-types.md](./call-types.md)
- Pipeline architecture: [architecture.md](./architecture.md)
