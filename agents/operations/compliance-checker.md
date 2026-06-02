# Compliance Checker

> After every analyzed customer call, scan the transcript against a five-category compliance checklist, classify any violation by severity with a verbatim quote as evidence, and alert the compliance channel. Stay silent on clean calls so an alert always means something real.

**Function:** Operations · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTComplianceChk01`
**Files:** [`compliance-checker.json`](./compliance-checker.json) (Attention agent-builder template) · [`compliance-checker.activepieces.json`](./compliance-checker.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

Turn each analyzed customer call into a compliance check that:
1. Scans the transcript across regulatory, legal, data-privacy, and company-policy dimensions.
2. Classifies each violation by category and severity (CRITICAL / HIGH / MEDIUM).
3. Backs every flag with a verbatim transcript quote and a specific corrective action.
4. Posts an alert only when a real violation is found, and stays silent otherwise.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (account, rep).
- Skip internal/non-customer calls and failed/partial recordings (see Edge cases).

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (full transcript + metadata: participants, account, rep, date) | Call recorder | `get_call_details` |
| The violation assessment (category, severity, evidence quote) | LLM over the transcript | `analyze_calls` |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `get_call_details` | Fetch the analyzed call's transcript by id | Attention `get_call_details` | recorder API, or the [gtmsi adapters](../../docs/adapters.md) over the export |
| `analyze_calls` | Scan against the checklist and assign severity | `ask_attention` | an LLM step over the transcript |
| `send_message` | Post the alert to the compliance channel | Slack/Teams tool | your chat tool's API/MCP |

## How it works (step by step)

1. **Retrieve the call.** `get_call_details` by the trigger's call id: full transcript, participants, account name, call date, rep name.
2. **Scan against the five-category checklist:** (A) unauthorized commercial commitments, (B) data handling and privacy, (C) regulatory and legal claims, (D) competitor disparagement, (E) sales conduct. Factual public competitive comparisons are not violations.
3. **Assign severity** to each violation: CRITICAL (immediate legal/regulatory exposure), HIGH (financial or reputational harm), MEDIUM (correct but no immediate risk).
4. **Alert (only if a violation is found):** `send_message` to the compliance or sales-ops channel in the exact [Output](#output) format, each violation backed by a verbatim quote. For any CRITICAL, prepend the critical banner.
5. **Clean call:** send nothing.

Run the alert through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** skill before posting.

> The verbatim operating prompt (with the full per-category checklist) is the single source of truth in [`compliance-checker.json`](./compliance-checker.json) under `template.agent.instructions`. This section is its readable summary.

## Output

Sent only when a violation is found:

```
:rotating_light: COMPLIANCE ALERT - [Severity: CRITICAL/HIGH/MEDIUM]
Call: [title/date] · Rep: [name] · Account: [name]

Violation(s):
1. [Category]: [label]
   Transcript evidence: "[exact quote, max 2-3 sentences]"
   Risk: [one sentence]
   Recommended action: [step]
2. ...

Overall recommendation: [summary action]
```
For CRITICAL violations, prepend: `:warning: This alert is CRITICAL and may require immediate management review.`

## Edge cases

- **No violations:** send nothing. Only alert when a violation is detected.
- **Internal / non-customer call:** skip analysis entirely. This agent only monitors customer-facing conversations.
- **Too short / failed recording (under ~30 seconds of dialogue):** skip analysis.
- **Uncertain whether something is a violation:** flag as MEDIUM with the note "Possible violation - manual review recommended."
- **Repeat offender:** if the same rep was flagged for the same violation type on multiple recent calls, note "This is the [Nth] occurrence of [type] for this rep in the last 30 days."

## Guardrails

- **Alert only, to an internal channel.** Never contacts the customer.
- Every flag is backed by a verbatim transcript quote. No speculation presented as fact.
- Silent on clean calls, so an alert always carries signal.
- Mandatory **humanizer** pass before posting.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`compliance-checker.activepieces.json`](./compliance-checker.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") -> an `askAttention` step that scans the call against the checklist -> a Slack `send_channel_message`. On import, connect your Attention and Slack accounts and fill the placeholders `<YOUR_ATTENTION_USER_ID>` and `<YOUR_SLACK_CHANNEL_ID>`. The scan step emits `NO_VIOLATIONS` on clean calls; add a filter before the post step (or skip empty/`NO_VIOLATIONS` output) so clean calls stay silent.

**Any other builder (n8n / Zapier / Make / LangGraph / custom):** wire it as:
1. **Trigger:** your recorder's "conversation analyzed" webhook (or poll for newly analyzed calls).
2. **Retrieve step** (`get_call_details`): fetch the transcript and metadata.
3. **Scan step** (LLM with the operating prompt): classify violations and severity; emit nothing on a clean call.
4. **Deliver step** (`send_message`): post to the compliance channel only when a violation is found, after the humanizer pass.

The agent logic does not change between platforms. Only the bound connectors do.

---
_From GTM Superintelligence agent templates. Machine-readable: [`compliance-checker.json`](./compliance-checker.json) · [`compliance-checker.activepieces.json`](./compliance-checker.activepieces.json)._
