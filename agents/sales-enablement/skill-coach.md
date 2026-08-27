# Skill Coach

> Weekly per-rep coaching: evaluate five core selling skills from the rep's calls, flag each gap with the exact call moment and what to do instead, and assign one ready-to-run coaching exercise a manager can hand off.

**Function:** Sales Enablement · **Trigger:** scheduled (weekly, Monday 08:00) · **Template id:** `AGTSkillCoach01`
**Files:** [`skill-coach.json`](./skill-coach.json) (Attention agent-builder template) · [`skill-coach.activepieces.json`](./skill-coach.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, produce targeted coaching that:
1. Evaluates each rep across five core selling skills and detects concrete gaps from transcript evidence.
2. Ties every gap to a specific call moment (what happened, what the rep should have done instead), never a generic critique.
3. Assigns one concrete, ready-to-run coaching exercise per gap that a manager can hand off immediately.
4. Sends one alert per rep with a gap, and rolls the no-gap reps into a clean summary.

## When it fires

- **Type:** schedule. **Default:** `0 8 * * 1` (Monday 08:00, workspace timezone). **Lookback:** trailing 7 days.
- **Alternative trigger:** run it on demand after a big week of calls, or change the cadence by editing the cron. Weekly is the default so each rep has enough calls for a fair read before a manager gets pinged.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Each rep's conversations in the window | Call recorder | `search_calls` |
| The exact call moment behind each flagged gap | Call recorder | `get_call_details` |
| The content of those conversations (to evaluate the five skills) | Call recorder + LLM | `analyze_calls` |
| The rep roster and managers, to route each alert | Organization | `search_calls` metadata |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Find each rep's calls in the window | Attention `search_calls` | your recorder's API, or ingest exports via the [dealtrace adapters](../../docs/adapters.md) |
| `get_call_details` | Pull the exact coaching moment from a specific call | Attention `get_call_details` | your recorder's transcript fetch |
| `analyze_calls` | Evaluate the five selling skills per rep | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the coaching alerts to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message per flagged rep.

## How it works (step by step)

1. **Retrieve calls.** `search_calls` for the trailing 7 days; group by rep and collect each rep's call ids (up to 25 per analysis request). If a rep has fewer than 2 calls, note "Limited data" and only flag high-confidence gaps.
2. **Evaluate five skills per rep** and decide proficient (no alert) or gap (alert): **Discovery Depth, Presentation Clarity, Objection Recovery, Rapport Building, Closing Technique.**
3. **Extract the coaching moment.** For each gap, use `get_call_details` to pull one specific moment: the call name/date, a paraphrase of what happened, and what the rep should have done instead.
4. **Assign a coaching exercise** per gap, concrete and ready to run (e.g. Discovery Depth -> role-play the 5-Whys to reach financial impact within 5 follow-ups; Closing -> end every call with a calendar invite before hanging up).
5. **Send manager alerts:** one message per rep with at least one gap (up to 3 gap blocks per rep), plus a short "No coaching gaps detected" summary for the rest.
6. **Compose and post** in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full skill definitions and gap indicators) is the single source of truth in [`skill-coach.json`](./skill-coach.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message (one block per flagged rep):

```
Weekly Coaching Alert -- [date range]

Rep: [Rep Name] · Calls reviewed: [N]
Skill Gap: [skill]
What happened: on the [date] call with [account], [the coaching moment]
Better move: [what the rep should have done]
Coaching exercise: [specific exercise for the manager to assign]
(repeat the gap block, up to 3 per rep)

No Gaps Detected: [reps with no coaching flags this week]
```

## Edge cases

- **Rep with fewer than 2 calls:** note "Limited data -- coaching assessment based on [n] call(s)" and only flag high-confidence gaps.
- **No gaps for a rep:** do not send an alert; include them in the "No coaching gaps detected" summary.
- **No calls for any rep:** post a single message "No calls recorded this week. Coaching alerts skipped." and stop.
- **More than 3 gaps for one rep:** cap at the 3 highest-impact gaps so the alert stays actionable.

## Guardrails

- Read-only on the recorder. The only write is the coaching messages.
- Every gap, moment, and better-move ties to a specific call and quote. No speculation presented as fact.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`skill-coach.activepieces.json`](./skill-coach.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger → an `askAttention` step (pulls the week's calls per rep, evaluates five skills, flags gaps with a moment and an exercise) → a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. The fully-managed alternative is to import the agent template [`skill-coach.json`](./skill-coach.json).

**Any other builder — pre-built for you** in [`skill-coach.builds/`](./skill-coach.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./skill-coach.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./skill-coach.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./skill-coach.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./skill-coach.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./skill-coach.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./skill-coach.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/sales-enablement/skill-coach.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`skill-coach.json`](./skill-coach.json) · [`skill-coach.activepieces.json`](./skill-coach.activepieces.json) (Attention). Other builders: [`skill-coach.builds/`](./skill-coach.builds/)._
