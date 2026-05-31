---
description: Coach one sales call transcript — classify, score, and return evidence-bound coaching.
argument-hint: <transcript-path-or-paste>
---

Coach the following sales call using the **sales-coach** skill and the YAML knowledge
base in this repo (no API key required — read the rubrics directly).

Target: $ARGUMENTS

Steps:
1. Load the transcript (a path above, or text the user pasted). Normalize to
   speaker-labeled turns; identify the rep (the seller/CSM to coach).
2. Classify the call type + phase using `config/call_types.yaml`.
3. Infer the desired outcomes from `config/outcomes.yaml` and status each.
4. Score against `scorecards/<call_type>.yaml` (read the cited `frameworks/*.yaml`).
5. Produce a Markdown coaching report matching `examples/reports/discovery_acme.md`:
   header (call type · phase · confidence · overall), executive summary, desired
   outcomes, scorecard table, what worked, what to improve (prioritized, each with a
   concrete "Try instead:" better move), and a next-call focus checklist.

Rules: never invent quotes; coach the rep; only use the scorecard's criteria;
calibrate honestly (average call 50–65, 80+ is strong). Offer JSON output (per
`schemas/coaching_report.schema.json`) if asked.

If $ARGUMENTS is empty, ask the user for a transcript path or pasted transcript.
