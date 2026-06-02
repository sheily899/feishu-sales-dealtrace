# Email Generator

> After every analyzed call, draft a short, personalized follow-up in the rep's voice that recaps the conversation and locks one clear next step, then hand it to the rep as a draft to review and send.

**Function:** Sales · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTEmailGen01`
**Files:** [`email-generator.json`](./email-generator.json) (Attention agent-builder template) · [`email-generator.activepieces.json`](./email-generator.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Turn each analyzed customer call into a follow-up the rep can send in under a minute:
1. Grounded in real specifics from the call (a quote, a metric, an owner, a date).
2. Always locking a single concrete next step.
3. Written in the rep's voice, never bot-like (mandatory humanizer pass).
4. Delivered as a draft to the rep. It never sends to the customer automatically.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (account, owner).
- Skip internal/non-customer calls (see Edge cases).

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (transcript + metadata: account, owner, attendees) | Call recorder | `search_calls` |
| Extracted recap, action items, commitments, next step (each with a quote) | LLM over the transcript | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Fetch the analyzed call by id | Attention `search_calls` | recorder API, or the [gtmsi adapters](../../docs/adapters.md) over the export |
| `analyze_calls` | Extract recap / actions / next step | `ask_attention` | an LLM step over the transcript |
| `send_direct_message` | DM the draft to the rep | Slack/Teams tool | your chat tool's API/MCP |

## How it works (step by step)

1. **Retrieve and analyze the call.** `search_calls` by the trigger's call id, then `analyze_calls` to extract, each backed by a verbatim quote where possible: attendees and roles (who is the rep vs buyer), the buyer's stated pain and any number attached, commitments by either side, agreed action items with owner and due date, open questions/objections, and the single most important next step. Note the call type (discovery / demo / technical-validation / negotiation / onboarding / check-in / renewal), which sets tone.
2. **Pick recipient and channel.** Default: DM the deal owner. Use a team channel if configured. Never address or send to the customer.
3. **Compose the follow-up:**
   - **Subject:** specific; references the company and topic. Not "Great meeting you".
   - **Opening:** one sentence, straight to the point.
   - **Recap:** 2-4 bullets, each tied to something real from the call.
   - **Agreed actions:** short list, each `owner -- action -- date`.
   - **Next step:** one clear ask with a concrete proposal (a specific time window, not "let me know").
   - **Sign-off** in the rep's voice. Body under ~150 words, skimmable on mobile.
   - Tone: discovery/new -> concise, value-first; established customer -> warmer, outcome-focused.
4. **Humanize (mandatory):** run the draft through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** skill. No em dashes, no "I hope this finds you well" / "I wanted to reach out", no hype adjectives, one clear ask, keep the rep's real voice.
5. **Deliver as a draft** to the rep, with the extracted action-item list beneath so they can verify it.

> The verbatim operating prompt is the single source of truth in [`email-generator.json`](./email-generator.json) under `template.agent.instructions`. This section is its readable summary.

## Output

```
Subject: <specific subject>
Body: <= ~150-word follow-up in the rep's voice, humanized>
---
Action items: <owner -- action -- date, one per line>
```
Delivered as a direct message to the deal owner (a draft to review and send), never to the customer.

## Edge cases

- **Internal / non-customer call:** skip; post a one-line note explaining why, no draft.
- **No next step agreed:** propose one from the call type and label it clearly as proposed, not agreed.
- **Multiple buyer contacts:** address the primary; list the others for the rep to CC.
- **Unconfirmed sensitive details (pricing not finalized, legal terms):** do not state numbers the rep did not confirm on the call; flag them for the rep.
- **Very short / low-content call:** produce a two-line nudge instead of a full recap.

## Guardrails

- **Draft only, to the rep.** Never auto-send to a customer.
- Every specific in the email comes from the call; no invented commitments, numbers, or names.
- Mandatory **humanizer** pass before delivery.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`email-generator.activepieces.json`](./email-generator.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") → an `askAttention` step that drafts the follow-up from the call context → a Slack `send_direct_message`. On import, connect your Attention and Slack accounts and fill the placeholders `<YOUR_ATTENTION_USER_ID>` and `<REP_SLACK_USER_ID>`.

**Any other builder (n8n / Zapier / Make / LangGraph / custom):** wire it as:
1. **Trigger:** your recorder's "conversation analyzed" webhook (or poll for newly analyzed calls).
2. **Analyze step** (`analyze_calls`): extract recap / actions / next step from the transcript.
3. **Compose step** (LLM with the operating prompt) then **humanizer**.
4. **Deliver step** (`send_direct_message`): DM the draft to the rep. Do not connect a "send to customer" action.

The agent logic does not change between platforms. Only the bound connectors do.

---
_From GTM Superintelligence agent templates. Machine-readable: [`email-generator.json`](./email-generator.json) · [`email-generator.activepieces.json`](./email-generator.activepieces.json)._
