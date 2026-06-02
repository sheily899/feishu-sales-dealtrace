# Risk Watch — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../risk-watch.md`](../risk-watch.md)). This is a per-call scenario. The CSM is the rep-equivalent;
the customer is the account on the other side. A verified, importable Make **blueprint JSON** will be
added here once we validate it against a blueprint exported from a real Make account (same way the
Attention flow schema was confirmed from a real export). Until then, assemble the scenario from these
modules.

## Modules (in order)

1. **Webhook → Custom webhook** as the trigger. Point your recorder's "conversation analyzed"
   webhook here; the payload should carry the call id and the account (and CSM/owner).
2. **HTTP → Make a request** to your call recorder's API to fetch the analyzed call (transcript +
   participants). (Recorder that only exports transcripts? Pull from where you store them, or
   pre-ingest via the gtmsi adapters.) If no transcript, stop.
3. **HTTP → Make a request** to your recorder for the same account's recent calls (last ~60 days), to
   build the last-30d vs prior-30d engagement baseline.
4. **Your CRM** (Salesforce "Search Records" / HubSpot "Search", or **HTTP → Make a request**) —
   read account metadata (owner/CSM, contract value, renewal date, open cases). Read-only.
5. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 2000`, a single user message = the **Risk Watch operating prompt**
     (see [`../risk-watch.md`](../risk-watch.md)) with the call (module 2), account history (module 3),
     and account metadata (module 4) mapped in. Instruct the prompt to reply with exactly `NO_RISK`
     when no indicators are present.
6. **Router / Filter** — continue to Slack only if the module 5 output does **not** contain `NO_RISK`.
7. **Slack → Create a Message** to the account-risk / CS-alerts channel; text = `{{5.content[0].text}}`.

## Notes
- **Alert only when a risk is present.** The filter in module 6 keeps the scenario silent on healthy accounts.
- Skip when the call has no transcript, and skip the engagement-drop check for an account's first-ever
  call (the prompt also handles these).
- To avoid duplicates, add a **Data store** check so the same account is not re-alerted within 24 hours
  for identical indicators.
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `5` above.
- Guardrails from the spec hold: read-only on CRM/recorder, every indicator tied to a transcript quote
  or a baseline metric, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
