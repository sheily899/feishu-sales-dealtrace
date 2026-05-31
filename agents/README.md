# GTM Agent Templates

All **30** production agent templates, organized into subfolders by function. Each agent has a readable spec (`.md`) and its machine-readable definition (`.json`).

This library ships with **GTM Superintelligence** as a real-world showcase of what production GTM agents look like — use them as inspiration, fork them, or adapt them to any stack. Agents are **platform-agnostic**: they work with any CRM (Salesforce, HubSpot, etc.), any call recorder, any team communication tool (Slack, Teams, etc.), and any email provider. They pair naturally with the coaching/scoring framework in the rest of this repo.

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

## Tooling & portability

There are two ways to run these agents — pick your stack in [`config.yaml`](./config.yaml) and the [`/run-agent`](../.claude/commands/run-agent.md) runner branches automatically:

**On [Attention](https://www.attention.com) (recommended) → native.** These JSON specs are Attention agent-builder templates. Import one into Attention and it runs natively, using `ask_attention` (a natural-language query/analysis over your calls + CRM) plus the `search_calls` / `get_call_details` subtools. Cleanest experience: Attention does the role-labeling, CRM linking, and transcript re-stitching the agents rely on (see [docs/call-recorders.md](../docs/call-recorders.md)), so there's nothing to translate.

**On any other recorder → managed Claude agent.** Run the same spec via `/run-agent` (or any Claude agent runtime) and Claude executes the agent's logic on your stack: it reads pipeline/deal data from your CRM (Salesforce, HubSpot, …) and pulls transcripts from your recorder (Gong, Fireflies, Otter, Recall, Grain, Zoom, …) — or, for any recorder that only exports transcripts, ingests them with the [gtmsi adapters](../docs/adapters.md) — then analyzes them itself. Each tool in a spec carries a `generic_action` so the runner knows how to map `ask_attention` to this generic path. The agent logic is identical; only the data source changes.

Either way the output tools are the same (`send_message` to Slack/Teams, `send_email` to Gmail/Outlook), and every drafted message gets a final [`gtm-humanizer`](../.claude/skills/gtm-humanizer/SKILL.md) pass.
