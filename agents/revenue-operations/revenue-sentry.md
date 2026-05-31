# Revenue Sentry

**Function:** Revenue Operations  ·  **Integrations:** crm, call_recorder, communication  ·  **Template id:** `AGTRevenueSent01`

> Monitors pipeline health and identifies at-risk deals requiring immediate intervention based on conversation analysis.

## When it fires

**Detector:** Trigger if the user wants to monitor pipeline health, identify at-risk deals, detect stalled opportunities, or get alerts about revenue risks.

**Signal keywords:** `pipeline health`, `at-risk deal`, `deal risk`, `revenue risk`, `stalled deal`, `pipeline alert`, `deal health`, `forecast risk`

## What it does

Monitor pipeline health, identify revenue risks from stalled conversations, declining engagement, unresolved objections, and competitive pressure. Send daily alerts for high-risk deals.

## Tools / actions
- **CRM** — Query Records
- **Call Recorder** — Search Calls, Ask Attention
- **Communication** — Send Message

## Tooling

Attention-native: this agent uses `ask_attention` (natural-language query/analysis over calls + CRM) plus `search_calls`/`get_call_details` where it needs specific calls. **On Attention** — import it into the agent builder, or run it here with Attention's MCP, and it works as written. **On any other recorder** — run it as a managed Claude agent with [`/run-agent`](../../.claude/commands/run-agent.md): Claude reads your CRM and pulls transcripts via your recorder or the [gtmsi adapters](../../docs/adapters.md), then does the same analysis. See [Tooling & portability](../README.md#tooling--portability).

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Schedule — runs every weekday at 07:00 (cron `0 7 * * 1-5`, set the timezone to the team's).

**Uses real CRM stages:** resolve this org's actual pipeline stages and where its open pipeline sits via [CRM stage discovery](../../docs/crm-stages.md) (`gtmsi crm-stages`) rather than assuming stage labels.

---
_From GTM Superintelligence agent templates. Raw definition: [`revenue-sentry.json`](./revenue-sentry.json)._
