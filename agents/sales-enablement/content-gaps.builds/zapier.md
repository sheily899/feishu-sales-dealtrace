# Content Gaps — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../content-gaps.md`](../content-gaps.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — Schedule by Zapier** → *Every Week*, Monday, 8:00 AM.
2. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Pull every analyzed call from the last 7 days across all reps (with account, product line, rep,
     sentiment). (No recorder app in Zapier? Use a Webhooks GET to its API.)
3. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Content Gaps operating prompt** (see [`../content-gaps.md`](../content-gaps.md) →
     How it works / Output), with the week's calls from step 2 mapped in.
4. **Action — Slack "Send Channel Message"**
   - Channel: your enablement channel. Message text: the model output from step 3.

## Notes
- For a high call volume, use a **Looping by Zapier** step to chunk the calls, then a final step to
  assemble the report.
- Keep the guardrails from the spec: read-only on the recorder, constructive tone, every gap tied to a
  real question or uncertainty signal, single stars not double, and the humanizer rules are part of
  the prompt (no em dashes, no throat-clearing, no hype, one clear ask).
