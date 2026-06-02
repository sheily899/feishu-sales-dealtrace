# Inbound Qualifier

> After every analyzed inbound call, score the lead on BANT (0-12) with transcript evidence, rate ICP fit, combine the two into a HOT / WARM / COOL / DISQUALIFIED disposition, and post one qualification report with the next steps and the quotes that justify it.

**Function:** Revenue Operations · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTInboundQual01`
**Files:** [`inbound-qualifier.json`](./inbound-qualifier.json) (Attention agent-builder template) · [`inbound-qualifier.activepieces.json`](./inbound-qualifier.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Qualify every inbound conversation while intent is fresh, so hot leads reach an AE fast:
1. Score BANT on a fixed 0-12 scale with one line of transcript evidence behind each dimension.
2. Rate ICP fit against the configured profile.
3. Combine BANT and ICP into a single disposition: HOT, WARM, COOL, or DISQUALIFIED.
4. Give the rep the next steps and the key quotes that justify routing or disqualifying the lead.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (company, rep).
- On a manual run with no call id, search the last 24 hours for calls tagged inbound / discovery / intro and process each.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (transcript, attendees/roles, company, rep, date) | Call recorder | `get_call_details` |
| BANT evidence and the key quotes, extracted from the transcript | LLM over the transcript | `analyze_calls` |
| Firmographic metadata for ICP fit (company size, industry, existing-customer flag) | CRM | `query_records` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `get_call_details` | Fetch the analyzed call by id (transcript + metadata) | Attention `get_call_details` | recorder API, or the [gtmsi adapters](../../docs/adapters.md) over the export |
| `search_calls` | Find recent inbound calls on a manual run | Attention `search_calls` | recorder API / exports |
| `query_records` | Read firmographics / existing-customer flag for ICP fit | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `send_message` | Post the qualification report to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Retrieve the conversation.** `get_call_details` with the call id from the trigger payload; pull the full transcript, attendees, company, rep. On a manual run, `search_calls` over the last 24 hours for inbound/discovery/intro calls and process each.
2. **Score BANT (0-3 per dimension, 12 max)**, each with one line of transcript evidence: **Budget**, **Authority**, **Need**, **Timeline** (3 CONFIRMED / 2 PARTIAL / 1 IMPLIED / 0 MISSING). Total = sum out of 12.
3. **Assess ICP fit** against the configured profile (industry, company size, use-case match, tech-stack fit, geography); pull firmographics from the CRM metadata where available. Rate **GOOD** (4-5 criteria), **PARTIAL** (2-3), or **POOR** (0-1).
4. **Determine disposition:** **HOT** (BANT 10-12, ICP Good), **WARM** (BANT 7-9, or 10+ with Partial ICP), **COOL** (BANT 4-6), **DISQUALIFIED** (BANT 0-3, or ICP Poor regardless of BANT).
5. **Compose and post** the report in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full 0-3 BANT rubric, the ICP criteria, and the disposition thresholds) is the single source of truth in [`inbound-qualifier.json`](./inbound-qualifier.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Inbound Lead Qualification Report
| Lead | Call Date | Rep | Lead Score | BANT Score | ICP Fit |   (header table)

BANT Breakdown
  Budget [0-3] · Authority [0-3] · Need [0-3] · Timeline [0-3]   (one line of evidence each)

ICP Fit Notes  ->  which criteria matched or missed and why
Recommended Next Steps  ->  concrete actions (route to AE, technical deep-dive, confirm budget holder)
Key Quotes  ->  > "[quote that best illustrates the lead's need or intent]"
```

## Edge cases

- **Very short call (under 5 minutes):** score what you can; mark unaddressed BANT dimensions 0 with "Not discussed, call too short" and recommend a follow-up to complete qualification.
- **Multiple prospects on the call:** qualify the primary contact (the one who spoke most about the business need); note the other attendees and their roles.
- **Existing customer calling about a new product:** flag as EXPANSION not inbound; still score BANT but note they are an existing customer and include current products owned.
- **No transcript available:** report that qualification could not be completed due to a missing transcript; recommend manual review.

## Guardrails

- Read-only on CRM and recorder. The only write is the one channel message.
- Every BANT score and disposition ties to a transcript quote or CRM firmographic. No speculation presented as fact.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`inbound-qualifier.activepieces.json`](./inbound-qualifier.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") -> an `askAttention` step that scores BANT and ICP fit from the call context -> a Slack `send_channel_message`. On import, connect your Attention and Slack accounts and fill `<YOUR_ATTENTION_USER_ID>` and `<YOUR_SLACK_CHANNEL_ID>`. The fully-managed alternative is to import the agent template [`inbound-qualifier.json`](./inbound-qualifier.json).

**Any other builder — pre-built for you** in [`inbound-qualifier.builds/`](./inbound-qualifier.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./inbound-qualifier.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./inbound-qualifier.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./inbound-qualifier.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./inbound-qualifier.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./inbound-qualifier.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./inbound-qualifier.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/revenue-operations/inbound-qualifier.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`inbound-qualifier.json`](./inbound-qualifier.json) · [`inbound-qualifier.activepieces.json`](./inbound-qualifier.activepieces.json) (Attention). Other builders: [`inbound-qualifier.builds/`](./inbound-qualifier.builds/)._
