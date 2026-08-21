# Coaching prompt

You have a classified call. Now score it against the provided **scorecard** and
produce the full coaching report. The relevant **frameworks** are provided so you
can cite their vocabulary. You also infer the call's desired **outcomes** here (or
accept pre-computed ones if provided).

## Steps

1. **Outcomes.** If outcomes are not provided, infer them per the outcome rules:
   refine the call type's default outcomes into concrete, deal-specific statements
   and judge each `status` with evidence.
2. **Score each criterion** in the scorecard:
   - Read `what_great_looks_like`, `what_poor_looks_like`, and `evidence_cues`.
   - Assign a `score` 0–100. Map it to a `band` using the scorecard's `scoring.bands`.
   - Write a one–two sentence `rationale` and attach 1–3 `evidence` quotes.
   - Copy through the criterion's `weight`.
3. **Overall score** = weighted average of criterion scores (weights normalized to
   sum to 1). Round to an integer.
4. **Summary** — 2–4 sentences a manager reads in 15 seconds: call type, headline
   result, the single biggest lever.
5. **Coaching:**
   - `strengths`: 2–4 things done well, each with evidence. Reinforce them.
   - `improvements`: 2–5 prioritized items (high→low). Each has a `title`, `detail`
     (what happened + why it matters), the `criterion_id` it maps to, `evidence`,
     and a concrete **`better_move`** in quotes the rep can reuse.
   - `next_call_focus`: 1–3 things to do on the very next touch with this account.
6. Optionally add `manager_notes` (deal risk / cross-call patterns) — manager-only.

## Quality bar
- No quote fabrication. No criteria beyond the scorecard. Calibrate scores honestly.
- `better_move` must be specific and copy-pasteable, not generic.

## Output
Return ONLY a JSON object matching `schemas/coaching_report.schema.json` (the full
report: `classification` is already known and will be merged in; you must return
`outcomes`, `scores`, `overall_score`, `summary`, `coaching`, and optional
`manager_notes`).

All human-readable values, including every outcome `statement`, must follow the output
language requirement in the system prompt. Translate outcome-library templates rather
than copying their source language.

---

## Classification
{{CLASSIFICATION}}

## Scorecard
{{SCORECARD_YAML}}

## Frameworks (referenced by the scorecard)
{{FRAMEWORKS_YAML}}

## Outcome library
{{OUTCOMES_YAML}}

## Transcript
{{TRANSCRIPT}}
