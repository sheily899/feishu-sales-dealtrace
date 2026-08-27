# Objection Drilldown

> Weekly objection intelligence: classify every prospect objection into a fixed taxonomy, score how well reps handled each, extract the best rebuttal per category, flag rising/declining/new trends, and surface the categories that stall deals.

**Function:** Sales Enablement · **Trigger:** scheduled (weekly, Monday 08:00) · **Template id:** `AGTObjectionDrill01`
**Files:** [`objection-drilldown.json`](./objection-drilldown.json) (Attention agent-builder template) · [`objection-drilldown.activepieces.json`](./objection-drilldown.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one structured report that:
1. Classifies every prospect objection from the week into one of a fixed 8-category taxonomy.
2. Scores how effectively the rep handled each objection (Effective / Partial / Ineffective).
3. Extracts the top-performing rebuttal per category as a reusable template the team can adopt.
4. Detects trends versus the prior week (rising, declining, and new categories) and flags the high-risk categories most associated with stalled deals.

## When it fires

- **Type:** schedule. **Default:** `0 8 * * 1` (Monday 08:00, workspace timezone). **Lookback:** trailing 7 days, compared against the prior 7-day window.
- **Alternative trigger:** you can run it on demand any time you want a fresh objection read, or shift the cadence (daily/monthly) by editing the cron. The weekly digest is the default because the trend comparison and best-rebuttal extraction need a full week of calls to be meaningful.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| All team conversations in the window (and the prior week, for trends) | Call recorder | `search_calls` |
| The exact wording of an objection or rebuttal on a specific call | Call recorder | `get_call_details` |
| The content of those conversations (to classify objections and score handling) | Call recorder + LLM | `analyze_calls` |
| The rep roster, to attribute each objection/rebuttal | Organization | `search_calls` metadata |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Find the week's calls (and the prior week) | Attention `search_calls` | your recorder's API, or ingest exports via the [dealtrace adapters](../../docs/adapters.md) |
| `get_call_details` | Pull a verbatim objection or rebuttal from a specific call | Attention `get_call_details` | your recorder's transcript fetch |
| `analyze_calls` | Classify objections, score handling, extract rebuttals | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the report to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Retrieve calls.** `search_calls` for the trailing 7 days; collect all call ids across the team. Batch into groups of up to 25 ids for analysis. If fewer than 5 calls, note the small sample and that trends may not be meaningful.
2. **Classify objections** into one category each, with the rep, call id, and a paraphrase, from this fixed taxonomy: **PRICING/BUDGET, TIMING/URGENCY, COMPETITION, FEATURE-GAPS, AUTHORITY/DECISION-PROCESS, SECURITY/LEGAL/COMPLIANCE, INTEGRATION/TECHNICAL, ROI/PROOF.**
3. **Score response effectiveness** per objection on a 3-point scale: Effective (3) acknowledged + substantive + conversation advanced; Partial (2) addressed but unresolved; Ineffective (1) ignored, deflected, or fumbled.
4. **Extract best-practice rebuttals.** For each category, take the highest-scoring response and use `get_call_details` to capture the exact language as a reusable rebuttal template.
5. **Analyze trends** against the prior 7-day window: rising categories (possible market shift or messaging gap), declining categories (positioning may be working), and new categories.
6. **Assess deal impact.** Correlate categories with outcomes; flag the categories most associated with calls where no next step was set as high-risk.
7. **Compose and post** the report in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full taxonomy and scoring rules) is the single source of truth in [`objection-drilldown.json`](./objection-drilldown.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Weekly Objection Intelligence Report -- [date range] · Calls analyzed: [N]

OBJECTION FREQUENCY BY CATEGORY
| Category | Count | Trend | Avg Effectiveness |   (one row per category)

HIGH-RISK OBJECTION CATEGORIES  ->  categories most tied to stalled deals

BEST-PRACTICE REBUTTALS  (per category)
[Category] -- [Rep] used: "[effective response]". Result: [what happened next]

TREND ALERTS  ->  Rising · Declining · New this week
```

## Edge cases

- **Fewer than 5 calls in the window:** note the limited sample size and flag that trends may not be statistically meaningful.
- **No objections detected:** post "No prospect objections detected in [n] calls this week. This may indicate early-stage pipeline or insufficient sample size." (confirms the agent is alive).
- **No prior-period data:** omit trend comparisons and note "First report -- trends will appear next period."
- **Same rebuttal works across categories:** attribute it once per category where it applies; do not double-count the objection.

## Guardrails

- Read-only on the recorder. The only write is the one channel message.
- Every objection, score, and rebuttal ties to a specific call and quote. No speculation presented as fact.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`objection-drilldown.activepieces.json`](./objection-drilldown.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger → an `askAttention` step (pulls the week's calls, classifies and scores objections, extracts rebuttals, compares to last week) → a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`objection-drilldown.json`](./objection-drilldown.json).

**Any other builder — pre-built for you** in [`objection-drilldown.builds/`](./objection-drilldown.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./objection-drilldown.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./objection-drilldown.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./objection-drilldown.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./objection-drilldown.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./objection-drilldown.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./objection-drilldown.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/sales-enablement/objection-drilldown.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`objection-drilldown.json`](./objection-drilldown.json) · [`objection-drilldown.activepieces.json`](./objection-drilldown.activepieces.json) (Attention). Other builders: [`objection-drilldown.builds/`](./objection-drilldown.builds/)._
