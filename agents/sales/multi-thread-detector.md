# Multi Thread Detector

**Function:** Sales  ·  **Integrations:** call_recorder, communication  ·  **Template id:** `AGTMultiThread01`

> Identifies multi-threading opportunities by detecting gaps in stakeholder engagement.

## When it fires

**Detector:** Trigger if the user wants to identify deals with single-threading risk, missing stakeholders, or opportunities to engage more decision makers.

**Signal keywords:** `multi-thread`, `single thread`, `stakeholder engagement`, `decision maker`, `buying committee`, `multi-threading`, `champion`, `executive sponsor`

## What it does

Analyze deal conversations to identify multi-threading gaps and stakeholder engagement opportunities. Alert for single-threaded deals and missing decision makers.

## Tools / actions
- **Call Recorder** — Search Calls, Ask Attention, Get Call Details
- **Communication** — Send Message

## Tooling

Attention-native: this agent uses `ask_attention` (natural-language query/analysis over calls + CRM) plus `search_calls`/`get_call_details` where it needs specific calls. **On Attention** — import it into the agent builder, or run it here with Attention's MCP, and it works as written. **On any other recorder** — run it as a managed Claude agent with [`/run-agent`](../../.claude/commands/run-agent.md): Claude reads your CRM and pulls transcripts via your recorder or the [gtmsi adapters](../../docs/adapters.md), then does the same analysis. See [Tooling & portability](../README.md#tooling--portability).

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Conversation analyzed — fires once per call, when your call recorder finishes analyzing it (the *Conversation Analyzed* webhook).

---
_From GTM Superintelligence agent templates. Raw definition: [`multi-thread-detector.json`](./multi-thread-detector.json)._
