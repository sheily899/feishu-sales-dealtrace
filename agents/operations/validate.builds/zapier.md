# Validate — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../validate.md`](../validate.md)). This is a per-call Zap. Swap the example apps for the ones you use.

## Steps

1. **Trigger — your call recorder ("conversation analyzed"), or Webhooks by Zapier → Catch Hook**
   - Fires once per analyzed customer call. Capture the call id, the call owner, and any known CRM record ids.
2. **Action — fetch the call (your recorder app, or Webhooks by Zapier → GET)**
   - Pull the transcript + participants for that call id. (If your recorder only exports transcripts,
     pull from where you store them.)
3. **Action — your CRM (e.g. Salesforce "Find Record(s)" / HubSpot "Find") — read current state**
   - Resolve the Account/Contact/Opportunity (by participant email, domain, or provided id) and read
     the current values of the fields you might update, to build the before/after diff.
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Validate operating prompt** (see [`../validate.md`](../validate.md) → How it works / Output), with the call from step 2 and the current CRM state from step 3 mapped in. The prompt extracts the CRM-impacting fields and renders the before/after review card, applying the humanizer rules.
5. **Action — Slack "Send Direct Message"**
   - To: the call owner. Message text: the review card from step 4 (the diff table + Approve / Edit / Skip / Remind actions).
6. **Action (gated) — your CRM "Update Record(s)" — Approve & Push**
   - Wire this to fire ONLY after the rep approves (e.g. behind a Slack interactive approval, or a
     second Zap triggered by the approval). Write ONLY the approved/edited fields; leave everything
     else untouched. Then add a Call/Task/Activity summarizing the changes.

## Notes
- **No CRM write without approval.** Step 6 must sit behind an explicit approval; never auto-fire it
  off step 5.
- Add a **Filter by Zapier** step after step 2 to skip internal/non-customer calls (the prompt also
  returns a one-line skip note for those, and for calls with no CRM-impacting fields).
- Keep the guardrails from the spec: every proposed field traces to a quote, timecode, or confidence
  score (no invented values), and the humanizer rules are part of the prompt (no em dashes, no
  throat-clearing, no hype, one clear ask).
