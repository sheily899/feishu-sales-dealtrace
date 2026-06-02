# Cross Seller Radar

> After every analyzed existing-customer call, score it for expansion signals against what the account already owns and post one alert for the real opportunities: the signals, the products they map to, the approach, and the value at stake.

**Function:** Revenue Operations · **Trigger:** per call (conversation analyzed) · **Template id:** `AGTCrossSeller01`
**Files:** [`cross-seller-radar.json`](./cross-seller-radar.json) (Attention agent-builder template) · [`cross-seller-radar.activepieces.json`](./cross-seller-radar.activepieces.json) (Activepieces flow)

This page is the build-ready spec. It is platform-agnostic: any agent builder (Attention/Activepieces, n8n, Zapier, Make, LangGraph, a custom GPT/Claude agent) can implement it from the sections below. See [Build it in your stack](#build-it-in-your-stack).

---

## Goal

For each existing-customer call, surface expansion opportunities the account team can act on:
1. Catch cross-sell and expansion signals the moment the call is analyzed.
2. Score the opportunity from five weighted signal categories and alert only on HIGH and MEDIUM.
3. Map every signal to a specific product the customer does not yet own, with a confidence rating.
4. Hand over a concrete approach and an estimated expansion value, timed around renewal.

## When it fires

- **Type:** per call. Fires once when a conversation finishes analyzing (the recorder's "conversation analyzed" webhook). The trigger payload carries the call id and basic metadata (account, rep).
- **Silent below threshold:** only HIGH (score 8+) and MEDIUM (4-7) opportunities are alerted. LOW and NONE send nothing.

## Inputs / data required

| Data | Source | Generic capability |
|---|---|---|
| The just-analyzed call (transcript, attendees/roles, account, rep, date) | Call recorder | `search_calls` |
| Extracted cross-sell signals across the five categories | LLM over the transcript | `analyze_calls` |
| What the account already owns (current products, ACV, renewal date) | CRM | `query_records` |
| The full product catalog and need-to-product mapping | Organization context | provided to the prompt |

## Tools / capabilities

| Generic action | What it does here | On Attention | On any other stack |
|---|---|---|---|
| `search_calls` | Fetch the analyzed call by id | Attention `search_calls` | recorder API, or the [gtmsi adapters](../../docs/adapters.md) over the export |
| `analyze_calls` | Score the five signal categories from the transcript | `ask_attention` | an LLM step over the transcript |
| `query_records` | Read current products / ACV / renewal for the account | CRM tool / `ask_attention` | your CRM's API/MCP (Salesforce, HubSpot, ...) |
| `send_message` | Post the alert to a channel | Slack/Teams tool | your chat tool's API/MCP |

This agent is **read-only on your data**. Its only side effect is posting one message (and only for qualified opportunities).

## How it works (step by step)

1. **Retrieve the conversation and customer context.** `search_calls` by the trigger's call id, then `ask_attention` to query what the account already owns (current products, ACV, renewal date) so you only pitch what they lack.
2. **Scan for cross-sell signals** across five categories: **A** explicit pain matching an unowned product (3 pts each), **B** questions about additional capabilities (2 pts each), **C** expansion signals like new teams, growth, volume pricing (2 pts each), **D** dissatisfaction with a third-party tool you could replace (3 pts each), **E** advocacy / strong satisfaction (1 pt each, enablers). Total = sum of points.
3. **Qualify the opportunity:** HIGH (8+), MEDIUM (4-7), LOW (1-3), NONE (0). Alert only on HIGH and MEDIUM.
4. **Map signals to specific products** the customer does not own, each with a confidence (HIGH direct / MEDIUM likely / LOW possible) and what they use today, if anything.
5. **Compose and post** the alert in the exact [Output](#output) format, then run it through the **[gtm-humanizer](../../.claude/skills/gtm-humanizer/SKILL.md)** as the final pass.

> The verbatim operating prompt (with the full scoring rules and product-mapping structure) is the single source of truth in [`cross-seller-radar.json`](./cross-seller-radar.json) under `template.agent.instructions`. This section is its readable summary.

## Output

A single message (only for HIGH and MEDIUM opportunities):

```
Cross-Sell Radar -- Expansion Opportunity Detected
| Account | Current Products | Current ACV | Renewal Date | Opportunity Score | Rep | Call Date |

SIGNALS DETECTED  (per signal)
  [category]: "[quote or paraphrase]" -> product match · confidence [HIGH/MEDIUM/LOW]

RECOMMENDED APPROACH  ->  ordered next steps (discovery, case study, bundled proposal pre-renewal)
ESTIMATED EXPANSION VALUE  ->  additional ACV, or "requires scoping call to estimate"
KEY QUOTES  ->  the most compelling customer quotes
```

## Edge cases

- **No signals (score 0):** send nothing. Silence means no opportunity was found.
- **Churn risk:** if the dissatisfaction is with the CURRENT product (not a third-party tool), do not flag as cross-sell. Note it may need a retention intervention and suggest involving customer success.
- **Unknown product catalog:** if the Organization context lists no products, list the raw signals for manual review and flag that mapping was not possible.
- **Prospect call (not a customer yet):** skip. Cross-sell applies only to existing customers.
- **Multiple opportunities in one call:** list all in a single alert, ordered by confidence (highest first).

## Guardrails

- Read-only on CRM and recorder. The only write is the one channel message, and only for qualified opportunities.
- Every signal ties to something the customer actually said; every product match is one they do not already own.
- Final **humanizer** pass: no em dashes, no AI throat-clearing, no hype, one clear ask.

## Build it in your stack

**Attention (Activepieces-based builder):** import [`cross-seller-radar.activepieces.json`](./cross-seller-radar.activepieces.json). It matches Attention's export schema: the `@activepieces/piece-attention` `webhookTrigger` ("when one of my calls is analyzed") -> an `askAttention` step that pulls what the account owns and scores the signals -> a Slack `send_channel_message`. On import, connect your Attention and Slack accounts and fill `<YOUR_ATTENTION_USER_ID>` and `<YOUR_SLACK_CHANNEL_ID>`. The fully-managed alternative is to import the agent template [`cross-seller-radar.json`](./cross-seller-radar.json).

**Any other builder — pre-built for you** in [`cross-seller-radar.builds/`](./cross-seller-radar.builds/):

| Builder | Build | Form |
|---|---|---|
| Claude Managed Agents (Agent SDK) | [`claude-agent.py`](./cross-seller-radar.builds/claude-agent.py) | runnable Python (custom tools + system prompt) |
| Claude Code subagent | [`claude-code-subagent.md`](./cross-seller-radar.builds/claude-code-subagent.md) | drop into `.claude/agents/` |
| n8n | [`n8n.json`](./cross-seller-radar.builds/n8n.json) | importable workflow |
| LangGraph / code | [`langgraph.py`](./cross-seller-radar.builds/langgraph.py) | runnable graph |
| Zapier | [`zapier.md`](./cross-seller-radar.builds/zapier.md) | step-by-step Zap |
| Make | [`make.md`](./cross-seller-radar.builds/make.md) | step-by-step scenario (blueprint JSON pending a sample export) |

On a builder not listed, run [`/build-agent`](../../.claude/commands/build-agent.md) `agents/revenue-operations/cross-seller-radar.md` and it generates the implementation from this spec. The agent logic does not change between platforms; only the bound connectors do.

---
_From GTM Superintelligence agent templates. Native: [`cross-seller-radar.json`](./cross-seller-radar.json) · [`cross-seller-radar.activepieces.json`](./cross-seller-radar.activepieces.json) (Attention). Other builders: [`cross-seller-radar.builds/`](./cross-seller-radar.builds/)._
