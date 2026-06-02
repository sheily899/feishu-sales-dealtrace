# Cross Seller Radar — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../cross-seller-radar.md`](../cross-seller-radar.md)). This is a per-call Zap. Swap the example
apps for the ones you use.

## Steps

1. **Trigger — your call recorder ("conversation analyzed"), or Webhooks by Zapier → Catch Hook**
   - Fires once per analyzed call. Capture the call id and the account.
2. **Action — fetch the call (your recorder app, or Webhooks by Zapier → GET)**
   - Pull the transcript + attendees for that call id. (If your recorder only exports transcripts,
     pull from where you store them.)
3. **Action — your CRM (e.g. Salesforce "Find Record" / HubSpot "Find Company")**
   - Read what the account already owns: current products, current ACV, and renewal date, so the
     prompt only pitches what they lack.
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Cross Seller Radar operating prompt** (see [`../cross-seller-radar.md`](../cross-seller-radar.md) → How it works / Output), with the call from step 2 and what the account owns from step 3 mapped in.
5. **Action — Slack "Send Channel Message"**
   - Channel: your expansion/cross-sell channel. Message text: the model output from step 4.

## Notes
- Add a **Filter by Zapier** step after the LLM so the Zap only posts for HIGH/MEDIUM opportunities
  (the prompt outputs a "No qualified cross-sell opportunity" line you can filter on). Skip prospect
  calls (the prompt also returns a one-line note for those).
- Keep the guardrails from the spec: read-only on CRM/recorder, every signal ties to something the
  customer said, every product match is one they do not already own, and the humanizer rules are part
  of the prompt (no em dashes, no throat-clearing, no hype, one clear ask).
