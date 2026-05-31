# Core Concepts

This page introduces the six building blocks of GTM Superintelligence and explains how they
fit together. Reading it takes about five minutes and will make every other doc
click into place.

---

## The six building blocks

| Concept | What it is | Where it lives |
|---|---|---|
| **Transcript** | The raw material: a speaker-turn record of a call | Any recorder → normalized JSON |
| **Call Type** | The label that classifies what kind of call it was | `config/call_types.yaml` |
| **Outcome** | A concrete goal the call should achieve | `config/outcomes.yaml` |
| **Framework** | A named sales methodology (SPICED, MEDDPICC, …) expressed as data | `frameworks/*.yaml` |
| **Scorecard** | A weighted rubric of criteria for one call type | `scorecards/*.yaml` |
| **Coaching Report** | The structured output: scores, strengths, improvements, next-call focus | JSON (`schemas/coaching_report.schema.json`) |

---

## Transcript

A **transcript** is the single required input. GTM Superintelligence never reads a vendor's
raw payload directly. Every recorder — Attention, Gong, Fireflies, Otter, Zoom, VTT, SRT,
or plain text — lands in the same `NormalizedTranscript` shape (via the native Attention
connection or a file **adapter**; see `schemas/transcript.schema.json`).

The transcript has two required fields:

- `schema_version` — always `"1.0"` so parsers can version-check.
- `turns` — an ordered list of speaker turns, each with a `speaker` and `text`.

Everything else — call metadata, participant roles, timestamps — enriches the
coaching but is optional. The `participants` array is the key enrichment: it
marks each person as `rep`, `prospect`, `customer`, `partner`, `internal`, or
`unknown`. The pipeline coaches the **rep side only**.

---

## Call Type

A **call type** is the pipeline's first decision: what kind of conversation just
happened? The classifier chooses exactly one primary type from the 14-entry
taxonomy in `config/call_types.yaml`.

Call types are organized into three phases:

- **pre-sales** — win the deal (cold call, discovery, demo, technical validation,
  go/no-go, negotiation, closing).
- **post-sales** — keep and grow it (`onboarding-kickoff`, `customer-check-in`,
  `renewal`, `qbr`).
- **neither** — internal, partner, or vendor calls that get a generic rubric or
  are skipped entirely.

Each call type carries `positive_signals`, `negative_signals`, and
`often_confused_with` hints that drive classification accuracy.

---

## Outcome

An **outcome** is a concrete goal a call should achieve. Outcomes bridge the
gap between "what type of call was this?" and "did it go well?".

The pipeline uses outcomes in two steps:

1. Each call type has `default_outcomes` — a set of generic goals (e.g.,
   `quantify-priority`, `secure-next-step`).
2. The outcome-inference step **refines** each generic goal into a specific,
   deal-aware statement using the actual transcript content (e.g., `secure-next-step`
   → "Book a 30-minute technical deep-dive with their Head of Data before month-end").

The coaching report records each outcome's status: `achieved`, `partial`,
`missed`, or `unknown`, with verbatim evidence quotes.

---

## Framework

A **framework** is a named sales methodology expressed as structured YAML. Each
framework has a list of **elements** — the named concepts (like "Pain" in SPICED
or "Economic Buyer" in MEDDPICC) — each with a core question, good signals,
missing signals, and example questions a rep can ask.

Frameworks give the coaching report a shared vocabulary. Instead of generic
advice, the coach can say "no Critical Event surfaced (SPICED)" or
"single-threaded — no Economic Buyer engaged (MEDDPICC)".

Frameworks are referenced by scorecards via `framework_refs` (e.g.,
`spiced.pain`, `meddpicc.economic_buyer`) so criterion-level feedback is always
grounded in the right methodology.

---

## Scorecard

A **scorecard** is a weighted list of **criteria** — the measurable behaviors
the coach evaluates. Each scorecard is specific to one or more call types
(a discovery scorecard would be inappropriate for a QBR).

Each criterion has:

- A `weight` (unnormalized; the engine sums and normalizes them to 1.0).
- `what_great_looks_like` and `what_poor_looks_like` — the gold standard and
  common failure modes the LLM uses to calibrate its score.
- `evidence_cues` — phrases or behaviors to look for in the transcript.
- `framework_refs` — links back to the framework elements it tests.

Scores run 0–100 and are bucketed into **bands** (e.g., `poor`, `developing`,
`good`, `great`) defined in the scorecard's `scoring` block.

---

## Coaching Report

The **coaching report** is the pipeline's output. It is a JSON document (see
`schemas/coaching_report.schema.json`) with five major sections:

| Section | Contents |
|---|---|
| `classification` | Chosen call type, phase, confidence, rationale, alternatives |
| `outcomes` | Each desired outcome and its achieved/partial/missed/unknown status |
| `scores` | One entry per criterion: score, band, weight, rationale, evidence |
| `overall_score` | Weighted average of all criterion scores |
| `coaching` | Strengths, prioritized improvements with "better moves", next-call focus |

Everything in the report is **evidence-bound**: every score, strength, and
improvement references verbatim (or near-verbatim) quotes from the transcript,
attributed to a speaker. No hand-wavy feedback.

---

## How they relate

```
┌───────────────────────────────────────────────────────────────────┐
│                         PIPELINE                                   │
│                                                                   │
│  Transcript                                                       │
│      │                                                            │
│      ▼                                                            │
│  [1] CLASSIFY ──── call_types.yaml ──► call_type + phase          │
│      │                                                            │
│      ▼                                                            │
│  [2] INFER OUTCOMES ── outcomes.yaml ──► deal-specific outcomes   │
│      │                                                            │
│      ▼                                                            │
│  [3] SCORE ──── scorecard/*.yaml ──► per-criterion scores         │
│      │              │                                             │
│      │         frameworks/*.yaml (via framework_refs)             │
│      ▼                                                            │
│  [4] COACH ──────────────────────────► coaching report (JSON)     │
│                                          strengths                │
│                                          improvements + moves     │
│                                          next-call focus          │
└───────────────────────────────────────────────────────────────────┘
```

The transcript flows through four stages, each informed by YAML configuration
you can fork and tune. The coaching report is the final contract between the
pipeline and the consumer (UI, webhook, email, Slack message).

---

## Cross-references

- Pipeline stages in detail: [architecture.md](./architecture.md)
- Call type taxonomy: [call-types.md](./call-types.md)
- Framework reference: [frameworks.md](./frameworks.md)
- Scorecard anatomy: [scorecards.md](./scorecards.md)
- How to write a new scorecard: [writing-a-scorecard.md](./writing-a-scorecard.md)
- Transcript adapters: [adapters.md](./adapters.md)
- Three scoring layers (call / deal / account): [scoring-layers.md](./scoring-layers.md)
- The coaching inbox (rep / team / company): [inbox.md](./inbox.md)
- CRM auto-fill (any CRM): [crm.md](./crm.md)
- CRM stage discovery (resolve the org's real stages): [crm-stages.md](./crm-stages.md)
- Choosing a call recorder & the re-stitching tax: [call-recorders.md](./call-recorders.md)
- Using GTM Superintelligence inside Claude Code: [claude-native.md](./claude-native.md)
- How it spreads + how to support it: [distribution.md](./distribution.md)
- Telemetry & privacy (opt-in): [telemetry.md](./telemetry.md)
- Privacy and responsible use: [privacy-and-pii.md](./privacy-and-pii.md)
