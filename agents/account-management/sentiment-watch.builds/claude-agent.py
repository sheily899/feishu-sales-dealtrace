"""Sentiment Watch — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/account-management/sentiment-watch.md).
Custom tools wrap your stack: get_call, send_slack_dm. Claude reads the call's sentiment, decides
whether it hit an extreme, and DMs the account owner only when it did.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You invoke it per
    analyzed call from your recorder's "conversation analyzed" webhook. Custom tools are registered
    via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) for Anthropic-hosted sessions you invoke from your webhook handler. Either way, paste
    SYSTEM_PROMPT and wire the same two tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Sentiment Watch agent. For the analyzed call you are given:
1. Use get_call to read the call: overall and customer sentiment, top emotion tags, attendees and
   roles (customer vs rep/owner), and the single most revealing quote, verbatim.
2. Classify the sentiment: HIGHLY POSITIVE (strong satisfaction, delight, advocacy, specific praise
   tied to a result), HIGHLY NEGATIVE (strong frustration, churn risk, escalation, threats to
   cancel), or NEUTRAL (routine working tone, polite thanks, logistics). Routine politeness does NOT
   count. When in doubt, treat as NEUTRAL.
3. If NEUTRAL, do nothing and stop. Silence on a non-extreme call is correct.
4. If POSITIVE or NEGATIVE, use send_slack_dm to alert the account owner with: polarity + account,
   a 1-2 sentence why tied to the call, the verbatim quote, one concrete suggested next step, and the
   call link.
Tie every flag to a sentiment read and a verbatim quote. Never message the customer. Humanizer rules
on the alert: no em dashes, no AI throat-clearing, no hype adjectives, one clear ask."""


@tool("get_call", "Read a call's transcript, sentiment, and metadata by id.", {"call_id": str})
async def get_call(args):
    # TODO: call your recorder's API, or load the transcript via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("send_slack_dm", "DM the sentiment alert to the account owner.", {"user_id": str, "text": str})
async def send_slack_dm(args):
    # TODO: send a Slack DM (Web API or webhook).
    raise NotImplementedError("Wire to Slack")


async def run_for_call(call_id: str):
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[get_call, send_slack_dm])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__get_call",
            "mcp__gtm_tools__send_slack_dm",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt=f"Evaluate the sentiment of call {call_id} and alert the owner if it is an extreme.", options=options):
        pass


if __name__ == "__main__":
    # Invoke per analyzed call, e.g. from your recorder's "conversation analyzed" webhook handler.
    import sys
    asyncio.run(run_for_call(sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"))
