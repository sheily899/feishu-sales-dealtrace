# Renewal Countdown

> Weekly tiered digest of every upcoming renewal across 30/60/90-day horizons, each with a health read from the account's recent calls and a prep action sized to its risk and timeline.

**Function:** Account Management · **Trigger:** scheduled (daily 07:00) · **Template id:** `AGTRenewalCount01`
**Files:** [`renewal-countdown.json`](./renewal-countdown.json) (Attention agent-builder template) · [`renewal-countdown.activepieces.json`](./renewal-countdown.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce one tiered renewal digest that:
1. Surfaces every upcoming renewal across the 30/60/90-day horizons before it becomes urgent.
2. Attaches a health read to each renewal from the account's recent call history, not just the CRM date.
3. Flags the at-risk renewals (low engagement, negative sentiment, competitor mentions) so teams prioritize them.
4. Gives each renewal a concrete prep action sized to its health and time horizon.

## When it fires

- **Type:** schedule. **Default:** `0 7 * * *` (daily 07:00, workspace timezone). **Horizons:** renewals due in the next 30 / 60 / 90 days. **Lookback per account:** roughly the trailing 90 days of calls.
- **Renewal date resolution:** resolve the real renewal-date field in your CRM (use `dealtrace crm-fields` or your CRM's schema) rather than hardcoding a label. The CSM is the rep-equivalent here; the customer is the account on the other side.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Accounts with renewals in the next 30/60/90 days (name, renewal date, contract value, assigned CSM/owner, last-call date) | CRM | `query_records` |
| Each renewing account's calls over the last ~90 days | Call recorder | `search_calls` |
| Health signals per account (call count, sentiment trend, unresolved issues, competitor mentions, expansion) | Call recorder + LLM | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `query_records` | Build the renewal pipeline across the 30/60/90-day horizons | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `search_calls` | Find each renewing account's recent calls | Attention `search_calls` | your recorder's API, or ingest exports via the [dealtrace adapters](../../docs/adapters.md) |
| `analyze_calls` | Grade each renewal HEALTHY / AT RISK / CRITICAL from its calls | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the digest to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Identify upcoming renewals.** `query_records`: accounts with renewal dates in the next 30, 60, and 90 days. For each, capture account name, renewal date, contract value (ARR/ACV), assigned CSM/owner, and the date of the most recent customer call. This is the renewal pipeline.
2. **Assess customer health per account.** `search_calls` for each account's calls over the last 90 days, then `analyze_calls` (batch up to 25 per request) to report: total calls, average sentiment, unresolved issues or open action items, competitor or alternative mentions, expansion/upsell signals, and any dissatisfaction.
3. **Grade each renewal.** **HEALTHY** (green): 3+ calls in the last 90 days, mostly positive sentiment, no unresolved issues, no competitor mentions. **AT RISK** (yellow): 1-2 calls, OR mixed sentiment, OR 1+ unresolved issues. **CRITICAL** (red): 0 calls in 90 days, OR a negative sentiment trend, OR competitor mentions, OR explicit dissatisfaction.
4. **Size a prep action to the health and horizon.** CRITICAL: schedule an urgent check-in this week and review unresolved issues before outreach. AT RISK: send a value-recap and schedule a renewal discussion within two weeks. HEALTHY: prepare the renewal proposal with expansion options and confirm stakeholder alignment.
5. **Compose and post** the digest in the exact [Output](#output) format (30 / 60 / 90-day sections) to the renewals / account-management channel, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full health-grade thresholds and per-tier prep actions) is the single source of truth in [`renewal-countdown.json`](./renewal-countdown.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Renewal Countdown -- Weekly Digest

30-DAY RENEWALS (Immediate Action Required)
[Account Name] | Renews: [DATE] | Value: [ARR/ACV] · Owner: [CSM/AE]
  Health: [HEALTHY / AT RISK / CRITICAL]
  Recent engagement: [X] calls in last 90 days, last call [DATE]
  Risk factors: [low engagement, negative sentiment, competitor mentions, unresolved issues -- or "None identified"]
  Prep actions: [sized to health + horizon]

60-DAY RENEWALS (Begin Preparation)   -> same format per account
90-DAY RENEWALS (On the Radar)        -> same format per account

Summary: [X] renewals in next 30 days ([Y] critical), [Z] in 60 days, [W] in 90 days.
```
Posted to the renewals / account-management channel.

## Edge cases

- **No renewals in any horizon:** post "No upcoming renewals in the next 90 days. Next scan scheduled for [next run date]."
- **No call data for an account:** mark health CRITICAL with "No recorded calls found, engagement status unknown. Immediate outreach recommended."
- **Renewal date in the past, not marked renewed:** flag it separately under an "OVERDUE -- Needs Status Update" section.
- **Contract value missing:** show "Value: Not available, check your CRM."
- **Single renewal:** still place it under its horizon section; the format does not change.

## Guardrails

- Read-only on CRM and recorder. The only write is the one channel message.
- Resolve the real renewal-date field rather than hardcoding a label. Every health grade ties to a call count or a conversation signal; no speculation presented as fact.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`renewal-countdown.activepieces.json`](./renewal-countdown.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger → an `askAttention` step (builds the 30/60/90-day renewal pipeline, grades each account's health from its calls, writes the digest) → a Slack `send_channel_message`. On import, connect Attention, your CRM, and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`renewal-countdown.json`](./renewal-countdown.json).

**Any other builder — pre-built for you** in [`renewal-countdown.builds/`](./renewal-countdown.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./renewal-countdown.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./renewal-countdown.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./renewal-countdown.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./renewal-countdown.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./renewal-countdown.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./renewal-countdown.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/account-management/renewal-countdown.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`renewal-countdown.json`](./renewal-countdown.json) · [`renewal-countdown.activepieces.json`](./renewal-countdown.activepieces.json) (Attention). Other builders: [`renewal-countdown.builds/`](./renewal-countdown.builds/)._
