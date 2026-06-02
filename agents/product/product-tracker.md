# Product Tracker

> Each week, scan the past week's customer calls, extract every product signal (feature requests, bugs, workarounds, competitive gaps, praise, usability complaints), categorize and prioritize them, and post one structured digest to the product team.

**Function:** Product · **Trigger:** scheduled (weekly, Monday 08:00) · **Template id:** `AGTProductTrack01`
**Files:** [`product-tracker.json`](./product-tracker.json) (Attention agent-builder template) · [`product-tracker.activepieces.json`](./product-tracker.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one digest that:
1. Turns the past week's customer calls into a single read on product feedback for the product team.
2. Extracts every product signal and grounds each in a verbatim quote and the account it came from.
3. Categorizes signals (UX, performance, integrations, missing features, bugs, workflow gaps) and prioritizes them P1-P4 by frequency and customer tier.
4. Surfaces week-over-week trends and the loudest single signal, in one skimmable message.

## When it fires

- **Type:** schedule. **Default:** `0 8 * * 1` (Monday 08:00, workspace timezone). **Lookback:** trailing 7 days.
- **Alternative trigger:** you can also run it per-call on the recorder's "conversation analyzed" webhook to file signals in real time, but the weekly digest is the default because frequency and trend analysis (how many customers asked for the same thing) only make sense across a set of calls.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| All customer-facing calls in the window (title, account, date, link) | Call recorder | `search_calls` |
| Full call records where a signal needs context | Call recorder | `get_call_details` |
| The product signals (requests, bugs, workarounds, gaps, praise, complaints) + quotes | Call recorder + LLM | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Find the week's customer-facing calls | Attention `search_calls` | your recorder's API, or ingest exports via the [gtmsi adapters](../../docs/adapters.md) |
| `get_call_details` | Pull a full call record for context | Attention `get_call_details` | recorder API |
| `analyze_calls` | Extract, categorize, and prioritize the product signals | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the digest to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one digest.

## How it works (step by step)

1. **Retrieve the week's conversations.** `search_calls` for all customer-facing calls in the last 7 days (batch with `analyze_calls`); `get_call_details` where a signal needs context.
2. **Extract product signals.** For each call, pull every instance of: **FEATURE REQUESTS** (capability that does not exist yet), **BUG REPORTS** (broken or erroring), **WORKAROUND MENTIONS** (manual hacks because the product lacks a workflow), **COMPETITIVE FEATURE GAPS** (a competitor feature you lack), **PRAISE** (a feature they love), **USABILITY COMPLAINTS** (confusing, too many steps). Capture account, customer name + title, the exact quote, and the rep's response.
3. **Categorize each signal** into one of: UX / Usability, Performance, Integrations, Missing Features, Bugs, Workflow Gaps.
4. **Prioritize** by frequency (3+ customers = High, 2 = Medium, 1 = Low) and customer tier (enterprise/strategic outweigh SMB), combined into P1 (critical) -> P4 (monitor). Group duplicate requests under one item with a count.
5. **Compose and post** the digest in the [Output](#output) format (header, P1-P4 blocks, Positive Feedback, Competitive Intel, Trends vs last week), then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full extraction query, categories, and priority rules) is the single source of truth in [`product-tracker.json`](./product-tracker.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Product Feedback Digest -- this week
Calls analyzed: [X] | Signals extracted: [Y] | Accounts represented: [Z]

P1 -- Critical (act this sprint)   -> per item: label, category, mentions, accounts, representative quote, customer impact
P2 -- Important (next sprint)
P3 -- Notable (backlog)
P4 -- Monitor (single mentions, one line each)

Positive Feedback   -> what customers love, with quotes
Competitive Intel   -> competitor mentions by feature/capability
Trends vs last week -> brief comparison
```
(If one request dominates with 5+ mentions, it is called out as a "Top Signal" at the very top.)

## Edge cases

- **No calls this week:** post "No customer calls recorded this week. No product feedback to report. Next digest: [date]."
- **Calls but no product signals:** post "Analyzed [X] calls. No explicit product feedback, requests, or bugs detected. Customers focused on [topic]."
- **A single request dominates (5+ mentions):** call it out as a "Top Signal" before the priority breakdown.
- **Customer tier undeterminable:** default to P3 for single mentions, P2 for multiple.
- **Duplicate / near-duplicate requests:** group under one item with the count, not separate lines.

## Guardrails

- Read-only on the recorder. The only write is the one digest.
- Every signal ties to a verbatim quote and a named account. No invented feedback or inflated counts.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`product-tracker.activepieces.json`](./product-tracker.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger -> an `askAttention` step (scans the week's calls, extracts and prioritizes the signals, writes the digest) -> a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`.

**Build notes (confirm against your own export):** because the schema sample we modeled on was a per-call agent, confirm three things against a flow you export from your own workspace: (1) the schedule piece name/version, (2) the `askAttention` context scope for a cross-call query (we use `contextType: "user"`), and (3) the Slack channel-post action name. The fully-managed alternative is to import the agent template [`product-tracker.json`](./product-tracker.json).

**Any other builder — pre-built for you** in [`product-tracker.builds/`](./product-tracker.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./product-tracker.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./product-tracker.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./product-tracker.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./product-tracker.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./product-tracker.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./product-tracker.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/product/product-tracker.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`product-tracker.json`](./product-tracker.json) · [`product-tracker.activepieces.json`](./product-tracker.activepieces.json) (Attention). Other builders: [`product-tracker.builds/`](./product-tracker.builds/)._
