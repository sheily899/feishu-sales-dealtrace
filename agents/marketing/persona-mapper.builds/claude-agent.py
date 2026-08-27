"""Persona Mapper — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/marketing/persona-mapper.md). Custom tools
wrap your stack: get_call, send_slack_message. Claude maps the personas on the call and their
marketing-relevant priorities, then posts a concise brief to the marketing channel.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You invoke it per
    analyzed call from your recorder's "conversation analyzed" webhook. Custom tools are registered
    via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions). Either way, paste SYSTEM_PROMPT and wire the same two tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Persona Mapper agent. For the analyzed call you are given:
1. Use get_call to read the call. Identify every persona mentioned or speaking: title, department,
   inferred buyer role (economic buyer, champion, technical evaluator, end user, blocker). Pull each
   persona's goals, challenges, and marketing-relevant priorities, and map the buying-group shape.
2. Translate into concrete marketing opportunities: messaging angles, segments worth targeting,
   content/campaign gaps, positioning language the customer used.
3. Use send_slack_message to post a brief with three sections: Personas Identified (one line each),
   Key Priorities, Opportunities for Marketing. Label inferred roles as inferred. Do not invent
   personas, titles, or priorities the call did not support.
This is a working draft for the marketing team to refine. Humanizer rules on the brief: no em dashes,
no AI throat-clearing, no hype adjectives."""


@tool("get_call", "Read a call's transcript, speakers, and metadata by id.", {"call_id": str})
async def get_call(args):
    # TODO: call your recorder's API, or load the transcript via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("send_slack_message", "Post the persona brief to a Slack channel.", {"channel": str, "text": str})
async def send_slack_message(args):
    # TODO: post to Slack (Web API or webhook).
    raise NotImplementedError("Wire to Slack")


async def run_for_call(call_id: str):
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[get_call, send_slack_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__get_call",
            "mcp__gtm_tools__send_slack_message",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt=f"Map the personas and marketing priorities on call {call_id} and post the brief.", options=options):
        pass


if __name__ == "__main__":
    # Invoke per analyzed call, e.g. from your recorder's "conversation analyzed" webhook handler.
    import sys
    asyncio.run(run_for_call(sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"))
