# Pre-Call Prep — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../pre-call-prep.md`](../pre-call-prep.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — Schedule by Zapier** → *Every Day*, 7:00 AM (gate to weekdays with a Filter step).
2. **Action — your calendar (Google Calendar "Find Events" / Microsoft Outlook, or Webhooks → GET)**
   - Find today's meetings between 7:00 AM and 7:00 PM. Return title, times, link/location, attendees.
3. **Action — your CRM (Salesforce "Find Record(s)" / HubSpot "Find Deals")**
   - Match attendee emails / company domains to an account and the most relevant opportunity
     (prefer open, else most recent closed). Return stage, amount, close date, forecast category.
4. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch prior conversations for those accounts/opportunities; take the most recent 3-5 summaries.
     (No recorder app in Zapier? Use a Webhooks GET to its API.)
5. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Pre-Call Prep operating prompt** (see [`../pre-call-prep.md`](../pre-call-prep.md) → How it works / Output), with the meetings, CRM matches, and prior calls mapped in. Tell it to use emojis and headings and NO markdown bold.
6. **Action — Slack "Send Direct Message"**
   - To the rep. Message text: the model output from step 5.

## Notes
- For days with several meetings, use a **Looping by Zapier** step between 2 and 4 so each meeting's
  account and calls are fetched, then a final step to assemble the full briefing.
- Keep the guardrails from the spec: read-only on calendar/CRM/recorder, evidence-bound, DM to the
  rep only, and the humanizer rules are part of the prompt (no em dashes, no throat-clearing, no
  hype, one clear ask).
