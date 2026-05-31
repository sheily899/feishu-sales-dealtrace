# Upsell Alert

**Function:** Revenue Operations  ·  **Integrations:** crm, communication  ·  **Template id:** `AGTUpsellAlert01`

> Identifies upsell and expansion opportunities by analyzing customer conversations for budget availability signals and growth intent.

## When it fires

**Detector:** Trigger if the user wants to identify upsell or expansion opportunities based on budget availability signals and customer growth intent.

**Signal keywords:** `upsell`, `expansion`, `budget increase`, `upgrade`, `grow account`, `upsell opportunity`, `expand contract`, `increase deal size`

## What it does

# Upsell Alert
**Detects and reports when a prospect indicates available or increased budget.**

### Behavior
Monitors analyzed sales conversations for budget-expansion cues...

### Procedure
**Trigger:** conversation_analyzed
**Condition:** Detected budget-expansion language...

**Data Sources:** Call recorder analytics, CRM

**Analysis Steps:**
1. Detect and extract budget-related statement
2. Confirm prospect identity
3. Generate alert with details

### Tasks
- Parse conversations for budget-expansion signals
- Cross-reference speaker and account info
- Post message to #upsell-alerts

## Tools / actions
- **CRM** — Query Records
- **Communication** — Send Message

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Conversation analyzed — fires once per call, when your call recorder finishes analyzing it (the *Conversation Analyzed* webhook).

---
_From GTM Superintelligence agent templates. Raw definition: [`upsell-alert.json`](./upsell-alert.json)._
