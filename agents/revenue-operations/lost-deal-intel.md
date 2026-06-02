# Lost-Deal Intel

> Weekly, evidence-backed post-mortem of every recently lost deal: why it died, the turning-point call, cross-deal patterns, and what leadership should change this week.

**Function:** Revenue Operations · **Trigger:** scheduled (weekdays 08:00) · **Template id:** `AGTLostDealInt01`
**Files:** [`lost-deal-intel.json`](./lost-deal-intel.json) (Attention agent-builder template) · [`lost-deal-intel.activepieces.json`](./lost-deal-intel.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one structured report that:
1. Lists every deal lost in the lookback window with the dollars attached.
2. Classifies each loss into one primary reason (plus up to two contributing) from a fixed taxonomy.
3. Writes a per-deal post-mortem grounded in the actual call history, not just the CRM field.
4. Finds patterns across the set (repeat competitors, recurring product gaps, weak-execution segments).
5. Gives 2-3 org-level recommendations someone can act on this week.

## When it fires

- **Type:** schedule. **Default:** `0 8 * * 1-5` (weekdays 08:00, workspace timezone). **Lookback:** trailing 7 days.
- **Alternative trigger:** if your CRM emits stage-change events, you can instead fire per-deal on entry to a Closed-Lost stage (resolve your real lost stage with `gtmsi crm-stages` rather than hardcoding the label). The scheduled digest is the default because it also produces the cross-deal pattern analysis, which a single-deal trigger cannot.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Deals marked Closed-Lost in the window (name, account, owner, amount, stage-at-loss, CRM loss reason) | CRM | `query_records` |
| All conversations tied to each lost deal/account, in chronological order | Call recorder | `search_calls` |
| The content of those conversations (to determine the real loss reason) | Call recorder + LLM | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `query_records` | Read lost opportunities from the CRM | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `search_calls` | Find the calls linked to a deal/account | Attention `search_calls` | your recorder's API, or ingest exports via the [gtmsi adapters](../../docs/adapters.md) |
| `analyze_calls` | Classify the loss and reconstruct the deal from transcripts | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the report to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Identify recently lost deals.** `query_records`: deals where stage is Closed-Lost and close date is within the window. Capture name, account, owner, amount, stage-at-loss, and the CRM loss reason if present. If none, post the "no losses" confirmation (see Edge cases) and stop.
2. **Pull each deal's call history.** `search_calls` for every lost deal/account; sort chronologically to reconstruct the full arc.
3. **Classify the primary loss reason** (plus up to two contributing) from this fixed taxonomy, each with evidence: **PRICING, COMPETITION, PRODUCT-GAP, TIMING, SALES-EXECUTION, CHAMPION-LOSS, NO-DECISION, LEGAL-SECURITY.**
4. **Write the per-deal post-mortem** across five dimensions: (A) deal timeline + turning-point call, (B) customer perspective + the most revealing quote, (C) competitive intel (if COMPETITION), (D) sales-execution rating STRONG/ADEQUATE/WEAK, (E) product-market-fit / systemic-gap signal.
5. **Find cross-deal patterns** (only if 3+ losses): most common reason, repeat-winning competitors, recurring product gaps, over-represented rep/segment/size, execution patterns.
6. **Compose and post** the report in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full taxonomy evidence rules and dimension checklists) is the single source of truth in [`lost-deal-intel.json`](./lost-deal-intel.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Lost-Deal Intel -- Weekly Loss Analysis Report
Period: [start] to [end] · Deals lost: [N] · Total revenue lost: $[X]

LOSS REASON BREAKDOWN
| Reason | Count | Total Value | % |   (one row per reason, sorted by count)

DEAL POST-MORTEMS  (per deal)
[Deal] -- $[amount] · Account · Owner · Cycle length · Stage at loss
  Primary reason · Contributing factors · Sales execution [STRONG/ADEQUATE/WEAK]
  Timeline · Turning point · Customer's perspective · Key quote
  Lessons for the team

TREND ANALYSIS  (only if 3+ losses)  ->  top patterns
RECOMMENDATIONS  ->  2-3 org-level actions for this week
```

## Edge cases

- **No losses in the window:** post "Lost-Deal Intel ran for [range]. No deals were marked lost. Pipeline health is stable." (confirms the agent is alive).
- **Lost deal with no calls:** post-mortem from CRM data only; mark loss reason UNKNOWN if the field is empty; recommend a manual rep debrief.
- **Reopened deal:** flag "may have been prematurely marked lost, recent activity detected."
- **CRM reason conflicts with the calls:** flag the discrepancy and recommend correcting the CRM field.
- **Single loss:** skip Trend Analysis; produce just the one post-mortem.

## Guardrails

- Read-only on CRM and recorder. The only write is the one channel message.
- Every claim ties to CRM data or a call quote. No speculation presented as fact.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`lost-deal-intel.activepieces.json`](./lost-deal-intel.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger → an `askAttention` step (queries the lost deals, analyzes their calls, writes the report) → a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`lost-deal-intel.json`](./lost-deal-intel.json).

**Any other builder — pre-built for you** in [`lost-deal-intel.builds/`](./lost-deal-intel.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./lost-deal-intel.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./lost-deal-intel.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./lost-deal-intel.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./lost-deal-intel.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./lost-deal-intel.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./lost-deal-intel.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/revenue-operations/lost-deal-intel.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`lost-deal-intel.json`](./lost-deal-intel.json) · [`lost-deal-intel.activepieces.json`](./lost-deal-intel.activepieces.json) (Attention). Other builders: [`lost-deal-intel.builds/`](./lost-deal-intel.builds/)._
