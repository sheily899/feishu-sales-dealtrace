"""Competitor Ping — Claude managed agent (Claude Agent SDK).

Per-call agent: runs once per analyzed call. The agent's logic lives in SYSTEM_PROMPT
(mirrors agents/revenue-operations/competitor-ping.md). Custom tools wrap your stack:
get_call_details, search_calls, send_channel_message. Claude scans the transcript for competitor
mentions and extracts the intelligence itself, then posts the alert (only when competitors are found).

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You invoke it once
    per analyzed call (wire your recorder's "conversation analyzed" webhook to run_for_call(call_id)).
    Custom tools are registered via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) you invoke from your webhook handler. Either way, paste SYSTEM_PROMPT and wire the same
    three tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio
import sys

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Competitor Ping agent. You run once per analyzed call. On each run:
1. Use get_call_details for the triggering call (full transcript, attendees and roles, deal/account,
   rep, date). On a manual/backfill run, use search_calls over the last 7 days and process each call.
2. Detect competitor mentions: explicit competitor names, implicit references ('another vendor', 'the
   other tool we're looking at', 'the incumbent'), and competitor product references. Check the known
   competitor list; a company not on it is a NEW competitor to verify. If no competitor comes up in a
   competitive or evaluative context, send nothing and stop.
3. For each competitor, extract: mention context (PROSPECT-INITIATED / REP-INITIATED /
   ACTIVE-EVALUATION / INCUMBENT / PAST-USER), strengths cited (with quotes), weaknesses cited (with
   quotes), prospect sentiment toward the competitor (POSITIVE / NEUTRAL / NEGATIVE), the rep's
   positioning response and whether it landed, and win/loss risk (HIGH / MODERATE / LOW).
4. Post the alert with send_channel_message in the canonical format: header table (deal, rep, call
   date, competitors detected), one intelligence block per competitor (context, win/loss risk,
   sentiment, strengths, weaknesses, rep response, the most revealing quote), then 2-3 recommended
   actions (battlecard, bake-off, switcher case study).
A mention only in passing (e.g. 'I used to work at [Competitor]') is not flagged. On an internal call
label the source INTERNAL-DISCUSSION. Tie every strength, weakness, and risk call to a transcript
quote; no invented competitor claims. Humanizer rules on the message: no em dashes, no AI
throat-clearing, no hype adjectives, one clear ask."""


@tool("get_call_details", "Fetch a call's transcript, attendees, and metadata by id.", {"call_id": str})
async def get_call_details(args):
    # TODO: call your recorder's API, or load the transcript via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("search_calls", "Find recent calls (manual or backfill runs).", {"query": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the gtmsi adapters.
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("send_channel_message", "Post the competitive-intel alert to a team channel.", {"channel": str, "text": str})
async def send_channel_message(args):
    # TODO: post to Slack/Teams (Web API or webhook).
    raise NotImplementedError("Wire to your chat tool")


async def run_for_call(call_id: str):
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[get_call_details, search_calls, send_channel_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__get_call_details",
            "mcp__gtm_tools__search_calls",
            "mcp__gtm_tools__send_channel_message",
        ],
        permission_mode="acceptEdits",
    )
    prompt = f"A call was just analyzed (id: {call_id}). Scan it for competitor mentions and post the alert if any are found."
    async for _ in query(prompt=prompt, options=options):
        pass


if __name__ == "__main__":
    # Invoke per analyzed call, e.g. from your recorder's "conversation analyzed" webhook handler.
    asyncio.run(run_for_call(sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"))
