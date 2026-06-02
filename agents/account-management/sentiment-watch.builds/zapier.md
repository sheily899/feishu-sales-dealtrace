# Sentiment Watch — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../sentiment-watch.md`](../sentiment-watch.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — Webhooks by Zapier (Catch Hook)** → point your call recorder's "conversation
   analyzed" webhook here. The payload carries the call id. (No webhook? Use a Schedule + a "find
   new analyzed calls" step instead.)
2. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch the call's transcript, sentiment, and metadata by id. If your recorder only exports
     transcripts, pull them however you store them.
3. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Sentiment Watch operating prompt** (see [`../sentiment-watch.md`](../sentiment-watch.md) → How it works), with the call from step 2 mapped in. It returns `NEUTRAL - no alert` or a formatted alert.
4. **Filter — Only continue if** the step-3 output does **not** contain `NEUTRAL`.
5. **Action — Slack "Send Direct Message"**
   - To: the account owner. Message text: the model output from step 3.

## Notes
- Never connect a "send to customer" action. This agent only DMs the owner, and only on an extreme.
- Keep the guardrails from the spec: read-only on the recorder, evidence-bound (every flag ties to a
  verbatim quote), and the humanizer rules are part of the prompt (no em dashes, no throat-clearing,
  no hype, one clear ask).
