---
description: Map a GTM Superintelligence report to CRM fields (any CRM) and show the auto-fill patch (dry-run by default).
argument-hint: <report.json> [--crm salesforce|hubspot|generic]
---

Auto-fill the CRM from a GTM Superintelligence report using the **crm-sync** subagent.

Report / CRM: $ARGUMENTS

Steps:
1. Detect the report type (coaching / deal / account) and the target CRM (default
   `generic`).
2. Load `config/crm/<crm>.yaml`, resolve each mapped field from the report, apply
   transforms, and find the record id.
3. Show the resulting patch as JSON: `[{crm, object, record_id, fields}]` (dry-run).

Do NOT write to a live CRM unless the user explicitly asks AND provides credentials —
treat live writes as confirmation-required. Never invent CRM field names; if theirs
isn't mapped, help them copy `generic.yaml`. You may also run
`gtmsi crm <report.json> --crm <crm>` for the dry-run patch.
