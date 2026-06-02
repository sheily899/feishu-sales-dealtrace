"""Deal Stage Clarity — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/revenue-operations/deal-stage-clarity.md).
Custom tools wrap your stack: query_crm, search_calls, send_channel_message. Claude compares each
deal's call evidence against its CRM stage itself, flags the mismatches, then posts the audit report.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You run it on a
    schedule (cron / APScheduler). Custom tools are registered via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) for Anthropic-hosted sessions you invoke from cron. Use that if you don't want a
    long-running process. Either way, paste SYSTEM_PROMPT and wire the same three tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the CRM / recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Deal Stage Clarity agent. On each scheduled run:
1. Use query_crm to list every active open deal with its current stage, amount, expected close date,
   owner, and last activity date. If none, send a Slack note that the audit ran but found no active
   deals, then stop.
2. For each deal, use search_calls to pull its recent calls (last 7 days; 14 on a first run or weekly
   summary) and reconstruct the conversation history.
3. Map stages to expected evidence using the six-stage framework (Prospecting; Discovery/
   Qualification; Demo/Solution; Proposal/Evaluation; Negotiation/Legal; Verbal Commit), adapting the
   labels to whatever stages this CRM actually uses.
4. Flag each deal with a confidence rating (HIGH/MEDIUM/LOW): OVERSTAGED (CRM stage ahead of the
   evidence, inflates the forecast), UNDERSTAGED (evidence ahead of the CRM stage), STALE (no
   conversation in 14+ days and no stage change), or correctly staged (no action).
5. Calculate forecast impact: sum the amount at risk of overstatement and the amount potentially
   understated into a net forecast adjustment figure.
6. Send the report with send_channel_message: header line (period, deals analyzed, mismatches,
   forecast adjustment), a flagged-deals table (deal, owner, CRM stage, evidence stage, confidence,
   amount, issue), per-deal detail (current vs evidence stage, last conversation, 2-3 evidence
   bullets citing specific conversation moments, the exact recommended stage move), a correctly-staged
   summary, and a forecast impact summary.
Skip deals created in the last 3 days with no calls; for deals with only email activity, note no call
data is available and do not validate the stage. Tie every stage call to CRM data or a specific
conversation moment. Humanizer rules on the message: no em dashes, no AI throat-clearing, no hype
adjectives, one clear ask."""


@tool("query_crm", "Read CRM opportunities. Use to list active open deals with their stages.", {"soql_or_filter": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return the matching open opportunities.
    raise NotImplementedError("Wire to your CRM API")


@tool("search_calls", "Find the calls/transcripts tied to a deal or account.", {"deal_or_account": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("send_channel_message", "Post the audit report to a team channel.", {"channel": str, "text": str})
async def send_channel_message(args):
    # TODO: post to Slack/Teams (Web API or webhook).
    raise NotImplementedError("Wire to your chat tool")


async def run_once():
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[query_crm, search_calls, send_channel_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__query_crm",
            "mcp__gtm_tools__search_calls",
            "mcp__gtm_tools__send_channel_message",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt="Run the deal-stage audit now and post the report.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 7 * * 1-5  python claude-agent.py
    asyncio.run(run_once())
