# Churn Alert — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../churn-alert.md`](../churn-alert.md)). The CSM is the rep-equivalent; the customer is the account
on the other side. A verified, importable Make **blueprint JSON** will be added here once we validate
it against a blueprint exported from a real Make account (same way the Attention flow schema was
confirmed from a real export). Until then, assemble the scenario from these modules.

## Modules (in order)

1. **Schedule** (scenario clock) → run *Every day* at 07:00 (or *Every week* for a weekly digest).
2. **Your CRM** (Salesforce "Search Records" / HubSpot "Search", or **HTTP → Make a request**)
   - Find ACTIVE customer accounts (exclude open/live deals).
   - Output: account name, renewal date, health/success score, NPS, contract value, assigned CSM, open cases.
3. **Iterator** over the returned accounts (so each account's calls are fetched), then
   **HTTP → Make a request** to your call recorder's API for that account's calls over the last ~90
   days. (Recorder that only exports transcripts? Pull from where you store them, or pre-ingest via
   the dealtrace adapters.)
4. **Aggregator** to collect the per-account data back into one bundle.
5. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 3000`, a single user message = the **Churn Alert operating prompt**
     (see [`../churn-alert.md`](../churn-alert.md)) with the aggregated accounts + calls mapped in.
6. **Slack → Create a Message** to your CS / account-management channel; text = `{{5.content[0].text}}`.

## Notes
- Active customers only, never live deals. Anonymize account names with a stable alias per account
  (the prompt handles this).
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `5` above.
- Guardrails from the spec hold: read-only on CRM/recorder, every rating tied to CRM health data or a
  call signal, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
