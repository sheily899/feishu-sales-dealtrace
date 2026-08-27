"""Churn Alert — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/account-management/churn-alert.md).
Custom tools wrap your stack: query_crm, search_calls, send_slack_message. Claude scopes the active
customers, fuses CRM health with conversation sentiment, rates churn risk, then posts the report.
The CSM is the rep-equivalent; the customer is the account on the other side.

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

SYSTEM_PROMPT = """You are the Churn Alert agent. On each weekly run:
1. Use query_crm to list ACTIVE customer accounts (exclude open/live deals). For each, capture account
   name, renewal date, health/success score, NPS, contract value, assigned CSM, and any open support
   cases. If none are in scope, send a Slack note that no active customers were found, then stop.
2. For each active account, use search_calls to pull its calls over roughly the last 90 days, then
   analyze them (batch up to 25 per request) and report per account: call frequency and any drop
   versus the prior period, average sentiment and the trend, unresolved issues or open action items,
   competitor or alternative mentions, expressed dissatisfaction, and any expansion/upsell signals.
3. Fuse the CRM health data, usage trends, and conversation signals and assign severity. HIGH:
   multiple strong signals at once (usage down sharply AND negative sentiment, or a near-term renewal
   with no engagement and an open competitor mention). MEDIUM: one clear signal or a few mild ones (a
   single unresolved issue, a modest usage dip, or mixed sentiment). LOW (monitor): minor fluctuations
   or early signals, no immediate action needed.
4. For each at-risk account, summarize the key risk drivers and one specific proactive retention
   tactic the CSM can run this week. Anonymize company names with a stable alias per account.
5. Send the report with send_slack_message to the CS / account-management channel, with High / Medium /
   Low (Monitor) sections and a summary line of the counts by category. If no churn signals are
   detected, send 'No churn signals detected this week. Customer base is stable.' instead.
This report covers ACTIVE customers, not live deals. Tie every rating to CRM health data or a call
signal. Apply humanizer rules to the message: no em dashes, no AI throat-clearing, no hype
adjectives, one clear ask."""


@tool("query_crm", "Scope the active-customer set and read their health signals.", {"soql_or_filter": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return ACTIVE customer accounts (exclude live deals).
    raise NotImplementedError("Wire to your CRM API")


@tool("search_calls", "Find an account's recent calls (last ~90 days).", {"account": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("send_slack_message", "Post the churn report to a Slack channel.", {"channel": str, "text": str})
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
    async for _ in query(prompt="Run the weekly churn-risk analysis now and post the report.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 7 * * *  python claude-agent.py
    asyncio.run(run_once())
