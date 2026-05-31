# Product Tracker

**Function:** Product  ·  **Integrations:** call_recorder, communication  ·  **Template id:** `AGTProductTrack01`

> Tracks product feature requests, feedback, and pain points from customer conversations for product teams.

## When it fires

**Detector:** Trigger if the user wants to track product feedback, feature requests, or customer pain points and route them to product teams.

**Signal keywords:** `product feedback`, `feature request`, `product request`, `roadmap feedback`, `customer feedback`, `product insights`, `product suggestions`, `feature gap`

## What it does

Capture and organize product feedback, feature requests, and pain points from customer conversations. Generate weekly insights for product teams with prioritized feedback.

## Tools / actions
- **Call Recorder** — Search Calls, Ask Attention
- **Communication** — Send Message

## Tooling

Attention-native: this agent uses `ask_attention` (natural-language query/analysis over calls + CRM) plus `search_calls`/`get_call_details` where it needs specific calls. **On Attention** — import it into the agent builder, or run it here with Attention's MCP, and it works as written. **On any other recorder** — run it as a managed Claude agent with [`/run-agent`](../../.claude/commands/run-agent.md): Claude reads your CRM and pulls transcripts via your recorder or the [gtmsi adapters](../../docs/adapters.md), then does the same analysis. See [Tooling & portability](../README.md#tooling--portability).

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Schedule — runs weekly, Monday 08:00 (cron `0 8 * * 1`, set the timezone to the team's).

---
_From GTM Superintelligence agent templates. Raw definition: [`product-tracker.json`](./product-tracker.json)._
