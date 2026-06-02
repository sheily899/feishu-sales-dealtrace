"""Case Study Generator — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/marketing/case-study-generator.md).
Custom tools wrap your stack: get_call, query_crm, send_slack_dm. Claude confirms the call is a win,
drafts a structured case study from the call + CRM facts, and DMs it to the marketing owner as a
DRAFT. It never publishes and never contacts the customer.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You invoke it per
    analyzed call from your recorder's "conversation analyzed" webhook. Custom tools are registered
    via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions). Either way, paste SYSTEM_PROMPT and wire the same three tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / CRM / Slack calls marked TODO with your real APIs.
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Case Study Generator agent. For the analyzed call you are given:
1. Use get_call to read the call and confirm it is a success story (strong positive outcome,
   measurable result, satisfied customer, or a closed-won deal). If it is NOT, send a one-line Slack
   note that no case study was drafted and why, then stop.
2. Use query_crm to gather the deal facts: account, industry, size, deal value, contacts, the dates
   that anchor the timeline. From the call, extract the customer's stated challenge, what they
   adopted and why, the results with any metric, and the most quotable moments verbatim.
3. Draft a structured case study with sections: Title, Client Overview, Challenge, Solution, Results,
   Customer Quote (verbatim), Why it matters. Do not invent numbers, quotes, or outcomes.
4. Use send_slack_dm to deliver the draft to the marketing owner with a review checklist beneath:
   source call link, quotes needing customer approval, and any unverified fact to confirm.
This is a DRAFT for review. Never publish and never address the customer. Humanizer rules on the
draft: no em dashes, no AI throat-clearing, no hype adjectives."""


@tool("get_call", "Read a call's transcript and metadata by id.", {"call_id": str})
async def get_call(args):
    # TODO: call your recorder's API, or load the transcript via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("query_crm", "Read CRM account/opportunity facts for the case study.", {"account_or_deal": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return account, industry, size, value, contacts, dates.
    raise NotImplementedError("Wire to your CRM API")


@tool("send_slack_dm", "DM the case-study draft to the marketing owner.", {"user_id": str, "text": str})
async def send_slack_dm(args):
    # TODO: send a Slack DM (Web API or webhook).
    raise NotImplementedError("Wire to Slack")


async def run_for_call(call_id: str):
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[get_call, query_crm, send_slack_dm])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__get_call",
            "mcp__gtm_tools__query_crm",
            "mcp__gtm_tools__send_slack_dm",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt=f"Draft a case study from call {call_id} if it is a success story, and DM it to marketing.", options=options):
        pass


if __name__ == "__main__":
    # Invoke per analyzed call, e.g. from your recorder's "conversation analyzed" webhook handler.
    import sys
    asyncio.run(run_for_call(sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"))
