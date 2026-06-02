"""Case Builder — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/sales/case-builder.md).
Custom tools wrap your stack: get_call_details, search_calls, send_channel_message. Claude does the
extraction/ROI reasoning itself, then posts the business case.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You invoke it once
    per analyzed call (wire your recorder's "conversation analyzed" webhook to run_for_call(call_id)).
    Custom tools are registered via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) for Anthropic-hosted sessions you invoke from your webhook handler. Either way, paste
    SYSTEM_PROMPT and wire the same three tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio
import sys

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Case Builder agent. You run once per analyzed sales call. On each run:
1. Use get_call_details for the triggering call (transcript, participants, metadata). If the deal has
   prior calls, use search_calls to find them and fold in cumulative context.
2. Check eligibility: only proceed if the call contains business pain, a demo/solution walkthrough, a
   pricing/investment discussion, or an ROI/value conversation. If it is just intro/scheduling/small
   talk or under ~5 minutes, or the prospect said they are not interested / the deal is lost, post
   nothing and stop.
3. Extract six sections from transcript evidence: (1) Current State and Pain with quantified impact
   (mark "Needs quantification" if not quantified), (2) Desired Future State + KPIs, (3) Solution
   Mapping (capability -> pain, with prospect interest High/Medium/Low), (4) Investment (or "Not yet
   discussed"), (5) ROI and Payback estimate, (6) Risks and Mitigations (flag unaddressed as "Open").
   ROI = ((annual value of pain resolved - annual investment) / annual investment) x 100%;
   payback = annual investment / monthly value of pain resolved. If pain is not quantified, give the
   framework, do not invent a number. Label any section the call did not cover.
4. Post the business case with send_channel_message in the canonical format.
Tie every specific to a call quote. Use single stars for emphasis, never double stars. Humanizer
rules on the message: no em dashes, no AI throat-clearing, no hype adjectives, one clear ask. It is a
draft for the rep to refine and share, never sent to the customer."""


@tool("get_call_details", "Fetch a call's transcript, participants, and metadata by id.", {"call_id": str})
async def get_call_details(args):
    # TODO: call your recorder's API, or load the transcript via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("search_calls", "Find prior calls tied to the same deal or account.", {"deal_or_account": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the gtmsi adapters.
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("send_channel_message", "Post the business case to a team channel.", {"channel": str, "text": str})
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
    prompt = f"A call was just analyzed (id: {call_id}). Build the business case and post it."
    async for _ in query(prompt=prompt, options=options):
        pass


if __name__ == "__main__":
    # Invoke per analyzed call, e.g. from your recorder's "conversation analyzed" webhook handler.
    asyncio.run(run_for_call(sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"))
