# Rubric scoring prompt (deals & accounts)

You score a **{{KIND}}** across MANY calls, not a single conversation. You are given:
- the **rubric** (dimensions, weights, signals, risk flags) as cached context,
- the **frameworks** it cites as cached context,
- a chronological set of **per-call coaching reports** for this {{SUBJECT_NOUN}}
  (each already classified and scored), plus any CRM/usage metadata.

## How to score

1. Read the call reports in time order. Build a picture of the whole
   {{SUBJECT_NOUN}}, not any single call. Later calls outweigh stale ones.
2. For **each rubric dimension**: weigh the `strong_signals` vs `weak_signals`
   across the history, assign a `score` 0–100, write a one–two sentence `rationale`,
   and attach 1–3 `evidence` items (each with the `call_id` it came from and a
   verbatim quote). If a dimension's `risk_flags` are present, you MUST surface them
   in `risks`.
3. Compute `overall_score` as the weighted average of dimension scores (weights
   normalized). Map it to `band` and `risk` using the rubric's `scoring.bands` and
   `risk_bands`.
4. **risks**: the prioritized red flags (single-threading, no economic buyer, no
   compelling event, ghosting, churn precursors, etc.), each with a `severity` and
   evidence.
5. **recommended_actions**: the concrete next moves that would most improve the score
   / reduce risk, prioritized, with an owner where obvious.
6. **summary**: 2–4 sentences a manager reads in 15 seconds — the state, the single
   biggest risk, and the next move.
7. **trend**: improving / flat / declining across the call history, if inferable.

## Rules
- Evidence-bound: cite real quotes with their `call_id`. Never fabricate.
- Calibrate honestly. A typical live {{SUBJECT_NOUN}} is mid-band, not "strong".
- Only use the rubric's dimensions.

## Output
Return ONLY a JSON object matching `schemas/rubric_report.schema.json` with
`kind: "{{KIND}}"` and the `subject` filled from the metadata provided.

---

## Subject
{{SUBJECT}}

## Rubric
{{RUBRIC_YAML}}

## Frameworks (referenced by the rubric)
{{FRAMEWORKS_YAML}}

## Call reports (chronological)
{{CALL_REPORTS}}
