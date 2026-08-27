# Cross Seller Radar — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../cross-seller-radar.md`](../cross-seller-radar.md)). This is a per-call scenario. A verified,
importable Make **blueprint JSON** will be added here once we validate it against a blueprint
exported from a real Make account (same way the Attention flow schema was confirmed from a real
export). Until then, assemble the scenario from these modules.

## Modules (in order)

1. **Webhook → Custom webhook** as the trigger. Point your recorder's "conversation analyzed"
   webhook here; the payload should carry the call id and the account.
2. **HTTP → Make a request** to your call recorder's API to fetch the analyzed call (transcript +
   attendees). (Recorder that only exports transcripts? Pull from where you store them, or
   pre-ingest via the dealtrace adapters.)
3. **Your CRM** (Salesforce "Search Records" / HubSpot "Search Companies", or **HTTP → Make a request**)
   - Read what the account already owns: current products, current ACV, and renewal date.
4. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 2000`, a single user message = the **Cross Seller Radar operating prompt**
     (see [`../cross-seller-radar.md`](../cross-seller-radar.md)) with the call + what the account owns mapped in.
5. **Router / Filter** so the scenario only posts for HIGH/MEDIUM opportunities (filter on the
   prompt's "No qualified cross-sell opportunity" line; skip prospect calls), then
6. **Slack → Create a Message** to your expansion/cross-sell channel; text = `{{4.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `4` above.
- Guardrails from the spec hold: read-only on CRM/recorder, every signal ties to something the
  customer said, every product match is one they do not own, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
