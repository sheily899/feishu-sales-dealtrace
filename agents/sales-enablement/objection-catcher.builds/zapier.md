# Objection Catcher — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../objection-catcher.md`](../objection-catcher.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — Schedule by Zapier** → *Every Week*, Monday, 8:00 AM.
2. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Pull every call from the last 7 days that has a transcript. (No recorder app in Zapier? Use a
     Webhooks GET to its API.)
3. **Action — your CRM (optional, e.g. Salesforce "Find Record(s)")**
   - Fetch deal outcomes (stage, advanced, won/lost) to weight rebuttal scores. Skip this step if you
     have no CRM; the prompt handles missing outcome data.
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Objection Catcher operating prompt** (see
     [`../objection-catcher.md`](../objection-catcher.md) → How it works / Output), with the calls
     from step 2 and the outcomes from step 3 mapped in.
5. **Action — Gmail / Email by Zapier "Send Email"**
   - To: the enablement owner(s), CC relevant leads. Body: the model output from step 4 (plain text).

## Notes
- For a high call volume, use a **Looping by Zapier** step to chunk the calls, then a final step to
  assemble the digest.
- Keep the guardrails from the spec: read-only on the recorder/CRM, constructive tone, every objection
  and rebuttal tied to a real call quote and timestamp, and the humanizer rules are part of the prompt
  (no em dashes, no throat-clearing, no hype, one clear ask).
