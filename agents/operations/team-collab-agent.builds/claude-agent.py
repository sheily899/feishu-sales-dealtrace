"""Team Collab Agent — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/operations/team-collab-agent.md).
Custom tools wrap your stack: get_call_details, send_slack_message. Claude checks the analyzed call
against routing rules for six internal teams and posts a targeted alert to each team that is needed.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). You trigger
    run_once(call_id) from your recorder's "conversation analyzed" webhook. Custom tools are
    registered via an in-process MCP server.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions) for Anthropic-hosted sessions you invoke per call. Either way, paste SYSTEM_PROMPT and
    wire the same two tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio
import sys

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Team Collaboration agent. You run once per analyzed customer call:
1. Use get_call_details with the call id to get the full transcript, participants, account, deal
   stage, rep. If the call is internal (no customer participants), stop without posting.
2. Scan the transcript against routing rules and flag every team genuinely needed (a call can need
   several): SALES ENGINEERING (unanswered technical questions, deep-dive/POC/architecture requests,
   complex integrations, technical blockers, custom technical demo); LEGAL (MSA/DPA/SLA changes,
   indemnification/liability/IP concerns, their legal must review, regulatory or jurisdiction terms);
   FINANCE/DEAL DESK (non-standard pricing, volume discounts, custom payment/multi-year terms,
   budget-driven pricing, PO/net-60-90 procurement); PROFESSIONAL SERVICES/IMPLEMENTATION (timeline/
   onboarding/migration questions, complex deployment, dedicated resources or named PM, change-
   management or adoption concerns, training/certification); PRODUCT (missing feature the rep confirms
   is unavailable, workflow gap blocking the use case, roadmap questions, a bug on the call, a
   competitor feature gap); EXECUTIVE (exec-sponsor or exec meeting request, their C-suite/VP wants in,
   strategic large deal, serious dissatisfaction, churn or escalation threat). Do NOT flag a team if
   the rep already fully resolved the question on the call.
3. If no team is needed, do NOT post anything. For EACH flagged team, use send_slack_message to that
   team's channel with: ":handshake: Cross-Team Collaboration Needed - [Team]"; Account; Deal stage
   (or N/A); Call; Rep; "Why [Team] is needed" (1-2 sentences); "Key quotes" (customer quote, rep
   response if relevant); "Suggested next step" (specific); "Urgency" (High customer is blocked /
   Medium needed before next meeting / Low informational). Send a SEPARATE message per team.
Back every alert with a verbatim quote. Humanizer rules on the message: no em dashes, no AI
throat-clearing, no hype adjectives, one clear ask. Never contact the customer."""


@tool("get_call_details", "Fetch the analyzed call's transcript and metadata by id.", {"call_id": str})
async def get_call_details(args):
    # TODO: call your recorder's API, or load the transcript via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("send_slack_message", "Post a team alert to a Slack channel.", {"channel": str, "text": str})
async def send_slack_message(args):
    # TODO: post to Slack (Web API or webhook). Map each team to its channel.
    raise NotImplementedError("Wire to Slack")


async def run_once(call_id: str):
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[get_call_details, send_slack_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__get_call_details",
            "mcp__gtm_tools__send_slack_message",
        ],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt=f"Review call {call_id} and route alerts to any teams that are needed.", options=options):
        pass


if __name__ == "__main__":
    # Invoke per analyzed call from your recorder's "conversation analyzed" webhook.
    asyncio.run(run_once(sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"))
