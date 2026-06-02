# Win Loss Insights

> Monthly, evidence-backed report on every deal closed in the trailing 30 days: win themes, loss themes, competitive dynamics, sales-cycle metrics, and pricing sensitivity, compared to the prior month, with strategic recommendations leadership can act on.

**Function:** Revenue Operations · **Trigger:** scheduled (weekly, Monday 08:00; analyzes trailing 30 days) · **Template id:** `AGTWinLossIns01`
**Files:** [`win-loss-insights.json`](./win-loss-insights.json) (Attention agent-builder template) · [`win-loss-insights.activepieces.json`](./win-loss-insights.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one report that:
1. Lists every deal closed won and lost in the trailing 30 days with the dollars and cycle length.
2. Analyzes the won and lost cohorts separately across five dimensions.
3. Maps the competitive landscape (who appears in wins vs losses, and the trend).
4. Compares the period to the prior 30 days so leadership sees what is changing.
5. Gives 3-5 strategic recommendations someone can act on (battlecards, process, enablement).

## When it fires

- **Type:** schedule. **Default:** `0 8 * * 1` (Monday 08:00, workspace timezone). **Lookback:** trailing 30 days, with the prior 30 days (days 31-60) for trend comparison.
- **Why weekly for a monthly report:** running weekly over a rolling 30-day window keeps the intelligence fresh and the competitive trend current, instead of one stale snapshot per month.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Deals closed won/lost in the window (account, outcome, owner, amount, stage, close date, cycle length) | CRM | `query_records` |
| All conversations tied to each closed deal/account, grouped by deal | Call recorder | `search_calls` |
| The content of those conversations (to extract themes, competitors, pricing) | Call recorder + LLM | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `query_records` | Read closed opportunities and outcomes from the CRM | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `search_calls` | Find the calls linked to a closed deal/account | Attention `search_calls` | your recorder's API, or ingest exports via the [gtmsi adapters](../../docs/adapters.md) |
| `analyze_calls` | Extract themes, competitors, and pricing signals from transcripts | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the report to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Identify closed deals.** `query_records`: every deal closed won or lost in the past 30 days with account, outcome, rep, value, stage, and cycle length. If stages are not exposed, infer outcomes from conversation context.
2. **Retrieve associated calls.** `search_calls` for each closed deal/account; collect call IDs grouped by deal.
3. **Analyze five dimensions, won and lost cohorts separately** (batch the calls per request): **Win Themes, Loss Themes, Competitive Dynamics, Sales Cycle Patterns, Pricing Sensitivity.**
4. **Compare to the prior period** (days 31-60 ago): win-rate trend, theme shifts, competitive shifts, cycle-length change.
5. **Generate 3-5 strategic recommendations** with rationale tied to the findings.
6. **Compose and post** the report in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full five-dimension question checklists) is the single source of truth in [`win-loss-insights.json`](./win-loss-insights.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Monthly Win/Loss Intelligence Report -- [date range]

Executive Summary  ->  won/lost counts + value, win rate (+ trend), avg cycle won vs lost

Win Themes  ->  top patterns across won deals
Loss Themes  ->  top patterns across lost deals + most common loss reason + most common stall stage

Competitive Landscape
| Competitor | Appeared in Won | Appeared in Lost | Trend |   + key competitive insight

Sales Cycle Patterns  ->  avg calls / stakeholders won vs lost, deal-size pattern
Pricing Insights  ->  pricing cited in [n]% of losses, discount correlation, top objection

Strategic Recommendations  ->  3-5 actions with rationale
Trend vs Prior Period  ->  win-rate, win/loss theme shifts, competitive shift
Source  ->  [n] calls across [n] closed deals
```

## Edge cases

- **Fewer than 3 closed deals in the window:** note the limited sample size and flag that patterns may not be reliable. Still produce the report with available data.
- **No closed-lost deals:** report only win themes and note "no closed-lost deals this period, loss analysis resumes when data is available."
- **No closed-won deals:** report only loss themes and flag this as a concern.
- **No prior-period data:** omit trend comparisons and note "first report, trend comparisons appear next period."
- **Outcomes undeterminable (no CRM access, outcomes not discussed in calls):** post a note to ensure CRM stages are accessible or that reps discuss deal status on recorded calls.

## Guardrails

- Read-only on CRM and recorder. The only write is the one channel message.
- Every theme and number ties to CRM data or a call quote. No speculation presented as fact.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`win-loss-insights.activepieces.json`](./win-loss-insights.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger -> an `askAttention` step (pulls closed deals over the trailing 30 days, analyzes won and lost cohorts, compares to the prior period, writes the report) -> a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. Because the schema sample we modeled on was a per-call agent, confirm three things against a flow you export from your own workspace: (1) the schedule piece name/version, (2) the `askAttention` context scope for a cross-deal/CRM query (we use `contextType: "user"`), and (3) the Slack channel-post action name. The fully-managed alternative is to import the agent template [`win-loss-insights.json`](./win-loss-insights.json).

**Any other builder — pre-built for you** in [`win-loss-insights.builds/`](./win-loss-insights.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./win-loss-insights.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./win-loss-insights.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./win-loss-insights.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./win-loss-insights.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./win-loss-insights.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./win-loss-insights.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/revenue-operations/win-loss-insights.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`win-loss-insights.json`](./win-loss-insights.json) · [`win-loss-insights.activepieces.json`](./win-loss-insights.activepieces.json) (Attention). Other builders: [`win-loss-insights.builds/`](./win-loss-insights.builds/)._
