# Sentiment Watch — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../sentiment-watch.md`](../sentiment-watch.md)). A verified, importable Make **blueprint JSON**
will be added here once we validate it against a blueprint exported from a real Make account
(same way the Attention flow schema was confirmed from a real export). Until then, assemble the
scenario from these modules.

## Modules (in order)

1. **Webhooks → Custom webhook** → point your call recorder's "conversation analyzed" webhook here.
   The payload carries the call id.
2. **Your call recorder** (or **HTTP → Make a request**) → fetch the call's transcript, sentiment,
   and metadata by id. (Recorder that only exports transcripts? Pull from where you store them, or
   pre-ingest via the gtmsi adapters.)
3. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 1000`, a single user message = the **Sentiment Watch operating prompt**
     (see [`../sentiment-watch.md`](../sentiment-watch.md)) with the call from module 2 mapped in.
4. **Filter** between module 3 and 4: only continue if the model output does **not** contain `NEUTRAL`.
5. **Slack → Send a Direct Message** to the account owner; text = `{{3.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `3` above.
- Never add a "send to customer" module. This agent only DMs the owner, and only on an extreme.
- Guardrails from the spec hold: read-only on the recorder, evidence-bound, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
