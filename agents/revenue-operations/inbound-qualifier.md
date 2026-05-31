# Inbound Qualifier

**Function:** Revenue Operations  ·  **Integrations:** crm, call_recorder, communication  ·  **Template id:** `AGTInboundQual01`

> Qualifies inbound leads by analyzing initial conversations for BANT signals and fit with ideal customer profile.

## When it fires

**Detector:** Trigger if the user wants to qualify inbound leads using BANT criteria, assess fit with ideal customer profile, or score lead quality from conversations.

**Signal keywords:** `lead qualification`, `BANT`, `qualify lead`, `inbound lead`, `lead scoring`, `ICP fit`, `qualification`, `qualify prospect`, `lead quality`

## What it does

Analyze initial prospect conversations to qualify inbound leads using BANT criteria (Budget, Authority, Need, Timeline) and ICP fit assessment.

## Tools / actions
- **CRM** — Query Records
- **Call Recorder** — Search Calls, Get Call Details
- **Communication** — Send Message

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Conversation analyzed — fires once per call, when your call recorder finishes analyzing it (the *Conversation Analyzed* webhook).

---
_From GTM Superintelligence agent templates. Raw definition: [`inbound-qualifier.json`](./inbound-qualifier.json)._
