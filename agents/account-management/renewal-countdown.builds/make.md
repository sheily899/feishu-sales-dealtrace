# Renewal Countdown — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../renewal-countdown.md`](../renewal-countdown.md)). The CSM is the rep-equivalent; the customer is
the account on the other side. A verified, importable Make **blueprint JSON** will be added here once
we validate it against a blueprint exported from a real Make account (same way the Attention flow
schema was confirmed from a real export). Until then, assemble the scenario from these modules.

## Modules (in order)

1. **Schedule** (scenario clock) → run *Every day* at 07:00 (or *Every week* for a weekly digest).
2. **Your CRM** (Salesforce "Search Records" / HubSpot "Search", or **HTTP → Make a request**)
   - Find accounts with renewal dates in the next 90 days (resolve the real renewal-date field, do
     not hardcode a label). Bucket into 30/60/90-day horizons downstream.
   - Output: account name, renewal date, contract value, assigned CSM/owner, last-call date.
3. **Iterator** over the returned accounts (so each account's calls are fetched), then
   **HTTP → Make a request** to your call recorder's API for that account's calls over the last ~90
   days. (Recorder that only exports transcripts? Pull from where you store them, or pre-ingest via
   the dealtrace adapters.)
4. **Aggregator** to collect the per-account data back into one bundle.
5. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 3000`, a single user message = the **Renewal Countdown operating prompt**
     (see [`../renewal-countdown.md`](../renewal-countdown.md)) with the aggregated renewals + calls mapped in.
6. **Slack → Create a Message** to your renewals / account-management channel; text = `{{5.content[0].text}}`.

## Notes
- Resolve the real renewal-date field rather than hardcoding a label. Accounts with no call data are
  graded CRITICAL by the prompt; past-due, not-renewed accounts go under an "OVERDUE" section.
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `5` above.
- Guardrails from the spec hold: read-only on CRM/recorder, every health grade tied to a call count or
  a conversation signal, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
