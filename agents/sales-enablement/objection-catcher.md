# Objection Catcher

**Function:** Sales Enablement  ·  **Integrations:** crm, email  ·  **Template id:** `AGTObjection01`

> Analyzes recorded calls weekly to identify common objections and surface the highest-performing rebuttals, delivering actionable coaching insights via email.

## When it fires

**Detector:** Trigger if the user wants to identify common objections in sales calls, find effective rebuttals, or analyze objection handling performance.

**Signal keywords:** `objection`, `objection handling`, `rebuttal`, `overcome objection`, `pricing objection`, `common objections`, `handle objections`, `objection response`

## What it does

Behavior

Goal: Each week, analyze all recorded calls, identify the most common objections, and surface the highest-performing rebuttals reps used.

Trigger: conversation_analyzed events (primary). Weekly roll-up on Mondays 08:00 ET.

Systems: Call recorder transcripts + analytics; optional CRM context (stage/outcome), optional team communication for alerts; Email for delivery.

Procedure

Collect calls where call_date ∈ last 7 days and has_transcript = true.

Extract Objections per call:

Use model to pull objection snippet(s) + category + moment timestamp.

Normalize categories (semantic clustering; e.g., "price", "budget", "too expensive" → Pricing).

Score Responses:

For each objection/response pair, compute a response quality score (clarity, empathy, proof, next step).

Weight by downstream outcomes (meeting booked, stage advanced, opp won) when available from your CRM.

Rank top objection categories by frequency and impact (lost/won delta, conversion uplift).

Select Best Messaging per category:

Choose 1–3 rebuttal snippets with highest composite score.

Include concise guidance pattern (why it worked).

Generate Digest (HTML + plain text).

Send Email to owner(s) and CC relevant leads; log artifact to analytics store.

Tasks

Detect and cluster objection variants; maintain category taxonomy: Pricing, Timing/Priority, Competitor, Feature Gap, Security/Legal, Integration, Authority, ROI/Proof, Contract/Procurement, Other.

Extract: objection quote, timestamp (mm:ss), rep response quote, response pattern label, score (0–100), outcome signals (advanced/won/lost).

Compute weekly stats: counts, % of calls with objections, WoW change, best-performing rebuttal patterns, coaching opportunities (low-score patterns).

Produce actionable guidance: 2–4 bullet coaching tips per top category.

Email the digest in plain text.

## Tools / actions
- **CRM** — Query Records
- **Email** — Send Email

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Schedule — runs weekly, Monday 08:00 (cron `0 8 * * 1`, set the timezone to the team's).

---
_From GTM Superintelligence agent templates. Raw definition: [`objection-catcher.json`](./objection-catcher.json)._
