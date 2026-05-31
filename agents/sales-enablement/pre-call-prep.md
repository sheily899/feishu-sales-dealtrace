# Pre-Call Prep

**Function:** Sales Enablement  ·  **Integrations:** crm, communication  ·  **Template id:** `AGTPreCallPrep01`

> Every morning at 7:30 AM, review the sales rep’s calendar and identify all meetings scheduled for that day between 7:00 AM and 7:00 PM.

## When it fires

**Detector:** Trigger if the user wants to prepare for upcoming calls or meetings with customer context, CRM history, previous conversations, and talking points.

**Signal keywords:** `pre-call`, `call prep`, `meeting prep`, `briefing`, `before meeting`, `morning prep`, `calendar prep`, `daily prep`, `preparar llamada`, `reunion`, `upcoming meetings`

## What it does

Every morning at 7:30 AM, review the sales rep's calendar and identify all meetings scheduled for that day between 7:00 AM and 7:00 PM. For each meeting, collect the title, start and end times, meeting link or location, and all attendee names and emails. Use those attendees to identify the people and companies the rep will be meeting with.

Then, check your CRM to see if any of the attendees match a contact, account, or opportunity. If an attendee's email or company domain matches an account, associate that meeting with that account and the most relevant opportunity. Prefer open opportunities, and if none exist, use the most recent closed one. Once identified, store the associated account and opportunity IDs with the meeting.

Next, look in your call recorder for all prior conversations related to those same accounts or opportunities. Gather summaries of past interactions — no full transcripts, only high-level conversation summaries. Include the following context for each conversation:

The date and type of interaction (call, meeting, email, or message)

Duration of the meeting (if available)

Participants and their roles (for example, champion, economic buyer, or technical evaluator)

What topics were discussed (pricing, contract terms, product capabilities, security, implementation, ROI, etc.)

Any objections or concerns raised

Competitor mentions

Next steps or action items that came out of the call

Sentiment or tone of the conversation (positive, neutral, negative, uncertain)

The decision-making clues gathered (such as who influences the deal or who has final authority)

Use this to understand the deal context before today's meeting — how long the opportunity has been open, the overall stage of the process, and whether the tone is trending positively or negatively.

For each meeting record:

Meeting details (title, time, attendees, location or link)

The matched CRM account and opportunity information (name, stage, amount, close date, forecast category)

Key people and their roles (economic buyer, champion, influencer, end user)

Summaries of the most recent 3–5 conversations from your call recorder

Engagement metrics (meeting count, total minutes, last interaction date, sentiment trend)

Open items or tasks the rep owes, including due dates or blockers

Known objections, competitive pressure, or unresolved issues

Notable commitments made by the customer

Helpful resources or documents already shared (decks, proposals, contracts, etc.)

Any timing signals (upcoming renewal dates, budget cycles, procurement steps)

Once all this data is determined ,analyze it and generate a detailed pre-call preparation summary for the rep. Each meeting's section should be rich and practical, showing not just data but context and insight.

For each meeting you should provide:

A short, human-style TL;DR explaining where the deal or relationship stands and why today's meeting matters.

Attendee context: who will be on the call, their roles, and what they've been involved with so far.

Relationship summary: the account history, how long this relationship has been active, and any major wins or issues from past interactions.

Opportunity context: deal stage, value, close date, forecast category, and any recent changes in amount or timing.

Recent activity recap: what's happened in the last few interactions, what was agreed on, and whether action items were completed.

Risks or challenges: any red flags or blockers identified in previous calls, such as pricing objections, legal delays, or lack of executive alignment.

Competitive landscape: if other vendors were mentioned, how this deal compares, and what arguments have been effective so far.

Recommended talking points and focus areas for today: what the rep should aim to accomplish, questions to ask, and decisions to push forward.

Strategic tips: cues for tone, relationship management, or value reinforcement — for example, "Reinforce ROI from pilot results" or "Remind them of onboarding readiness."

Useful artifacts: which materials to have ready (proposal, security document, ROI deck, case study, etc.).

Finally, send the pre-call briefing to the rep via your team communication tool as a single, clearly structured message. The message should not use any bold text or markdown symbols (no ** or *). It should be formatted with emojis and clean headings, easy to skim but full of context.

Each meeting should appear in this general structure:

📅 10:30 AM — Acme Corp
Attendees: John Doe (CFO), Sarah Green (Director of IT)
Opportunity: Enterprise renewal — Stage: Negotiation — Amount: $150,000 — Close Date: 2024-11-05

TL;DR: Renewal discussions nearing final terms; pricing and contract structure under review. Sarah requested updated SOC 2 documentation before signing.

Recent Activity:

Last call (Oct 10): discussed contract length and multi-year discount.

Email follow-up (Oct 13): rep shared revised pricing sheet.

Customer reviewing redlines; legal feedback pending.

Risks and Challenges:

Potential delay from legal review.

Procurement might request additional security paperwork.

Recommended Focus for Today:

Confirm legal status and expected sign-off date.

Reinforce ROI and renewal benefits.

Offer optional onboarding session to show readiness for 2025.

Helpful Materials: Updated pricing proposal, SOC 2 doc, onboarding checklist.

If multiple meetings are scheduled, list them in chronological order, one detailed block per meeting. If there are no meetings that day, send a simple message that says:
"Good morning! You have no customer meetings on your calendar today."

The message should read naturally, use emojis for structure, and avoid all markdown bolding or special formatting. Each section should feel like a personalized prep briefing — short enough to skim quickly, but with enough depth to give the rep real context, risks, and action steps for every conversation.

## Tools / actions
- **CRM** — Query Records
- **Communication** — Send Direct Message

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Schedule — runs every weekday at 07:00 (the rep's local morning) (cron `0 7 * * 1-5`, set the timezone to the team's).

---
_From GTM Superintelligence agent templates. Raw definition: [`pre-call-prep.json`](./pre-call-prep.json)._
