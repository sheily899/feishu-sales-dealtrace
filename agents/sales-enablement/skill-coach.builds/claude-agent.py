"""Skill Coach — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/sales-enablement/skill-coach.md).
Custom tools wrap your stack: search_calls, get_call_details, send_slack_message. Claude does the
skill evaluation and coaching synthesis itself, then posts one alert per flagged rep.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You run it on a
    schedule (cron / APScheduler). Custom tools are registered via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) for Anthropic-hosted sessions you invoke from cron. Use that if you don't want a
    long-running process. Either way, paste SYSTEM_PROMPT and wire the same tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Skill Coach agent. On each run:
1. Use search_calls to pull every team call from the last 7 days and group by rep. If a rep has
   fewer than 2 calls, note 'Limited data' and only flag high-confidence gaps.
2. For each rep, evaluate five skills and decide proficient (no alert) or gap (alert): Discovery
   Depth, Presentation Clarity, Objection Recovery, Rapport Building, Closing Technique.
3. For each gap, use get_call_details to extract one specific call moment (call name/date, a
   paraphrase of what happened, and what the rep should have done instead).
4. Assign one concrete coaching exercise per gap (e.g. Discovery Depth -> role-play the 5-Whys to
   reach financial impact within 5 follow-ups; Closing -> end every call with a calendar invite).
5. Send one alert per rep with at least one gap (up to 3 gap blocks per rep) via send_slack_message,
   and list reps with no gaps in a short summary. If no calls for any rep, send a note that alerts
   were skipped and stop.
Tie every gap and moment to a specific call and quote. Humanizer rules on the message: no em dashes,
no AI throat-clearing, no hype adjectives, one clear ask."""


@tool("search_calls", "Find team calls in a date window. Returns call ids + metadata (rep, account).", {"date_range": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("get_call_details", "Fetch the transcript/details for one call id (for coaching moments).", {"call_id": str})
async def get_call_details(args):
    # TODO: call your recorder's API for the full transcript of this call.
    raise NotImplementedError("Wire to your call recorder")


@tool("send_slack_message", "Post a coaching alert to a Slack channel.", {"channel": str, "text": str})
async def send_slack_message(args):
    # TODO: post to Slack (Web API or webhook).
    raise NotImplementedError("Wire to Slack")


async def run_once():
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[search_calls, get_call_details, send_slack_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__search_calls",
            "mcp__gtm_tools__get_call_details",
            "mcp__gtm_tools__send_slack_message",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt="Run the weekly skill coaching now and post the alerts.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 8 * * 1  python claude-agent.py
    asyncio.run(run_once())
