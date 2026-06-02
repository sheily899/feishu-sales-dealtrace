# Deal Stage Clarity

> Scheduled pipeline-hygiene audit that compares what the calls actually show against each deal's CRM stage, flags overstaged, understaged, and stale deals with a confidence rating and the evidence behind them, and quantifies the net forecast adjustment in dollars.

**Function:** Revenue Operations · **Trigger:** scheduled (weekdays 07:00) · **Template id:** `AGTDealStage01`
**Files:** [`deal-stage-clarity.json`](./deal-stage-clarity.json) (Attention agent-builder template) · [`deal-stage-clarity.activepieces.json`](./deal-stage-clarity.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one audit report that:
1. Pulls every active open deal from the CRM with its current stage, amount, and last activity.
2. Reconstructs each deal's recent call history and compares the conversation evidence to the system stage.
3. Flags every overstaged, understaged, and stale deal with a confidence rating and the evidence behind it.
4. Quantifies the net forecast adjustment in dollars, not just hygiene noise.
5. Tells each rep the exact stage move to make and why, grounded in specific conversation moments.

## When it fires

- **Type:** schedule. **Default:** `0 7 * * 1-5` (weekdays 07:00, workspace timezone). **Lookback:** trailing 7 days of calls (expand to 14 on a first run or weekly summary).
- **Alternative trigger:** if your CRM emits stage-change events, you can fire per-deal on a stage move to validate it. The scheduled audit is the default because it sweeps the whole open pipeline and produces the net forecast adjustment, which a single-deal trigger cannot.
- **Uses real CRM stages:** resolve this org's actual pipeline stages and where its open pipeline sits via [CRM stage discovery](../../docs/crm-stages.md) (`gtmsi crm-stages`) rather than assuming the stage labels in the framework below.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Active open deals (name, current stage, amount, expected close date, owner, last activity date) | CRM | `query_records` |
| Recent calls (last 7-14 days), grouped by deal/account | Call recorder | `search_calls` |
| The content of those calls (to determine the stage the evidence actually supports) | Call recorder + LLM | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `query_records` | Read open opportunities and their stages from the CRM | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `search_calls` | Find the calls linked to a deal/account | Attention `search_calls` | your recorder's API, or ingest exports via the [gtmsi adapters](../../docs/adapters.md) |
| `analyze_calls` | Compare each deal's call evidence against its CRM stage | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the audit report to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Gather active deals and recent conversations.** `query_records`: every open deal with current stage, amount, expected close date, owner, last activity. `search_calls`: calls from the last 7 days (14 on a first run or weekly summary), grouped by deal so each deal's call history is available.
2. **Map stages to expected evidence.** Use the six-stage framework (Prospecting, Discovery/Qualification, Demo/Solution, Proposal/Evaluation, Negotiation/Legal, Verbal Commit), adapting the labels to whatever stages this CRM actually uses. Each stage has the conversational evidence that should exist and the red flags if it is missing.
3. **Analyze each deal for mismatches** with a confidence rating (HIGH / MEDIUM / LOW): **OVERSTAGED** (CRM stage ahead of the evidence, inflates the forecast), **UNDERSTAGED** (evidence ahead of the CRM stage, revenue may arrive sooner), **STALE** (no conversation in 14+ days and no stage change), or **correctly staged** (no action).
4. **Calculate forecast impact:** sum the amount at risk of overstatement and the amount potentially understated into a net forecast adjustment figure.
5. **Compose and post** the report in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full stage-to-evidence mapping and the confidence rules) is the single source of truth in [`deal-stage-clarity.json`](./deal-stage-clarity.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Deal Stage Clarity -- Weekly Audit Report
Period: [start] to [end] · Deals analyzed: [N] · Mismatches found: [N] · Forecast adjustment: [+/- $X]

FLAGGED DEALS -- Action Required
| Deal | Owner | CRM Stage | Evidence Stage | Confidence | Amount | Issue |
                                              (OVERSTAGED / UNDERSTAGED / STALE)

Detail per flagged deal:
[Deal] -- [OVERSTAGED / UNDERSTAGED / STALE]
  Current CRM stage · Evidence supports · Last conversation [N days ago]
  Key evidence (2-3 bullets citing specific conversation moments)
  Recommended action (the exact stage move to make and why)

CORRECTLY STAGED DEALS (summary)  ->  [N] deals correctly staged, no action
FORECAST IMPACT SUMMARY  ->  overstated $ / understated $ / net adjustment
```

## Edge cases

- **New deal with no conversations yet:** skip deals created in the last 3 days with no calls; too new to audit.
- **Deal with only email activity (no calls):** note no call data is available; recommend the rep log a call or update the stage manually. Do not validate a stage without conversation data.
- **Custom CRM stages:** if the org's stages do not match the standard six, query what stages exist and map the evidence criteria to them before auditing.
- **No deals found:** post a brief confirmation that the audit ran but found no active deals to analyze (confirms the agent is alive).

## Guardrails

- Read-only on CRM and recorder. The only write is the one channel message.
- Every stage call ties to CRM data or a specific conversation moment. No speculation presented as fact.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`deal-stage-clarity.activepieces.json`](./deal-stage-clarity.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger -> an `askAttention` step (pulls open deals, analyzes their calls, compares against the stage, writes the report) -> a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`deal-stage-clarity.json`](./deal-stage-clarity.json).

**Any other builder — pre-built for you** in [`deal-stage-clarity.builds/`](./deal-stage-clarity.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./deal-stage-clarity.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./deal-stage-clarity.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./deal-stage-clarity.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./deal-stage-clarity.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./deal-stage-clarity.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./deal-stage-clarity.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/revenue-operations/deal-stage-clarity.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`deal-stage-clarity.json`](./deal-stage-clarity.json) · [`deal-stage-clarity.activepieces.json`](./deal-stage-clarity.activepieces.json) (Attention). Other builders: [`deal-stage-clarity.builds/`](./deal-stage-clarity.builds/)._
