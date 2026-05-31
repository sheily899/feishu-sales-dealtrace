# Outcome-inference prompt

Given the classified call type and the transcript, determine the **desired outcomes
for this specific call** and whether each was achieved.

## How to infer

1. Start from the `default_outcomes` for the call type (provided) and the outcome
   library (provided as YAML).
2. **Refine each generic outcome into a concrete, deal-specific statement** using
   the actual content. Example: `secure-next-step` →
   "Book a 30-minute technical deep-dive with Acme's Head of Data before month-end."
3. Add any *additional* outcome that the call clearly aimed at but isn't in the
   defaults (use the closest library `id`, or `id: "custom"` with a clear statement).
4. Drop defaults that plainly didn't apply to this call.
5. For each outcome, judge `status`:
   - `achieved` — clear evidence it happened.
   - `partial` — attempted/progressed but incomplete.
   - `missed` — needed and not achieved.
   - `unknown` — not enough evidence.
   Attach `evidence` quotes for `achieved`/`partial`/`missed`.

## Output
Return ONLY a JSON array matching the `outcomes` array of
`schemas/coaching_report.schema.json`:

```json
[
  {
    "id": "quantify-priority",
    "statement": "Quantify the cost of Acme's manual reporting (named ~10 hrs/week, not yet in dollars).",
    "status": "partial",
    "evidence": [{"speaker": "Sam", "text": "It's probably ten hours a week across the team."}]
  }
]
```

---

## Call type & default outcomes

Call type: {{CALL_TYPE}}
Default outcomes: {{DEFAULT_OUTCOMES}}

## Outcome library

{{OUTCOMES_YAML}}

## Transcript

{{TRANSCRIPT}}
