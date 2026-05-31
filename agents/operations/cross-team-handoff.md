# Cross Team Handoff

**Function:** Operations  ·  **Integrations:** crm, call_recorder, communication  ·  **Template id:** `AGTCrossTeamHO01`

> Orchestrates smooth handoffs between teams by creating comprehensive context summaries with conversation history and action items.

## When it fires

**Detector:** Trigger if the user wants to create comprehensive handoff summaries when accounts transition between teams (sales to CS, CS to support, etc.).

**Signal keywords:** `team handoff`, `account handoff`, `transition`, `transfer account`, `handover`, `team transition`, `account transition`, `ownership change`

## What it does

Create comprehensive handoff summaries when accounts transition between teams (sales to implementation, CSM to support). Include conversation history, stakeholder information, commitments made, and next steps.

## Tools / actions
- **CRM** — Query Records
- **Call Recorder** — Search Calls, Ask Attention
- **Communication** — Send Message

## Tooling

Attention-native: this agent uses `ask_attention` (natural-language query/analysis over calls + CRM) plus `search_calls`/`get_call_details` where it needs specific calls. **On Attention** — import it into the agent builder, or run it here with Attention's MCP, and it works as written. **On any other recorder** — run it as a managed Claude agent with [`/run-agent`](../../.claude/commands/run-agent.md): Claude reads your CRM and pulls transcripts via your recorder or the [gtmsi adapters](../../docs/adapters.md), then does the same analysis. See [Tooling & portability](../README.md#tooling--portability).

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** CRM stage change — fires when an Opportunity's stage enters a **Closed-Won** stage (hand the account to CS/onboarding).

**Resolve stages first — don't hardcode "Closed Won":** every org names stages differently. Resolve this org's actual won stage(s) via [CRM stage discovery](../../docs/crm-stages.md) (`gtmsi crm-stages`) — e.g., Salesforce: `OpportunityStage` where `IsWon = true`; HubSpot: the deal pipeline stage with `metadata.probability = 1.0`.

---
_From GTM Superintelligence agent templates. Raw definition: [`cross-team-handoff.json`](./cross-team-handoff.json)._
