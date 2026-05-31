# Competitor Ping

**Function:** Revenue Operations  ·  **Integrations:** call_recorder, communication  ·  **Template id:** `AGTCompetitorPing01`

> Detects and alerts when competitors are mentioned, tracking competitive positioning and objections.

## When it fires

**Detector:** Trigger if the user wants to track competitor mentions in conversations, gather competitive intelligence, or monitor competitive positioning.

**Signal keywords:** `competitor`, `competitive intel`, `competitor mention`, `competitive analysis`, `battlecard`, `competitor tracking`, `competition`, `rival`

## What it does

Monitor conversations for competitor mentions, track competitive intelligence, capture strengths/weaknesses discussed, and generate weekly competitive reports.

## Tools / actions
- **Call Recorder** — Search Calls, Get Call Details
- **Communication** — Send Message

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Conversation analyzed — fires once per call, when your call recorder finishes analyzing it (the *Conversation Analyzed* webhook).

---
_From GTM Superintelligence agent templates. Raw definition: [`competitor-ping.json`](./competitor-ping.json)._
