# Frameworks

A **framework** is a named sales methodology expressed as structured YAML. Each
framework gives the coaching engine a shared, citable vocabulary — so instead
of vague feedback like "ask better questions," the coach can say "no Critical
Event surfaced (SPICED)" or "single-threaded — no Economic Buyer engaged
(MEDDPICC)."

Frameworks live in `frameworks/*.yaml` and conform to
`schemas/framework.schema.json`.

---

## What a framework contains

Every framework file has:

| Field | Purpose |
|---|---|
| `id` | Stable slug (e.g., `spiced`, `meddpicc`). Referenced in scorecard `framework_refs`. |
| `name` / `acronym` | Human-readable labels. |
| `origin` | Attribution to the methodology's creators, for credit and further reading. |
| `summary` | A concise description of the framework's core idea. |
| `best_for` | Call-type IDs where the framework is most applicable. |
| `elements` | The building blocks (e.g., the letters of the acronym). |
| `further_reading` | Links to the source material. |

Each **element** contains:

| Field | Purpose |
|---|---|
| `id` | Stable slug (e.g., `pain`, `critical_event`). Used in `framework_refs`. |
| `name` | The element's name (e.g., "Pain", "Critical Event"). |
| `question` | The core question this element answers about the deal. |
| `why_it_matters` | One paragraph on why this element drives deal outcomes. |
| `good_signals` | Observable behaviors that indicate the element was covered well. |
| `missing_signals` | Anti-patterns that indicate the element was missed or weak. |
| `example_questions` | Discovery questions a rep can ask to satisfy this element. |

---

## Frameworks shipped with GTM Superintelligence

### SPICED

**File:** `frameworks/spiced.yaml` | **Origin:** Winning by Design

A discovery framework organized around five elements: **S**ituation, **P**ain,
**I**mpact, **C**ritical Event, **D**ecision. It pushes past surface problems to
quantified impact and a compelling event — the two things that actually move
deals. SPICED is the default framework referenced by the discovery scorecard.

| Element | Core question |
|---|---|
| Situation | What is the buyer's current state — context, tools, team, scale? |
| Pain | What problem is the buyer trying to solve, and is it a top priority? |
| Impact | What is the quantified business impact of the pain (and of solving it)? |
| Critical Event | Is there a deadline or event that forces a decision by a date? |
| Decision | How will the buyer decide — who, what criteria, and what process? |

**Best for:** discovery, demo, technical validation, renewal, QBR

---

### MEDDPICC

**File:** `frameworks/meddpicc.yaml` | **Origin:** Jack Napoli & Dick Dunkel (PTC, 1990s)

A rigorous enterprise qualification framework across eight dimensions:
**M**etrics, **E**conomic Buyer, **D**ecision Criteria, **D**ecision Process,
**P**aper Process, **I**dentify Pain, **C**hampion, **C**ompetition. Built for
complex, multi-stakeholder deals where incomplete qualification is the leading
cause of forecast misses. The most comprehensive framework in the set.

| Element | Core question |
|---|---|
| Metrics | What quantified outcomes will the economic buyer use to justify and measure success? |
| Economic Buyer | Who has budget authority to say yes — and have we spoken to them? |
| Decision Criteria | What criteria will the buyer use to evaluate and select a solution? |
| Decision Process | What are the specific steps, owners, and sequence needed to reach a signed agreement? |
| Paper Process | What legal, procurement, and security reviews must run before a contract is executed? |
| Identify Pain | What is the specific, quantified pain that is forcing a change now? |
| Champion | Is there an internal advocate with influence and personal motivation actively selling for us? |
| Competition | Who else is being evaluated, and how does the buyer compare us? |

**Best for:** discovery, technical validation, go/no-go, negotiation, closing

---

### BANT

**File:** `frameworks/bant.yaml` | **Origin:** IBM (1950s–60s)

A four-element rapid qualification filter: **B**udget, **A**uthority, **N**eed,
**T**imeline. BANT is deliberately lightweight — fast to apply at the top of the
funnel, but insufficient for complex enterprise deals. Use it to decide whether a
conversation is worth pursuing, not to deeply understand a deal.

| Element | Core question |
|---|---|
| Budget | Does the buyer have allocated or available budget? |
| Authority | Is the person we're speaking with the decision-maker? |
| Need | Does the buyer have a genuine, specific problem this solution addresses? |
| Timeline | Is there a realistic timeframe for a decision, and what is driving it? |

**Best for:** cold call, early discovery

---

### Next Steps / Mutual Action Plan (MAP)

**File:** `frameworks/next-steps.yaml` | **Origin:** Winning by Design, Force Management et al.

A discipline framework that evaluates whether every agreed next step is
concrete, owned, dated, and brings the right people to the table. Weak next
steps are the single most common cause of pipeline stall. Elements: **Clear
Owner**, **Specific Action**, **Committed Date**, **Right People**, **Mutual
Value**, **Written Confirmation**.

**Best for:** discovery, demo, technical validation, go/no-go, negotiation, closing

---

### Command of the Message

**File:** `frameworks/command-of-the-message.yaml` | **Origin:** Force Management

A value-based selling framework that trains reps to lead buyer conversations
with quantified business outcomes rather than product features. Elements:
**Before Scenario**, **Required Capabilities**, **Metrics**, **Differentiated
Value**, **Proof Points**, **Positive Business Outcomes**.

**Best for:** demo, discovery, negotiation, QBR

---

### Gap Selling

**File:** `frameworks/gap-selling.yaml` | **Origin:** Keenan (A Sales Growth Company, 2018)

A problem-centric methodology built on a core principle: buyers buy the distance
between where they are and where they want to be. The rep's job is to define,
quantify, and make that gap felt. Elements: **Current State**, **Future State**,
**The Gap**, **Impact**, **Root Cause**, **Intangibles**.

**Best for:** discovery, demo

---

### Sandler Pain Funnel

**File:** `frameworks/sandler-pain.yaml` | **Origin:** David Sandler / Sandler Training (1960s)

A structured eight-step sequence that takes a buyer from a vague surface
complaint to deeply felt, personally owned, quantified pain. Read top-to-bottom:
**Surface Problem**, **Tell Me More**, **Specific Example**, **Tried to Fix**,
**How Long**, **Quantified Cost**, **Personal Impact**, **Give Up**.

**Best for:** discovery, demo

---

## Selecting a framework by motion

| If you are running… | Reach for… |
|---|---|
| High-volume SMB, fast cycles | BANT (filter) + Next Steps (discipline) |
| Mid-market discovery | SPICED |
| Enterprise / complex multi-stakeholder | MEDDPICC |
| Value-led demos and messaging | Command of the Message |
| Problem-centric consultative selling | Gap Selling |
| Pain-deepening in early conversations | Sandler Pain Funnel |
| Post-sales QBR and renewals | SPICED (Impact + Decision) + Command of the Message (Metrics + PBOs) |

You can combine frameworks in a single scorecard. The discovery scorecard
shipped with GTM Superintelligence references both `spiced` and `meddpicc` — SPICED for the
discovery flow and MEDDPICC for qualification rigor.

---

## How scorecards cite framework elements

In a scorecard YAML, each criterion can list `framework_refs`:

```yaml
criteria:
  - id: priority_quantified
    name: Top Priority Identified & Quantified
    weight: 2
    framework_refs: [spiced.pain, spiced.impact, meddpicc.metrics]
    what_great_looks_like:
      - "The #1 priority is named in the buyer's words."
      - "Impact is quantified (time, money, or risk)."
```

The format is `<framework_id>.<element_id>` (e.g., `spiced.critical_event`,
`meddpicc.economic_buyer`). The coaching engine uses these references to:

1. Pull `example_questions` it can include in improvement feedback.
2. Use the element's `why_it_matters` to explain why the criterion matters to
   deal outcomes.
3. Name the framework in the coaching report for clarity (e.g.,
   "No Critical Event surfaced (SPICED)").

---

## Adding a framework

Frameworks are plain YAML. To add one:

1. Create `frameworks/<id>.yaml` conforming to `schemas/framework.schema.json`.
2. Reference it from scorecard criteria via `framework_refs: [<id>.<element_id>]`.
3. Run `dealtrace validate` to check the YAML.

Frameworks are purely additive — you can add them without changing the pipeline.

---

## Cross-references

- Core concepts: [concepts.md](./concepts.md)
- Scorecard anatomy: [scorecards.md](./scorecards.md)
- Writing a scorecard: [writing-a-scorecard.md](./writing-a-scorecard.md)
- Call types: [call-types.md](./call-types.md)
