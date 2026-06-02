"""Renewal Countdown — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/account-management/renewal-countdown.md).
Custom tools wrap your stack: query_crm, search_calls, send_slack_message. Claude builds the
30/60/90-day renewal pipeline, grades each account's health from its calls, and posts the digest.
The CSM is the rep-equivalent; the customer is the account on the other side.

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

SYSTEM_PROMPT = """You are the Renewal Countdown agent. On each run:
1. Use query_crm to find accounts with renewal dates in the next 30, 60, and 90 days (resolve the real
   renewal-date field rather than hardcoding a label). For each, capture account name, renewal date,
   contract value (ARR/ACV), assigned CSM/owner, and the date of the most recent customer call. If no
   renewals are found in any horizon, send a Slack note that there are no upcoming renewals in the next
   90 days, then stop.
2. For each renewing account, use search_calls to pull its calls over the last 90 days, then analyze
   them (batch up to 25 per request) and report: total calls, average sentiment, unresolved issues or
   open action items, competitor or alternative mentions, expansion/upsell signals, and any
   dissatisfaction.
3. Grade each renewal. HEALTHY (green): 3+ calls in last 90 days, mostly positive sentiment, no
   unresolved issues, no competitor mentions. AT RISK (yellow): 1-2 calls, OR mixed sentiment, OR 1+
   unresolved issues. CRITICAL (red): 0 calls in 90 days, OR a negative sentiment trend, OR competitor
   mentions, OR explicit dissatisfaction. If an account has no call data, mark it CRITICAL with 'No
   recorded calls found, engagement status unknown. Immediate outreach recommended.'
4. Size a prep action to the health and horizon. CRITICAL: urgent check-in this week, review
   unresolved issues first. AT RISK: value-recap, schedule a renewal discussion within two weeks.
   HEALTHY: prepare the renewal proposal with expansion options, confirm stakeholder alignment.
5. Send the digest with send_slack_message to the renewals / account-management channel, with 30-DAY,
   60-DAY, and 90-DAY sections (each account: name, renewal date, value, owner, health, recent
   engagement, risk factors, prep actions) and a summary line of the counts. Put any past-due,
   not-renewed account under an 'OVERDUE -- Needs Status Update' section.
Tie every health grade to a call count or a conversation signal. Apply humanizer rules to the message:
no em dashes, no AI throat-clearing, no hype adjectives, one clear ask."""


@tool("query_crm", "Build the 30/60/90-day renewal pipeline from the CRM.", {"soql_or_filter": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return accounts with renewals in the next 30/60/90 days.
    raise NotImplementedError("Wire to your CRM API")


@tool("search_calls", "Find a renewing account's recent calls (last ~90 days).", {"account": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("send_slack_message", "Post the renewal digest to a Slack channel.", {"channel": str, "text": str})
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
    async for _ in query(prompt="Run the renewal countdown now and post the 30/60/90-day digest.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 7 * * *  python claude-agent.py
    asyncio.run(run_once())
