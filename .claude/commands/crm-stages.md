---
description: Resolve the org's real CRM opportunity stages (won/lost/open) and where its pipeline sits.
argument-hint: [--crm salesforce|hubspot]
---

Resolve this org's **actual** CRM stages from its own data using the **crm-stage-mapper**
subagent — never assume labels like "Closed Won".

Target CRM: $ARGUMENTS

Steps:
1. Salesforce: query `OpportunityStage` (`MasterLabel, IsClosed, IsWon, IsActive, SortOrder`)
   for the real stage set; HubSpot: `GET /crm/v3/pipelines/deals` for `stages[]` with
   `metadata.isClosed`/`probability` (both are strings).
2. Classify won (`IsWon` / probability `1.0`), lost (`IsClosed & not IsWon` / `0.0`), open.
3. Find where opportunities sit: Salesforce `GROUP BY StageName` aggregate; HubSpot a
   per-stage `deals/search` count.
4. Report won / lost / open stage labels and the busiest open stages (count + amount).

You can run the implemented version directly: `gtmsi crm-stages --crm salesforce`
(dry-run prints the queries; add `--instance-url`/`--access-token` or env creds to run
live). Full reference: docs/crm-stages.md. Use the result to configure stage-triggered
agents (e.g. "AE Handoff fires when StageName enters {resolved won stages}").
