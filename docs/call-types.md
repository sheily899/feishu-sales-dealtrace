# Call Types

GTM Superintelligence classifies every call into exactly one **call type**. The classifier
picks the type whose definition and signals best match the dominant purpose of
the call — a single screen share inside a discovery call does not make it a Demo.

The full taxonomy is defined in `config/call_types.yaml` and conforms to
`schemas/call_type.schema.json`.

---

## The three phases

| Phase | What it covers | Example types |
|---|---|---|
| **pre-sales** | Winning the deal | Cold Call, Discovery, Demo, Technical Validation, Go/No-Go, Negotiation, Closing |
| **post-sales** | Keeping and growing the relationship | Onboarding, Customer Check-in, Renewal, QBR |
| **neither** | Calls where standard sales coaching does not apply | Internal, Partner, Vendor |

"Neither" calls receive a `generic-conversation` scorecard by default, or can
be excluded from coaching entirely depending on your configuration.

---

## Full taxonomy reference

### Pre-sales

| ID | Name | What it is | Scorecard | Often confused with |
|---|---|---|---|---|
| `cold-call` | Cold Call / Prospecting | First-touch outbound; no prior relationship; the ask is a meeting, not a sale | `cold-call` | `discovery` |
| `discovery` | Discovery | Scheduled first substantive conversation; questioning > pitching; uncovers priorities, pain, impact, decision process | `discovery` | `cold-call`, `demo`, `technical-validation` |
| `demo` | Demo / Solution Walkthrough | Product is shown (screen share); features mapped to the buyer's stated priorities; buyer reacts to what they see | `demo` | `discovery`, `technical-validation` |
| `technical-validation` | Technical Validation / POV / POC | Buyer tests the product against explicit success criteria; technical stakeholders present; integrations and environments discussed | `technical-validation` | `demo`, `go-no-go` |
| `go-no-go` | Go / No-Go / Mutual Decision | Checkpoint to decide whether to proceed; surfaces remaining risks, decision criteria, path to a decision | `go-no-go` | `technical-validation`, `negotiation`, `closing` |
| `negotiation` | Negotiation / Pricing | Price, terms, packaging, procurement; rep defends value and handles concessions deliberately | `negotiation` | `closing`, `go-no-go` |
| `closing` | Closing / Commit | Final steps to signature; confirms mutual plan, removes last blockers, secures commitment | `closing` | `negotiation`, `go-no-go` |

### Post-sales

| ID | Name | What it is | Scorecard | Often confused with |
|---|---|---|---|---|
| `onboarding-kickoff` | Onboarding / Kickoff | First post-sale working session; sets goals, success metrics, timeline, roles, path to first value | `onboarding-kickoff` | `customer-check-in`, `technical-validation` |
| `customer-check-in` | Customer Check-in / Success | Ongoing relationship call; drives adoption, surfaces value realized, catches risk, finds expansion | `customer-check-in` | `renewal`, `onboarding-kickoff` |
| `renewal` | Renewal / Expansion | Contract renewal or expansion; recaps value, addresses risk, frames the commercial conversation | `renewal` | `customer-check-in`, `negotiation` |
| `qbr` | Quarterly Business Review (QBR) | Structured strategic review: results, goal alignment, roadmap, joint plan for the next period; senior stakeholders | `qbr` | `customer-check-in`, `renewal` |

### Neither

| ID | Name | What it is | Scorecard |
|---|---|---|---|
| `internal` | Internal | All participants are from the same organization; not coached on a sales rubric | `generic-conversation` |
| `partner` | Partner / Channel | Collaboration, enablement, or co-selling with a partner (not an end buyer evaluating for themselves) | `generic-conversation` |
| `vendor` | Vendor (we are the buyer) | Our team member is the buyer evaluating someone else's product; sales coaching does not apply | `generic-conversation` |

---

## How disambiguation works

The classifier uses three mechanisms to avoid misclassification:

1. **`positive_signals`** — explicit cues that confirm a type (e.g., "rep asks
   for permission to continue" signals Cold Call; "screen share occurs" signals Demo).

2. **`negative_signals`** — cues that rule a type out (e.g., "a meeting was
   clearly pre-booked" rules out Cold Call; "no product is shown" rules out Demo).

3. **`often_confused_with`** — the classifier prompt has explicit tie-breakers
   for the most common confusions:

| Common confusion | How to decide |
|---|---|
| Cold Call vs. Discovery | Cold Call = first touch, no prior relationship, ask is a meeting. Discovery = scheduled, ask is information + a next step. |
| Discovery vs. Demo | Majority of call is questioning → Discovery. Majority is product walkthrough mapped to needs → Demo. |
| Demo vs. Technical Validation | Demo = seller shows, buyer reacts. Technical Validation = buyer tests against explicit success criteria, often with technical stakeholders. |
| Negotiation vs. Closing vs. Go/No-Go | Negotiation = price/terms in play. Closing = terms largely settled, navigating to signature. Go/No-Go = deciding whether to proceed at all. |
| Customer Check-in vs. Renewal | A contract event (renewal date/terms) in focus → Renewal. General adoption/value with no contract event → Check-in. |
| Anything vs. Neither | All participants internal → `internal`. Counterparty is a partner discussing collaboration → `partner`. Our team member is the buyer asking for pricing → `vendor`. |

---

## The `alternatives` field

The coaching report's `classification` block always includes an `alternatives`
array — up to three runner-up call types with their confidence scores. This
transparency lets a reviewer override the classification or understand why the
model hesitated.

Example:

```json
{
  "call_type": "discovery",
  "phase": "pre-sales",
  "confidence": 0.82,
  "rationale": "Scheduled first conversation; rep spends most of the call asking open questions …",
  "alternatives": [
    {"call_type": "demo", "confidence": 0.12},
    {"call_type": "cold-call", "confidence": 0.04}
  ]
}
```

---

## Wiring a scorecard to a call type

Each call type specifies one or more `scorecards` (the IDs from `scorecards/*.yaml`).
If a call type should use a different scorecard in your environment, edit the
`scorecards` list in `config/call_types.yaml`. Today only the **first** scorecard
listed for a call type is used: `registry.scorecard_for()` resolves `scorecards[0]`
and the pipeline scores against that single scorecard. Additional entries act as
documented alternates and are reserved for future multi-scorecard support.

---

## Adding or modifying call types

The taxonomy is plain YAML. To add a call type:

1. Add an entry to `config/call_types.yaml` following the schema.
2. Create (or reuse) a scorecard in `scorecards/`.
3. Add outcomes to `config/outcomes.yaml` if needed.
4. Run `dealtrace validate` to check the YAML is valid.

---

## Cross-references

- Core concepts: [concepts.md](./concepts.md)
- Pipeline architecture: [architecture.md](./architecture.md)
- Framework reference: [frameworks.md](./frameworks.md)
- Scorecard anatomy: [scorecards.md](./scorecards.md)
- Writing a scorecard: [writing-a-scorecard.md](./writing-a-scorecard.md)
