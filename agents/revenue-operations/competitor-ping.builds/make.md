# Competitor Ping — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../competitor-ping.md`](../competitor-ping.md)). This is a per-call scenario. A verified,
importable Make **blueprint JSON** will be added here once we validate it against a blueprint
exported from a real Make account (same way the Attention flow schema was confirmed from a real
export). Until then, assemble the scenario from these modules.

## Modules (in order)

1. **Webhook → Custom webhook** as the trigger. Point your recorder's "conversation analyzed"
   webhook here; the payload should carry the call id.
2. **HTTP → Make a request** to your call recorder's API to fetch the analyzed call (transcript +
   attendees). (Recorder that only exports transcripts? Pull from where you store them, or
   pre-ingest via the gtmsi adapters.)
3. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 2000`, a single user message = the **Competitor Ping operating prompt**
     (see [`../competitor-ping.md`](../competitor-ping.md)) with the call mapped in.
4. **Router / Filter** so the scenario only posts when competitors are detected (filter on the
   prompt's "No competitor mentions detected" line), then
5. **Slack → Create a Message** to your competitive-intel channel; text = `{{3.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `3` above.
- Guardrails from the spec hold: read-only on the recorder, every strength/weakness/risk call ties to
  a transcript quote (no invented competitor claims), humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
