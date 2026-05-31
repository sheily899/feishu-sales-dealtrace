# Operations agents

5 agents.

| Agent | What it does | Trigger | Integrations |
|---|---|---|---|
| [AE Handoff](./ae-handoff.md) | Closed-Won Handoff Summarizer  When a CRM Opportunity stage changes to Closed Won, start the handoff process for … | 🔁 stage → won | communication, crm, call_recorder |
| [Compliance Checker](./compliance-checker.md) | Monitors conversations for compliance with regulations, company policies, and legal requirements. | 📞 per call | call_recorder, communication |
| [Cross Team Handoff](./cross-team-handoff.md) | Orchestrates smooth handoffs between teams by creating comprehensive context summaries with conversation history and act… | 🔁 stage → won | call_recorder, communication, crm |
| [Team Collab Agent](./team-collab-agent.md) | Facilitates cross-team collaboration by identifying when other teams need involvement. | 📞 per call | call_recorder, communication |
| [Validate](./validate.md) | Validates and updates CRM data by analyzing conversation intelligence, presenting proposed field changes to reps for approval, and syncing approved updates to your CRM. | 📞 per call | call_recorder, communication, crm |

_🗓\* = resolves the org's real CRM stages/renewal field first (see [../../docs/crm-stages.md](../../docs/crm-stages.md))._
