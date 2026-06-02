# Deal Stage Clarity — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../deal-stage-clarity.md`](../deal-stage-clarity.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — Schedule by Zapier** → *Every Day*, weekdays, 7:00 AM.
2. **Action — your CRM (e.g. Salesforce "Find Record(s)" / HubSpot "Find Deals")**
   - Find open Opportunities where `IsClosed = false`.
   - Return: name, current stage, amount, expected close date, owner, last activity date. Resolve the
     org's real pipeline stages rather than assuming labels.
3. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch the calls tied to those deals/accounts from the last 7-14 days. (No recorder app in
     Zapier? Use a Webhooks GET to its API, or pull from where you store transcripts.)
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Deal Stage Clarity operating prompt** (see [`../deal-stage-clarity.md`](../deal-stage-clarity.md) → How it works / Output), with the deals from step 2 and the calls from step 3 mapped in.
5. **Action — Slack "Send Channel Message"**
   - Channel: your pipeline-hygiene channel. Message text: the model output from step 4.

## Notes
- For more than a handful of deals, use a **Looping by Zapier** step between 2 and 3 so each deal's
  calls are fetched and analyzed, then a final step to assemble the report.
- Keep the guardrails from the spec: read-only on CRM/recorder, every stage call ties to CRM data or
  a specific conversation moment, and the humanizer rules are part of the prompt (no em dashes, no
  throat-clearing, no hype, one clear ask).
