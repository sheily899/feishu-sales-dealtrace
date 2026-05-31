# Revenue Operations agents

8 agents.

| Agent | What it does | Trigger | Integrations |
|---|---|---|---|
| [Competitor Ping](./competitor-ping.md) | Detects and alerts when competitors are mentioned, tracking competitive positioning and objections. | 📞 per call | call_recorder, communication |
| [Cross Seller Radar](./cross-seller-radar.md) | Detects cross-sell opportunities by analyzing customer needs and product interest signals. | 📞 per call | call_recorder, communication, crm |
| [Deal Stage Clarity](./deal-stage-clarity.md) | Ensures accurate deal staging by analyzing conversation content vs CRM stage. | 🗓 daily* | call_recorder, communication, crm |
| [Inbound Qualifier](./inbound-qualifier.md) | Qualifies inbound leads by analyzing initial conversations for BANT signals and fit with ideal customer profile. | 📞 per call | call_recorder, communication, crm |
| [Lost-Deal Intel](./lost-deal-intel.md) | Extracts actionable intelligence from lost deals including reasons, competitive insights, and improvements. | 🔁 stage → lost | call_recorder, communication |
| [Revenue Sentry](./revenue-sentry.md) | Monitors pipeline health and identifies at-risk deals requiring immediate intervention based on conversation analysis. | 🗓 daily* | call_recorder, communication, crm |
| [Upsell Alert](./upsell-alert.md) | Identifies upsell and expansion opportunities by analyzing customer conversations for budget availability signals and gr… | 📞 per call | call_recorder, communication, crm |
| [Win Loss Insights](./win-loss-insights.md) | Analyzes won and lost deals to identify patterns, competitive dynamics, and key factors influencing outcomes. | 🗓 weekly* | call_recorder, communication |

_🗓\* = resolves the org's real CRM stages/renewal field first (see [../../docs/crm-stages.md](../../docs/crm-stages.md))._
