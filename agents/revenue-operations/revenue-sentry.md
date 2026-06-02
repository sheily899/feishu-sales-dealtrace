# Revenue Sentry

> Daily scan of the active pipeline that scores every open deal for risk, sorts the at-risk ones into RED / ORANGE / YELLOW tiers, and posts one alert with a specific intervention for each, so the team fixes deals before they slip.

**Function:** Revenue Operations · **Trigger:** scheduled (weekdays 07:00) · **Template id:** `AGTRevenueSent01`
**Files:** [`revenue-sentry.json`](./revenue-sentry.json) (Attention agent-builder template) · [`revenue-sentry.activepieces.json`](./revenue-sentry.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one alert that:
1. Scans every open deal in the pipeline and scores it for risk from real call evidence.
2. Rates each deal 0-3 on five risk dimensions for a total out of 15.
3. Sorts at-risk deals into RED / ORANGE / YELLOW tiers and omits the healthy ones.
4. Attaches a specific recommended intervention to every RED and ORANGE deal.
5. Quantifies total revenue at risk so leadership knows where to spend attention today.

## When it fires

- **Type:** schedule. **Default:** `0 7 * * 1-5` (weekdays 07:00, workspace timezone). **Lookback:** trailing 14 days of calls.
- **Alternative trigger:** if your CRM emits stage-change or stale-deal events, you can fire per-deal on a risk event. The scheduled scan is the default because it sweeps the whole pipeline and ranks risk across deals, which a single-deal trigger cannot.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Open deals (name, stage, amount, expected close date, owner, last activity date) | CRM | `query_records` |
| All calls from the last 14 days, grouped by deal/account | Call recorder | `search_calls` |
| The content of those calls (to score sentiment, objections, competition) | Call recorder + LLM | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `query_records` | Read open opportunities from the CRM | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `search_calls` | Find the calls linked to a deal/account | Attention `search_calls` | your recorder's API, or ingest exports via the [gtmsi adapters](../../docs/adapters.md) |
| `analyze_calls` | Score each deal's risk from its transcripts | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the alert to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Retrieve pipeline and recent calls.** `query_records`: every open deal with stage, amount, expected close date, owner, last activity. `search_calls`: all calls from the last 14 days, grouped by deal. Note conversation count last 7 days vs the prior 7 to read the engagement trend. If a deal exists with zero calls, flag it (see Edge cases).
2. **Score each deal 0-3 on five risk dimensions** (higher = riskier), each backed by call evidence: **Engagement Cadence, Sentiment Trajectory, Unresolved Objections, Competitive Pressure, Timeline Slippage.** Total Risk = sum out of 15.
3. **Classify into tiers:** RED ALERT (10-15), ORANGE WARNING (6-9), YELLOW WATCH (3-5), GREEN HEALTHY (0-2). Include only RED, ORANGE, and YELLOW in the alert; omit GREEN to keep it actionable.
4. **Attach a recommended intervention** to every RED and ORANGE deal, specific to its top risk dimension.
5. **Compose and post** the alert in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full 0-3 scoring rubric per dimension and the tier thresholds) is the single source of truth in [`revenue-sentry.json`](./revenue-sentry.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Revenue Sentry -- Daily Pipeline Risk Alert
Date: [today] · Deals scanned: [N]
Red: [N] | Orange: [N] | Yellow: [N] · Revenue at risk (Red+Orange): $[X]

RED ALERT -- Immediate Action Required  (per deal)
[Deal] -- $[amount] -- [Rep] · Risk [X/15] · Stage · Expected close
  | Dimension | Score | Evidence |   (one row per dimension, 0-3 + brief evidence)
  Recommended intervention: [specific action]

ORANGE WARNING -- Attention This Week  (condensed, one line per deal)
YELLOW WATCH -- Monitor  (bulleted, one-line risk summary each)

PIPELINE HEALTH SUMMARY  ->  healthy vs at-risk counts and value, pipeline risk ratio
```

## Edge cases

- **No at-risk deals:** post a brief "all clear" confirming the scan ran, with total pipeline value and deal count so leadership sees the scope.
- **Deal with no calls at all:** flag it ORANGE with note "no conversation data, cannot assess risk from call evidence, rep should confirm deal status."
- **Very large pipeline (50+ deals):** prioritize RED and ORANGE in the body; summarize YELLOW as a count and total value rather than listing each.
- **Close date today or past due:** automatically boost Timeline Slippage to 3. A deal past its close date without a closed-won marker is at risk by definition.

## Guardrails

- Read-only on CRM and recorder. The only write is the one channel message.
- Every risk score ties to CRM data or a call quote. No speculation presented as fact.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`revenue-sentry.activepieces.json`](./revenue-sentry.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger -> an `askAttention` step (scans open deals, analyzes their calls, scores risk, writes the alert) -> a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`revenue-sentry.json`](./revenue-sentry.json).

**Any other builder — pre-built for you** in [`revenue-sentry.builds/`](./revenue-sentry.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./revenue-sentry.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./revenue-sentry.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./revenue-sentry.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./revenue-sentry.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./revenue-sentry.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./revenue-sentry.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/revenue-operations/revenue-sentry.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`revenue-sentry.json`](./revenue-sentry.json) · [`revenue-sentry.activepieces.json`](./revenue-sentry.activepieces.json) (Attention). Other builders: [`revenue-sentry.builds/`](./revenue-sentry.builds/)._
