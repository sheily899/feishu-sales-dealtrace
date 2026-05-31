# Email Generator

**Function:** Sales  ·  **Integrations:** call_recorder, communication  ·  **Template id:** `AGTEmailGen01`

> Generates personalized follow-up emails based on conversation content and action items.

## When it fires

**Detector:** Trigger if the user wants to automatically generate personalized follow-up emails after customer calls or meetings.

**Signal keywords:** `follow-up email`, `email draft`, `generate email`, `post-call email`, `meeting follow-up`, `email summary`, `write email`, `recap email`

## What it does

After a conversation is analyzed:
1. Use the call recorder's analysis to extract: key discussion points, action items, commitments made, next steps, and any pain points mentioned
2. Generate a professional follow-up message that summarizes the conversation and outlines agreed actions
3. Customize tone based on the relationship context (discovery call vs established customer)
4. Include specific references from the call to personalize
5. Send the summary via direct message to the rep or to a designated channel

## Tools / actions
- **Call Recorder** — Search Calls, Ask Attention
- **Communication** — Send Direct Message, Send Message

## Tooling

Attention-native: this agent uses `ask_attention` (natural-language query/analysis over calls + CRM) plus `search_calls`/`get_call_details` where it needs specific calls. **On Attention** — import it into the agent builder, or run it here with Attention's MCP, and it works as written. **On any other recorder** — run it as a managed Claude agent with [`/run-agent`](../../.claude/commands/run-agent.md): Claude reads your CRM and pulls transcripts via your recorder or the [gtmsi adapters](../../docs/adapters.md), then does the same analysis. See [Tooling & portability](../README.md#tooling--portability).

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Conversation analyzed — fires once per call, when your call recorder finishes analyzing it (the *Conversation Analyzed* webhook).

---
_From GTM Superintelligence agent templates. Raw definition: [`email-generator.json`](./email-generator.json)._
