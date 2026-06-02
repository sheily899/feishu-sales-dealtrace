# Compliance Checker — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../compliance-checker.md`](../compliance-checker.md)). A verified, importable Make **blueprint
JSON** will be added here once we validate it against a blueprint exported from a real Make account.
Until then, assemble the scenario from these modules.

## Modules (in order)

1. **Webhooks → Custom webhook** — point your call recorder's "conversation analyzed" webhook here.
   The payload should carry the call id.
2. **HTTP → Make a request** to your call recorder's API — fetch the transcript + metadata for that
   call. (Recorder that only exports transcripts? Pull from where you store them, or pre-ingest via
   the gtmsi adapters.)
3. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 2000`, a single user message = the **Compliance Checker operating prompt**
     (see [`../compliance-checker.md`](../compliance-checker.md)) with the call mapped in. Tell it to
     output `NO_VIOLATIONS` on a clean call.
4. **Router / Filter** — only continue if `{{3.content[0].text}}` does not contain `NO_VIOLATIONS`.
5. **Slack → Create a Message** to your compliance / sales-ops channel; text = `{{3.content[0].text}}`.

## Notes
- The filter at step 4 is what keeps clean calls silent.
- Guardrails from the spec hold: alert-only to an internal channel, evidence-bound, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
