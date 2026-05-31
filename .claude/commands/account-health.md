---
description: Score a customer account's health (CSM) across its post-sales calls; surface churn risk + plays.
argument-hint: <folder-of-one-account's-calls> [account name]
---

Score this customer account's health using the **account-health-scorer** subagent and
`rubrics/account-health.yaml`.

Account calls / name: $ARGUMENTS

Steps:
1. Gather the post-sales calls for this ONE account (onboarding/check-in/renewal/QBR).
   Coach any raw transcripts first.
2. Score every account-health dimension across the history (recent signals weigh more),
   with evidence tagged by call. Watch leading churn indicators (usage decline,
   sentiment drop, single-threading, champion loss, renewal with no plan).
3. Output a Markdown account-health report: health score, band, churn-risk, dimension
   table, risks, recommended plays, trend.

Be explicit when an account looks fine but has a flashing leading indicator. Never
fabricate quotes. Offer JSON on request. If $ARGUMENTS is empty, ask for the calls and
account name.
