# Case Study Generator — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../case-study-generator.md`](../case-study-generator.md)). A verified, importable Make **blueprint
JSON** will be added here once we validate it against a blueprint exported from a real Make account
(same way the Attention flow schema was confirmed from a real export). Until then, assemble the
scenario from these modules.

## Modules (in order)

1. **Webhooks → Custom webhook** → point your call recorder's "conversation analyzed" webhook here.
   The payload carries the call id.
2. **Your call recorder** (or **HTTP → Make a request**) → fetch the call's transcript and metadata
   by id, and confirm it reads as a success story. (Recorder that only exports transcripts? Pull from
   where you store them, or pre-ingest via the gtmsi adapters.)
3. **Your CRM** (Salesforce "Search Records" / HubSpot "Search Deals", or **HTTP → Make a request**)
   → pull the deal facts: account, industry, size, deal value, contacts, dates.
4. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 2000`, a single user message = the **Case Study operating prompt**
     (see [`../case-study-generator.md`](../case-study-generator.md)) with the call from module 2 and the CRM facts from module 3 mapped in.
5. **Slack → Send a Direct Message** to the marketing owner; text = `{{4.content[0].text}}`, labeled as a draft.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `4` above.
- Draft only. Never add a "publish" or "send to customer" module.
- Guardrails from the spec hold: read-only on CRM/recorder, evidence-bound, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
