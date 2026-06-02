"""Objection Drilldown — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/sales-enablement/objection-drilldown.md).
Custom tools wrap your stack: search_calls, get_call_details, send_slack_message. Claude does the
classification/scoring/trend analysis itself, then posts the report.

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

SYSTEM_PROMPT = """You are the Objection Drilldown agent. On each run:
1. Use search_calls to pull every team call from the last 7 days. If fewer than 5, note the small
   sample and that trends may not be meaningful.
2. Classify every prospect objection into ONE category, recording the rep, call id, and a paraphrase,
   from: PRICING/BUDGET, TIMING/URGENCY, COMPETITION, FEATURE-GAPS, AUTHORITY/DECISION-PROCESS,
   SECURITY/LEGAL/COMPLIANCE, INTEGRATION/TECHNICAL, ROI/PROOF.
3. Score the rep's response per objection: Effective (3), Partial (2), Ineffective (1).
4. For each category, extract the top-scoring rebuttal as a reusable template; use get_call_details
   to pull the exact language from that call.
5. Compare this week's frequency by category to the prior 7-day window: flag rising, declining, and
   new categories.
6. Correlate categories with outcomes; flag the categories most tied to calls with no next step as
   high-risk. If no objections at all, send a Slack note saying none were detected and stop.
7. End by posting the report with send_slack_message in the canonical format.
Tie every objection, score, and rebuttal to a specific call and quote. Humanizer rules on the
message: no em dashes, no AI throat-clearing, no hype adjectives, one clear ask."""


@tool("search_calls", "Find team calls in a date window. Returns call ids + metadata (rep, account).", {"date_range": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("get_call_details", "Fetch the transcript/details for one call id (for verbatim rebuttals).", {"call_id": str})
async def get_call_details(args):
    # TODO: call your recorder's API for the full transcript of this call.
    raise NotImplementedError("Wire to your call recorder")


@tool("send_slack_message", "Post the report to a Slack channel.", {"channel": str, "text": str})
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
    async for _ in query(prompt="Run the weekly objection drilldown now and post the report.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 8 * * 1  python claude-agent.py
    asyncio.run(run_once())
