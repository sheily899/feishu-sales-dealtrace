# Churn Alert — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../churn-alert.md`](../churn-alert.md)). The CSM is the rep-equivalent; the customer is the account
on the other side. Swap the example apps for the ones you use.

## Steps

1. **Trigger — Schedule by Zapier** → *Every Day*, 7:00 AM (or *Every Week* for a weekly digest).
2. **Action — your CRM (e.g. Salesforce "Find Record(s)" / HubSpot "Find Companies")**
   - Find ACTIVE customer accounts (exclude open/live deals).
   - Return: account name, renewal date, health/success score, NPS, contract value, assigned CSM, open cases.
3. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch each active account's calls over roughly the last 90 days. If your recorder only exports
     transcripts, pull from where you store them. (No recorder app in Zapier? Use a Webhooks GET to its API.)
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Churn Alert operating prompt** (see [`../churn-alert.md`](../churn-alert.md) → How it works / Output), with the active accounts from step 2 and the calls from step 3 mapped in.
5. **Action — Slack "Send Channel Message"**
   - Channel: your CS / account-management channel. Message text: the model output from step 4.

## Notes
- For more than a handful of accounts, use a **Looping by Zapier** step between 2 and 3 so each
  account's calls are fetched and analyzed, then a final step to assemble the report.
- Active customers only, never live deals. Anonymize account names with a stable alias per account
  (the prompt handles this).
- Keep the guardrails from the spec: read-only on CRM/recorder, every rating tied to CRM health data
  or a call signal, and the humanizer rules are part of the prompt (no em dashes, no throat-clearing,
  no hype, one clear ask).
