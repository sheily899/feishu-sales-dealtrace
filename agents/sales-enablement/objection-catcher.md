# Objection Catcher

> Weekly objection-handling digest: the most common objections across recorded calls, clustered into categories, with the highest-performing rebuttals reps actually used and concrete coaching tips for the patterns that fall flat.

**Function:** Sales Enablement · **Trigger:** scheduled (weekly, Monday 08:00) · **Template id:** `AGTObjection01`
**Files:** [`objection-catcher.json`](./objection-catcher.json) (Attention agent-builder template) · [`objection-catcher.activepieces.json`](./objection-catcher.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one coaching digest that:
1. Finds the most common objections across the week's calls and clusters them into a stable category taxonomy.
2. Surfaces the highest-performing rebuttals reps used, scored on clarity, empathy, proof, and next step, weighted by deal outcomes.
3. Gives 2-4 concrete coaching tips per top category, focused on the low-scoring patterns.
4. Delivered by email in a constructive tone that reads like a real person wrote it.

## When it fires

- **Type:** schedule. **Default:** `0 8 * * 1` (Monday 08:00, workspace timezone). **Lookback:** trailing 7 days.
- **Alternative trigger:** the underlying signal is per-call (objections surface on each conversation), but the digest is weekly so it can rank categories by frequency and impact, which a single call cannot.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Every call from the last 7 days with a transcript | Call recorder | `search_calls` |
| The objection quote + timestamp, the rep's response, and the response pattern | LLM over the transcripts | `analyze_calls` |
| Optional deal outcome per call (stage, meeting booked, advanced, won/lost) for weighting | CRM | `query_records` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Pull the week's calls that have transcripts | Attention `search_calls` | recorder API, or the [dealtrace adapters](../../docs/adapters.md) over the export |
| `analyze_calls` | Extract and cluster objections, score rebuttals | `ask_attention` | an LLM step over the transcripts |
| `query_records` | Read deal outcomes to weight rebuttal scores | CRM tool | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `send_email` | Email the digest to enablement | Email tool | your email tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is sending one email.

## How it works (step by step)

1. **Collect the week's calls.** `search_calls` for calls in the last 7 days that have a transcript. If none, send the "no calls" confirmation (see Edge cases) and stop.
2. **Extract objections per call.** `analyze_calls`: the objection quote, its moment timestamp (mm:ss), the category, the rep's response quote, and a short response-pattern label.
3. **Normalize into the taxonomy.** Cluster variants into the fixed set, keeping categories stable week to week: **Pricing, Timing/Priority, Competitor, Feature Gap, Security/Legal, Integration, Authority, ROI/Proof, Contract/Procurement, Other.**
4. **Score the responses.** Each objection/response pair 0-100 on clarity, empathy, proof, and next step. Where CRM outcome data exists (`query_records`), weight by meeting booked / stage advanced / won/lost.
5. **Rank and select best messaging.** Rank categories by frequency and impact; per top category, the 1-3 highest-scoring rebuttal snippets with a one-line note on why each worked.
6. **Compute stats and tips.** Total objections, percent of calls with objections, week-over-week change, best-performing patterns, low-scoring coaching opportunities; 2-4 coaching tips per top category.
7. **Email the digest** in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full taxonomy and scoring rubric) is the single source of truth in [`objection-catcher.json`](./objection-catcher.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single plain-text email:

```
Objection Catcher - Weekly Objection-Handling Digest - Week of [date range]

Top Objection Categories (by frequency and impact)
  1. [Category] - [N] objections, WoW [+/-]
     Best rebuttal: "[snippet]"  (why it worked: [one line])
     Coaching tips:
       - [tip]
       - [tip]
  2. ...

Weekly Stats
  - Total objections: [N] · Calls with objections: [%] · WoW change: [+/-]
  - Best-performing patterns: [...] · Coaching opportunities: [low-score patterns]
```

## Edge cases

- **No calls with transcripts in the period:** send "Objection Catcher ran for [range]. No recorded calls with transcripts were found this week." (confirms the agent is alive).
- **Objection with no captured rep response:** list it under its category as unhandled and flag it as a coaching opportunity, rather than scoring a rebuttal.
- **No CRM outcome data available:** score rebuttals on the four quality dimensions only and note that outcome weighting was unavailable.

## Guardrails

- Read-only on the recorder and CRM. The only write is the one email.
- Every objection and rebuttal ties to a real call quote and timestamp. No invented examples.
- Constructive, improvement-focused tone, not performance criticism.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`objection-catcher.activepieces.json`](./objection-catcher.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger → an `askAttention` step (analyzes the week's calls, clusters objections, scores rebuttals, writes the digest) → an email send. On import, connect Attention and your email piece and fill `<ENABLEMENT_RECIPIENT_EMAIL>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`objection-catcher.json`](./objection-catcher.json).

**Any other builder - pre-built for you** in [`objection-catcher.builds/`](./objection-catcher.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./objection-catcher.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./objection-catcher.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./objection-catcher.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./objection-catcher.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./objection-catcher.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./objection-catcher.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/sales-enablement/objection-catcher.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`objection-catcher.json`](./objection-catcher.json) · [`objection-catcher.activepieces.json`](./objection-catcher.activepieces.json) (Attention). Other builders: [`objection-catcher.builds/`](./objection-catcher.builds/)._
