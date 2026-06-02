# Risk Watch

> After every analyzed call, evaluate it against the account's recent baseline for risk indicators, rate the severity, and post a tiered alert to the CS channel only when a real risk is present.

**Function:** Account Management · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTRiskWatch01`
**Files:** [`risk-watch.json`](./risk-watch.json) (Attention agent-builder template) · [`risk-watch.activepieces.json`](./risk-watch.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Turn each analyzed customer call into an account-risk read the CSM team can act on:
1. Evaluate the call against a fixed set of risk indicators (sentiment, engagement, competitors, escalation, usage, relationship).
2. Set each detection against the account's recent baseline to catch engagement drops and emerging patterns.
3. Rate severity (Critical / High / Medium) and alert only when a real risk is present, never noise.
4. Post an evidence-backed alert with concrete next actions to the CS channel.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (account, CSM/owner).
- It posts an alert only when at least one risk indicator is detected (see Edge cases).

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (transcript + metadata: participants, account, CSM/owner) | Call recorder | `search_calls` |
| The account's recent call history (last 30 days vs prior 30) for the baseline | Call recorder | `search_calls` |
| Risk signals: sentiment, unresolved issues, competitor mentions, escalation, usage challenges | LLM over the transcripts | `analyze_calls` |
| Account metadata not in the call: name, owner/CSM, contract value, renewal date, open cases | CRM | `query_records` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Fetch the analyzed call and the account's recent history | Attention `search_calls` | recorder API, or the [gtmsi adapters](../../docs/adapters.md) over the export |
| `analyze_calls` | Score risk indicators and the engagement-drop baseline | `ask_attention` | an LLM step over the transcripts |
| `query_records` | Enrich the alert with account metadata (owner, value, renewal, cases) | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `send_message` | Post the tiered alert to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one alert message, and only when a risk is detected.

## How it works (step by step)

1. **Retrieve the call.** `search_calls` by the trigger's call id, then `analyze_calls` to get the transcript, participants, account, and sentiment. If no transcript is available (failed recording), stop without alerting.
2. **Gather account context.** `search_calls` for the same account's recent history, then `analyze_calls` across those calls for the baseline: how many calls in the last 30 days versus the prior 30, the sentiment trend, and any unresolved issues, competitor mentions, or escalation requests. Use `query_records` to enrich with account metadata (owner/CSM, contract value, renewal date, open cases).
3. **Evaluate risk indicators** on the current call and the account context: **engagement drop** (fewer calls than the prior period, or key stakeholders absent), **negative sentiment** ("not happy", "frustrated", "reconsider"), **competitor mentions**, **escalation language** (manager/legal/SLA/termination), **usage challenges** (bugs, adoption struggles), **relationship risk** (champion leaving or gone silent, new stakeholder with no context).
4. **Assign severity.** **CRITICAL** (red): explicit cancellation/non-renewal/termination, active competitor evaluation, escalation to legal/exec threatened, or 2+ indicators at once. **HIGH** (orange): negative sentiment with an unresolved issue, engagement down 50%+, competitor mentioned in passing, or champion departure. **MEDIUM** (yellow): single mild frustration, minor engagement dip, a usage challenge the customer will work through, or one carried-over action item. If no indicators are detected, do NOT alert.
5. **Compose and post the alert** in the exact tiered [Output](#output) format with the indicators, their evidence quotes, the account context, and the recommended next actions, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full indicator definitions, severity rules, and per-tier alert formats) is the single source of truth in [`risk-watch.json`](./risk-watch.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single alert message, only when a risk is detected. The tier sets the format:

```
:red_circle: CRITICAL RISK ALERT -- [Account Name]
Severity · Detected on call (title/date, participants) · CSM/owner
Risk indicators found: <indicator>: "<quote/evidence>"  (one per line)
Account context: [X] calls in last 30 days (down from [Y]); sentiment trend
Recommended immediate actions: <numbered list>

:large_orange_circle: HIGH RISK -- [Account Name]   -> indicator(s) + evidence, context, 2 actions
:yellow_circle: MEDIUM RISK -- [Account Name]        -> single indicator + evidence, one suggested action
```
Posted to the account-risk / CS-alerts channel. The CSM is the rep-equivalent here; the customer is the account on the other side.

## Edge cases

- **No transcript** (failed recording): skip analysis, do not alert.
- **First-ever call for the account** (no prior calls): skip the engagement-drop check; evaluate only the current call's content.
- **Indicators span multiple tiers:** use the highest tier.
- **Duplicate alert:** do not re-alert the same account within 24 hours for identical indicators; if new, different indicators appear later the same day, send a follow-up that references the prior one.
- **No risk indicators:** send nothing (the agent stays silent when the account is healthy).

## Guardrails

- Read-only on CRM and recorder. The only write is the one channel alert, and only when warranted.
- Every indicator ties to a transcript quote or a baseline metric. No speculation presented as fact; no alert without an indicator.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`risk-watch.activepieces.json`](./risk-watch.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") → an `askAttention` step (evaluates the call against the account baseline and CRM metadata, rates severity, and drafts the alert) → a Slack `send_channel_message`. On import, connect your Attention, CRM, and Slack accounts and fill the placeholders `<YOUR_ATTENTION_USER_ID>` and `<YOUR_SLACK_CHANNEL_ID>`. The "alert only when a risk is present" rule lives in the operating prompt; add a downstream filter on the model output if your builder needs an explicit gate.

**Any other builder — pre-built for you** in [`risk-watch.builds/`](./risk-watch.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./risk-watch.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./risk-watch.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./risk-watch.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./risk-watch.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./risk-watch.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./risk-watch.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/account-management/risk-watch.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`risk-watch.json`](./risk-watch.json) · [`risk-watch.activepieces.json`](./risk-watch.activepieces.json) (Attention). Other builders: [`risk-watch.builds/`](./risk-watch.builds/)._
