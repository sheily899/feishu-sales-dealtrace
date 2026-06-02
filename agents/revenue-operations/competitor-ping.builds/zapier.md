# Competitor Ping — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../competitor-ping.md`](../competitor-ping.md)). This is a per-call Zap. Swap the example apps for
the ones you use.

## Steps

1. **Trigger — your call recorder ("conversation analyzed"), or Webhooks by Zapier → Catch Hook**
   - Fires once per analyzed call. Capture the call id and basic metadata (deal, rep).
2. **Action — fetch the call (your recorder app, or Webhooks by Zapier → GET)**
   - Pull the transcript + attendees for that call id. (If your recorder only exports transcripts,
     pull from where you store them.)
3. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Competitor Ping operating prompt** (see [`../competitor-ping.md`](../competitor-ping.md) → How it works / Output), with the call from step 2 mapped in.
4. **Action — Slack "Send Channel Message"**
   - Channel: your competitive-intel channel. Message text: the model output from step 3.

## Notes
- Add a **Filter by Zapier** step after the LLM so the Zap only posts when competitors are detected
  (the prompt outputs a "No competitor mentions detected" line you can filter on). Silence is the
  expected state for most calls.
- Keep the guardrails from the spec: read-only on the recorder, every strength/weakness/risk call
  ties to a transcript quote (no invented competitor claims), and the humanizer rules are part of the
  prompt (no em dashes, no throat-clearing, no hype, one clear ask).
