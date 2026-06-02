# Email Generator — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../email-generator.md`](../email-generator.md)). This is a per-call scenario. A verified,
importable Make **blueprint JSON** will be added here once we validate it against a blueprint
exported from a real Make account (same way the Attention flow schema was confirmed from a real
export). Until then, assemble the scenario from these modules.

## Modules (in order)

1. **Webhook → Custom webhook** as the trigger. Point your recorder's "conversation analyzed"
   webhook here; the payload should carry the call id and the deal owner (rep).
2. **HTTP → Make a request** to your call recorder's API to fetch the analyzed call (transcript +
   attendees). (Recorder that only exports transcripts? Pull from where you store them, or
   pre-ingest via the gtmsi adapters.)
3. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 1500`, a single user message = the **Email Generator operating prompt**
     (see [`../email-generator.md`](../email-generator.md)) with the call mapped in. The prompt drafts
     in the rep's voice and applies the humanizer rules.
4. **Slack → Create a Message** as a **direct message** to the rep (deal owner); text =
   `{{3.content[0].text}}`.

## Notes
- **Draft only, to the rep.** Do not add a "send to customer" module. The rep reviews and sends.
- Add a **Filter** after module 2 to skip internal/non-customer calls (the prompt also returns a
  one-line skip note for those).
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `3` above.
- Guardrails from the spec hold: every specific comes from the call (no invented commitments,
  numbers, or names), humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
