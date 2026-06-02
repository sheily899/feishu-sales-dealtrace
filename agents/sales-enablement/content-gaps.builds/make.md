# Content Gaps — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../content-gaps.md`](../content-gaps.md)). A verified, importable Make **blueprint JSON** will be
added here once we validate it against a blueprint exported from a real Make account (same way the
Attention flow schema was confirmed from a real export). Until then, assemble the scenario from these
modules.

## Modules (in order)

1. **Schedule** (scenario clock) → run *Every week*, Monday 08:00.
2. **Your call recorder** (or **HTTP → Make a request**) — pull every analyzed call from the last 7
   days across all reps (with account, product line, rep, sentiment). Recorder that only exports
   transcripts? Pull from where you store them, or pre-ingest via the gtmsi adapters.
3. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 3000`, a single user message = the **Content Gaps operating prompt**
     (see [`../content-gaps.md`](../content-gaps.md)) with the week's calls mapped in.
4. **Slack → Create a Message** to your enablement channel; text = `{{3.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `3` above.
- For high call volume, add an **Iterator** + **Aggregator** around step 2 to chunk the transcripts.
- Guardrails from the spec hold: read-only on the recorder, constructive tone, evidence-bound, single
  stars not double, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
