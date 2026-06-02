# Team Collab Agent — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../team-collab-agent.md`](../team-collab-agent.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — your call recorder (or Webhooks by Zapier → Catch Hook)**
   - Fire once when a conversation finishes analyzing. The payload carries the call id.
2. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch the transcript + metadata for that call. If your recorder only exports transcripts, pull
     them however you store them. (No recorder app in Zapier? Use a Webhooks GET to its API.)
3. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Team Collab operating prompt** (see
     [`../team-collab-agent.md`](../team-collab-agent.md) → How it works / Output), with the call from
     step 2 mapped in. Tell it to output `NO_SIGNALS` when no team is needed, otherwise one block per team.
4. **Filter by Zapier**
   - Only continue if the step 3 output does **not** contain `NO_SIGNALS`. This keeps quiet calls silent.
5. **Action — Slack "Send Channel Message"**
   - Post the model output. To send each team's block to its own channel, use **Paths by Zapier**
     (one path per team) and route the matching block + channel; otherwise post the combined output
     to a general collaboration channel.

## Notes
- Keep the guardrails from the spec: alerts-only to internal channels (never the customer),
  evidence-bound, and the humanizer rules are part of the prompt (no em dashes, no throat-clearing,
  no hype, one clear ask).
