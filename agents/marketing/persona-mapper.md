# Persona Mapper

> After every analyzed call, map the personas on it (who they are, what they care about, where they sit in the buying group), translate that into concrete marketing opportunities, and post a concise persona brief for the marketing team to refine.

**Function:** Marketing · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTPersonaMapper01`
**Files:** [`persona-mapper.json`](./persona-mapper.json) (Attention agent-builder template) · [`persona-mapper.activepieces.json`](./persona-mapper.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Turn each analyzed call into a usable read on the buying group:
1. Map the personas on the call: their role (economic buyer, champion, technical evaluator, end user, blocker), grounded in what they actually said.
2. Pull each persona's goals, challenges, and marketing-relevant priorities from their own words.
3. Translate those into concrete marketing opportunities (messaging angles, segments, content gaps).
4. Deliver a skimmable persona brief, drafted for the marketing team and humanized before posting.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (account, owner).
- Skip internal/non-customer calls (see Edge cases).

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (transcript + who spoke, roles, departments) | Call recorder | `search_calls` / `get_call_details` |
| Extracted personas, priorities, and marketing-relevant needs | LLM over the transcript | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Fetch the analyzed call by id | Attention `search_calls` | recorder API, or the [dealtrace adapters](../../docs/adapters.md) over the export |
| `get_call_details` | Pull the full call record when needed | Attention `get_call_details` | recorder API |
| `analyze_calls` | Identify personas + extract priorities and marketing needs | `ask_attention` | an LLM step over the transcript |
| `send_message` | Post the persona brief to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one brief.

## How it works (step by step)

1. **Retrieve and read the call.** `search_calls` (or `get_call_details`) by the trigger's call id, then `analyze_calls` to identify every persona mentioned or speaking (title, department, inferred buyer role), pull each one's goals, challenges, and priorities, and map the buying-group shape (who influences, who decides, who uses the product). Back each read with evidence from the transcript.
2. **Translate into marketing opportunities.** Identify messaging angles that would resonate, segments worth targeting, content or campaign gaps, and positioning language the customer used. Detect both explicit and implicit needs (demand gen, messaging, attribution, brand, sales enablement).
3. **Compose the persona brief** in three sections (Personas Identified, Key Priorities, Opportunities for Marketing), neutral and insight-driven. Label inferred roles as inferred. Do not invent personas, titles, or priorities the call did not support.
4. **Humanize (mandatory):** run the draft through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** skill. No em dashes, no throat-clearing, no hype, keep a real human voice.
5. **Deliver** the brief to the marketing channel (default), or DM the marketing owner. This is a working draft for the team to refine, not a finished asset.

> The verbatim operating prompt is the single source of truth in [`persona-mapper.json`](./persona-mapper.json) under `template.agent.instructions`. This section is its readable summary.

## Output

```
Persona Mapper -- <call title / link>

Personas Identified:
- <Persona 1>: <role and focus, one line>
- <Persona 2>: <role and focus, one line>

Key Priorities:
- <Priority 1>
- <Priority 2>

Opportunities for Marketing:
- <Opportunity 1>
- <Opportunity 2>

Source: conversation analyzed on <date>
```
Posted to the marketing channel as a working draft for the team to refine.

## Edge cases

- **Internal / non-customer call:** skip; post a one-line note explaining why, no brief.
- **Single persona on the call:** map the one persona and note the buying group was single-threaded (a signal in itself).
- **Roles unclear:** infer carefully from context and label inferences as inferred, not stated.
- **No marketing-relevant priorities:** still list the personas, and say plainly that no clear marketing opportunity surfaced.
- **Large group call:** focus on the personas with real influence or airtime; do not list every attendee mechanically.

## Guardrails

- Read-only on the recorder. The only write is the one brief.
- Every persona and priority ties to evidence from the call; inferences are labeled as inferred.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`persona-mapper.activepieces.json`](./persona-mapper.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") -> an `askAttention` step that maps the personas and marketing priorities from the call context -> a Slack `send_channel_message`. On import, connect your Attention and Slack accounts and fill the placeholders `<YOUR_ATTENTION_USER_ID>` and `<YOUR_SLACK_CHANNEL_ID>`.

**Any other builder (n8n / Zapier / Make / LangGraph / custom):** wire it as:
1. **Trigger:** your recorder's "conversation analyzed" webhook (or poll for newly analyzed calls).
2. **Analyze step** (`analyze_calls`): identify personas and extract priorities + marketing needs from the transcript.
3. **Compose step** (LLM with the operating prompt) then **humanizer**.
4. **Deliver step** (`send_message`): post the brief to the marketing channel.

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/marketing/persona-mapper.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Machine-readable: [`persona-mapper.json`](./persona-mapper.json) · [`persona-mapper.activepieces.json`](./persona-mapper.activepieces.json) (Attention)._
