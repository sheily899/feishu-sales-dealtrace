# Multi Thread Detector — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../multi-thread-detector.md`](../multi-thread-detector.md)). A verified, importable Make
**blueprint JSON** will be added here once we validate it against a blueprint exported from a real
Make account (same way the Attention flow schema was confirmed from a real export). Until then,
assemble the scenario from these modules.

## Modules (in order)

1. **Webhooks → Custom webhook** — receives your call recorder's "conversation analyzed" event; the
   call id is in the payload.
2. **Your call recorder** (or **HTTP → Make a request**) — get the triggering call (account, deal,
   participants, rep) by id.
3. **HTTP → Make a request** to your recorder for every prior call on the same deal/account (to build
   the cumulative stakeholder map). Recorder that only exports transcripts? Pull from where you store
   them, or pre-ingest via the gtmsi adapters.
4. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 2000`, a single user message = the **Multi-Thread-Detector operating prompt**
     (see [`../multi-thread-detector.md`](../multi-thread-detector.md)) with the call + prior calls
     mapped in.
5. **Filter** — only continue if `{{4.content[0].text}}` does not contain "no alert needed".
6. **Slack → Create a Message** to your team channel; text = `{{4.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `4` above.
- The "only alert on Medium+ risk" gate lives in the prompt; the Filter enforces it.
- Guardrails from the spec hold: read-only on the recorder, never fabricate stakeholders, single
  stars not double, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
