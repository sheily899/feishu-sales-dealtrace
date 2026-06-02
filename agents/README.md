# GTM Agent Templates

All **30** production agent templates, organized into subfolders by function. Each agent has a readable spec (`.md`) and its machine-readable definition (`.json`).

This library ships with **GTM Superintelligence** as a real-world showcase of what production GTM agents look like — use them as inspiration, fork them, or adapt them to any stack. Agents are **platform-agnostic**: they work with any CRM (Salesforce, HubSpot, etc.), any call recorder, any team communication tool (Slack, Teams, etc.), and any email provider. They pair naturally with the coaching/scoring framework in the rest of this repo.

**Run them:** first `/setup` (one time — it asks which recorder, CRM, comms, and email you use and writes [`config.yaml`](./config.yaml)), then `/run-agent agents/<category>/<agent>.json`. On Attention they run natively in its agent builder; on any other recorder they run as managed Claude agents (see [Tooling & portability](#tooling--portability)).

## By function

| Function | Agents |
|---|---|
| **[Revenue Operations](./revenue-operations/)** (8) | [Competitor Ping](./revenue-operations/competitor-ping.md), [Cross Seller Radar](./revenue-operations/cross-seller-radar.md), [Deal Stage Clarity](./revenue-operations/deal-stage-clarity.md), [Inbound Qualifier](./revenue-operations/inbound-qualifier.md), [Lost-Deal Intel](./revenue-operations/lost-deal-intel.md), [Revenue Sentry](./revenue-operations/revenue-sentry.md), [Upsell Alert](./revenue-operations/upsell-alert.md), [Win Loss Insights](./revenue-operations/win-loss-insights.md) |
| **[Sales](./sales/)** (3) | [Case Builder](./sales/case-builder.md), [Email Generator](./sales/email-generator.md), [Multi Thread Detector](./sales/multi-thread-detector.md) |
| **[Sales Enablement](./sales-enablement/)** (6) | [Content Gaps](./sales-enablement/content-gaps.md), [Objection Catcher](./sales-enablement/objection-catcher.md), [Objection Drilldown](./sales-enablement/objection-drilldown.md), [Pre-Call Prep](./sales-enablement/pre-call-prep.md), [Scorecard per Rep](./sales-enablement/scorecard-per-rep.md), [Skill Coach](./sales-enablement/skill-coach.md) |
| **[Operations](./operations/)** (5) | [AE Handoff](./operations/ae-handoff.md), [Compliance Checker](./operations/compliance-checker.md), [Cross Team Handoff](./operations/cross-team-handoff.md), [Team Collab Agent](./operations/team-collab-agent.md), [Validate](./operations/validate.md) |
| **[Account Management](./account-management/)** (4) | [Churn Alert](./account-management/churn-alert.md), [Renewal Countdown](./account-management/renewal-countdown.md), [Risk Watch](./account-management/risk-watch.md), [Sentiment Watch](./account-management/sentiment-watch.md) |
| **[Marketing](./marketing/)** (3) | [Case Study Generator](./marketing/case-study-generator.md), [Persona Mapper](./marketing/persona-mapper.md), [Social Proof Finder](./marketing/social-proof-finder.md) |
| **[Product](./product/)** (1) | [Product Tracker](./product/product-tracker.md) |

## Triggers

Each agent fires on the event that makes sense for it — not a generic catch-all:

- **📞 Per call** — runs when your call recorder finishes analyzing a conversation (most coaching/insight agents).
- **🔁 CRM stage change** — runs when an Opportunity enters a won/lost stage in your CRM (e.g. **AE Handoff** on Closed-Won, **Lost-Deal Intel** on Closed-Lost).
- **🗓 Schedule** — periodic digests/monitors (daily or weekly).

Stage- and date-aware agents **resolve the org's real CRM stages from its own data** (`gtmsi crm-stages`) instead of hardcoding labels like "Closed Won" — see [../docs/crm-stages.md](../docs/crm-stages.md). Each agent's exact trigger is in its page under **## Trigger**.

## Anatomy of an agent

Each template has: a **trigger** (per-call / CRM-stage / schedule), a **detector** (`detectorPrompt` + `signals`), **instructions** (what it does), and **integrations** (CRM, communication, call recorder, email -- all platform-agnostic, so they work with any vendor in each category). Configure which vendor you use per category in [`config.yaml`](./config.yaml).

> **Note on edits:** these templates are tuned for GTM Superintelligence — vendor-neutral integrations, triggers set to fire on the sensible event (e.g. AE Handoff on a Closed-Won stage change rather than a generic webhook), and a final humanize pass on any drafted message.

## Two ways to build & run these agents

Each agent ships pre-built for every builder: a build-ready, builder-agnostic spec (`<agent>.md`); the Attention forms (`<agent>.json` template + `<agent>.activepieces.json` flow); and a `<agent>.builds/` folder with the agent built for **n8n, Make, Zapier, LangGraph, the Claude Agent SDK, and a Claude Code subagent**. Set `agent_builder` in [`config.yaml`](./config.yaml) (or run [`/setup`](../.claude/commands/setup.md)); there are two paths:

**Path A — on [Attention](https://www.attention.com) → native, strongest.** Import `<agent>.activepieces.json` (or the `.json` template) straight into Attention's agent builder. It runs natively on `@activepieces/piece-attention`: an `askAttention` step does the query/analysis over your calls + CRM, with `listConversations` / routers / code steps as needed. Attention already provides the role-labeled, CRM-linked, re-stitched transcripts these agents assume (see [docs/call-recorders.md](../docs/call-recorders.md)), so there is nothing to translate. Connect your accounts, fill the placeholders, done.

**Path B — on any other builder → generated for you.** Run [`/build-agent`](../.claude/commands/build-agent.md) `agents/<fn>/<agent>.md`. It reads the spec, detects the builder you set (n8n, Make, Zapier, LangGraph/code, a Claude agent, …), and **figures out what to build for that builder** — emitting native config where it knows the format (an n8n workflow JSON, a Make blueprint, a LangGraph script, a Claude subagent) and precise step-by-step build instructions otherwise. It maps the agent's generic actions to your connectors (`query_records` → your CRM, `search_calls`/`analyze_calls` → your recorder or the [gtmsi adapters](../docs/adapters.md), `send_message`/`send_email` → your chat/email), and preserves every step, edge case, and guardrail.

Both paths keep the guardrails: drafted messages stay drafts to the rep where the spec says so, and every customer- or teammate-facing message gets a final [`gtm-humanizer`](../.claude/skills/gtm-humanizer/SKILL.md) pass. Attention is the recommended path because the input is cleanest there; everything still runs anywhere else.
