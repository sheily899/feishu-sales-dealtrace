# Persona Mapper — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../persona-mapper.md`](../persona-mapper.md)). A verified, importable Make **blueprint JSON** will
be added here once we validate it against a blueprint exported from a real Make account (same way the
Attention flow schema was confirmed from a real export). Until then, assemble the scenario from these
modules.

## Modules (in order)

1. **Webhooks → Custom webhook** → point your call recorder's "conversation analyzed" webhook here.
   The payload carries the call id.
2. **Your call recorder** (or **HTTP → Make a request**) → fetch the call's transcript, speakers, and
   metadata by id. (Recorder that only exports transcripts? Pull from where you store them, or
   pre-ingest via the dealtrace adapters.)
3. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 1500`, a single user message = the **Persona Mapper operating prompt**
     (see [`../persona-mapper.md`](../persona-mapper.md)) with the call from module 2 mapped in.
4. **Slack → Create a Message** to your marketing channel; text = `{{3.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `3` above.
- This is a working draft for the marketing team to refine, not a finished asset.
- Guardrails from the spec hold: read-only on the recorder, evidence-bound (inferences labeled as
  inferred), humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
