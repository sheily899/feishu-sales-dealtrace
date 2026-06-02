# Scorecard per Rep

> Weekly per-rep scorecard: score six core selling dimensions 1-5 from the rep's calls, track each against last week, and surface the top 3 coaching priorities with a specific example and a concrete next move.

**Function:** Sales Enablement · **Trigger:** scheduled (weekly, Monday 08:00) · **Template id:** `AGTScorecardRep01`
**Files:** [`scorecard-per-rep.json`](./scorecard-per-rep.json) (Attention agent-builder template) · [`scorecard-per-rep.activepieces.json`](./scorecard-per-rep.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one scorecard per rep that:
1. Scores six core selling dimensions on a 1-5 scale from the rep's recorded calls.
2. Grounds every score in concrete call evidence (a quote, a timestamp, a moment), never a vibe.
3. Tracks each dimension against the prior week so improvement and slippage are visible.
4. Surfaces the top 3 coaching priorities per rep with a specific example and a concrete suggestion a manager can act on.

## When it fires

- **Type:** schedule. **Default:** `0 8 * * 1` (Monday 08:00, workspace timezone). **Lookback:** trailing 7 days, compared against the prior 7-day window.
- **Alternative trigger:** run it on demand for a mid-week pulse, or change the cadence by editing the cron. Weekly is the default because the trend arrows and the team summary (most improved, team average) need a full prior week to compare against.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Each rep's conversations in the window (and the prior week, for trends) | Call recorder | `search_calls` |
| The specific call moment behind each coaching priority | Call recorder | `get_call_details` |
| The content of those conversations (to score the six dimensions) | Call recorder + LLM | `analyze_calls` |
| The rep roster, to group calls and compute the team summary | Organization | `search_calls` metadata |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Find each rep's calls (and the prior week) | Attention `search_calls` | your recorder's API, or ingest exports via the [gtmsi adapters](../../docs/adapters.md) |
| `get_call_details` | Pull the exact call moment behind a coaching priority | Attention `get_call_details` | your recorder's transcript fetch |
| `analyze_calls` | Score the six dimensions and estimate talk ratio | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the scorecard to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Retrieve reps and calls.** `search_calls` for the trailing 7 days; group by rep and collect each rep's call ids (up to 25 per analysis request).
2. **Score six dimensions (1-5)** from transcript evidence: **Discovery Quality, Objection Handling, Value Articulation, Next-Step Setting, Talk Ratio** (5 = rep talks 30-45%, 3 = 50-60%, 1 = over 70%), **Question Quality.** Compute each rep's average.
3. **Compute trends.** If prior-week calls exist, compare each dimension and mark improved / declined / stable.
4. **Identify the top 3 coaching priorities.** Take the 3 lowest-scoring dimensions per rep; for each, use `get_call_details` to pull a specific call example (timestamp or quote) and write one concrete coaching suggestion.
5. **Build the team summary:** highest performer, most improved, team average, total calls analyzed.
6. **Compose and post** the report in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full dimension definitions and scoring rules) is the single source of truth in [`scorecard-per-rep.json`](./scorecard-per-rep.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Weekly Rep Scorecard -- [date range]

[Rep Name]  (per rep)
| Dimension | Score | Trend |   (Discovery, Objection Handling, Value Articulation,
                                  Next-Step Setting, Talk Ratio, Question Quality)
Overall: [average]/5

Top 3 Coaching Priorities  ->  [dimension] -- observed (with call example). Try this: [suggestion]

TEAM SUMMARY  ->  highest performer · most improved · team average · total calls analyzed
```

## Edge cases

- **Rep with fewer than 3 calls:** score only the dimensions you can assess reliably; flag "Insufficient data for full scorecard."
- **No calls for any rep:** post "No calls recorded this period. Scorecard generation skipped." and stop.
- **No prior-period data:** omit trend arrows and note "First scorecard -- trends will appear next period."
- **Talk ratio unavailable on a recorder:** estimate from speaker turns and label it as approximate.

## Guardrails

- Read-only on the recorder. The only write is the one channel message.
- Every score and coaching priority ties to a specific call and quote. No speculation presented as fact.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`scorecard-per-rep.activepieces.json`](./scorecard-per-rep.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger → an `askAttention` step (pulls the week's calls per rep, scores six dimensions, compares to last week, picks coaching priorities) → a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`scorecard-per-rep.json`](./scorecard-per-rep.json).

**Any other builder — pre-built for you** in [`scorecard-per-rep.builds/`](./scorecard-per-rep.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./scorecard-per-rep.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./scorecard-per-rep.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./scorecard-per-rep.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./scorecard-per-rep.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./scorecard-per-rep.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./scorecard-per-rep.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/sales-enablement/scorecard-per-rep.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`scorecard-per-rep.json`](./scorecard-per-rep.json) · [`scorecard-per-rep.activepieces.json`](./scorecard-per-rep.activepieces.json) (Attention). Other builders: [`scorecard-per-rep.builds/`](./scorecard-per-rep.builds/)._
