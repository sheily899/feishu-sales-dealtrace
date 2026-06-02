"""Cross Team Handoff — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/operations/cross-team-handoff.md).
Custom tools wrap your stack: query_crm, search_calls, send_slack_message. Claude detects
transitioned accounts, reconstructs each from its calls, and posts the handoff to the receiving team.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You run it on a
    schedule (cron / APScheduler), or trigger it from a CRM stage/owner-change webhook. Custom tools
    are registered via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) for Anthropic-hosted sessions you invoke from cron. Use that if you don't want a
    long-running process. Either way, paste SYSTEM_PROMPT and wire the same three tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the CRM / recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Cross-Team Handoff agent. On each run:
1. Use query_crm to list accounts whose opportunity stage or owner changed in the last 2 hours
   (account, prev stage, new stage, prev owner, new owner, deal value). Also use search_calls for
   recent calls carrying transition signals ("handoff", "transition", "kickoff", "onboarding",
   "passing to", "your new point of contact", "introducing you to"). Combine into the list of
   accounts needing a handoff. If none, stop silently.
2. For each transitioned account, use search_calls to pull its calls from the last 90 days and
   reconstruct it: a chronological call history (date, participants, topics, decisions, action items),
   a stakeholder map (name, title, role, disposition: supportive/neutral/skeptical/decision-maker/
   influencer/blocker), and every commitment our team made with who, when, and fulfilled-or-outstanding.
3. Write the handoff: ":arrow_right: Account Handoff Summary - [Account]"; Transition, deal value,
   stage change, handoff date; "1. Deal Context" (2-3 sentences); "2. Stakeholder Map" (table + the
   primary contact going forward); "3. Conversation History Highlights" (5-10 most important calls);
   "4. Commitments and Promises Made" (:white_check_mark: fulfilled, :hourglass: outstanding, flag
   overdue); "5. Open Items and Risks"; "6. Recommended Next Steps for the receiving team" (numbered).
4. Post each account's handoff with send_slack_message to the receiving team's channel.
Tie every claim to CRM data or a call quote. Humanizer rules on the message: no em dashes, no AI
throat-clearing, no hype adjectives, one clear ask."""


@tool("query_crm", "Read CRM accounts/opportunities. Use to find stage or owner changes.", {"soql_or_filter": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return accounts that changed stage or owner.
    raise NotImplementedError("Wire to your CRM API")


@tool("search_calls", "Find the calls/transcripts tied to an account, or recent transition-signal calls.", {"account_or_query": str})
async def search_calls(args):
    # TODO: call your recorder's API, or load transcripts via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("send_slack_message", "Post the handoff to a Slack channel.", {"channel": str, "text": str})
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
    async for _ in query(prompt="Find accounts that just transitioned between teams and post their handoffs.", options=options):
        pass


if __name__ == "__main__":
    # Schedule externally, e.g. cron:  0 * * * *  python claude-agent.py
    # Better: trigger from your CRM's stage/owner-change webhook.
    asyncio.run(run_once())
