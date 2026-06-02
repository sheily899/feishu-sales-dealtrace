# Pre-Call Prep — Make build

Guided build for a Make (Integromat) scenario, mirroring the canonical spec
([`../pre-call-prep.md`](../pre-call-prep.md)). A verified, importable Make **blueprint JSON** will
be added here once we validate it against a blueprint exported from a real Make account (same way
the Attention flow schema was confirmed from a real export). Until then, assemble the scenario from
these modules.

## Modules (in order)

1. **Schedule** (scenario clock) → run *Every day*, 07:00 (restrict to weekdays in the schedule settings).
2. **Your calendar** (Google Calendar "Search Events" / Microsoft Outlook, or **HTTP → Make a request**)
   - Find today's meetings between 7:00 AM and 7:00 PM. Output: title, times, link/location, attendees.
3. **Iterator** over the meetings, then **your CRM** (Salesforce "Search Records" / HubSpot
   "Search Deals", or **HTTP → Make a request**)
   - Match attendee emails / domains to an account and the most relevant opportunity (prefer open,
     else most recent closed): stage, amount, close date, forecast category.
4. **HTTP → Make a request** to your call recorder's API for that account's/opportunity's prior
   conversations; keep the most recent 3-5 summaries. (Recorder that only exports transcripts? Pull
   from where you store them, or pre-ingest via the gtmsi adapters.)
5. **Aggregator** to collect each meeting's data back into one bundle.
6. **HTTP → Make a request** to `https://api.anthropic.com/v1/messages`
   - Headers: `x-api-key`, `anthropic-version: 2023-06-01`. Body: `model: claude-sonnet-4-5`,
     `max_tokens: 3000`, a single user message = the **Pre-Call Prep operating prompt**
     (see [`../pre-call-prep.md`](../pre-call-prep.md)) with the aggregated meetings + CRM + calls mapped in. Tell it to use emojis and headings and NO markdown bold.
7. **Slack → Create a Message** (direct message) to the rep; text = `{{6.content[0].text}}`.

## Notes
- Map fields with Make's `{{moduleId.field}}` references; the Anthropic module is `6` above.
- Guardrails from the spec hold: read-only on calendar/CRM/recorder, evidence-bound, DM to the rep
  only, humanizer rules in the prompt.
- Send me a blueprint exported from your Make account and I'll add the exact importable `make.json` here.
