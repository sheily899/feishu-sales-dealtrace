# Churn Alert

> Weekly, evidence-backed read of every active customer at risk of churning: the signals behind each rating, grouped by severity, with one concrete retention action per account the CSM can run this week.

**Function:** Account Management · **Trigger:** scheduled (daily 07:00) · **Template id:** `AGTChurnAlert01`
**Files:** [`churn-alert.json`](./churn-alert.json) (Attention agent-builder template) · [`churn-alert.activepieces.json`](./churn-alert.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one structured retention report that:
1. Scopes the active-customer base (existing customers only, never live deals).
2. Fuses CRM health data, product usage trends, and conversation sentiment into one risk read per account.
3. Groups at-risk accounts by severity (High / Medium / Low) with the specific signals that drove each rating.
4. Gives each at-risk account one concrete, proactive retention action the CSM can take this week.

## When it fires

- **Type:** schedule. **Default:** `0 7 * * *` (daily 07:00, workspace timezone). **Lookback:** roughly the trailing 90 days of conversation history per account.
- The report covers ACTIVE customers, not live deals. The CSM is the rep-equivalent here; the customer is the account on the other side.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Active customer accounts (name, renewal date, health/success score, NPS, contract value, assigned CSM, open cases) | CRM | `query_records` |
| Each account's calls over the last ~90 days, in order | Call recorder | `search_calls` |
| Conversation signals per account (call frequency/drop, sentiment trend, unresolved issues, competitor mentions, dissatisfaction, expansion) | Call recorder + LLM | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `query_records` | Scope the active-customer set and read health signals | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `search_calls` | Find each account's recent calls | Attention `search_calls` | your recorder's API, or ingest exports via the [gtmsi adapters](../../docs/adapters.md) |
| `analyze_calls` | Score sentiment, engagement, and churn signals per account | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the report to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Scope the active customers.** `query_records`: list ACTIVE customer accounts (exclude open/live deals). For each, capture account name, renewal date, health/success score, NPS, contract value, assigned CSM, and any open support cases. This is the set you analyze.
2. **Pull conversation signals per account.** `search_calls` for each account's calls over roughly the last 90 days, then `analyze_calls` (batch up to 25 calls per request) to report per account: (1) call frequency and any drop versus the prior period, (2) average sentiment and the trend, (3) unresolved issues or open action items, (4) competitor or alternative mentions, (5) expressed dissatisfaction, (6) any expansion/upsell signals.
3. **Detect churn signals and assign severity.** Fuse the CRM health data, usage trends, and conversation signals. **HIGH:** multiple strong signals at once (usage down sharply AND negative sentiment, or a near-term renewal with no engagement and an open competitor mention). **MEDIUM:** one clear signal or a few mild ones (a single unresolved issue, a modest usage dip, or mixed sentiment). **LOW (monitor):** minor fluctuations or early signals, no immediate action needed.
4. **Write the per-account read:** the key risk drivers behind the rating, plus one specific proactive retention tactic the CSM can run this week. Anonymize company names with a stable alias per account rather than the real name.
5. **Compose and post** the report in the exact [Output](#output) format to the CS / account-management channel, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full signal checklist and severity rules) is the single source of truth in [`churn-alert.json`](./churn-alert.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
⚠️ Weekly Churn Risk Report -- Week of [date_range]

High-Risk Accounts:
1. [Account alias] -- [key risk indicators, e.g. "usage down 40%, negative sentiment last call"]
   Recommendation: [specific proactive step]

Medium-Risk Accounts:
1. [Account alias] -- [moderate risk summary]
   Recommendation: [suggested engagement action]

Low-Risk (Monitor):
1. [Account alias] -- [minor fluctuations or early signals]

Summary: [# of accounts by risk category]
Source: CRM health data, product usage, and conversation insights
```
Posted to the CS / account-management channel. Active customers only, not live deals.

## Edge cases

- **No active accounts in scope:** post a one-line confirmation that no active customers were found to analyze (confirms the agent is alive).
- **No at-risk accounts:** post "No churn signals detected this week. Customer base is stable." rather than an empty report.
- **Account with no calls:** rate from CRM health data only; note "no recent calls, engagement unknown" and recommend a manual check-in.
- **CRM health conflicts with the calls** (green score but negative sentiment): flag the discrepancy and trust the conversation evidence for the rating.
- **Single at-risk account:** still group it under its severity tier; the format does not change.

## Guardrails

- Read-only on CRM and recorder. The only write is the one channel message.
- Active customers only, never live deals. Every rating ties to CRM health data or a call signal; no speculation presented as fact.
- Anonymize account names with a stable alias per account.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`churn-alert.activepieces.json`](./churn-alert.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger → an `askAttention` step (scopes active accounts, analyzes their calls, rates churn risk, writes the report) → a Slack `send_channel_message`. On import, connect Attention, your CRM, and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`churn-alert.json`](./churn-alert.json).

**Any other builder — pre-built for you** in [`churn-alert.builds/`](./churn-alert.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./churn-alert.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./churn-alert.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./churn-alert.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./churn-alert.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./churn-alert.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./churn-alert.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/account-management/churn-alert.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`churn-alert.json`](./churn-alert.json) · [`churn-alert.activepieces.json`](./churn-alert.activepieces.json) (Attention). Other builders: [`churn-alert.builds/`](./churn-alert.builds/)._
