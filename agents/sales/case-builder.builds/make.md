# Case Builder — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../case-builder.md`](../case-builder.md)). A verified, importable Make **blueprint JSON** will be
added here once we validate it against a blueprint exported from a real Make account (same way the
Attention flow schema was confirmed from a real export). Until then, assemble the scenario from
these modules.

## Modules (in order)

1. **Webhooks → Custom webhook** — receives your call recorder's "conversation analyzed" event; the
   call id is in the payload.
2. **Your call recorder** (or **HTTP → Make a request**) — get the triggering call's transcript +
   metadata by id.
3. **HTTP → Make a request** to your recorder for the deal's/account's prior calls (cumulative
   context). Recorder that only exports transcripts? Pull from where you store them, or pre-ingest
   via the gtmsi adapters.
4. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 3000`, a single user message = the **Case Builder operating prompt**
     (see [`../case-builder.md`](../case-builder.md)) with the call + prior calls mapped in.
5. **Slack → Create a Message** to your team channel; text = `{{4.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `4` above.
- Guardrails from the spec hold: read-only on the recorder, evidence-bound (no invented numbers),
  single stars not double, humanizer rules in the prompt, never send to the customer.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
