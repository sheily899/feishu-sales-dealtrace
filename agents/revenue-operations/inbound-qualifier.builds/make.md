# Inbound Qualifier — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../inbound-qualifier.md`](../inbound-qualifier.md)). This is a per-call scenario. A verified,
importable Make **blueprint JSON** will be added here once we validate it against a blueprint
exported from a real Make account (same way the Attention flow schema was confirmed from a real
export). Until then, assemble the scenario from these modules.

## Modules (in order)

1. **Webhook → Custom webhook** as the trigger. Point your recorder's "conversation analyzed"
   webhook here; the payload should carry the call id and the company.
2. **HTTP → Make a request** to your call recorder's API to fetch the analyzed call (transcript +
   attendees). (Recorder that only exports transcripts? Pull from where you store them, or
   pre-ingest via the gtmsi adapters.)
3. **Your CRM** (Salesforce "Search Records" / HubSpot "Search Companies", or **HTTP → Make a request**)
   - Read firmographics for ICP fit: company size, industry, and the existing-customer flag. If
     unmatched, the prompt infers fit from the conversation and notes the assumption.
4. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 2000`, a single user message = the **Inbound Qualifier operating prompt**
     (see [`../inbound-qualifier.md`](../inbound-qualifier.md)) with the call + firmographics mapped in.
5. **Slack → Create a Message** to your inbound/SDR channel; text = `{{4.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `4` above.
- Add a **Filter** after module 2 to skip internal/non-customer calls if your recorder does not
  pre-tag inbound calls.
- Guardrails from the spec hold: read-only on CRM/recorder, every BANT score and the disposition ties
  to a transcript quote or CRM firmographic, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
