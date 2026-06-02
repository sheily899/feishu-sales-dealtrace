# AE Handoff — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../ae-handoff.md`](../ae-handoff.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — your CRM (e.g. Salesforce "Updated Record" / HubSpot "Deal in Stage")**
   - Fire when an Opportunity enters a Closed-Won stage. (No event trigger? Use **Schedule by Zapier**
     → *Every Hour* and find Opportunities won in the last hour.)
2. **Action — your CRM (e.g. Salesforce "Find Record(s)")**
   - Pull the won opportunity's fields: name, account, amount, term, close date, AE owner, CSM owner,
     primary contact, opportunity team, products/line items, custom fields (tier, region, segment).
3. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch the calls tied to that deal's opportunity/account. If your recorder only exports
     transcripts, pull them however you store them. (No recorder app in Zapier? Use a Webhooks GET.)
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **AE Handoff operating prompt** (see [`../ae-handoff.md`](../ae-handoff.md) → How it
     works / Output), with the deal from step 2 and the calls from step 3 mapped in.
5. **Action — Slack "Send Channel Message"**
   - Channel: your delivery/CS handoff channel. Message text: the model output from step 4. Mention the AE and CSM.

## Notes
- Keep the guardrails from the spec: read-only on CRM/recorder, evidence-bound, and the humanizer
  rules are part of the prompt (no em dashes, no throat-clearing, no hype, one clear ask).
