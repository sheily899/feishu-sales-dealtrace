# Deal Stage Clarity

**Function:** Revenue Operations  ·  **Integrations:** crm, call_recorder, communication  ·  **Template id:** `AGTDealStage01`

> Ensures accurate deal staging by analyzing conversation content vs CRM stage.

## When it fires

**Detector:** Trigger if the user wants to validate CRM deal stages against actual conversation content or improve forecast and pipeline accuracy.

**Signal keywords:** `deal stage`, `stage validation`, `forecast accuracy`, `pipeline accuracy`, `stage mismatch`, `deal progression`, `opportunity stage`, `stage hygiene`

## What it does

Analyze deal conversations to validate CRM deal stages. Identify misalignments between conversation reality and system stage. Provide weekly forecast accuracy reports.

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
_From GTM Superintelligence agent templates. Raw definition: [`deal-stage-clarity.json`](./deal-stage-clarity.json)._
