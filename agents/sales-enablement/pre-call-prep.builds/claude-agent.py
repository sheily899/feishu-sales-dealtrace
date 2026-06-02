"""Pre-Call Prep — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/sales-enablement/pre-call-prep.md).
Custom tools wrap your stack: list_events, query_crm, search_calls, get_call_details,
send_slack_dm. Claude matches meetings to deals, reconstructs context, writes the briefing, then
DMs the rep.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You run it on a
    schedule (cron / APScheduler). Custom tools are registered via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) for Anthropic-hosted sessions you invoke from cron. Use that if you don't want a
    long-running process. Either way, paste SYSTEM_PROMPT and wire the same tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the calendar / CRM / recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Pre-Call Prep agent. On each run:
1. Use list_events to read the rep's meetings today between 7:00 AM and 7:00 PM (title, times,
   link/location, attendee names and emails). If no customer meetings, DM the rep
   'Good morning! You have no customer meetings on your calendar today.' and stop.
2. Use query_crm to match attendees to a CRM account and the most relevant opportunity (prefer
   open; else most recent closed): stage, amount, close date, forecast category.
3. Use search_calls (and get_call_details for specifics) to reconstruct each deal from prior
   conversations: dates/types, participants and roles, topics, objections, competitors, next steps,
   sentiment trend, commitments.
4. For each meeting, write a rich block: human-style TL;DR, attendee context, relationship summary,
   opportunity context, recent activity recap, risks/challenges, competitive landscape, recommended
   focus for today, strategic tips, useful artifacts. List meetings in chronological order.
5. DM the whole day to the rep with send_slack_dm. Use emojis and clean headings, NO markdown bold
   or '*' symbols.
Every fact comes from the calendar, CRM, or a prior call. Humanizer rules on the message: no em
dashes, no AI throat-clearing, no hype adjectives, one clear ask."""


@tool("list_events", "Read the rep's calendar events for a day (title, times, attendees).", {"date": str})
async def list_events(args):
    # TODO: call your calendar API (Google/Microsoft).
    raise NotImplementedError("Wire to your calendar API")


@tool("query_crm", "Match attendees to a CRM account + opportunity.", {"emails_or_domains": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return the matching account/opportunity.
    raise NotImplementedError("Wire to your CRM API")


@tool("search_calls", "Find prior calls for an account/opportunity.", {"account_or_opportunity": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("get_call_details", "Fetch the summary/details for one prior call id.", {"call_id": str})
async def get_call_details(args):
    # TODO: call your recorder's API for the summary of this call.
    raise NotImplementedError("Wire to your call recorder")


@tool("send_slack_dm", "DM the briefing to the rep.", {"user_id": str, "text": str})
async def send_slack_dm(args):
    # TODO: post a Slack DM (Web API or webhook).
    raise NotImplementedError("Wire to Slack")


async def run_once():
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[list_events, query_crm, search_calls, get_call_details, send_slack_dm])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__list_events",
            "mcp__gtm_tools__query_crm",
            "mcp__gtm_tools__search_calls",
            "mcp__gtm_tools__get_call_details",
            "mcp__gtm_tools__send_slack_dm",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt="Build today's pre-call prep and DM it to the rep.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 7 * * 1-5  python claude-agent.py
    asyncio.run(run_once())
