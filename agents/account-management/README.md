# Account Management agents

4 agents.

| Agent | What it does | Trigger | Integrations |
|---|---|---|---|
| [Churn Alert](./churn-alert.md) | Delivers weekly reports highlighting potential churn risks and recommended retention actions to help teams proacti… | 🗓 daily | call_recorder, communication, crm |
| [Renewal Countdown](./renewal-countdown.md) | Monitors upcoming contract renewals and sends proactive alerts with customer health context and engagement trends. | 🗓 daily* | call_recorder, communication, crm |
| [Risk Watch](./risk-watch.md) | Monitors accounts for risk indicators including negative sentiment, engagement drops, and unresolved issues. | 📞 per call | call_recorder, communication, crm |
| [Sentiment Watch](./sentiment-watch.md) | Monitors conversation analyses for extreme sentiment (highly positive or negative) and immediately flags those moments f… | 📞 per call | call_recorder, communication |

_🗓\* = resolves the org's real CRM stages/renewal field first (see [../../docs/crm-stages.md](../../docs/crm-stages.md))._
