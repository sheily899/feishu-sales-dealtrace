# Classifier prompt

Classify the call into exactly one **primary** call type from the taxonomy, plus
ranked alternatives. The taxonomy (ids, definitions, signals, and disambiguation
hints) is provided below as YAML.

## How to decide

1. Read the whole transcript first. Form a hypothesis from the dominant *purpose*
   of the call, not isolated moments (a single demo screen-share inside a discovery
   call does not make it a Demo).
2. Use `positive_signals` and `negative_signals` to confirm or rule out each
   candidate.
3. When two types are close, consult `often_confused_with` and apply the
   tie-breakers below.
4. Set `phase` from the chosen type (pre-sales / post-sales / neither).
5. Report `confidence` in [0,1] and a one-paragraph `rationale` citing concrete
   evidence (quote or paraphrase). List up to 3 `alternatives` with confidence.

## Tie-breakers (the common confusions)

- **Cold Call vs Discovery:** Cold Call = first touch, no prior relationship, the
  ask is *a meeting*. Discovery = scheduled, the ask is *information + a next step*.
- **Discovery vs Demo:** If the majority of the call is questioning and learning →
  Discovery. If the majority is showing the product mapped to needs → Demo.
- **Demo vs Technical Validation:** Demo = seller shows; the buyer reacts. Technical
  Validation/POV = buyer *tests* against explicit success criteria, often with
  technical stakeholders.
- **Negotiation vs Closing vs Go/No-Go:** Negotiation = price/terms in play.
  Closing = terms largely settled, navigating to signature. Go/No-Go = deciding
  *whether* to proceed at all.
- **Customer Check-in vs Renewal:** A contract event (renewal date/terms) in focus
  → Renewal. General adoption/value with no contract event → Check-in.
- **Anything vs Neither:** If all participants are internal → `internal`. If the
  counterparty is a partner discussing collaboration → `partner`. If *our* side is
  the buyer asking for pricing → `vendor`.

## Output
Return ONLY a JSON object matching the `classification` object of
`schemas/coaching_report.schema.json`:

```json
{
  "call_type": "discovery",
  "phase": "pre-sales",
  "confidence": 0.82,
  "rationale": "Scheduled first conversation; rep spends most of the call asking open questions about current state and priorities ('walk me through how you do this today'), minimal product shown, ends scoping a next step.",
  "alternatives": [{"call_type": "demo", "confidence": 0.12}]
}
```

---

## Taxonomy

{{CALL_TYPES_YAML}}

## Transcript

{{TRANSCRIPT}}
