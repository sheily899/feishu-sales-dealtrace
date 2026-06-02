# Product Tracker — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../product-tracker.md`](../product-tracker.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — Schedule by Zapier** → *Every Week*, Monday, 8:00 AM.
2. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch the customer-facing calls from the last 7 days. If your recorder only exports transcripts,
     pull them however you store them. (No recorder app in Zapier? Use a Webhooks GET to its API.)
3. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Product Tracker operating prompt** (see [`../product-tracker.md`](../product-tracker.md) → How it works / Output), with the calls from step 2 mapped in.
4. **Action — Slack "Send Channel Message"**
   - Channel: your #product-feedback channel. Message text: the model output from step 3.

## Notes
- For many calls, use a **Looping by Zapier** step between 2 and 3 so each call is scanned, then a
  final step to assemble the digest (frequency and trends need the full set).
- Keep the guardrails from the spec: read-only on the recorder, every signal ties to a verbatim quote
  and a named account, and the humanizer rules are part of the prompt (no em dashes, no throat-clearing, no hype).
