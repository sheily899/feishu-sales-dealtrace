# Multi Thread Detector — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../multi-thread-detector.md`](../multi-thread-detector.md)). Swap the example apps for the ones
you use.

## Steps

1. **Trigger — Webhooks by Zapier → Catch Hook.** Point your call recorder's "conversation analyzed"
   webhook here. The call id arrives in the payload. (No webhook? Use a polling trigger for newly
   analyzed calls.)
2. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Get the triggering call (account, deal, participants, rep) by its id.
3. **Action — your call recorder (or Webhooks → GET)**
   - Fetch every prior call on the same deal/account to build the cumulative stakeholder map.
     (Recorder that only exports transcripts? Pull from where you store them, or pre-ingest via the
     gtmsi adapters.)
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Multi-Thread-Detector operating prompt** (see
     [`../multi-thread-detector.md`](../multi-thread-detector.md) → How it works / Output), with the
     call from step 2 and the prior calls from step 3 mapped in.
5. **Filter by Zapier** — only continue if the model output does **not** contain "no alert needed"
   (Low-risk deals return that line so they are skipped).
6. **Action — Slack "Send Channel Message"**
   - Channel: your team channel. Message text: the model output from step 4.

## Notes
- The risk scoring and "only alert on Medium+" gate live in the prompt; the Filter step enforces it.
- Keep the guardrails from the spec: read-only on the recorder, never fabricate stakeholders, single
  stars not double, and the humanizer rules are part of the prompt (no em dashes, no throat-clearing,
  no hype, one clear ask).
