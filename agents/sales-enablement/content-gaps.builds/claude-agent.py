"""Content Gaps — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/sales-enablement/content-gaps.md).
Custom tools wrap your stack: search_calls, send_channel_message. Claude does the
extraction/clustering/ranking itself, then posts the weekly report.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You run it on a
    schedule (cron / APScheduler). Custom tools are registered via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) you invoke from cron. Either way, paste SYSTEM_PROMPT and wire the same two tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Content Gaps agent. On each weekly run:
1. Use search_calls to pull every analyzed call from the last 7 days across all reps (with account,
   product line, rep, sentiment). If none, send a Slack note that no calls were found this week, then
   stop.
2. From those calls, extract every prospect question/objection, the rep's answer (and whether it
   resolved the question), and rep uncertainty signals (filler, deflection, hedging, "I'll have to
   check", a promise to follow up). Quote the moment where possible.
3. Cluster the questions into recurring themes, merging variants of the same question.
4. Score each theme by frequency (calls and distinct reps) and impact (whether it surfaced in stalled
   or negative-sentiment deals). Rank by frequency then impact.
5. For each top theme, recommend one concrete enablement action (one-pager, FAQ, demo clip,
   battlecard update, micro-training), and separately call out broader training needs observed. If
   reps answered confidently across the board, say so and skip recommendations rather than inventing
   gaps.
6. Post the report with send_channel_message in the canonical format.
Keep a constructive, improvement-focused tone. Use single stars for emphasis, never double stars.
Humanizer rules on the message: no em dashes, no AI throat-clearing, no hype adjectives, one clear
ask."""


@tool("search_calls", "Pull the week's analyzed calls (with metadata).", {"since_days": int})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("send_channel_message", "Post the content-gap report to a team channel.", {"channel": str, "text": str})
async def send_channel_message(args):
    # TODO: post to Slack/Teams (Web API or webhook).
    raise NotImplementedError("Wire to your chat tool")


async def run_once():
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[search_calls, send_channel_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__search_calls",
            "mcp__gtm_tools__send_channel_message",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt="Run this week's content-gap analysis now and post the report.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 8 * * 1  python claude-agent.py
    asyncio.run(run_once())
