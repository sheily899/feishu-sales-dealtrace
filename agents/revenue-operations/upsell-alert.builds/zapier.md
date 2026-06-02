# Upsell Alert — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../upsell-alert.md`](../upsell-alert.md)). This is a per-call Zap. Swap the example apps for the
ones you use.

## Steps

1. **Trigger — your call recorder ("conversation analyzed"), or Webhooks by Zapier → Catch Hook**
   - Fires once per analyzed customer call. Capture the call id and basic metadata.
2. **Action — fetch the call (your recorder app, or Webhooks by Zapier → GET)**
   - Pull the transcript + attendees for that call id. (If your recorder only exports transcripts,
     pull from where you store them.)
3. **Action — your CRM (e.g. Salesforce "Find Record" / HubSpot "Find Contact")**
   - Confirm the speaker, the linked account, current ACV, and the owner. If unmatched, the prompt
     flags it and still posts.
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Upsell Alert operating prompt** (see [`../upsell-alert.md`](../upsell-alert.md) → How it works / Output), with the call from step 2 and the CRM match from step 3 mapped in.
5. **Action — Slack "Send Channel Message"**
   - Channel: your upsell-alerts channel. Message text: the model output from step 4.

## Notes
- Add a **Filter by Zapier** step after the LLM so the Zap only posts when a signal is found (the
  prompt outputs a "no expansion signal detected" line you can filter on, or skip the filter to keep
  the screened-but-clear notes).
- Keep the guardrails from the spec: read-only on CRM/recorder, evidence-bound, do not inflate
  hypothetical language, and the humanizer rules are part of the prompt (no em dashes, no
  throat-clearing, no hype, one clear ask).
