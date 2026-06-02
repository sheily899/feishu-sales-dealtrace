# Team Collab Agent

> After every analyzed customer call, check the transcript against routing rules for six internal teams and post a targeted alert to each team that is genuinely needed, with the quotes that prove it and a suggested next step. Stay silent when the rep already handled it.

**Function:** Operations · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTTeamCollab01`
**Files:** [`team-collab-agent.json`](./team-collab-agent.json) (Attention agent-builder template) · [`team-collab-agent.activepieces.json`](./team-collab-agent.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Turn each analyzed customer call into routing decisions that:
1. Scan for signals that another team (SE, legal, finance, professional services, product, or executives) is needed.
2. Route a separate, targeted alert to each team that is genuinely needed, with the quotes that prove it.
3. Give each team a specific suggested next step and an urgency level.
4. Stay silent when the rep already resolved the question, so alerts only fire on real follow-up needs.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (account, deal stage, rep).
- Skip internal/non-customer calls (see Edge cases).

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (full transcript + metadata: participants, account, deal stage, rep) | Call recorder | `get_call_details` |
| The routing decisions (which teams, the quotes, the next step) | LLM over the transcript | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `get_call_details` | Fetch the analyzed call's transcript by id | Attention `get_call_details` | recorder API, or the [gtmsi adapters](../../docs/adapters.md) over the export |
| `analyze_calls` | Check against the routing rules and pick the teams | `ask_attention` | an LLM step over the transcript |
| `send_message` | Post each alert to the relevant team channel | Slack/Teams tool | your chat tool's API/MCP |

## How it works (step by step)

1. **Retrieve the call.** `get_call_details` by the trigger's call id: full transcript, participants, account name, deal stage, rep name.
2. **Scan against the per-team routing rules:** Sales Engineering / Solutions, Legal, Finance / Deal Desk, Professional Services / Implementation, Product, Executive / Leadership. A single call can trigger several teams. Do not flag a team if the rep already fully resolved the question on the call.
3. **Compose one alert per needed team** in the exact [Output](#output) format, each with the customer quote(s), a suggested next step, and an urgency level.
4. **Route** each alert to that team's channel (`#se-requests`, `#legal-reviews`, `#deal-desk`, `#ps-requests`, `#product-feedback`, `#exec-alerts`). If a team's channel is unknown, default to `#collaboration-requests` and name the team.
5. **No signals:** send nothing.

Run each alert through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** skill before posting.

> The verbatim operating prompt (with the full per-team trigger rules) is the single source of truth in [`team-collab-agent.json`](./team-collab-agent.json) under `template.agent.instructions`. This section is its readable summary.

## Output

One alert per needed team, sent only when that team is genuinely needed:

```
:handshake: Cross-Team Collaboration Needed - [Team]
Account: [name] · Deal stage: [stage or N/A] · Call: [title/date] · Rep: [name]

Why [Team] is needed: [1-2 sentences]
Key quotes:
- "[customer quote]"
- "[rep response, if relevant]"
Suggested next step: [specific action]
Urgency: [High - customer is blocked / Medium - needed before next meeting / Low - informational]
```

## Edge cases

- **Multiple teams needed:** send a separate alert to each relevant team. Do not combine into one message.
- **Internal / non-customer call:** skip analysis.
- **Rep already resolved it on the call:** do not alert. Only fire when the need is unresolved or requires follow-up.
- **No signals:** send nothing.
- **Channel unknown:** default to a general `#collaboration-requests` channel and note which team should pick it up.

## Guardrails

- **Alerts only, to internal channels.** Never contacts the customer.
- Every alert is backed by a verbatim transcript quote. No invented requests or quotes.
- Silent on calls with no unresolved cross-team need, so alerts carry signal.
- Mandatory **humanizer** pass before posting.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`team-collab-agent.activepieces.json`](./team-collab-agent.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") -> an `askAttention` step that checks the routing rules -> a Slack `send_channel_message`. On import, connect your Attention and Slack accounts and fill the placeholders `<YOUR_ATTENTION_USER_ID>` and `<YOUR_SLACK_CHANNEL_ID>`. The detect step emits `NO_SIGNALS` when no team is needed; add a filter before the post step so silent calls stay silent. Because one call can route to several teams, duplicate the post step (one per team channel) and route each team's block to its channel, or fan out on the detect step's output.

**Any other builder (n8n / Zapier / Make / LangGraph / custom):** wire it as:
1. **Trigger:** your recorder's "conversation analyzed" webhook (or poll for newly analyzed calls).
2. **Retrieve step** (`get_call_details`): fetch the transcript and metadata.
3. **Routing step** (LLM with the operating prompt): pick the teams and write a block per team; emit nothing when no team is needed.
4. **Deliver step(s)** (`send_message`): post each block to its team channel, after the humanizer pass.

The agent logic does not change between platforms. Only the bound connectors do.

---
_From GTM Superintelligence agent templates. Machine-readable: [`team-collab-agent.json`](./team-collab-agent.json) · [`team-collab-agent.activepieces.json`](./team-collab-agent.activepieces.json)._
