# Validate — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../validate.md`](../validate.md)). This is a per-call scenario. A verified, importable Make
**blueprint JSON** will be added here once we validate it against a blueprint exported from a real
Make account (same way the Attention flow schema was confirmed from a real export). Until then,
assemble the scenario from these modules.

## Modules (in order)

1. **Webhook → Custom webhook** as the trigger. Point your recorder's "conversation analyzed"
   webhook here; the payload should carry the call id, the call owner, and any known CRM record ids.
2. **HTTP → Make a request** to your call recorder's API to fetch the analyzed call (transcript +
   participants). (Recorder that only exports transcripts? Pull from where you store them, or
   pre-ingest via the gtmsi adapters.)
3. **Your CRM** (Salesforce "Search Records" / HubSpot "Search", or **HTTP → Make a request**) —
   read current state. Resolve the Account/Contact/Opportunity by participant email, domain, or
   provided id, and read the current values of the fields you might update.
4. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 2000`, a single user message = the **Validate operating prompt**
     (see [`../validate.md`](../validate.md)) with the call (module 2) and current CRM state (module 3)
     mapped in. The prompt extracts the CRM-impacting fields and renders the before/after review card.
5. **Slack → Create a Message** as a **direct message** to the call owner; text = `{{4.content[0].text}}`.
6. **Your CRM "Update a Record" (gated) — Approve & Push.** Wire this to run ONLY after the rep
   approves (behind a Slack interactive approval or a second scenario triggered by the approval).
   Write ONLY the approved/edited fields; add a Call/Task/Activity summarizing the changes.

## Notes
- **No CRM write without approval.** Module 6 must sit behind an explicit approval; never auto-fire
  it off module 5.
- Add a **Filter** after module 2 to skip internal/non-customer calls (the prompt also returns a
  one-line skip note for those, and for calls with no CRM-impacting fields).
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `4` above.
- Guardrails from the spec hold: every proposed field traces to a quote, timecode, or confidence
  score (no invented values), humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
