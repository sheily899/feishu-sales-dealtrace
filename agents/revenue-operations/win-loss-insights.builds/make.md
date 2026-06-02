# Win Loss Insights — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../win-loss-insights.md`](../win-loss-insights.md)). A verified, importable Make **blueprint JSON**
will be added here once we validate it against a blueprint exported from a real Make account
(same way the Attention flow schema was confirmed from a real export). Until then, assemble the
scenario from these modules.

## Modules (in order)

1. **Schedule** (scenario clock) → run *Every week*, Monday 08:00.
2. **Your CRM** (Salesforce "Search Records" / HubSpot "Search Deals", or **HTTP → Make a request**)
   - Query Opportunities: `IsClosed = true AND CloseDate within last 30 days` (add a second query
     for days 31-60 for the trend comparison).
   - Output: name, account, owner, amount, stage, close date, won/lost, cycle length.
3. **Iterator** over the returned deals (so each deal's calls are fetched), then
   **HTTP → Make a request** to your call recorder's API for that deal's/account's calls. (Recorder
   that only exports transcripts? Pull from where you store them, or pre-ingest via the gtmsi adapters.)
4. **Aggregator** to collect the per-deal data back into one bundle.
5. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 3000`, a single user message = the **Win Loss Insights operating prompt**
     (see [`../win-loss-insights.md`](../win-loss-insights.md)) with the aggregated deals + calls mapped in.
6. **Slack → Create a Message** to your team channel; text = `{{5.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `5` above.
- Guardrails from the spec hold: read-only on CRM/recorder, evidence-bound, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
