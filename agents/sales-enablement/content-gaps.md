# Content Gaps

**Function:** Sales Enablement  ·  **Integrations:** call_recorder, communication  ·  **Template id:** `AGTContentGaps01`

> Identifies prospect questions and objections that reps struggle to answer, delivering weekly summaries highlighting content and training gaps for enablement teams.

## When it fires

**Detector:** Trigger if the user wants to find questions that sales reps cannot answer, identify missing sales content, or discover training and enablement gaps.

**Signal keywords:** `content gap`, `training gap`, `unanswered questions`, `rep struggles`, `enablement`, `FAQ`, `sales content`, `missing content`, `training needs`

## What it does

Identify prospect questions and objections reps struggle to answer during calls. Cluster recurring topics by frequency and deal impact, then deliver a weekly team summary with recommended content and enablement actions (new FAQs, one-pagers, demo snippets, training) — framed constructively, not as performance criticism.

## Tools / actions
- **Call Recorder** — Search Calls, Ask Attention
- **Communication** — Send Message

## Tooling

Attention-native: this agent uses `ask_attention` (natural-language query/analysis over calls + CRM) plus `search_calls`/`get_call_details` where it needs specific calls. **On Attention** — import it into the agent builder, or run it here with Attention's MCP, and it works as written. **On any other recorder** — run it as a managed Claude agent with [`/run-agent`](../../.claude/commands/run-agent.md): Claude reads your CRM and pulls transcripts via your recorder or the [gtmsi adapters](../../docs/adapters.md), then does the same analysis. See [Tooling & portability](../README.md#tooling--portability).

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Schedule — runs weekly, Monday 08:00 (cron `0 8 * * 1`, set the timezone to the team's).

---
_From GTM Superintelligence agent templates. Raw definition: [`content-gaps.json`](./content-gaps.json)._
