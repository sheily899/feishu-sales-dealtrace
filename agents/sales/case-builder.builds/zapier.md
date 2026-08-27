# Case Builder — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../case-builder.md`](../case-builder.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — Webhooks by Zapier → Catch Hook.** Point your call recorder's "conversation analyzed"
   webhook here. The call id arrives in the payload. (No webhook? Use a polling trigger for newly
   analyzed calls.)
2. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Get the triggering call's transcript + metadata by its id.
3. **Action — your call recorder (or Webhooks → GET)**
   - Fetch the deal's/account's prior calls for cumulative context. (Recorder that only exports
     transcripts? Pull them however you store them, or pre-ingest via the dealtrace adapters.)
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Case Builder operating prompt** (see [`../case-builder.md`](../case-builder.md) →
     How it works / Output), with the call from step 2 and the prior calls from step 3 mapped in.
5. **Action — Slack "Send Channel Message"**
   - Channel: your team channel. Message text: the model output from step 4.

## Notes
- Build the case only when the call has substantive business discussion; the eligibility check is in
  the prompt, so a non-qualifying call returns a short "no business case" line you can filter on.
- Keep the guardrails from the spec: read-only on the recorder, evidence-bound (no invented numbers),
  single stars not double, and the humanizer rules are part of the prompt (no em dashes, no
  throat-clearing, no hype, one clear ask). Never wire a "send to customer" step.
