"""Revenue Sentry — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/revenue-operations/revenue-sentry.md).
Custom tools wrap your stack: query_crm, search_calls, send_slack_message. Claude does the
risk scoring/classification itself, then posts the alert.

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

SYSTEM_PROMPT = """You are the Revenue Sentry agent. On each run:
1. Use query_crm to list every OPEN deal in the pipeline (name, stage, amount, expected close date,
   owner, last activity date).
2. For each deal, use search_calls to pull the calls from the last 14 days and group them by deal.
3. Score each deal 0-3 on five risk dimensions (higher = riskier), each backed by call evidence:
   Engagement Cadence, Sentiment Trajectory, Unresolved Objections, Competitive Pressure,
   Timeline Slippage. Total Risk = sum out of 15. If the close date is today or past due, boost
   Timeline Slippage to 3.
4. Classify each deal: RED ALERT (10-15), ORANGE WARNING (6-9), YELLOW WATCH (3-5),
   GREEN HEALTHY (0-2). Include only RED, ORANGE, and YELLOW in the alert; omit GREEN.
5. Attach a specific recommended intervention to every RED and ORANGE deal.
6. Send the alert with send_slack_message in the canonical format (per-dimension evidence table for
   RED deals, condensed ORANGE list, YELLOW watch list, pipeline health summary with revenue at risk).
If no at-risk deals, send a brief all-clear with total pipeline value and deal count.
Tie every score to CRM data or a call quote. Humanizer rules on the message: no em dashes, no AI
throat-clearing, no hype adjectives, one clear ask."""


@tool("query_crm", "Read CRM opportunities. Use to list open pipeline deals.", {"soql_or_filter": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return the matching opportunities.
    raise NotImplementedError("Wire to your CRM API")


@tool("search_calls", "Find the calls/transcripts tied to a deal or account.", {"deal_or_account": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("send_slack_message", "Post the alert to a Slack channel.", {"channel": str, "text": str})
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
    async for _ in query(prompt="Run the daily pipeline risk scan now and post the alert.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 7 * * 1-5  python claude-agent.py
    asyncio.run(run_once())
