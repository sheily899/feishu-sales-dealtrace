# Cross Team Handoff — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../cross-team-handoff.md`](../cross-team-handoff.md)). A verified, importable Make **blueprint
JSON** will be added here once we validate it against a blueprint exported from a real Make account
(same way the Attention flow schema was confirmed from a real export). Until then, assemble the
scenario from these modules.

## Modules (in order)

1. **Schedule** (scenario clock) → run *Every hour*. (Better: trigger from your CRM's stage/owner-change
   webhook so it fires per account rather than polling.)
2. **Your CRM** (Salesforce "Search Records" / HubSpot "Search Deals", or **HTTP → Make a request**)
   - Query accounts whose opportunity stage or owner changed in the last 2 hours.
   - Output: account, prev/new stage, prev/new owner, deal value.
3. **Iterator** over the returned accounts, then **HTTP → Make a request** to your call recorder's API
   for each account's calls in the last 90 days. (Recorder that only exports transcripts? Pull from
   where you store them, or pre-ingest via the dealtrace adapters.)
4. **Aggregator** to collect the per-account data back into one bundle.
5. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 3000`, a single user message = the **Cross-Team Handoff operating prompt**
     (see [`../cross-team-handoff.md`](../cross-team-handoff.md)) with the aggregated accounts + calls mapped in.
6. **Slack → Create a Message** to the receiving team's channel; text = `{{5.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `5` above.
- Guardrails from the spec hold: read-only on CRM/recorder, evidence-bound, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
