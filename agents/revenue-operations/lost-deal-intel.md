# Lost-Deal Intel

**Function:** Revenue Operations  ·  **Integrations:** crm, call_recorder, communication  ·  **Template id:** `AGTLostDealInt01`

> Extracts actionable intelligence from lost deals including reasons, competitive insights, and improvements.

## When it fires

**Detector:** Trigger if the user wants to analyze lost deals to extract actionable intelligence about loss reasons, competitive factors, and improvement opportunities.

**Signal keywords:** `lost deal`, `deal lost`, `loss reason`, `why we lost`, `lost opportunity`, `deal post-mortem`, `closed lost`, `loss analysis`

## What it does

Conduct deep analysis of lost deals: loss reasons, competitive intelligence, sales execution gaps, customer perspective, and product/market fit. Generate searchable loss intelligence database.

## Tools / actions
- **CRM** — Query Records
- **Call Recorder** — Search Calls, Ask Attention
- **Communication** — Send Message

## Tooling

Attention-native: this agent uses `ask_attention` (natural-language query/analysis over calls + CRM) plus `search_calls`/`get_call_details` where it needs specific calls. **On Attention** — import it into the agent builder, or run it here with Attention's MCP, and it works as written. **On any other recorder** — run it as a managed Claude agent with [`/run-agent`](../../.claude/commands/run-agent.md): Claude reads your CRM and pulls transcripts via your recorder or the [gtmsi adapters](../../docs/adapters.md), then does the same analysis. See [Tooling & portability](../README.md#tooling--portability).

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** CRM stage change — fires when an Opportunity's stage enters a **Closed-Lost** stage.

**Resolve stages first — don't hardcode "Closed Lost":** resolve this org's actual lost stage(s) via [CRM stage discovery](../../docs/crm-stages.md) (`gtmsi crm-stages`) — e.g., Salesforce: `OpportunityStage` where `IsClosed = true AND IsWon = false`; HubSpot: the pipeline stage with `metadata.probability = 0.0`.

---
_From GTM Superintelligence agent templates. Raw definition: [`lost-deal-intel.json`](./lost-deal-intel.json)._
