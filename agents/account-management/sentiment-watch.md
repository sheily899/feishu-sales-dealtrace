# Sentiment Watch

> After every analyzed call, decide whether it hit an emotional extreme (highly positive or highly negative) and, if so, alert the account owner with the proving quote so a human can follow up. Routine calls stay silent.

**Function:** Account Management · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTSentiment01`
**Files:** [`sentiment-watch.json`](./sentiment-watch.json) (Attention agent-builder template) · [`sentiment-watch.activepieces.json`](./sentiment-watch.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Turn each analyzed call into a fast, evidence-backed signal of emotional risk or opportunity:
1. Catch calls that swing to a positive or negative extreme the moment they finish analyzing.
2. Ground every flag in a sentiment read plus the verbatim quote that proves it.
3. Route the alert to the account owner so a human decides whether to save, intervene, or amplify.
4. Stay quiet on routine, neutral, or merely polite calls. A low false-positive rate is the point.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (account, owner).
- It only alerts on extremes. Neutral calls produce no message (see Edge cases).

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (transcript + metadata: account, owner, attendees) | Call recorder | `search_calls` / `get_call_details` |
| Overall and customer sentiment, top emotion tags, the driving quote | LLM over the transcript | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Fetch the analyzed call by id | Attention `search_calls` | recorder API, or the [gtmsi adapters](../../docs/adapters.md) over the export |
| `get_call_details` | Pull the full call record when needed | Attention `get_call_details` | recorder API |
| `analyze_calls` | Read sentiment, emotion tags, and the proving quote | `ask_attention` | an LLM step over the transcript |
| `send_direct_message` | DM the alert to the account owner | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one alert, and only on an extreme.

## How it works (step by step)

1. **Retrieve and read the call.** `search_calls` (or `get_call_details`) by the trigger's call id, then `analyze_calls` to read overall and customer sentiment, the top emotion tags, attendees and roles (customer vs rep / owner), and the single most revealing quote, verbatim.
2. **Classify the sentiment:** **HIGHLY POSITIVE** (strong satisfaction, delight, advocacy, specific praise tied to a result), **HIGHLY NEGATIVE** (strong frustration, churn risk, escalation, threats to cancel), or **NEUTRAL** (routine working tone, polite thanks, logistics). Routine politeness does not qualify. When in doubt, treat as neutral.
3. **Pick recipient and channel.** Default: DM the account owner. Use a team channel (e.g. #cs-alerts) if configured and @mention the owner. Never message the customer.
4. **Compose the alert:** polarity + account, a 1-2 sentence "why" tied to the call, the verbatim quote, one concrete suggested next step, and the call link.
5. **Humanize (mandatory):** run the draft through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** skill. No em dashes, no throat-clearing, no hype, one clear ask, keep the sender's real voice.

> The verbatim operating prompt is the single source of truth in [`sentiment-watch.json`](./sentiment-watch.json) under `template.agent.instructions`. This section is its readable summary.

## Output

```
Sentiment: <POSITIVE | NEGATIVE>
Account: <account> -- Owner: <rep>
Why: <1-2 sentences tied to the call>
Quote: "<verbatim customer quote>"
Suggested next step: <one concrete action>
Call: <link>
```
Delivered as a direct message to the account owner (or a channel + @mention), only when the call hit an extreme.

## Edge cases

- **Neutral / routine call:** send nothing. Silence on a non-extreme call is correct behavior.
- **Internal / non-customer call:** skip; no alert.
- **Mixed sentiment in one call:** flag the dominant extreme; note the other in one line.
- **Extreme sentiment but no clear owner:** post to the team channel and ask who owns the account.
- **Sentiment read conflicts with the quotes:** trust the verbatim quotes; if neither is clearly extreme, stay quiet.

## Guardrails

- Read-only on the recorder. The only write is the one alert message, and only on an extreme.
- Every flag ties to a sentiment read and a verbatim quote. No speculation presented as fact.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`sentiment-watch.activepieces.json`](./sentiment-watch.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") -> an `askAttention` step that reads the sentiment and decides whether it is an extreme -> a Slack `send_direct_message`. On import, connect your Attention and Slack accounts and fill the placeholders `<YOUR_ATTENTION_USER_ID>` and `<REP_SLACK_USER_ID>`.

**Any other builder (n8n / Zapier / Make / LangGraph / custom):** wire it as:
1. **Trigger:** your recorder's "conversation analyzed" webhook (or poll for newly analyzed calls).
2. **Analyze step** (`analyze_calls`): read sentiment, emotion tags, and the driving quote.
3. **Classify + compose step** (LLM with the operating prompt) then **humanizer**. If neutral, exit without sending.
4. **Deliver step** (`send_direct_message`): DM the account owner. Never connect a "message the customer" action.

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/account-management/sentiment-watch.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Machine-readable: [`sentiment-watch.json`](./sentiment-watch.json) · [`sentiment-watch.activepieces.json`](./sentiment-watch.activepieces.json) (Attention)._
