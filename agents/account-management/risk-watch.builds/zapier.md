# Risk Watch — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../risk-watch.md`](../risk-watch.md)). This is a per-call Zap. The CSM is the rep-equivalent; the
customer is the account on the other side. Swap the example apps for the ones you use.

## Steps

1. **Trigger — your call recorder ("conversation analyzed"), or Webhooks by Zapier → Catch Hook**
   - Fires once per analyzed customer call. Capture the call id and the account (and CSM/owner).
2. **Action — fetch the call (your recorder app, or Webhooks by Zapier → GET)**
   - Pull the transcript + participants for that call id. (If your recorder only exports transcripts,
     pull from where you store them.)
3. **Action — your call recorder (or Webhooks → GET) — account history**
   - Fetch the same account's recent calls (last ~60 days) to build the last-30d vs prior-30d
     engagement baseline.
4. **Action — your CRM (e.g. Salesforce "Find Record" / HubSpot "Find") — account metadata**
   - Read account metadata to enrich the alert: owner/CSM, contract value, renewal date, open cases. Read-only.
5. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Risk Watch operating prompt** (see [`../risk-watch.md`](../risk-watch.md) → How it works / Output), with the call (step 2), account history (step 3), and account metadata (step 4) mapped in. Instruct the prompt to reply with exactly `NO_RISK` when no indicators are present.
6. **Filter by Zapier** — continue only if the step 5 output does **not** contain `NO_RISK`.
   - This enforces the spec's "alert only when a risk is present" rule.
7. **Action — Slack "Send Channel Message"**
   - Channel: the account-risk / CS-alerts channel. Message text: the alert from step 5.

## Notes
- **Alert only when a risk is present.** The Filter in step 6 stays silent on healthy accounts.
- Add an upstream check to skip when the call has no transcript (failed recording), and skip the
  engagement-drop check for an account's first-ever call (the prompt also handles these).
- To avoid duplicates, you can add a **Delay/Storage** check so the same account is not re-alerted
  within 24 hours for identical indicators.
- Keep the guardrails from the spec: read-only on CRM/recorder, every indicator tied to a transcript
  quote or a baseline metric, and the humanizer rules are part of the prompt (no em dashes, no
  throat-clearing, no hype, one clear ask).
