# Case Study Generator

> After a customer success call is analyzed, draft a structured, publication-ready case study from the call and your CRM facts, then hand it to the marketing team as a draft to review. It never publishes and never contacts the customer.

**Function:** Marketing · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTCaseStudy01`
**Files:** [`case-study-generator.json`](./case-study-generator.json) (Attention agent-builder template) · [`case-study-generator.activepieces.json`](./case-study-generator.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Turn a winning customer call into a case study draft the marketing team can polish in minutes:
1. Grounded in real evidence: CRM facts (deal size, industry, dates) plus verbatim quotes and metrics from the call.
2. Structured into the sections marketing actually uses (overview, challenge, solution, results, quote).
3. Delivered as a draft, with every quote flagged for customer approval before publication.
4. Written like a person, not a bot (mandatory humanizer pass). It never publishes automatically.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (account, owner).
- It first confirms the call is a success story; non-wins are skipped (see Edge cases).

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| Deal facts: account, industry, size, deal value, contacts, dates | CRM | `query_records` |
| The just-analyzed call (challenge, solution, results, quotable moments) | Call recorder | `search_calls` / `get_call_details` |
| Extracted challenge / solution / results + verbatim quotes | LLM over the transcript | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `query_records` | Read the account / deal facts from the CRM | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `search_calls` | Fetch the analyzed call by id | Attention `search_calls` | recorder API, or the [dealtrace adapters](../../docs/adapters.md) over the export |
| `get_call_details` | Pull the full call record when needed | Attention `get_call_details` | recorder API |
| `analyze_calls` | Extract challenge / solution / results + quotes | `ask_attention` | an LLM step over the transcript |
| `send_direct_message` | DM the draft to the marketing owner | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is delivering one draft. It never publishes.

## How it works (step by step)

1. **Confirm this is a success story.** `search_calls` (or `get_call_details`) by the trigger's call id, then `analyze_calls` to confirm a win (strong positive outcome, measurable result, satisfied customer, or a closed-won deal). If not, skip and post a one-line note.
2. **Gather the facts.** From the CRM (`query_records`): account, industry, size, deal value, contacts, the dates that anchor the timeline. From the call: the customer's stated challenge, what they adopted and why, the results they reported with any metric, and the most quotable moments, verbatim.
3. **Draft the case study** in these sections, each grounded in evidence: **Client Overview, Challenge, Solution, Results, Customer Quote, Why it matters.** Do not invent numbers, quotes, or outcomes the call did not support.
4. **Humanize (mandatory):** run the draft through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** skill. No em dashes, no throat-clearing, no hype, keep a real human voice.
5. **Deliver as a draft** to the marketing owner (DM by default, or a #marketing-content channel if configured), with a review checklist beneath: source call link, quotes needing customer approval, and any unverified fact to confirm.

> The verbatim operating prompt is the single source of truth in [`case-study-generator.json`](./case-study-generator.json) under `template.agent.instructions`. This section is its readable summary.

## Output

```
Title: <case study title>
Client Overview: <...>
Challenge: <...>
Solution: <...>
Results: <...>
Customer Quote: "<verbatim quote>"
Why it matters: <...>
---
Review checklist: <source call link; quotes needing customer approval; unverified facts to confirm>
```
Delivered as a draft to the marketing team. Never published and never sent to the customer.

## Edge cases

- **Not a success story / internal call:** skip; post a one-line note explaining why, no draft.
- **Missing CRM facts:** draft what the call supports and mark the gaps (e.g. "deal value: confirm in CRM") rather than guessing.
- **No quotable customer line:** draft the narrative and flag that a quote still needs sourcing before publication.
- **Sensitive or unconfirmed numbers:** never state metrics the customer did not say on the call; flag for human confirmation and customer approval.
- **Multiple accounts in one call:** focus on the primary success account; note the others for the marketing team.

## Guardrails

- **Draft only, to marketing.** Never publish, never send to a customer.
- Every section ties to CRM data or a call quote. No invented metrics, quotes, or outcomes.
- Quotes are flagged for customer approval before any public use.
- Mandatory **humanizer** pass before delivery.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`case-study-generator.activepieces.json`](./case-study-generator.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") -> an `askAttention` step that drafts the case study from the call context -> a Slack `send_direct_message`. On import, connect your Attention and Slack accounts and fill the placeholders `<YOUR_ATTENTION_USER_ID>` and `<REP_SLACK_USER_ID>`. The CRM facts can be supplied to the `askAttention` step or fetched in a CRM step you add before it.

**Any other builder (n8n / Zapier / Make / LangGraph / custom):** wire it as:
1. **Trigger:** your recorder's "conversation analyzed" webhook (or poll for newly analyzed calls).
2. **CRM step** (`query_records`): pull the account / deal facts.
3. **Analyze step** (`analyze_calls`): extract challenge / solution / results + quotes from the transcript.
4. **Compose step** (LLM with the operating prompt) then **humanizer**.
5. **Deliver step** (`send_direct_message`): DM the draft to the marketing owner. Do not connect a "publish" or "send to customer" action.

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/marketing/case-study-generator.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Machine-readable: [`case-study-generator.json`](./case-study-generator.json) · [`case-study-generator.activepieces.json`](./case-study-generator.activepieces.json) (Attention)._
