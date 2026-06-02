# Case Builder

> After every analyzed sales call, build a structured business case the rep can send to the buying committee: current-state pain, desired outcomes, solution mapping, investment, ROI/payback, and risks, each grounded in what was actually said on the call.

**Function:** Sales · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTCaseBuilder01`
**Files:** [`case-builder.json`](./case-builder.json) (Attention agent-builder template) · [`case-builder.activepieces.json`](./case-builder.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Turn each substantive sales call into a business case the rep can refine and share in minutes:
1. Quantifies the cost of inaction and estimates ROI and payback from numbers the prospect actually stated.
2. Maps each product capability discussed to the specific pain it resolves.
3. Flags every section the call did not cover, so nothing is silently invented.
4. Written so it reads like the rep wrote it (mandatory humanizer pass). It never sends to the customer automatically.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (account, owner).
- Skips intro, scheduling, and low-content calls (see Edge cases). Only builds a case when there is substantive business discussion.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (transcript + metadata: account, owner, participants) | Call recorder | `get_call_details` |
| Prior calls on the same deal/account, for cumulative context | Call recorder | `search_calls` |
| Extracted pain, outcomes, solution fit, investment, ROI inputs, risks (each with a quote) | LLM over the transcripts | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `get_call_details` | Fetch the triggering call's transcript and metadata | Attention `get_call_details` | recorder API, or the [gtmsi adapters](../../docs/adapters.md) over the export |
| `search_calls` | Find the deal's prior calls | Attention `search_calls` | recorder API / adapters |
| `analyze_calls` | Extract the six business-case sections | `ask_attention` | an LLM step over the transcripts |
| `send_message` | Post the business case to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message.

## How it works (step by step)

1. **Retrieve call data.** `get_call_details` for the triggering call id (transcript, participants, CRM metadata). If the deal has prior calls, `search_calls` to find them and `analyze_calls` to fold in cumulative context (pain points, stakeholders, prior discussions).
2. **Check eligibility.** Proceed only if the call contains at least one of: a discussion of business challenges/pain, a demo or solution walkthrough, a pricing/investment discussion, or an ROI/value conversation. Otherwise skip and post nothing.
3. **Extract the six sections** from transcript evidence: (1) Current State and Pain with quantified impact, (2) Desired Future State and KPIs, (3) Solution Mapping (capability to pain, with prospect interest), (4) Investment, (5) ROI and Payback estimate, (6) Risks and Mitigations. Label anything the call did not cover as "Not yet discussed - follow up to fill this in."
4. **Estimate ROI.** ROI = ((annual value of pain resolved - annual investment) / annual investment) x 100%. Payback = annual investment / monthly value of pain resolved. If pain is not quantified, give the framework instead of a fabricated number.
5. **Assemble and post** the business case in the exact [Output](#output) format to the team channel, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full section checklists and ROI formula) is the single source of truth in [`case-builder.json`](./case-builder.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message:

```
Business Case - [Account/Prospect]
Based on: [call date] call with [prospect names] | Rep: [Rep]

1. Current State and Pain   -> problems + quantified impact (or "Needs quantification")
2. Desired Future State     -> outcomes, success metrics, KPIs
3. Solution Mapping         -> | Pain | Capability | Prospect interest (High/Med/Low) |
4. Investment               -> pricing discussed, or "Not yet discussed - placeholder"
5. ROI Estimate             -> annual value, annual investment, ROI %, payback months
6. Risks and Mitigations    -> risk : mitigation (or "Open - address in follow-up")

Next steps for rep -> review, fill any TBD sections, share with the buying committee
```
Posted to the team channel for the rep to refine and share. Never sent to the customer.

## Edge cases

- **Too short / only small talk or scheduling (under ~5 min):** skip generation entirely.
- **Key sections missing (no pain, no solution presented):** produce a partial case and label incomplete sections "Not yet discussed - follow up to fill this in."
- **Prospect said not interested / deal lost:** do not generate a business case.
- **Pain described but not quantified:** keep it qualitative and mark "Needs quantification"; use the ROI framework rather than inventing a number.

## Guardrails

- Read-only on the recorder. The only write is the one channel message.
- Every specific in the case comes from the call; no invented numbers, commitments, or names.
- Single stars for emphasis, never double stars.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask. It is a draft for the rep, never sent to the customer.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`case-builder.activepieces.json`](./case-builder.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") → an `askAttention` step that builds the business case from the call context → a Slack `send_channel_message`. On import, connect your Attention and Slack accounts and fill `<YOUR_ATTENTION_USER_ID>` and `<YOUR_SLACK_CHANNEL_ID>`. The fully-managed alternative is to import the agent template [`case-builder.json`](./case-builder.json).

**Any other builder - pre-built for you** in [`case-builder.builds/`](./case-builder.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./case-builder.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./case-builder.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./case-builder.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./case-builder.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./case-builder.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./case-builder.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/sales/case-builder.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`case-builder.json`](./case-builder.json) · [`case-builder.activepieces.json`](./case-builder.activepieces.json) (Attention). Other builders: [`case-builder.builds/`](./case-builder.builds/)._
