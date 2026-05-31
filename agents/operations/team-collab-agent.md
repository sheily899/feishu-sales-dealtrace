# Team Collab Agent

**Function:** Operations  ·  **Integrations:** call_recorder, communication  ·  **Template id:** `AGTTeamCollab01`

> Facilitates cross-team collaboration by identifying when other teams need involvement.

## When it fires

**Detector:** Trigger if the user wants to identify when other teams (engineering, legal, product, executives) should be involved in customer conversations.

**Signal keywords:** `team collaboration`, `cross-team`, `involve team`, `escalate`, `bring in expert`, `team handoff`, `loop in`, `involve engineering`, `involve legal`

## What it does

Monitor conversations to identify when cross-team collaboration is needed (sales engineering, product, support, executives, legal). Send alerts to appropriate teams via your team communication tool.

## Tools / actions
- **Call Recorder** — Get Call Details
- **Communication** — Send Message

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Conversation analyzed — fires once per call, when your call recorder finishes analyzing it (the *Conversation Analyzed* webhook).

---
_From GTM Superintelligence agent templates. Raw definition: [`team-collab-agent.json`](./team-collab-agent.json)._
