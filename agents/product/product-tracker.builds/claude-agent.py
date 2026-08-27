"""Product Tracker — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/product/product-tracker.md). Custom tools
wrap your stack: search_calls, send_slack_message. Claude scans the week's calls for product signals,
categorizes and prioritizes them, and posts a structured digest to the product team.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You run it on a
    schedule (cron / APScheduler). Custom tools are registered via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) for Anthropic-hosted sessions you invoke from cron. Either way, paste SYSTEM_PROMPT and
    wire the same two tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Product Tracker agent. On each run:
1. Use search_calls to find all customer-facing calls from the last 7 days. If none, send a Slack
   note that no calls were recorded and there is no product feedback to report, then stop.
2. Extract every product signal, each with account, customer name and title, the exact quote, and the
   rep's response: FEATURE REQUESTS, BUG REPORTS, WORKAROUND MENTIONS, COMPETITIVE FEATURE GAPS,
   PRAISE, USABILITY COMPLAINTS.
3. Categorize each into UX / Usability, Performance, Integrations, Missing Features, Bugs, or Workflow
   Gaps. Prioritize by frequency (3+ customers = High, 2 = Medium, 1 = Low) and customer tier
   (enterprise/strategic outweigh SMB) into P1 (critical) through P4 (monitor). Group duplicates with
   a count.
4. Use send_slack_message to post the digest: a header (calls analyzed, signals extracted, accounts),
   then P1-P4 blocks (label, category, mentions, accounts, representative quote, customer impact),
   then Positive Feedback, Competitive Intel, and Trends vs last week. If one request dominates (5+),
   call it out as a Top Signal at the top.
Every signal ties to a verbatim quote and a named account. Humanizer rules on the digest: no em
dashes, no AI throat-clearing, no hype adjectives, one clear ask."""


@tool("search_calls", "Find customer-facing calls in a window and their transcripts.", {"window": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("send_slack_message", "Post the product-feedback digest to a Slack channel.", {"channel": str, "text": str})
async def send_slack_message(args):
    # TODO: post to Slack (Web API or webhook).
    raise NotImplementedError("Wire to Slack")


async def run_once():
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[search_calls, send_slack_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__search_calls",
            "mcp__gtm_tools__send_slack_message",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt="Run the weekly product-feedback scan now and post the digest.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 8 * * 1  python claude-agent.py
    asyncio.run(run_once())
