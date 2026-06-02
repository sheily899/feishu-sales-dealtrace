# Skill Coach — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../skill-coach.md`](../skill-coach.md)). A verified, importable Make **blueprint JSON** will be
added here once we validate it against a blueprint exported from a real Make account (same way the
Attention flow schema was confirmed from a real export). Until then, assemble the scenario from
these modules.

## Modules (in order)

1. **Schedule** (scenario clock) → run *Every week*, Monday 08:00.
2. **Your call recorder** (**HTTP → Make a request**)
   - Fetch all team calls from the last 7 days. Output: call ids + metadata (rep, account).
   - (Recorder that only exports transcripts? Pull from where you store them, or pre-ingest via the gtmsi adapters.)
3. **Aggregator** to collect the calls into one bundle, grouped by rep.
4. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 3000`, a single user message = the **Skill Coach operating prompt**
     (see [`../skill-coach.md`](../skill-coach.md)) with the calls mapped in. Ask it to evaluate the five skills and write one alert per rep with a gap.
5. **Slack → Create a Message** to your team channel; text = `{{4.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `4` above.
- Guardrails from the spec hold: read-only on the recorder, evidence-bound, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
