---
description: Score a sales opportunity's health across all its calls (MEDDPICC/SPICED) and surface risks + next moves.
argument-hint: <folder-of-one-deal's-calls> [deal name]
---

Score the health of this opportunity using the **deal-scorer** subagent and
`rubrics/deal-health.yaml`.

Deal calls / name: $ARGUMENTS

Steps:
1. Gather the calls for this ONE opportunity (transcripts or existing coaching
   reports). Coach any raw transcripts first.
2. Score every deal-health dimension across the call history (recent calls weigh more),
   with evidence quotes tagged by call.
3. Output a Markdown deal-health report: overall score, band, churn/slip risk, a
   dimension table, prioritized risks, recommended next actions, and the trend.

Calibrate honestly (a typical live deal is mid-band). Never fabricate quotes. Offer
JSON (per `schemas/rubric_report.schema.json`) on request. If $ARGUMENTS is empty, ask
for the folder/calls and the deal name.
