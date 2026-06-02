# Cross Team Handoff

> When an account transitions between teams (sales to implementation, implementation to CSM, CSM to support), produce one structured handoff so the receiving team starts with full context: deal background, the stakeholder map, every commitment made, open risks, and the next steps.

**Function:** Operations · **Trigger:** scheduled (hourly) / CRM stage or owner change · **Template id:** `AGTCrossTeamHO01`
**Files:** [`cross-team-handoff.json`](./cross-team-handoff.json) (Attention agent-builder template) · [`cross-team-handoff.activepieces.json`](./cross-team-handoff.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each run, post a handoff for every account that just transitioned that:
1. Detects the transition (a stage change, an owner change, or a handoff signal on a recent call).
2. Reconstructs the account from its full call history: deal context, stakeholder map, conversation highlights.
3. Lists every commitment the team made and separates fulfilled from outstanding.
4. Flags open items and risks the receiving team needs to know.
5. Gives a ranked list of next steps tied to the account's real context.

## When it fires

- **Type:** schedule. **Default:** `0 * * * *` (hourly, workspace timezone). **Lookback:** trailing 2 hours for the transition scan.
- **Alternative trigger:** if your CRM emits stage-change or owner-change events, fire per-account on the transition instead of polling. Resolve your real stages with `gtmsi crm-stages` rather than hardcoding labels. The hourly schedule is the portable default because every builder supports a clock.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Accounts that changed stage or owner in the window (account, prev/new stage, prev/new owner, deal value) | CRM | `query_records` |
| Recent calls carrying transition signals ("handoff", "kickoff", "passing to") | Call recorder | `search_calls` |
| The account's full call history (history, stakeholders, commitments) | Call recorder + LLM | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `query_records` | Read accounts that changed stage/owner | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `search_calls` | Find the account's calls and transition-signal calls | Attention `search_calls` | your recorder's API, or ingest exports via the [gtmsi adapters](../../docs/adapters.md) |
| `analyze_calls` | Build the stakeholder map, history, and commitment list from transcripts | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the handoff to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message per transitioned account.

## How it works (step by step)

1. **Detect transitions.** `query_records` for accounts whose opportunity stage or owner changed in the window. Also `search_calls` for recent calls with transition signals ("handoff", "transition", "kickoff", "onboarding", "passing to", "your new point of contact", "introducing you to"). Combine into the list of accounts needing a handoff. If none, send nothing (expected on most hourly runs).
2. **Reconstruct each account** from its calls in the last 90 days: a chronological call history (date, participants, topics, decisions, action items), a stakeholder map (name, title, role, disposition), and every commitment the team made with who, when, and fulfilled-or-outstanding status.
3. **Compose the handoff** in the exact [Output](#output) format.
4. **Post** to the receiving team's channel (`#implementations`, `#cs-team`, `#support-escalations`) and a general `#handoffs` channel for visibility, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt is the single source of truth in [`cross-team-handoff.json`](./cross-team-handoff.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message per account:

```
:arrow_right: Account Handoff Summary - [Account]
Transition: [prev owner/team] -> [new owner/team] · Deal value · Stage change · Handoff date

1. Deal Context            -> 2-3 sentences: what was sold, use case, why they bought
2. Stakeholder Map         -> table: Name | Title | Role | Disposition | Notes  (+ primary contact going forward)
3. Conversation History Highlights -> the 5-10 most important calls
4. Commitments and Promises Made   -> :white_check_mark: fulfilled · :hourglass: outstanding (flag overdue)
5. Open Items and Risks
6. Recommended Next Steps for [receiving team]  -> numbered, tied to account context
```

## Edge cases

- **No transitions in the window:** send nothing. This is expected for most hourly runs.
- **Transitioned account with no calls:** note "No call recordings found. Handoff context limited to CRM data. Recommend the previous owner provide a briefing."
- **Receiving team/channel unknown:** post to a general `#handoffs` channel and tag the new owner if identifiable.
- **Very large call history (20+):** summarize only the 10 most recent and note the rest are available in the recorder.
- **Commitment status unclear:** mark it ":question: Status unknown - verify with previous owner."

## Guardrails

- Read-only on CRM and recorder. The only write is the channel message(s).
- Every claim ties to CRM data or a call quote. No invented commitments, stakeholders, or dates.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`cross-team-handoff.activepieces.json`](./cross-team-handoff.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger -> an `askAttention` step (finds transitioned accounts, reconstructs each from its calls, writes the handoff) -> a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. Because the schema sample we modeled on was a per-call agent, confirm three things against a flow you export from your own workspace: (1) the schedule piece name/version, (2) the `askAttention` context scope for a cross-account/CRM query (we use `contextType: "user"`), and (3) the Slack channel-post action name. If your CRM emits stage/owner events, swap the schedule trigger for a transition trigger. The fully-managed alternative is to import the agent template [`cross-team-handoff.json`](./cross-team-handoff.json).

**Any other builder — pre-built for you** in [`cross-team-handoff.builds/`](./cross-team-handoff.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./cross-team-handoff.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./cross-team-handoff.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./cross-team-handoff.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./cross-team-handoff.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./cross-team-handoff.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./cross-team-handoff.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/operations/cross-team-handoff.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`cross-team-handoff.json`](./cross-team-handoff.json) · [`cross-team-handoff.activepieces.json`](./cross-team-handoff.activepieces.json) (Attention). Other builders: [`cross-team-handoff.builds/`](./cross-team-handoff.builds/)._
