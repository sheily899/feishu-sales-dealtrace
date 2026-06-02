# AE Handoff

> When a deal reaches Closed-Won, produce one structured handoff that gives the delivery or CS team full context: what was sold, who the stakeholders are, what the AE promised, the scope and integrations, the risks, and the next steps for kickoff.

**Function:** Operations · **Trigger:** scheduled (hourly) / CRM Closed-Won stage · **Template id:** `AGTAEHandoff01`
**Files:** [`ae-handoff.json`](./ae-handoff.json) (Attention agent-builder template) · [`ae-handoff.activepieces.json`](./ae-handoff.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Each time a deal closes won, post one structured handoff that:
1. Captures the commercial facts from the CRM (account, amount, term, close date, AE, CSM, products, custom fields).
2. Reconstructs the deal from its call history, not just the closing email.
3. Maps the stakeholders, the customer's goals, the scope and integrations, and the commitments the AE made.
4. Flags the risks and watchouts the delivery team needs before kickoff.
5. Gives 3-5 concrete next steps with owners so nothing the AE promised gets dropped.

## When it fires

- **Type:** schedule. **Default:** `0 * * * *` (hourly, workspace timezone). Each run picks up deals that reached Closed-Won since the last run.
- **Alternative trigger:** if your CRM emits stage-change events, fire per-deal on entry to a Closed-Won stage instead of polling. This is the better setup; resolve your real won stage with `gtmsi crm-stages` rather than hardcoding the label. The hourly schedule is the portable default because every builder supports a clock.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Deals that reached Closed-Won (name, account, amount, term, close date, AE owner, CSM owner, primary contact, opportunity team, products, custom fields) | CRM | `query_records` |
| All conversations tied to the won deal/account, in chronological order | Call recorder | `search_calls` |
| The content of those conversations (goals, commitments, technical detail, risks) | Call recorder + LLM | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `query_records` | Read Closed-Won opportunities and their fields | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `search_calls` | Find the calls linked to the deal/account | Attention `search_calls` | your recorder's API, or ingest exports via the [gtmsi adapters](../../docs/adapters.md) |
| `analyze_calls` | Reconstruct goals, commitments, scope, and risks from transcripts | `ask_attention` | an LLM step over the normalized transcripts |
| `send_message` | Post the handoff to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Identify the won deal.** `query_records`: opportunities that reached Closed-Won in the window. Capture name, account, amount, term, close date, AE owner, CSM owner, primary contact, opportunity team, products or line items, and custom fields like implementation tier, region, and segment. If none, post the "no closed-won deals" confirmation and stop.
2. **Pull the deal's call history.** `search_calls` for the opportunity, falling back to the account if no calls are linked to the opportunity directly. Sort chronologically.
3. **Extract the handoff content** from those calls: participants and roles, customer goals and pain points, decisions and AE commitments, technical details and integrations, and any timelines, blockers, or risk indicators. If conversation data is missing, add practical guidance ("review CRM notes", "schedule a follow-up with AE").
4. **Compose the handoff** in the exact [Output](#output) format, with the emoji section headers.
5. **Post** to the delivery/CS handoff channel and mention the AE and CSM, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt is the single source of truth in [`ae-handoff.json`](./ae-handoff.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
:tada: NEW CLOSED WON HANDOFF
:receipt: DEAL OVERVIEW           -> customer, what they bought, commercials
:busts_in_silhouette: KEY STAKEHOLDERS  -> Champion, Decision Maker, Technical Contact, AE, Implementation Lead (names + titles)
:dart: GOALS AND SUCCESS CRITERIA -> objectives and desired outcomes
:jigsaw: SCOPE AND INTEGRATIONS   -> products/services, systems, integrations, timelines
:handshake: COMMITMENTS OR SPECIAL TERMS -> promises, delivery expectations, non-standard agreements
:warning: RISKS AND WATCHOUTS     -> blockers, dependencies, misalignments
:rocket: NEXT STEPS               -> 3-5 kickoff actions, owners + dates
:paperclip: RESOURCES             -> links to CRM opp, linked calls, proposal/SOW

Generated by GTM Superintelligence | Opportunity ID: [ID] | [Date and Time UTC]
```
Posted to the delivery/CS handoff channel (e.g. `#deal-handoffs` or the account channel), mentioning the AE and CSM.

## Edge cases

- **No closed-won deals in the window:** post "AE Handoff ran for [range]. No deals reached Closed-Won." (confirms the agent is alive).
- **Won deal with no calls:** build the handoff from CRM data only; for the missing sections add guidance like "review CRM notes" or "schedule a follow-up with AE."
- **Calls linked to the account but not the opportunity:** use the account's calls and note that they were matched at the account level.
- **Missing CSM or implementation owner:** flag it in Key Stakeholders and recommend assigning one before kickoff.
- **Custom fields absent (tier/region/segment):** omit the line rather than guessing.

## Guardrails

- Read-only on CRM and recorder. The only write is the one channel message.
- Every claim ties to CRM data or a call quote. No invented commitments, numbers, or names.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`ae-handoff.activepieces.json`](./ae-handoff.activepieces.json). It follows Attention's export schema: a `@activepieces/piece-schedule` trigger -> an `askAttention` step (finds Closed-Won deals, reconstructs each from its calls, writes the handoff) -> a Slack `send_channel_message`. On import, connect Attention and Slack and fill `<YOUR_SLACK_CHANNEL_ID>`. The `@activepieces/piece-schedule` `cron_expression` trigger (v0.1.17) is verified against Activepieces. Confirm the rest against a flow you export from your own workspace: the `askAttention` context scope for a non-conversation query (we use `contextType: "user"`) and your output piece's action name. If your CRM emits stage events, swap the schedule trigger for a Closed-Won stage trigger. The fully-managed alternative is to import the agent template [`ae-handoff.json`](./ae-handoff.json).

**Any other builder — pre-built for you** in [`ae-handoff.builds/`](./ae-handoff.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./ae-handoff.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./ae-handoff.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./ae-handoff.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./ae-handoff.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./ae-handoff.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./ae-handoff.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/operations/ae-handoff.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`ae-handoff.json`](./ae-handoff.json) · [`ae-handoff.activepieces.json`](./ae-handoff.activepieces.json) (Attention). Other builders: [`ae-handoff.builds/`](./ae-handoff.builds/)._
