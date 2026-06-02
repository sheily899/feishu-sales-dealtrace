# Product Tracker — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../product-tracker.md`](../product-tracker.md)). A verified, importable Make **blueprint JSON**
will be added here once we validate it against a blueprint exported from a real Make account (same way
the Attention flow schema was confirmed from a real export). Until then, assemble the scenario from
these modules.

## Modules (in order)

1. **Schedule** (scenario clock) → run *Every week*, Monday 08:00.
2. **Your call recorder** (or **HTTP → Make a request**) → fetch the customer-facing calls from the
   last 7 days. (Recorder that only exports transcripts? Pull from where you store them, or
   pre-ingest via the gtmsi adapters.)
3. **Iterator** over the returned calls (optional, for large volumes), then an **Aggregator** to
   collect them into one bundle (frequency and trends need the full set).
4. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 3000`, a single user message = the **Product Tracker operating prompt**
     (see [`../product-tracker.md`](../product-tracker.md)) with the aggregated calls mapped in.
5. **Slack → Create a Message** to your #product-feedback channel; text = `{{4.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `4` above.
- Guardrails from the spec hold: read-only on the recorder, every signal ties to a verbatim quote and
  a named account, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
