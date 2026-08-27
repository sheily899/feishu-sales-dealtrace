# Content Gaps

> Weekly report of the prospect questions and objections reps struggle to answer: clustered into themes, ranked by frequency and deal impact, with the specific content or training that would close each gap.

**Function:** Sales Enablement · **Trigger:** scheduled (weekly, Monday 08:00) · **Template id:** `AGTContentGaps01`
**Files:** [`content-gaps.json`](./content-gaps.json) (Attention agent-builder template) · [`content-gaps.activepieces.json`](./content-gaps.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one report that:
1. Surfaces the prospect questions and objections reps struggled to answer this week, grounded in real call evidence.
2. Clusters those moments into recurring themes and ranks them by frequency and deal impact.
3. Recommends the specific content or training that would close each gap (one-pager, FAQ, demo clip, micro-training).
4. Keeps a constructive, improvement-focused tone, and reads like a real person wrote it.

## When it fires

- **Type:** schedule. **Default:** `0 8 * * 1` (Monday 08:00, workspace timezone). **Lookback:** trailing 7 days.
- **Alternative trigger:** you can also run it on demand after a big week of calls. The scheduled weekly digest is the default because the value is in the cross-call pattern (which gaps recur), which a single-call trigger cannot see.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Every analyzed call from the last 7 days (transcripts, Q&A, rep confidence signals) | Call recorder | `search_calls` |
| Conversation metadata (account, product line, rep, sentiment) for clustering and weighting | Call recorder | `search_calls` |
| The questions/objections, the rep's answers, and rep uncertainty signals | LLM over the transcripts | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Pull the week's analyzed calls | Attention `search_calls` | recorder API, or the [dealtrace adapters](../../docs/adapters.md) over the export |
| `analyze_calls` | Extract questions, answers, and uncertainty signals; cluster themes | `ask_attention` | an LLM step over the transcripts |
| `send_message` | Post the report to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Pull the week's calls.** `search_calls` for every analyzed conversation in the last 7 days across all reps, with account / product line / rep / sentiment. If none, post the "no calls" confirmation (see Edge cases) and stop.
2. **Extract questions and uncertainty signals.** `analyze_calls`: for each call, every prospect question or objection, the rep's answer and whether it resolved the question, and rep uncertainty signals (filler, deflection, hedging, "I'll have to check," a promise to follow up). Quote the moment where possible.
3. **Cluster recurring topics.** Group questions/objections by semantic theme (pricing model, integrations, implementation timeline, security/compliance, competitor comparison, API capabilities), merging variants of the same question.
4. **Score frequency and impact.** Per theme: how many calls and distinct reps it appeared in, and whether it tended to surface in stalled or negative-sentiment deals. Rank by frequency, then impact.
5. **Recommend enablement actions.** Per top theme, one concrete action (one-pager, FAQ, demo clip, battlecard update, micro-training), plus broader training needs observed.
6. **Compose and post** the report in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt is the single source of truth in [`content-gaps.json`](./content-gaps.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Weekly Content Gap Report - Week of [date range]

Frequently Asked (Unanswered) Questions
  1. "[question]" - mentioned [N]x, reps showed uncertainty
     Recommendation: [concrete content action]
  2. ...

Training Needs Observed
  - [theme reps were unsure on]

Suggested Actions
  - [enablement / content action for this week]

Source: call analyses across all reps, [week range]
```

## Edge cases

- **No calls in the period:** post "Weekly Content Gap Report ran for [range]. No analyzed calls were found this week, so there is nothing to summarize." (confirms the agent is alive).
- **No clear gaps found:** if reps answered confidently across the board, say so plainly and skip recommendations rather than inventing gaps.
- **A single dominant theme:** still produce the full report; rank the one theme first and note the concentration.

## Guardrails

- Read-only on the recorder. The only write is the one channel message.
- Every gap ties to a real question or uncertainty signal from a call. No invented gaps.
- Constructive tone, focused on improvement, not performance criticism. Single stars for emphasis, never double stars.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`content-gaps.activepieces.json`](./content-gaps.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger → an `askAttention` step (scans the week's calls, clusters the gaps, writes the report) → a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`content-gaps.json`](./content-gaps.json).

**Any other builder - pre-built for you** in [`content-gaps.builds/`](./content-gaps.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./content-gaps.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./content-gaps.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./content-gaps.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./content-gaps.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./content-gaps.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./content-gaps.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/sales-enablement/content-gaps.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`content-gaps.json`](./content-gaps.json) · [`content-gaps.activepieces.json`](./content-gaps.activepieces.json) (Attention). Other builders: [`content-gaps.builds/`](./content-gaps.builds/)._
