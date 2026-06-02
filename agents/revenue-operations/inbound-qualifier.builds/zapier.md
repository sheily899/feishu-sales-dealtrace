# Inbound Qualifier — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../inbound-qualifier.md`](../inbound-qualifier.md)). This is a per-call Zap. Swap the example apps
for the ones you use.

## Steps

1. **Trigger — your call recorder ("conversation analyzed"), or Webhooks by Zapier → Catch Hook**
   - Fires once per analyzed inbound call. Capture the call id and the company.
2. **Action — fetch the call (your recorder app, or Webhooks by Zapier → GET)**
   - Pull the transcript + attendees for that call id. (If your recorder only exports transcripts,
     pull from where you store them.)
3. **Action — your CRM (e.g. Salesforce "Find Record" / HubSpot "Find Company")**
   - Read firmographics for ICP fit: company size, industry, and the existing-customer flag. If
     unmatched, the prompt infers fit from the conversation and notes the assumption.
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Inbound Qualifier operating prompt** (see [`../inbound-qualifier.md`](../inbound-qualifier.md) → How it works / Output), with the call from step 2 and the firmographics from step 3 mapped in.
5. **Action — Slack "Send Channel Message"**
   - Channel: your inbound/SDR channel. Message text: the model output from step 4.

## Notes
- Add a **Filter by Zapier** step after step 2 to skip internal/non-customer calls if your recorder
  does not pre-tag inbound calls.
- Keep the guardrails from the spec: read-only on CRM/recorder, every BANT score and the disposition
  ties to a transcript quote or CRM firmographic, and the humanizer rules are part of the prompt (no
  em dashes, no throat-clearing, no hype, one clear ask).
