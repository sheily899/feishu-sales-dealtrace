# Objection Drilldown — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../objection-drilldown.md`](../objection-drilldown.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — Schedule by Zapier** → *Every Week*, Monday, 8:00 AM.
2. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch all team calls from the last 7 days. Return call ids + metadata (rep, account).
   - (No recorder app in Zapier? Use a Webhooks GET to its API.)
3. **Action — your call recorder (or Webhooks → GET)**
   - Fetch the prior 7-day window's calls too, so the model can compute trends.
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Objection Drilldown operating prompt** (see [`../objection-drilldown.md`](../objection-drilldown.md) → How it works / Output), with this week's calls from step 2 and last week's from step 3 mapped in.
5. **Action — Slack "Send Channel Message"**
   - Channel: your team channel. Message text: the model output from step 4.

## Notes
- For a large team, use a **Looping by Zapier** step to batch calls into groups of ~25 for analysis,
  then a final step to assemble the report.
- Keep the guardrails from the spec: read-only on the recorder, evidence-bound, and the humanizer
  rules are part of the prompt (no em dashes, no throat-clearing, no hype, one clear ask).
