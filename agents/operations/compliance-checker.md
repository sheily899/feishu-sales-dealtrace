# Compliance Checker

**Function:** Operations  ·  **Integrations:** call_recorder, communication  ·  **Template id:** `AGTComplianceChk01`

> Monitors conversations for compliance with regulations, company policies, and legal requirements.

## When it fires

**Detector:** Trigger if the user wants to monitor conversations for compliance violations, regulatory issues, legal requirements, or company policy adherence.

**Signal keywords:** `compliance`, `regulation`, `GDPR`, `legal compliance`, `policy violation`, `compliance check`, `audit`, `HIPAA`, `CCPA`, `regulatory`

## What it does

Monitor sales and customer conversations for compliance violations, regulatory requirements (GDPR, CCPA, HIPAA), company policies, and sales conduct standards.

## Tools / actions
- **Call Recorder** — Get Call Details
- **Communication** — Send Message

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Conversation analyzed — fires once per call, when your call recorder finishes analyzing it (the *Conversation Analyzed* webhook).

---
_From GTM Superintelligence agent templates. Raw definition: [`compliance-checker.json`](./compliance-checker.json)._
