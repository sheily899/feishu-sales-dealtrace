"""Social Proof Finder — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/marketing/social-proof-finder.md). Custom
tools wrap your stack: search_calls, send_slack_message. Claude scans the week's calls for genuine
social proof and posts a report for marketing and sales.

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

SYSTEM_PROMPT = """You are the Social Proof Finder agent. On each run:
1. Use search_calls to find all customer-facing calls from the last 7 days. If none, send a Slack
   note that no calls were recorded and there is no social proof to report, then stop.
2. Flag moments of genuine customer satisfaction, success, or positive outcomes. PRIORITIZE quotes
   that are specific, authentic, and mention a measurable result. AVOID false positives: routine
   politeness ('thanks for your help'), neutral status talk, or anything lukewarm does NOT count.
3. Group results by account, lead with a one-line header (count of stories), then one entry per
   story: call title, one-line summary, the verbatim quote, account / speaker + title, call link.
   Sort the strongest, results-backed quotes first.
4. Use send_slack_message to post the report, noting clearly that quotes are unverified draft
   material and need customer approval before any public use.
Every quote is verbatim and tied to its source call. Humanizer rules on the report: no em dashes, no
AI throat-clearing, no hype adjectives, one clear ask."""


@tool("search_calls", "Find customer-facing calls in a window and their transcripts.", {"window": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("send_slack_message", "Post the social-proof report to a Slack channel.", {"channel": str, "text": str})
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
    async for _ in query(prompt="Run the weekly social-proof scan now and post the report.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 8 * * 1  python claude-agent.py
    asyncio.run(run_once())
