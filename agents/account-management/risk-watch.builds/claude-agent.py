"""Risk Watch — Claude managed agent (Claude Agent SDK).

Per-call agent: runs once per analyzed customer call. The agent's logic lives in SYSTEM_PROMPT
(mirrors agents/account-management/risk-watch.md). Custom tools wrap your stack: get_call,
search_calls, query_crm, send_slack_message. Claude evaluates the call against the account's recent
baseline and CRM metadata, rates severity, and posts a tiered alert to a channel ONLY when a real
risk is present. The CSM is the rep-equivalent; the customer is the account on the other side.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). Trigger run_once()
    from your recorder's "conversation analyzed" webhook handler, passing the call id.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions). Either way, paste SYSTEM_PROMPT and wire the same four tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / CRM / Slack calls marked TODO with your real APIs.
"""
import asyncio
import sys

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Risk Watch agent, triggered once per analyzed customer call. On each run:
1. Use get_call to fetch the analyzed call by its id (transcript, participants, account, sentiment).
   If no transcript is available (failed recording), stop without alerting.
2. Use search_calls for the same account's recent history and build the baseline: how many calls in
   the last 30 days versus the prior 30, the sentiment trend, and any unresolved issues, competitor
   mentions, or escalation requests. Use query_crm to enrich with account metadata (owner/CSM,
   contract value, renewal date, open cases). If this is the account's first-ever call, skip the
   engagement-drop check and evaluate only the current call.
3. Evaluate risk indicators on the current call and the account context: engagement drop (fewer calls
   than the prior period, or key stakeholders absent), negative sentiment ('not happy', 'frustrated',
   'reconsider'), competitor mentions, escalation language (manager/legal/SLA/termination), usage
   challenges (bugs, adoption struggles), relationship risk (champion leaving or gone silent, new
   stakeholder with no context).
4. Assign severity. CRITICAL: explicit cancellation/non-renewal/termination, active competitor
   evaluation, escalation to legal/exec threatened, or 2+ indicators at once. HIGH: negative sentiment
   with an unresolved issue, engagement down 50%+, competitor mentioned in passing, or champion
   departure. MEDIUM: single mild frustration, minor engagement dip, a usage challenge the customer
   will work through, or one carried-over action item. If indicators span tiers, use the highest. If
   NO indicators are detected, do NOT send an alert.
5. Only when a risk is present, use send_slack_message to post a tiered alert to the CS channel with
   the indicators and their evidence quotes, the account context (calls last 30d vs prior 30d, the
   sentiment trend), and the recommended next actions, in the per-tier format from the spec
   (CRITICAL :red_circle:, HIGH :large_orange_circle:, MEDIUM :yellow_circle:).
Do not re-alert the same account within 24 hours for identical indicators. Tie every indicator to a
transcript quote or a baseline metric; no speculation. Apply humanizer rules to the alert: no em
dashes, no AI throat-clearing, no hype adjectives, one clear ask."""


@tool("get_call", "Fetch an analyzed call (transcript + metadata) by its id.", {"call_id": str})
async def get_call(args):
    # TODO: call your recorder's API, or load the transcript via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("search_calls", "Find the account's recent calls to build the engagement baseline.", {"account": str})
async def search_calls(args):
    # TODO: call your recorder's API for the account's recent calls (last ~60 days), or load via dealtrace adapters.
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("query_crm", "Read account metadata (owner/CSM, contract value, renewal date, open cases).", {"account": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return the account's metadata.
    raise NotImplementedError("Wire to your CRM API")


@tool("send_slack_message", "Post the tiered risk alert to a channel (only when a risk is present).", {"channel": str, "text": str})
async def send_slack_message(args):
    # TODO: post to Slack (Web API or webhook).
    raise NotImplementedError("Wire to Slack")


async def run_once(call_id: str):
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[get_call, search_calls, query_crm, send_slack_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__get_call",
            "mcp__gtm_tools__search_calls",
            "mcp__gtm_tools__query_crm",
            "mcp__gtm_tools__send_slack_message",
        ],
        permission_mode="acceptEdits",
    )
    prompt = f"A customer call (id: {call_id}) was just analyzed. Evaluate the account for risk and post a tiered alert only if a real risk is present."
    async for _ in query(prompt=prompt, options=options):
        pass


if __name__ == "__main__":
    # Invoke from your recorder's "conversation analyzed" webhook with the call id.
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    asyncio.run(run_once(call_id))
