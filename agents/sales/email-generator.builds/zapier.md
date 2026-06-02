# Email Generator — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../email-generator.md`](../email-generator.md)). This is a per-call Zap. Swap the example apps for
the ones you use.

## Steps

1. **Trigger — your call recorder ("conversation analyzed"), or Webhooks by Zapier → Catch Hook**
   - Fires once per analyzed customer call. Capture the call id and the deal owner (rep).
2. **Action — fetch the call (your recorder app, or Webhooks by Zapier → GET)**
   - Pull the transcript + attendees for that call id. (If your recorder only exports transcripts,
     pull from where you store them.)
3. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Email Generator operating prompt** (see [`../email-generator.md`](../email-generator.md) → How it works / Output), with the call from step 2 mapped in. The prompt drafts in the rep's voice and applies the humanizer rules.
4. **Action — Slack "Send Direct Message"**
   - To: the rep (deal owner). Message text: the model output from step 3.

## Notes
- **Draft only, to the rep.** Do not connect a "send email to customer" action. The rep reviews and sends.
- Add a **Filter by Zapier** step after step 2 to skip internal/non-customer calls (the prompt also
  handles this by returning a one-line skip note).
- Keep the guardrails from the spec: every specific in the email comes from the call (no invented
  commitments, numbers, or names), and the humanizer rules are part of the prompt (no em dashes, no
  throat-clearing, no hype, one clear ask).
