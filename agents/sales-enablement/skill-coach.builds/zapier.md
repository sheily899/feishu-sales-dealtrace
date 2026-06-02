# Skill Coach — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../skill-coach.md`](../skill-coach.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — Schedule by Zapier** → *Every Week*, Monday, 8:00 AM.
2. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch all team calls from the last 7 days. Return call ids + metadata (rep, account).
   - (No recorder app in Zapier? Use a Webhooks GET to its API.)
3. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Skill Coach operating prompt** (see [`../skill-coach.md`](../skill-coach.md) → How it works / Output), with the calls from step 2 mapped in. Ask it to group by rep, evaluate the five skills, and write one alert per rep with a gap.
4. **Action — Slack "Send Channel Message"**
   - Channel: your team channel. Message text: the model output from step 3.

## Notes
- For a large team, use a **Looping by Zapier** step to evaluate each rep's calls (groups of ~25)
  separately, then a final step to assemble the alerts and the no-gap summary.
- Keep the guardrails from the spec: read-only on the recorder, evidence-bound, and the humanizer
  rules are part of the prompt (no em dashes, no throat-clearing, no hype, one clear ask).
