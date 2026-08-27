"""Objection Catcher — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/sales-enablement/objection-catcher.md).
Custom tools wrap your stack: search_calls, query_crm, send_email. Claude does the
extraction/clustering/scoring itself, then emails the weekly digest.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You run it on a
    schedule (cron / APScheduler). Custom tools are registered via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) you invoke from cron. Either way, paste SYSTEM_PROMPT and wire the same three tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / CRM / email calls marked TODO with your real APIs.
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Objection Catcher agent. On each weekly run:
1. Use search_calls to collect every call from the last 7 days that has a transcript. If none, send a
   short email that no recorded calls with transcripts were found this week, then stop.
2. For each call, extract every objection: the objection quote, its moment timestamp (mm:ss), the
   category, the rep's response quote, and a short response-pattern label.
3. Normalize objections into this fixed taxonomy (merge variants): Pricing, Timing/Priority,
   Competitor, Feature Gap, Security/Legal, Integration, Authority, ROI/Proof, Contract/Procurement,
   Other.
4. Score each objection/response pair 0-100 on clarity, empathy, proof, and a clear next step. Where
   CRM outcome data is available (use query_crm), weight by meeting booked / stage advanced /
   won/lost. If an objection has no captured rep response, list it as unhandled and flag it as a
   coaching opportunity.
5. Rank categories by frequency and impact; per top category select the 1-3 highest-scoring rebuttal
   snippets with a one-line note on why each worked.
6. Compute weekly stats (total objections, % of calls with objections, week-over-week change,
   best-performing patterns, low-score coaching opportunities) and 2-4 coaching tips per top category.
7. Email the digest (plain text) with send_email.
Keep a constructive tone. Tie every objection and rebuttal to a real call quote and timestamp.
Humanizer rules on the email: no em dashes, no AI throat-clearing, no hype adjectives, one clear ask."""


@tool("search_calls", "Collect the week's calls that have transcripts.", {"since_days": int})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("query_crm", "Read deal outcomes (stage/advanced/won/lost) to weight rebuttal scores.", {"soql_or_filter": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) for outcome context. Optional - skip if unavailable.
    raise NotImplementedError("Wire to your CRM API (optional)")


@tool("send_email", "Email the weekly objection-handling digest.", {"to": str, "subject": str, "body": str})
async def send_email(args):
    # TODO: send via your email tool (Gmail/Outlook API or SMTP).
    raise NotImplementedError("Wire to your email tool")


async def run_once():
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[search_calls, query_crm, send_email])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__search_calls",
            "mcp__gtm_tools__query_crm",
            "mcp__gtm_tools__send_email",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt="Run this week's objection analysis now and email the digest.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 8 * * 1  python claude-agent.py
    asyncio.run(run_once())
