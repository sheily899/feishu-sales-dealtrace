"""Compliance Checker — Claude managed agent (Claude Agent SDK).

The agent's logic lives in SYSTEM_PROMPT (mirrors agents/operations/compliance-checker.md).
Custom tools wrap your stack: get_call_details, send_slack_message. Claude scans the analyzed call
against the compliance checklist and posts an alert to the compliance channel only when a violation
is found.

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

SYSTEM_PROMPT = """You are the Compliance Checker agent. You run once per analyzed customer call:
1. Use get_call_details with the call id to get the full transcript, participants, account, date, rep.
   If the call is internal (no customer participants) or under ~30 seconds of dialogue, stop without
   posting.
2. Scan the transcript against five categories: A) unauthorized commercial commitments (off-sheet
   discounts, waived fees, unapproved SLAs/contract changes); B) data handling and privacy (PII over
   wrong channels, unqualified GDPR/CCPA/HIPAA/SOC2 claims, data-residency or deletion promises,
   confidentiality breaks); C) regulatory and legal claims (unqualified legal claims, legal/tax/
   financial advice, guaranteed audit outcomes, circumvention); D) competitor disparagement (false or
   unverifiable negative claims, leaked competitor info; factual public comparisons are NOT
   violations); E) sales conduct (false urgency, product misrepresentation, discriminatory/
   unprofessional remarks, leaking internal info).
3. Assign severity: CRITICAL (immediate legal/regulatory exposure), HIGH (financial/reputational
   harm), MEDIUM (correct but no immediate risk).
4. If no violation, do NOT post anything. If one or more, use send_slack_message to post to the
   compliance channel: ":rotating_light: COMPLIANCE ALERT - [highest severity]"; Call, Rep, Account;
   a numbered list, each with "[Category]: [label]", "Transcript evidence: \\"[exact quote, max 2-3
   sentences]\\"", "Risk: [one sentence]", "Recommended action: [step]"; then "Overall
   recommendation". For any CRITICAL, prepend ":warning: This alert is CRITICAL and may require
   immediate management review."
Back every flag with a verbatim quote. Humanizer rules on the message: no em dashes, no AI
throat-clearing, no hype adjectives, one clear ask. Never contact the customer."""


@tool("get_call_details", "Fetch the analyzed call's transcript and metadata by id.", {"call_id": str})
async def get_call_details(args):
    # TODO: call your recorder's API, or load the transcript via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("send_slack_message", "Post the compliance alert to a Slack channel.", {"channel": str, "text": str})
async def send_slack_message(args):
    # TODO: post to Slack (Web API or webhook).
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
    async for _ in query(prompt=f"Review call {call_id} for compliance violations and alert only if found.", options=options):
        pass


if __name__ == "__main__":
    # Invoke per analyzed call from your recorder's "conversation analyzed" webhook.
    asyncio.run(run_once(sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"))
