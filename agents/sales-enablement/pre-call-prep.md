# Pre-Call Prep

> Every morning, turn the rep's calendar into a per-meeting briefing: match each customer meeting to its CRM account and opportunity, reconstruct the deal from prior calls, and DM the rep a skimmable prep with a TL;DR, risks, recommended focus, and the materials to have ready.

**Function:** Sales Enablement · **Trigger:** scheduled (weekday mornings) · **Template id:** `AGTPreCallPrep01`
**Files:** [`pre-call-prep.json`](./pre-call-prep.json) (Attention agent-builder template) · [`pre-call-prep.activepieces.json`](./pre-call-prep.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each morning, produce one direct message that:
1. Lists every customer meeting on the rep's calendar that day, in chronological order.
2. Matches each meeting's attendees to a CRM account and the most relevant opportunity.
3. Reconstructs each deal from prior call-recorder conversations: history, sentiment trend, open items, objections, competitors, and commitments.
4. Writes a rich per-meeting briefing (TL;DR, attendee context, recent activity, risks, recommended focus, materials), delivered to the rep before the day starts.

## When it fires

- **Type:** schedule. **Default:** `0 7 * * 1-5` (weekday mornings, the rep's local time). **Window:** meetings that day between 7:00 AM and 7:00 PM.
- **Alternative trigger:** if your calendar emits event-created webhooks you could prep a single meeting on demand, but the morning digest is the default because it batches the whole day into one message the rep reads with their coffee.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Today's meetings (title, times, link/location, attendee names + emails) | Calendar | `list_events` |
| CRM account + most relevant opportunity per attendee (stage, amount, close date, forecast) | CRM | `query_records` |
| Summaries of the most recent 3-5 prior conversations per account/opportunity | Call recorder | `search_calls` |
| The detail behind a specific prior conversation (objection, commitment, next step) | Call recorder | `get_call_details` |
| The synthesized deal context and per-meeting briefing | Call recorder + LLM | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `list_events` | Read today's meetings and attendees | Calendar tool | Google/Microsoft Calendar API/MCP |
| `query_records` | Match attendees to an account + opportunity | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `search_calls` | Find prior conversations for the account/opportunity | Attention `search_calls` | your recorder's API, or ingest exports via the [gtmsi adapters](../../docs/adapters.md) |
| `get_call_details` | Pull the detail of a specific prior conversation | Attention `get_call_details` | your recorder's transcript fetch |
| `analyze_calls` | Synthesize deal context and write the briefing | `ask_attention` | an LLM step over the summaries |
| `send_direct_message` | DM the briefing to the rep | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data** (calendar, CRM, recorder). Its only side effect is the one direct message.

## How it works (step by step)

1. **Read the calendar.** `list_events` for today between 7:00 AM and 7:00 PM. For each meeting capture title, start/end, link or location, and every attendee name and email.
2. **Match to the CRM.** `query_records` to map attendee emails / company domains to an account and the most relevant opportunity (prefer open; else the most recent closed). Capture stage, amount, close date, forecast category.
3. **Reconstruct the deal.** `search_calls` for prior conversations on the matched account/opportunity; summarize the most recent 3-5 (date and type, participants and roles, topics, objections, competitor mentions, next steps, sentiment trend, commitments). Use `get_call_details` when you need the exact wording of an objection or commitment.
4. **Write the per-meeting briefing:** a short human-style TL;DR (where the deal stands, why today matters), attendee context, relationship summary, opportunity context, recent activity recap, risks or challenges, competitive landscape, recommended focus for today, strategic tips, and useful artifacts.
5. **Deliver** the whole day as one direct message to the rep, in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full per-meeting checklist and message structure) is the single source of truth in [`pre-call-prep.json`](./pre-call-prep.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single direct message, one block per meeting, in chronological order. Use emojis and clean headings; no markdown bold or `*` symbols.

```
📅 10:30 AM -- Acme Corp
Attendees: John Doe (CFO), Sarah Green (Director of IT)
Opportunity: Enterprise renewal -- Stage: Negotiation -- Amount: $150,000 -- Close Date: 2024-11-05

TL;DR: ...
Recent Activity: ...
Risks and Challenges: ...
Recommended Focus for Today: ...
Helpful Materials: ...
```

If there are no customer meetings that day: "Good morning! You have no customer meetings on your calendar today."

## Edge cases

- **No meetings today:** send the one-line "no customer meetings" note.
- **Attendee matches no CRM record:** include the meeting with what the calendar knows; note "no CRM match" so the rep can link it.
- **Account matched but no prior calls:** brief from CRM context only; note there is no conversation history yet.
- **Multiple open opportunities on one account:** pick the one whose stage/close date best fits the meeting; list the others briefly.
- **Internal / non-customer meeting:** skip it; do not generate a deal briefing.

## Guardrails

- Read-only on calendar, CRM, and recorder. The only write is the one direct message to the rep.
- Every fact in the briefing comes from the calendar, CRM, or a prior call. No invented context.
- The message uses no markdown bold; emojis and headings only.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`pre-call-prep.activepieces.json`](./pre-call-prep.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger → an `askAttention` step (reads today's calendar, matches meetings to CRM accounts/opportunities, reconstructs each deal from prior calls, writes the briefing) → a Slack `send_direct_message` to the rep. On import, connect Attention and Slack and fill `<REP_SLACK_USER_ID>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`pre-call-prep.json`](./pre-call-prep.json).

**Any other builder — pre-built for you** in [`pre-call-prep.builds/`](./pre-call-prep.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./pre-call-prep.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./pre-call-prep.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./pre-call-prep.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./pre-call-prep.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./pre-call-prep.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./pre-call-prep.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/sales-enablement/pre-call-prep.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`pre-call-prep.json`](./pre-call-prep.json) · [`pre-call-prep.activepieces.json`](./pre-call-prep.activepieces.json) (Attention). Other builders: [`pre-call-prep.builds/`](./pre-call-prep.builds/)._
