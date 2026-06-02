# Case Study Generator — Zapier build

Zapier has no import file, so this is the exact Zap to assemble. It mirrors the canonical spec
([`../case-study-generator.md`](../case-study-generator.md)). Swap the example apps for the ones you use.

## Steps

1. **Trigger — Webhooks by Zapier (Catch Hook)** → point your call recorder's "conversation
   analyzed" webhook here. The payload carries the call id.
2. **Action — your call recorder (or Webhooks by Zapier → GET)**
   - Fetch the call's transcript and metadata by id, and confirm it reads as a success story.
3. **Action — your CRM (e.g. Salesforce "Find Record" / HubSpot "Find Deal")**
   - Pull the deal facts: account, industry, size, deal value, contacts, dates.
4. **Action — Anthropic (or "AI by Zapier", or Webhooks → POST to `https://api.anthropic.com/v1/messages`)**
   - Header `x-api-key: <your key>`, `anthropic-version: 2023-06-01`. Body model `claude-sonnet-4-5`.
   - Prompt = the **Case Study operating prompt** (see [`../case-study-generator.md`](../case-study-generator.md) → How it works / Output), with the call from step 2 and the CRM facts from step 3 mapped in.
5. **Action — Slack "Send Direct Message"**
   - To: the marketing owner. Message text: the model output from step 4, labeled as a draft.

## Notes
- Draft only. Never connect a "publish to CMS" or "send to customer" action. A human reviews, fact-checks, and gets quote approval before publishing.
- Keep the guardrails from the spec: read-only on CRM/recorder, evidence-bound (no invented quotes or
  metrics), and the humanizer rules are part of the prompt (no em dashes, no throat-clearing, no hype).
