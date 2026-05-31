# Validate

**Function:** Operations  ·  **Integrations:** crm, communication  ·  **Template id:** `AGTValidate01`

> Validates and updates CRM data by analyzing conversation intelligence, presenting proposed field changes to reps for approval, and syncing approved updates to your CRM.

## When it fires

**Detector:** Trigger if the user wants to validate CRM data against conversation content, get approval before updating CRM fields, or improve data accuracy.

**Signal keywords:** `crm validation`, `data validation`, `update crm`, `crm sync`, `field validation`, `data hygiene`, `crm accuracy`, `validate fields`, `sync crm`

## What it does

Behavior

Trigger on conversation_analyzed.

Read trigger metadata from extracted intelligence and map those keys to CRM fields.

DM the call owner via your team communication tool with a compact review card showing the proposed CRM updates (before → after) and options to Approve & Push, Edit, Skip, or Remind me later.

On approval (or edit + approval), write updates to the correct CRM records, then confirm via your team communication tool.

Procedure

Trigger & Context

Event: conversation_analyzed

Inputs: call_id, call_owner_user_id, extracted_intelligence (key/value; may include confidence + evidence spans), any known CRM IDs (Account/Contact/Opportunity) under linkedCRMrecords.

Field Mapping

Use a mapping table: { intelligence_key -> { sobject, field, upsert_key? } }.

Only include keys present in extracted_intelligence. Ignore null/empty.

Fetch Current CRM State

Resolve records:

Contact by email (from call participants) or provided ContactId.

Account by domain or AccountId.

Opportunity by provided OpportunityId; fallback: open opp(s) on the Account for the Contact; else create "Pending Validation" draft opp (do not save until approved).

Pull current field values for each proposed update.

Compose Review Message

Recipient: call_owner_user_id.

Card sections:

Header: "Validate CRM Fields for <Account | Contact | Opportunity>"

Key fields in a diff table (Current → Proposed), with confidence %, and "view evidence" buttons that open transcript snippets/timecodes.

Timestamps + link to the call recording/notes.

Actions:

Approve & Push (primary): push all checked fields.

Edit Fields: open modal with editable inputs for each proposed field (prefilled).

Skip: dismiss, log reason.

Remind me later: snooze 24h (configurable).

Per-field checkboxes to allow partial approval.

Write to CRM

On approval:

Upsert in this order: Account → Contact → Opportunity (respect upsert_key).

Only write fields approved/edited by the user.

Add a Call/Task/Activity with summary of changes + link to transcript.

On success: confirmation message with links to updated records.

On failure: error message with retry button and surfaced error message.

Edge Cases & Rules

If mapping targets a locked or picklist field, validate values; if invalid, prompt user to select from allowed choices in the Edit modal.

If multiple candidate records match, show chooser in the modal before approval.

If no fields extracted, post a brief DM: "No CRM-impacting fields detected."

Privacy: include only conversation snippets necessary for validation; respect workspace retention.

Metrics & Logging

Track: #cards sent, approval rate, time-to-approval, field-level acceptance, error rate.

Emit analytics events to internal telemetry.

Tasks

Extract-Read: Parse extracted_intelligence, normalize values (dates to ISO, currency to org default, picklists to canonical labels).

Diff-Build: For each mapped field, fetch CRM current value and compute {current, proposed, confidence, evidence}.

Notify: Render interactive DM with sections + actions + modal for edits.

CRM-Upsert: Validate values, transform to API shapes, and write to the appropriate CRM objects.

Confirm/Retry: Acknowledge success, handle retries with exponential backoff (max 3), and surface actionable errors.

Snooze/Reminder: Re-DM after the snooze window; close the loop after 3 unanswered reminders.

## Tools / actions
- **CRM** — Query Records
- **Communication** — Send Direct Message

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Conversation analyzed — fires once per call, when your call recorder finishes analyzing it (the *Conversation Analyzed* webhook).

---
_From GTM Superintelligence agent templates. Raw definition: [`validate.json`](./validate.json)._
