# Social Proof Finder

> Each week, scan the past week's calls for the strongest social proof (testimonials, success stories, quotable wins), pull the best verbatim quotes with their source links, and post a report for marketing and sales as a draft to mine. Quotes need customer approval before any public use.

**Function:** Marketing · **Trigger:** scheduled (weekly, Monday 08:00) · **Template id:** `AGTProofFinder01`
**Files:** [`social-proof-finder.json`](./social-proof-finder.json) (Attention agent-builder template) · [`social-proof-finder.activepieces.json`](./social-proof-finder.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one report that:
1. Surfaces the strongest social proof from the past week's calls: testimonials, success stories, quotable wins.
2. Prioritizes quotes that are specific, authentic, and tied to a measurable result over generic praise.
3. Grounds every item in a verbatim quote and a link back to the source call so marketing can verify and reuse it.
4. Lands as a draft, with quotes flagged for customer approval before any public use.

## When it fires

- **Type:** schedule. **Default:** `0 8 * * 1` (Monday 08:00, workspace timezone). **Lookback:** trailing 7 days.
- **Alternative trigger:** you can also run it per-call on the recorder's "conversation analyzed" webhook to capture quotes in real time, but the weekly digest is the default because it groups stories by account and gives marketing one place to mine, rather than a stream of one-offs.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| All customer-facing calls in the window (title, account, date, link) | Call recorder | `search_calls` |
| Full call records where a quote needs context | Call recorder | `get_call_details` |
| The satisfaction / success moments and verbatim quotes | Call recorder + LLM | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Find the week's customer-facing calls | Attention `search_calls` | your recorder's API, or ingest exports via the [dealtrace adapters](../../docs/adapters.md) |
| `get_call_details` | Pull a full call record for context | Attention `get_call_details` | recorder API |
| `analyze_calls` | Flag genuine social proof and pull the best quotes | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the report to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one report.

## How it works (step by step)

1. **Retrieve the week's conversations.** `search_calls` for all customer-facing calls in the last 7 days; `get_call_details` where a quote needs context.
2. **Flag genuine social proof.** `analyze_calls` to find moments of satisfaction, success, or positive outcomes. PRIORITIZE quotes that are specific, authentic, and mention a measurable result. AVOID false positives: routine politeness ("thanks for your help"), neutral status talk, or anything lukewarm does not count. Capture account, speaker + title, verbatim quote, one-line context, and the call link.
3. **Compose the report.** Group by account, lead with a one-line header (count of stories), then one entry per story (call title, summary, quote, account/speaker, view-call link). Sort the strongest, results-backed quotes first.
4. **Humanize (mandatory):** run the report through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** skill as the final pass.
5. **Deliver** to the marketing / sales channel, noting clearly that quotes are unverified draft material and need customer approval before public use.

> The verbatim operating prompt is the single source of truth in [`social-proof-finder.json`](./social-proof-finder.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Social Proof Finder -- weekly success stories  (N stories found)

Call Title: <title>
Summary: <one-line context>
Quote: "<verbatim customer quote>"
Account / Speaker: <account> -- <name, title>
View Call: <link>

(grouped by account; strongest, results-backed quotes first)

Note: draft material, get customer approval before any public use.
```

## Edge cases

- **No calls this week:** post "Social Proof Finder ran for [range]. No customer calls recorded this week, so no social proof to report." (confirms the agent is alive).
- **Calls but no genuine social proof:** post "Analyzed [X] calls. No specific, quotable success moments surfaced. Mostly neutral or in-progress conversations."
- **Borderline quotes:** leave mildly-positive lines out rather than padding the report.
- **Sensitive accounts:** summarize the sentiment without naming a confidential account and note the quote needs clearance.
- **Same customer, multiple strong quotes:** group under one account entry; do not double-count as separate stories.

## Guardrails

- Read-only on the recorder. The only write is the one report.
- Every quote is verbatim and linked to its source call. No paraphrased or invented testimonials.
- Quotes are draft material and need customer approval before any public use.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`social-proof-finder.activepieces.json`](./social-proof-finder.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger -> an `askAttention` step (scans the week's calls, flags social proof, writes the report) -> a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`.

**Build notes (confirm against your own export):** The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`social-proof-finder.json`](./social-proof-finder.json).

**Any other builder — pre-built for you** in [`social-proof-finder.builds/`](./social-proof-finder.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./social-proof-finder.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./social-proof-finder.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./social-proof-finder.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./social-proof-finder.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./social-proof-finder.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./social-proof-finder.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/marketing/social-proof-finder.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`social-proof-finder.json`](./social-proof-finder.json) · [`social-proof-finder.activepieces.json`](./social-proof-finder.activepieces.json) (Attention). Other builders: [`social-proof-finder.builds/`](./social-proof-finder.builds/)._
