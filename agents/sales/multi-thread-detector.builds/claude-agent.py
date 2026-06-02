"""Multi Thread Detector — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/sales/multi-thread-detector.md).
Custom tools wrap your stack: get_call_details, search_calls, send_channel_message. Claude builds the
stakeholder map and scores threading risk itself, then posts the alert.

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

SYSTEM_PROMPT = """You are the Multi Thread Detector agent. You run once per analyzed sales call.
On each run:
1. Use get_call_details for the triggering call (account, deal, participants, rep). Use search_calls
   to find every prior call on the same deal/account.
2. Build a cumulative stakeholder map: for every prospect-side participant, name, title/role where
   stated, and the MEDDPICC role they most likely fill - Champion, Economic Buyer, Technical
   Evaluator, Coach, End User (use the behavioral indicators).
3. Score threading risk: Critical (1 stakeholder or 1 role), High (2 stakeholders but no Economic
   Buyer or no Champion), Medium (3+ stakeholders but 2+ roles uncovered), Low (4+ stakeholders
   covering at least Champion, Economic Buyer, Technical Evaluator). If this is the first call on a
   new deal, use "Early Stage - monitor" instead of Critical; if the only call was inbound/intro, do
   not alert and note that threading assessment begins after more calls. If titles were not stated,
   note "Roles inferred - confirm titles with the rep".
4. For each missing role, give one specific action tied to the pain discussed.
5. Only post (send_channel_message) when risk is Medium or higher; otherwise do nothing.
Never fabricate stakeholders who did not appear on a call. Use single stars for emphasis, never
double stars. Humanizer rules on the message: no em dashes, no AI throat-clearing, no hype, one clear
ask. Output the alert in the canonical format including the Deal Threading Score (roles covered/5)."""


@tool("get_call_details", "Fetch a call's transcript, participants, and metadata by id.", {"call_id": str})
async def get_call_details(args):
    # TODO: call your recorder's API, or load the transcript via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("search_calls", "Find every prior call tied to the same deal or account.", {"deal_or_account": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the gtmsi adapters.
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("send_channel_message", "Post the threading alert to a team channel.", {"channel": str, "text": str})
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
    prompt = f"A call was just analyzed (id: {call_id}). Assess threading on this deal and alert if at risk."
    async for _ in query(prompt=prompt, options=options):
        pass


if __name__ == "__main__":
    # Invoke per analyzed call, e.g. from your recorder's "conversation analyzed" webhook handler.
    asyncio.run(run_for_call(sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"))
