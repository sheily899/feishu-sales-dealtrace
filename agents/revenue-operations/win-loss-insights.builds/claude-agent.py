"""Win Loss Insights — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/revenue-operations/win-loss-insights.md).
Custom tools wrap your stack: query_crm, search_calls, send_slack_message. Claude does the
analysis itself, then posts the monthly report.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You run it on a
    schedule (cron / APScheduler). Custom tools are registered via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) for Anthropic-hosted sessions you invoke from cron. Use that if you don't want a
    long-running process. Either way, paste SYSTEM_PROMPT and wire the same three tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the CRM / recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Win Loss Insights agent. You run weekly but analyze the trailing 30
days. On each run:
1. Use query_crm to list every deal closed-won or closed-lost in the past 30 days (account, outcome,
   rep, value if known, cycle length if determinable). If stages are not exposed, infer outcomes
   from call context.
2. For each closed deal, use search_calls to pull its calls, grouped by deal.
3. Analyze the WON and LOST cohorts SEPARATELY across five dimensions: Win Themes, Loss Themes,
   Competitive Dynamics, Sales Cycle Patterns, Pricing Sensitivity.
4. Repeat for the prior 30-day window (days 31-60 ago) and compare: win-rate trend, theme shifts,
   competitive shifts, cycle-length change.
5. Produce 3-5 strategic recommendations with rationale.
6. Send the report with send_slack_message in the canonical format (executive summary, win themes,
   loss themes, competitive table, sales-cycle patterns, pricing insights, recommendations, trend
   vs prior period, source line).
Edge cases: fewer than 3 closed deals -> flag the small sample; no losses -> wins only, note loss
analysis resumes when data is available; no prior-period data -> omit trend comparisons.
Tie every theme and number to CRM data or a call quote. Humanizer rules on the message: no em dashes,
no AI throat-clearing, no hype adjectives, one clear ask."""


@tool("query_crm", "Read CRM opportunities. Use to list closed-won/closed-lost deals in a window.", {"soql_or_filter": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return the matching opportunities.
    raise NotImplementedError("Wire to your CRM API")


@tool("search_calls", "Find the calls/transcripts tied to a deal or account.", {"deal_or_account": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("send_slack_message", "Post the report to a Slack channel.", {"channel": str, "text": str})
async def send_slack_message(args):
    # TODO: post to Slack (Web API or webhook).
    raise NotImplementedError("Wire to Slack")


async def run_once():
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[query_crm, search_calls, send_slack_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__query_crm",
            "mcp__gtm_tools__search_calls",
            "mcp__gtm_tools__send_slack_message",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt="Run the monthly win/loss analysis now and post the report.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 8 * * 1  python claude-agent.py
    asyncio.run(run_once())
