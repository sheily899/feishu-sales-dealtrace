# Churn Alert

**Function:** Account Management  ·  **Integrations:** crm, communication  ·  **Template id:** `AGTChurnAlert01`

> Delivers weekly reports highlighting potential churn risks and recommended retention actions to help teams proactively address at-risk accounts.

## When it fires

**Detector:** Trigger if the user wants to identify, monitor, or report on customers at risk of churning or leaving, or wants retention alerts and churn risk analysis.

**Signal keywords:** `churn`, `retention`, `at-risk`, `churn risk`, `cancellation`, `customer health`, `renewal risk`, `riesgo de churn`, `clientes en riesgo`

## What it does

Purpose

This agent delivers a weekly team report highlighting potential churn risks and recommended retention actions. It helps Customer Success, Sales, and Marketing teams proactively address at-risk accounts.

Behavior

Runs automatically once per week (e.g., Monday 9:00 AM).

Reviews customer data from your CRM, product analytics, and conversation insights to detect early churn signals.

Focuses on pattern recognition — declining usage, negative sentiment, or upcoming renewals without engagement.

Produces a concise, structured team summary grouped by risk level (High, Medium, Low).

Includes specific action recommendations for each account, written in a professional, solution-oriented tone.

Procedure

Input Sources:

CRM account data (renewal date, success score, NPS, CSM owner).

Product analytics (login frequency, usage trends, adoption rate).

Conversation sentiment and engagement data from your call recorder.

Support interactions or unresolved cases from CRM/ticketing systems.

Analysis Steps:

Detect churn risk indicators using multi-source data fusion.

Assign severity levels (High / Medium / Low).

Summarize key risk drivers and recommended retention tactics.

Compile results into a team-communication-friendly message for executive or CSM review.

Make sure this only refers to active customers and not live deals! Further, anonymize the company names instead of using the actual ones.

Output Format (Team Message):

⚠️ *Weekly Churn Risk Report* — Week of {date_range}

🧾 *High-Risk Accounts:*
1. *{Account Name}* — {Key risk indicators, e.g., "Usage down 40%, negative sentiment last call"}
   🔹 *Recommendation:* {Specific proactive step, e.g., "Schedule renewal strategy call and share success metrics."}

🟠 *Medium-Risk Accounts:*
1. *{Account Name}* — {Moderate risk summary}
   🔹 *Recommendation:* {Suggested engagement action}

🟢 *Low-Risk (Monitor):*
1. *{Account Name}* — {Minor fluctuations or early signals}

📊 *Summary:* {# of accounts by risk category}
🧩 *Source:* Data combined from your CRM, product analytics, and conversation insights

## Tools / actions
- **CRM** — Query Records
- **Communication** — Send Message

## Before sending: humanize

This agent drafts a customer- or teammate-facing message, so run the draft through the [`gtm-humanizer`](../../.claude/skills/gtm-humanizer/SKILL.md) skill as the final step (it auto-loads `humanizer-context.md` for sender voice). Strip AI tells — em dashes, throat-clearing openers, hype words, rule-of-three padding — and keep one clear ask. A message that reads like a bot kills reply rates.

## Trigger

**Type:** Schedule — runs daily at 07:00 (cron `0 7 * * *`, set the timezone to the team's).

---
_From GTM Superintelligence agent templates. Raw definition: [`churn-alert.json`](./churn-alert.json)._
