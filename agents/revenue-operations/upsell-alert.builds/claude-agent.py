"""Upsell Alert — Claude managed agent (Claude Agent SDK).

Per-call agent: runs once per analyzed customer call. The agent's logic lives in SYSTEM_PROMPT
(mirrors agents/revenue-operations/upsell-alert.md). Custom tools wrap your stack: get_call,
query_crm, send_slack_message. Claude detects and classifies the expansion signal, confirms the
speaker/account against the CRM, then posts the alert.

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

SYSTEM_PROMPT = """You are the Upsell Alert agent, triggered once per analyzed customer call. On each run:
1. Use get_call to fetch the analyzed call by its id. If the call is internal/non-customer, post a
   one-line skip note and stop.
2. Read the conversation and detect any expansion signal: budget increase, seat/headcount growth, a
   new use case, interest in a higher tier or features, or multi-year/renewal intent. Back every
   finding with a verbatim quote and note which contact said it.
3. Classify the primary signal (and any secondary) from: BUDGET-INCREASE, SEAT-GROWTH, NEW-USE-CASE,
   TIER-UPGRADE, MULTI-YEAR/RENEWAL-INTENT. If no genuine signal, post "reviewed, no expansion
   signal detected" and stop.
4. Use query_crm to confirm the speaker, the linked account, current ACV, and the owner so the alert
   routes correctly. If unmatched, flag it but still post.
5. Post the alert with send_slack_message in the canonical format: header, account/owner/ACV line, a
   fields table (signal type, secondary signals, speaker, confidence HIGH/MEDIUM/LOW), the most
   revealing quote, why it matters, and a specific recommended next move.
Do not inflate hypothetical language into commitment (mark it LOW confidence). Tie every claim to a
call quote or CRM data. Humanizer rules on the message: no em dashes, no AI throat-clearing, no hype
adjectives, one clear ask."""


@tool("get_call", "Fetch an analyzed call (transcript + metadata) by its id.", {"call_id": str})
async def get_call(args):
    # TODO: call your recorder's API, or load the transcript via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("query_crm", "Confirm the speaker, account, ACV, and owner in the CRM.", {"contact_or_account": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return the matched contact/account.
    raise NotImplementedError("Wire to your CRM API")


@tool("send_slack_message", "Post the alert to a Slack channel.", {"channel": str, "text": str})
async def send_slack_message(args):
    # TODO: post to Slack (Web API or webhook).
    raise NotImplementedError("Wire to Slack")


async def run_once(call_id: str):
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[get_call, query_crm, send_slack_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__get_call",
            "mcp__gtm_tools__query_crm",
            "mcp__gtm_tools__send_slack_message",
        ],
        permission_mode="acceptEdits",
    )
    prompt = f"A customer call (id: {call_id}) was just analyzed. Screen it for an expansion signal and post the alert if there is one."
    async for _ in query(prompt=prompt, options=options):
        pass


if __name__ == "__main__":
    # Invoke from your recorder's "conversation analyzed" webhook with the call id.
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    asyncio.run(run_once(call_id))
