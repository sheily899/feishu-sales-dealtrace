# Validate

> After every analyzed call, turn the conversation into proposed CRM field updates, DM the call owner a before/after review card, and write back only the fields the rep approves.

**Function:** Operations · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTValidate01`
**Files:** [`validate.json`](./validate.json) (Attention agent-builder template) · [`validate.activepieces.json`](./validate.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Turn each analyzed customer call into CRM updates the rep can approve in seconds:
1. Extract every CRM-impacting field from the conversation, each grounded in evidence (a quote, a timecode, a confidence score).
2. Read the current CRM state and build a per-field before/after diff.
3. DM the call owner a review card with per-field approval, never writing without explicit approval.
4. Write back only the fields the rep approves, then confirm. It never writes to the CRM unattended.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id, the call owner, and any known CRM record ids.
- Skip internal/non-customer calls (see Edge cases).

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (transcript + metadata: participants, emails, account, owner) | Call recorder | `search_calls` |
| Extracted CRM-impacting fields (stage, next steps, budget, timeline, competitors, pain) with confidence + evidence | LLM over the transcript | `analyze_calls` |
| Current Account/Contact/Opportunity field values and record ids | CRM | `query_records` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Fetch the analyzed call by id | Attention `search_calls` | recorder API, or the [gtmsi adapters](../../docs/adapters.md) over the export |
| `analyze_calls` | Extract CRM-impacting fields with confidence + evidence | `ask_attention` | an LLM step over the transcript |
| `query_records` | Read current CRM record state to build the diff | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `update_records` | Write the approved fields back to the CRM | CRM tool | your CRM's API/MCP |
| `send_direct_message` | DM the review card to the call owner | Slack/Teams tool | your chat tool's API/MCP |

This agent writes to the CRM **only on explicit rep approval**. Reads are non-destructive; the one write path is gated behind the review card.

## How it works (step by step)

1. **Retrieve and analyze the call.** `search_calls` by the trigger's call id, then `analyze_calls` to extract every CRM-impacting field, each backed by a verbatim quote and a confidence score where possible: participants and roles/emails (to resolve the Contact and the owner), the account and any domain, and deal signals (stage movement, next steps with owners/dates, budget or contract value, decision timeline, competitors named, pain points, commitments). Normalize values: dates to ISO, currency to the org default, picklists to canonical labels. Drop null/empty keys.
2. **Map to CRM fields and fetch current state.** Use a mapping table `{ intelligence_key -> { object, field, upsert_key? } }`. For each mapped field, resolve the target record and read its current value via `query_records`: Contact by participant email or provided ContactId, Account by domain or AccountId, Opportunity by provided OpportunityId (fallback: open opp(s) on the Account for the Contact; else propose a "Pending Validation" draft opp, do not create it until approved). Build a per-field diff of `{ current, proposed, confidence, evidence }`.
3. **Compose the review card and DM the call owner.** `send_direct_message` to the rep with a header ("Validate CRM Fields for <Account | Contact | Opportunity>"), a diff table (one row per field: Field | Current -> Proposed | Confidence% | Evidence quote+timecode), a link to the call, and clear actions: Approve & Push, Edit Fields, Skip (log reason), Remind me later (snooze 24h). Per-field checkboxes allow partial approval.
4. **Write to the CRM on approval (never before).** On approval or edit+approval, upsert in order Account -> Contact -> Opportunity (respect upsert_key), writing ONLY the approved/edited fields and leaving everything else untouched. Log a Call/Task/Activity summarizing the changes with a transcript link. On success, confirm with links to the updated records; on failure, surface the error with a retry (exponential backoff, max 3 attempts).
5. **Humanize (mandatory):** run the review-card message through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** skill before sending. No em dashes, no AI throat-clearing, no hype adjectives, one clear ask, keep the rep's real voice.

> The verbatim operating prompt (with the full mapping rules, diff format, and write order) is the single source of truth in [`validate.json`](./validate.json) under `template.agent.instructions`. This section is its readable summary.

## Output

The review card, delivered as a direct message to the call owner:

```
Validate CRM Fields for <record>
| Field | Current -> Proposed | Confidence | Evidence |
|-------|---------------------|------------|----------|
| <field> | <current> -> <proposed> | <X>% | "<quote @ timecode>" |
Actions: Approve & Push | Edit Fields | Skip | Remind me later
```
The CRM write happens only after the rep approves. Nothing is written unattended.

## Edge cases

- **No CRM-impacting fields detected:** DM "No CRM-impacting fields detected on this call." and stop.
- **Locked or picklist field:** validate the proposed value against allowed choices; if invalid, ask the rep to pick from the allowed values in Edit.
- **Multiple candidate records match:** show a chooser so the rep selects the right record before approval.
- **Internal / non-customer call:** skip; no review card.
- **Privacy:** include only the conversation snippets necessary to justify each field; respect workspace retention.
- **Snooze/reminder:** re-DM after the snooze window; close the loop after 3 unanswered reminders.

## Guardrails

- **No CRM write without approval.** The rep approves per field; only approved/edited fields are written.
- Every proposed field traces to a conversation quote, timecode, or confidence score; no invented values.
- Final **humanizer** pass on the review-card message: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`validate.activepieces.json`](./validate.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") → an `askAttention` step that extracts the CRM fields, reads current state, and builds the before/after review card → a Slack `send_direct_message` to the call owner. On import, connect your Attention, CRM, and Slack accounts and fill the placeholders `<YOUR_ATTENTION_USER_ID>` and `<REP_SLACK_USER_ID>`. Wire the CRM write step (Approve & Push) to your own CRM connection; the approval gate must sit in front of it.

**Any other builder — pre-built for you** in [`validate.builds/`](./validate.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./validate.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./validate.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./validate.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./validate.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./validate.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./validate.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/operations/validate.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`validate.json`](./validate.json) · [`validate.activepieces.json`](./validate.activepieces.json) (Attention). Other builders: [`validate.builds/`](./validate.builds/)._
