# Competitor Ping

> After every analyzed call, scan it for competitor mentions and post one structured intelligence alert: who came up, how, the strengths and weaknesses cited, the win/loss risk, and what the team should do about it.

**Function:** Revenue Operations · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTCompetitorPing01`
**Files:** [`competitor-ping.json`](./competitor-ping.json) (Attention agent-builder template) · [`competitor-ping.activepieces.json`](./competitor-ping.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

For each analyzed call, produce competitive intelligence the team can act on:
1. Catch every competitor mention while the intel is fresh, the moment the call is analyzed.
2. Classify how each competitor came up and the sentiment toward it.
3. Capture the strengths and weaknesses the prospect cited, grounded in quotes.
4. Rate win/loss risk and note how the rep handled it, then give 2-3 next actions.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (deal, rep).
- **Silent by default:** if no competitor is mentioned in a competitive or evaluative context, the agent sends nothing. An alert means real competitive intel was found.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (transcript, attendees/roles, deal/account, rep, date) | Call recorder | `get_call_details` |
| Other recent calls (manual/backfill runs) | Call recorder | `search_calls` |
| The list of known/tracked competitors and positioning | Organization context | provided to the prompt |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `get_call_details` | Fetch the analyzed call by id (transcript + metadata) | Attention `get_call_details` | recorder API, or the [gtmsi adapters](../../docs/adapters.md) over the export |
| `search_calls` | Find recent calls on a manual or backfill run | Attention `search_calls` | recorder API / exports |
| `analyze_calls` | Detect mentions and extract the intelligence from the transcript | the model over the call | an LLM step over the transcript |
| `send_message` | Post the alert to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message (and only when competitors are detected).

## How it works (step by step)

1. **Retrieve the conversation.** `get_call_details` with the call id from the trigger payload; pull the full transcript, attendees, deal name, and rep. On a manual/backfill run, `search_calls` over the last 7 days and process each call.
2. **Detect competitor mentions.** Scan for explicit competitor names, implicit references ("another vendor", "the other tool we're looking at", "the incumbent"), and competitor product references. Check the Organization competitor list; a company not on it is a NEW competitor to verify. If none in a competitive context, stop and send nothing.
3. **Extract structured intelligence per competitor:** mention context (PROSPECT-INITIATED / REP-INITIATED / ACTIVE-EVALUATION / INCUMBENT / PAST-USER), strengths cited (with quotes), weaknesses cited (with quotes), prospect sentiment toward the competitor (POSITIVE / NEUTRAL / NEGATIVE), the rep's positioning response and whether it landed, and win/loss risk (HIGH / MODERATE / LOW).
4. **Compose and post** the alert in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full context and risk rules) is the single source of truth in [`competitor-ping.json`](./competitor-ping.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message (only when competitors are detected):

```
Competitor Ping -- Competitive Intelligence Alert
| Deal | Rep | Call Date | Competitors Detected |   (header table)

(per competitor)
[Competitor] -- [ACTIVE-EVALUATION / INCUMBENT / PROSPECT-INITIATED / ...]
  Win/Loss Risk [HIGH/MODERATE/LOW] · Prospect Sentiment [POSITIVE/NEUTRAL/NEGATIVE]
  Strengths cited · Weaknesses cited · Rep's positioning response
  Key quote: > "[most revealing prospect quote about the competitor]"

RECOMMENDED ACTIONS  ->  2-3 concrete moves (battlecard, bake-off, switcher case study)
```

## Edge cases

- **No competitor mentions:** send nothing. Silence is the expected state for most calls.
- **Mention only in passing** (e.g. "I used to work at [Competitor]"): do not flag; report only competitive/evaluative mentions.
- **Multiple competitors in one call:** one intelligence block per competitor inside the same alert.
- **Unknown company as a competitor:** still report it, noted as "New competitor detected, not in current list, verify and consider adding."
- **Internal call (no prospect):** still extract the intel but label the source INTERNAL-DISCUSSION, not a prospect conversation.

## Guardrails

- Read-only on the recorder. The only write is the one channel message, and only when there is something to report.
- Every strength, weakness, and risk call ties to a transcript quote. No invented competitor claims.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`competitor-ping.activepieces.json`](./competitor-ping.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") -> an `askAttention` step that scans the call context for competitors and writes the alert -> a Slack `send_channel_message`. On import, connect your Attention and Slack accounts and fill `<YOUR_ATTENTION_USER_ID>` and `<YOUR_SLACK_CHANNEL_ID>`. The fully-managed alternative is to import the agent template [`competitor-ping.json`](./competitor-ping.json).

**Any other builder — pre-built for you** in [`competitor-ping.builds/`](./competitor-ping.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./competitor-ping.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./competitor-ping.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./competitor-ping.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./competitor-ping.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./competitor-ping.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./competitor-ping.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/revenue-operations/competitor-ping.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`competitor-ping.json`](./competitor-ping.json) · [`competitor-ping.activepieces.json`](./competitor-ping.activepieces.json) (Attention). Other builders: [`competitor-ping.builds/`](./competitor-ping.builds/)._
