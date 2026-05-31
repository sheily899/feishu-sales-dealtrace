# Cross Seller Radar

**Function:** Revenue Operations  ·  **Integrations:** crm, call_recorder, communication  ·  **Template id:** `AGTCrossSeller01`

> Detects cross-sell opportunities by analyzing customer needs and product interest signals.

## When it fires

**Detector:** Trigger if the user wants to identify cross-sell opportunities by detecting customer needs that match other products in the portfolio.

**Signal keywords:** `cross-sell`, `cross sell`, `additional products`, `expand account`, `product expansion`, `adjacent products`, `complementary products`

## What it does

Analyze customer conversations to identify cross-sell opportunities: detect pain points matching other products, questions about additional capabilities, and expansion signals. Send alerts for qualified opportunities.

## Tools / actions
- **CRM** — Query Records
- **Call Recorder** — Search Calls, Ask Attention
- **Communication** — Send Message

## Tooling

Attention-native: this agent uses `ask_attention` (natural-language query/analysis over calls + CRM) plus `search_calls`/`get_call_details` where it needs specific calls. **On Attention** — import it into the agent builder, or run it here with Attention's MCP, and it works as written. **On any other recorder** — run it as a managed Claude agent with [`/run-agent`](../../.claude/commands/run-agent.md): Claude reads your CRM and pulls transcripts via your recorder or the [gtmsi adapters](../../docs/adapters.md), then does the same analysis. See [Tooling & portability](../README.md#tooling--portability).

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Conversation analyzed — fires once per call, when your call recorder finishes analyzing it (the *Conversation Analyzed* webhook).

---
_From GTM Superintelligence agent templates. Raw definition: [`cross-seller-radar.json`](./cross-seller-radar.json)._
