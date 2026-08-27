"""Lost-Deal Intel — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/revenue-operations/lost-deal-intel.md).
Custom tools wrap your stack: query_crm, search_calls, send_slack_message. Claude does the
analysis/classification itself, then posts the report.

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

SYSTEM_PROMPT = """You are the Lost-Deal Intel agent. On each run:
1. Use query_crm to list every deal marked Closed-Lost in the last 7 days (name, account, owner,
   amount, stage-at-loss, and the CRM loss reason if present). If none, send a Slack note that no
   deals were lost and pipeline health is stable, then stop.
2. For each lost deal, use search_calls to pull its conversations and reconstruct the timeline.
3. Classify each loss into ONE primary reason plus up to two contributing, each with evidence, from:
   PRICING, COMPETITION, PRODUCT-GAP, TIMING, SALES-EXECUTION, CHAMPION-LOSS, NO-DECISION, LEGAL-SECURITY.
4. Write a per-deal post-mortem: timeline + the turning-point call, the customer's perspective + the
   single most revealing quote, competitive intel (if COMPETITION), a sales-execution rating
   (STRONG/ADEQUATE/WEAK), and a product-fit/systemic-gap signal.
5. If 3+ losses, add cross-deal patterns (repeat competitors, recurring gaps, weak-execution segments).
6. End with 2-3 org-level recommendations for this week, then send the report with send_slack_message.
Tie every claim to CRM data or a call quote. Humanizer rules on the message: no em dashes, no AI
throat-clearing, no hype adjectives, one clear ask."""


@tool("query_crm", "Read CRM opportunities. Use to list Closed-Lost deals in a window.", {"soql_or_filter": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return the matching opportunities.
    raise NotImplementedError("Wire to your CRM API")


@tool("search_calls", "Find the calls/transcripts tied to a deal or account.", {"deal_or_account": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("send_slack_message", "Post the report to a Slack channel.", {"channel": str, "text": str})
async def send_slack_message(args):
    # TODO: post to Slack (Web API or webhook).
    raise NotImplementedError("Wire to Slack")


async def run_once():
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[query_crm, search_calls, send_slack_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__query_crm",
            "mcp__gtm_tools__search_calls",
            "mcp__gtm_tools__send_slack_message",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt="Run the weekly lost-deal analysis now and post the report.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 8 * * 1-5  python claude-agent.py
    asyncio.run(run_once())
