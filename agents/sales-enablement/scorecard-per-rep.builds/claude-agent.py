"""Scorecard per Rep — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/sales-enablement/scorecard-per-rep.md).
Custom tools wrap your stack: search_calls, get_call_details, send_slack_message. Claude does the
scoring/trend/coaching analysis itself, then posts the scorecard.

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

SYSTEM_PROMPT = """You are the Scorecard per Rep agent. On each run:
1. Use search_calls to pull every team call from the last 7 days and group by rep. If a rep has
   fewer than 3 calls, score only what is reliable and flag 'Insufficient data for full scorecard'.
2. For each rep, score these six dimensions 1-5 from transcript evidence: Discovery Quality,
   Objection Handling, Value Articulation, Next-Step Setting, Talk Ratio (5 = rep talks 30-45%,
   3 = 50-60%, 1 = over 70%), Question Quality. Compute the rep's average.
3. Compare each dimension to the prior 7-day window and mark improved / declined / stable.
4. Pick the 3 lowest-scoring dimensions per rep; for each, use get_call_details to pull a specific
   call example (timestamp or quote) and write one concrete coaching suggestion.
5. Add a team summary: highest performer, most improved, team average, total calls analyzed. If no
   calls for any rep, send a Slack note that none were recorded and stop.
6. End by posting the scorecard with send_slack_message in the canonical format.
Tie every score and coaching priority to a specific call and quote. Humanizer rules on the message:
no em dashes, no AI throat-clearing, no hype adjectives, one clear ask."""


@tool("search_calls", "Find team calls in a date window. Returns call ids + metadata (rep, account).", {"date_range": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("get_call_details", "Fetch the transcript/details for one call id (for coaching examples).", {"call_id": str})
async def get_call_details(args):
    # TODO: call your recorder's API for the full transcript of this call.
    raise NotImplementedError("Wire to your call recorder")


@tool("send_slack_message", "Post the scorecard to a Slack channel.", {"channel": str, "text": str})
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
    async for _ in query(prompt="Run the weekly rep scorecards now and post the report.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 8 * * 1  python claude-agent.py
    asyncio.run(run_once())
