"""Inbound Qualifier — Claude managed agent (Claude Agent SDK).

Per-call agent: runs once per analyzed inbound call. The agent's logic lives in SYSTEM_PROMPT
(mirrors agents/revenue-operations/inbound-qualifier.md). Custom tools wrap your stack:
get_call_details, query_crm, send_channel_message. Claude scores BANT and ICP fit, derives the
disposition, then posts the qualification report.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). Trigger run_once()
    from your recorder's "conversation analyzed" webhook handler, passing the call id.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions). Either way, paste SYSTEM_PROMPT and wire the same three tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / CRM / Slack calls marked TODO with your real APIs.
"""
import asyncio
import sys

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Inbound Qualifier agent, triggered once per analyzed inbound call. On
each run:
1. Use get_call_details to fetch the analyzed call by its id (transcript, attendees/roles, company,
   rep). If no transcript is available, post that qualification could not be completed and recommend
   manual review, then stop.
2. Score BANT (0-3 per dimension, 12 max), each with one line of transcript evidence: Budget,
   Authority, Need, Timeline (3 CONFIRMED / 2 PARTIAL / 1 IMPLIED / 0 MISSING). Total = sum out of 12.
3. Use query_crm to read firmographics for ICP fit (company size, industry, existing-customer flag).
   Rate ICP fit against the configured profile (industry, company size, use-case match, tech-stack
   fit, geography): GOOD (4-5 criteria), PARTIAL (2-3), POOR (0-1).
4. Determine disposition: HOT (BANT 10-12, ICP Good), WARM (BANT 7-9, or 10+ with Partial ICP), COOL
   (BANT 4-6), DISQUALIFIED (BANT 0-3, or ICP Poor regardless of BANT).
5. Post the report with send_channel_message in the canonical format: header table (lead, call date,
   rep, lead score, BANT score, ICP fit), BANT breakdown (one line of evidence per dimension), ICP
   fit notes, recommended next steps, and the key quotes that justify it.
If the call is under 5 minutes, score what you can and mark unaddressed dimensions 0 with 'Not
discussed, call too short'. Qualify the primary contact if several prospects are present. If it is an
existing customer asking about a new product, flag it EXPANSION not inbound. Tie every BANT score and
the disposition to a transcript quote or CRM firmographic. Humanizer rules on the message: no em
dashes, no AI throat-clearing, no hype adjectives, one clear ask."""


@tool("get_call_details", "Fetch an analyzed call (transcript + metadata) by its id.", {"call_id": str})
async def get_call_details(args):
    # TODO: call your recorder's API, or load the transcript via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("query_crm", "Read firmographics / existing-customer flag for ICP fit.", {"company_or_contact": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return company size, industry, customer flag.
    raise NotImplementedError("Wire to your CRM API")


@tool("send_channel_message", "Post the qualification report to a team channel.", {"channel": str, "text": str})
async def send_channel_message(args):
    # TODO: post to Slack/Teams (Web API or webhook).
    raise NotImplementedError("Wire to your chat tool")


async def run_once(call_id: str):
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[get_call_details, query_crm, send_channel_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__get_call_details",
            "mcp__gtm_tools__query_crm",
            "mcp__gtm_tools__send_channel_message",
        ],
        permission_mode="acceptEdits",
    )
    prompt = f"An inbound call (id: {call_id}) was just analyzed. Score BANT and ICP fit and post the qualification report."
    async for _ in query(prompt=prompt, options=options):
        pass


if __name__ == "__main__":
    # Invoke from your recorder's "conversation analyzed" webhook with the call id.
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    asyncio.run(run_once(call_id))
