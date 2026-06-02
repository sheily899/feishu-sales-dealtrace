# Renewal Countdown — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../renewal-countdown.md`](../renewal-countdown.md)). The CSM is the rep-equivalent; the customer is
the account on the other side. Swap the example apps for the ones you use.

## Steps

1. **Trigger — Schedule by Zapier** → *Every Day*, 7:00 AM (or *Every Week* for a weekly digest).
2. **Action — your CRM (e.g. Salesforce "Find Record(s)" / HubSpot "Find Companies")**
   - Find accounts with renewal dates in the next 90 days (resolve the real renewal-date field, do
     not hardcode a label). Bucket into 30/60/90-day horizons downstream.
   - Return: account name, renewal date, contract value, assigned CSM/owner, last-call date.
3. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch each renewing account's calls over roughly the last 90 days. If your recorder only exports
     transcripts, pull from where you store them. (No recorder app in Zapier? Use a Webhooks GET to its API.)
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Renewal Countdown operating prompt** (see [`../renewal-countdown.md`](../renewal-countdown.md) → How it works / Output), with the renewals from step 2 and the calls from step 3 mapped in.
5. **Action — Slack "Send Channel Message"**
   - Channel: your renewals / account-management channel. Message text: the model output from step 4.

## Notes
- For more than a handful of accounts, use a **Looping by Zapier** step between 2 and 3 so each
  account's calls are fetched and graded, then a final step to assemble the digest.
- Resolve the real renewal-date field rather than hardcoding a label. Accounts with no call data are
  graded CRITICAL by the prompt; past-due, not-renewed accounts go under an "OVERDUE" section.
- Keep the guardrails from the spec: read-only on CRM/recorder, every health grade tied to a call
  count or a conversation signal, and the humanizer rules are part of the prompt (no em dashes, no
  throat-clearing, no hype, one clear ask).
