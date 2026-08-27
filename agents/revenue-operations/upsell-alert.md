# Upsell Alert

> Catches expansion signals the moment they surface on a customer call: budget, seats, new use cases, tier upgrades, or multi-year intent. It classifies the signal, confirms the speaker and account against the CRM, and posts one actionable alert to the team.

**Function:** Revenue Operations · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTUpsellAlert01`
**Files:** [`upsell-alert.json`](./upsell-alert.json) (Attention agent-builder template) · [`upsell-alert.activepieces.json`](./upsell-alert.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

For each analyzed customer call, produce at most one alert that:
1. Detects whether the call contains a real expansion or upsell signal.
2. Classifies it into a fixed taxonomy, backed by a verbatim quote.
3. Confirms the speaker and account against the CRM so it routes to the right owner.
4. Posts a tight alert naming the owner, the signal, the quote, and the recommended next move.

## When it fires

- **Type:** per call. Fires once when a customer conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (account, owner).
- Skip internal/non-customer calls (see Edge cases).

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (transcript + metadata: account, owner, attendees) | Call recorder | `search_calls` |
| Extracted expansion language and the speaker behind it (each with a quote) | LLM over the transcript | `analyze_calls` |
| The matched contact, account, current ACV, and owner | CRM | `query_records` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Fetch the analyzed call by id | Attention `search_calls` | recorder API, or the [dealtrace adapters](../../docs/adapters.md) over the export |
| `analyze_calls` | Detect and classify the expansion signal | `ask_attention` | an LLM step over the transcript |
| `query_records` | Confirm the speaker, account, ACV, and owner | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `send_message` | Post the alert to the team channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Retrieve and read the call.** `search_calls` by the trigger's call id, then `analyze_calls` to extract, each backed by a verbatim quote: attendees and roles, and any language about budget, seats, usage, new teams, new use cases, tier interest, or renewal timing, plus the context that says whether it is a genuine forward-looking signal. If the call is internal/non-customer, stop (see Edge cases).
2. **Classify the signal** into one primary type (plus secondaries if present) from this taxonomy, each needing direct evidence: **BUDGET-INCREASE, SEAT-GROWTH, NEW-USE-CASE, TIER-UPGRADE, MULTI-YEAR / RENEWAL-INTENT.** If no genuine signal, post the "no signal" note and stop.
3. **Confirm speaker and account.** `query_records` to match the contact, linked account, current ACV, and owner so the alert routes correctly. If unmatched, flag it but still post.
4. **Compose and post** the alert in the exact [Output](#output) format with a HIGH / MEDIUM / LOW confidence rating, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full taxonomy evidence rules and confidence guidance) is the single source of truth in [`upsell-alert.json`](./upsell-alert.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message (only when a signal is found):

```
Upsell Alert -- Expansion Signal Detected
Call: [title] -- [date] · Account: [company] | Owner: [rep] | Current ACV: $[X if known]

| Field | Value |   (signal type, secondary signals, speaker, confidence HIGH/MEDIUM/LOW)

What they said: > "[most revealing verbatim quote]"
Why it matters: [1-2 sentences on the opportunity and rough size if estimable]
Recommended next move: [specific action for the owner]
```

## Edge cases

- **Internal / non-customer call:** skip; post a one-line note that no signal was evaluated and why. Do not run the taxonomy.
- **No expansion signal present:** post a brief "reviewed [call], no expansion signal detected" so the team knows it was screened.
- **Speaker not matched in CRM:** still post, but flag "could not match speaker to a CRM contact, owner unconfirmed, verify the account."
- **Ambiguous / hypothetical language:** mark Confidence LOW and quote the exact words. Do not inflate a maybe into a commitment.
- **Signal contradicts CRM (e.g., account flagged churn-risk):** note the conflict so the owner reconciles it before acting.

## Guardrails

- Read-only on CRM and recorder. The only write is the one channel message.
- Every claim ties to a call quote or CRM data. No invented numbers, contacts, or intent.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`upsell-alert.activepieces.json`](./upsell-alert.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") -> an `askAttention` step that screens and classifies the signal from the call context -> a Slack `send_channel_message`. On import, connect your Attention and Slack accounts and fill the placeholders `<YOUR_ATTENTION_USER_ID>` and `<YOUR_SLACK_CHANNEL_ID>`.

**Any other builder — pre-built for you** in [`upsell-alert.builds/`](./upsell-alert.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./upsell-alert.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./upsell-alert.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./upsell-alert.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./upsell-alert.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./upsell-alert.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./upsell-alert.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/revenue-operations/upsell-alert.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`upsell-alert.json`](./upsell-alert.json) · [`upsell-alert.activepieces.json`](./upsell-alert.activepieces.json) (Attention). Other builders: [`upsell-alert.builds/`](./upsell-alert.builds/)._
