# Renewal Countdown

**Function:** Account Management  ·  **Integrations:** crm, call_recorder, communication  ·  **Template id:** `AGTRenewalCount01`

> Monitors upcoming contract renewals and sends proactive alerts with customer health context and engagement trends.

## When it fires

**Detector:** Trigger if the user wants to track upcoming renewals, monitor renewal health, or get proactive alerts about approaching contract expiration dates.

**Signal keywords:** `renewal`, `contract renewal`, `upcoming renewal`, `renewal alert`, `renewal countdown`, `expiring contract`, `renewal date`, `subscription renewal`

## What it does

Monitor upcoming contract renewals and send proactive alerts with customer health context. Track renewal timelines, engagement frequency, sentiment trends, and risk indicators to help account teams prepare for renewal conversations.

## Tools / actions
- **CRM** — Query Records
- **Call Recorder** — Search Calls, Ask Attention
- **Communication** — Send Message

## Tooling

Attention-native: this agent uses `ask_attention` (natural-language query/analysis over calls + CRM) plus `search_calls`/`get_call_details` where it needs specific calls. **On Attention** — import it into the agent builder, or run it here with Attention's MCP, and it works as written. **On any other recorder** — run it as a managed Claude agent with [`/run-agent`](../../.claude/commands/run-agent.md): Claude reads your CRM and pulls transcripts via your recorder or the [gtmsi adapters](../../docs/adapters.md), then does the same analysis. See [Tooling & portability](../README.md#tooling--portability).

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Schedule — runs daily at 07:00 (cron `0 7 * * *`, set the timezone to the team's).

**Resolve the renewal date field:** find the org's renewal/close-date field (e.g., Salesforce `CloseDate` or a custom renewal-date field; HubSpot `closedate`) via your CRM rather than assuming a field name.

---
_From GTM Superintelligence agent templates. Raw definition: [`renewal-countdown.json`](./renewal-countdown.json)._
