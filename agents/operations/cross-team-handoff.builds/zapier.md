# Cross Team Handoff — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../cross-team-handoff.md`](../cross-team-handoff.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — your CRM (e.g. Salesforce "Updated Record" / HubSpot "Deal in Stage")**
   - Fire when an Opportunity's stage or owner changes. (No event trigger? Use **Schedule by Zapier**
     → *Every Hour* and find accounts that changed stage/owner in the last 2 hours.)
2. **Action — your CRM (e.g. Salesforce "Find Record(s)")**
   - Capture the transition: account, prev/new stage, prev/new owner, deal value.
3. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch the account's calls from the last 90 days. If your recorder only exports transcripts,
     pull them however you store them. (No recorder app in Zapier? Use a Webhooks GET to its API.)
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Cross-Team Handoff operating prompt** (see
     [`../cross-team-handoff.md`](../cross-team-handoff.md) → How it works / Output), with the account
     from step 2 and the calls from step 3 mapped in.
5. **Action — Slack "Send Channel Message"**
   - Channel: the receiving team's channel. Message text: the model output from step 4.

## Notes
- For more than a handful of accounts, use a **Looping by Zapier** step between 2 and 3 so each
  account's calls are fetched and analyzed, then a final step to post each handoff.
- Keep the guardrails from the spec: read-only on CRM/recorder, evidence-bound, and the humanizer
  rules are part of the prompt (no em dashes, no throat-clearing, no hype, one clear ask).
