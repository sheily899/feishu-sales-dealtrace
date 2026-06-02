# Persona Mapper — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../persona-mapper.md`](../persona-mapper.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — Webhooks by Zapier (Catch Hook)** → point your call recorder's "conversation
   analyzed" webhook here. The payload carries the call id.
2. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch the call's transcript, speakers, and metadata by id.
3. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Persona Mapper operating prompt** (see [`../persona-mapper.md`](../persona-mapper.md) → How it works / Output), with the call from step 2 mapped in.
4. **Action — Slack "Send Channel Message"**
   - Channel: your marketing channel. Message text: the model output from step 3.

## Notes
- This is a working draft for the marketing team to refine, not a finished asset.
- Keep the guardrails from the spec: read-only on the recorder, every persona and priority ties to
  evidence from the call (inferences labeled as inferred), and the humanizer rules are part of the
  prompt (no em dashes, no throat-clearing, no hype, one clear ask).
