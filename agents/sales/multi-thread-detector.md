# Multi Thread Detector

> After every analyzed call, build a cumulative stakeholder map for the deal against the MEDDPICC roles, score single-thread risk, and alert the team with specific multi-threading actions when a deal is leaning on too few people.

**Function:** Sales · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTMultiThread01`
**Files:** [`multi-thread-detector.json`](./multi-thread-detector.json) (Attention agent-builder template) · [`multi-thread-detector.activepieces.json`](./multi-thread-detector.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Catch single-threaded deals before they stall:
1. Build a cumulative stakeholder map across all the deal's calls and score how many MEDDPICC roles are covered.
2. Flag single-threaded and under-covered deals, while distinguishing genuinely early-stage deals from risky ones.
3. Give the rep specific, role-by-role multi-threading actions tied to the pain discussed.
4. Read like a teammate wrote it (mandatory humanizer pass).

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (account, owner).
- Alerts only when threading risk is Medium or higher; first/intro calls are noted, not alerted (see Edge cases).

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The triggering call (transcript + participants, account, deal, rep) | Call recorder | `get_call_details` |
| All prior calls on the same deal/account, to build the stakeholder map | Call recorder | `search_calls` |
| Each prospect-side participant's name, title/role, and likely MEDDPICC role | LLM over the transcripts | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `get_call_details` | Fetch the triggering call's transcript and participants | Attention `get_call_details` | recorder API, or the [gtmsi adapters](../../docs/adapters.md) over the export |
| `search_calls` | Find every prior call on the deal/account | Attention `search_calls` | recorder API / adapters |
| `analyze_calls` | Identify stakeholders and map them to MEDDPICC roles | `ask_attention` | an LLM step over the transcripts |
| `send_message` | Post the threading alert to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Retrieve call and deal context.** `get_call_details` for the triggering call (account, deal, participants, rep). `search_calls` by the same account/deal to gather all prior call ids on the opportunity.
2. **Build the stakeholder map.** `analyze_calls` across the deal's calls (up to 25): for every prospect-side participant, capture name, title/role where stated, and the MEDDPICC role they most likely fill: **Champion, Economic Buyer, Technical Evaluator, Coach, End User** (each with its behavioral indicators).
3. **Score threading risk.** Count unique stakeholders and distinct roles covered: **Critical** (1 stakeholder or 1 role), **High** (2 stakeholders but no Economic Buyer or no Champion), **Medium** (3+ stakeholders but 2+ roles uncovered), **Low** (4+ stakeholders covering at least Champion, Economic Buyer, Technical Evaluator).
4. **Generate role-by-role actions.** For each missing role, a specific next move tied to the pain discussed (e.g. missing Economic Buyer → "Ask who approves investments of this size; propose a 20-minute exec briefing on ROI").
5. **Post the alert** (only if Medium or higher) in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full MEDDPICC indicators, risk scoring, and per-role actions) is the single source of truth in [`multi-thread-detector.json`](./multi-thread-detector.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message (only when risk is Medium or higher):

```
Multi-Threading Alert - [Deal/Account]
Latest call: [date] | Rep: [Rep]

Stakeholder Map -> | Name | Title/Role | MEDDPICC Role | Calls involved |
                    (missing roles shown as "0 - Missing")

Threading Risk: [Critical / High / Medium]
  Unique stakeholders: [n] · Roles covered: [n]/5 · Key gap: [most important missing role]

Recommended Actions -> per missing role, one specific move the rep can make next
Deal Threading Score: [n]/5 roles covered
```

## Edge cases

- **First call on a new deal:** normal to have 1 stakeholder. Set risk to "Early Stage - monitor" (not Critical) and remind the rep to multi-thread early.
- **Only one call and it was an inbound/intro call:** do not alert; note "First call - threading assessment will begin after additional calls."
- **Roles cannot be determined (titles not stated):** note "Roles inferred - confirm titles with the rep" and assess on the best available info.
- **No other calls found:** assess on the triggering call alone and flag it as preliminary.

## Guardrails

- Read-only on the recorder. The only write is the one channel message.
- Never fabricate stakeholders who did not appear on a call; every name and role traces to call evidence.
- Single stars for emphasis, never double stars.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`multi-thread-detector.activepieces.json`](./multi-thread-detector.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") → an `askAttention` step that builds the stakeholder map and scores risk → a Slack `send_channel_message`. On import, connect your Attention and Slack accounts and fill `<YOUR_ATTENTION_USER_ID>` and `<YOUR_SLACK_CHANNEL_ID>`. The fully-managed alternative is to import the agent template [`multi-thread-detector.json`](./multi-thread-detector.json).

**Any other builder - pre-built for you** in [`multi-thread-detector.builds/`](./multi-thread-detector.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./multi-thread-detector.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./multi-thread-detector.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./multi-thread-detector.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./multi-thread-detector.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./multi-thread-detector.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./multi-thread-detector.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/sales/multi-thread-detector.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`multi-thread-detector.json`](./multi-thread-detector.json) · [`multi-thread-detector.activepieces.json`](./multi-thread-detector.activepieces.json) (Attention). Other builders: [`multi-thread-detector.builds/`](./multi-thread-detector.builds/)._
