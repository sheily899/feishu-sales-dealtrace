"""Email Generator — Claude managed agent (Claude Agent SDK).

Per-call agent: runs once per analyzed customer call. The agent's logic lives in SYSTEM_PROMPT
(mirrors agents/sales/email-generator.md). Custom tools wrap your stack: get_call,
send_slack_direct_message. Claude extracts the recap/actions/next step, drafts the follow-up in the
rep's voice, humanizes it, and DMs it to the rep as a DRAFT. It never sends to the customer.

There are two Claude paths:
  - THIS file: the in-process Claude Agent SDK (`pip install claude-agent-sdk`). Trigger run_once()
    from your recorder's "conversation analyzed" webhook handler, passing the call id.
  - Hosted alternative: the Managed Agents API (`anthropic` SDK, `client.beta.agents.create` +
    sessions). Either way, paste SYSTEM_PROMPT and wire the same two tools.

Verify against the current SDK (version-sensitive): import paths and the @tool / query surface.
Fill the recorder / Slack calls marked TODO with your real APIs.
"""
import asyncio
import sys

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, query, tool

SYSTEM_PROMPT = """You are the Email Generator agent, triggered once per analyzed customer call. On each run:
1. Use get_call to fetch the analyzed call by its id. If it is internal/non-customer, DM the rep a
   one-line note that no follow-up was generated and why, then stop.
2. Extract, each backed by a verbatim quote where possible: attendees and roles (rep vs buyer), the
   buyer's stated pain and any number attached, commitments by either side, agreed action items with
   owner and due date, open questions, the single most important next step, and the call type
   (discovery / demo / technical-validation / negotiation / onboarding / check-in / renewal), which sets tone.
3. Draft a short follow-up in the REP's voice: a specific subject (reference the company and topic,
   not 'Great meeting you'); a one-line opening; 2-4 recap bullets each tied to something real from
   the call; agreed actions as 'owner - action - date'; one clear next step with a concrete proposed
   time window (not 'let me know'); a sign-off. Body under ~150 words, skimmable on mobile.
4. Apply humanizer rules: no em dashes, no 'I hope this finds you well' or 'I wanted to reach out',
   no hype adjectives, one clear ask, keep the rep's real voice.
5. DM the finished draft to the rep with send_slack_direct_message, in this exact plain-text format:
   'Subject: ...' then 'Body: ...' then '---' then 'Action items:' (one owner - action - date per line).
This is a DRAFT for the rep to review and send. NEVER address or send it to the customer. If no next
step was agreed, propose one from the call type and label it clearly as proposed, not agreed."""


@tool("get_call", "Fetch an analyzed call (transcript + metadata) by its id.", {"call_id": str})
async def get_call(args):
    # TODO: call your recorder's API, or load the transcript via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("send_slack_direct_message", "DM the draft to the rep (never to the customer).", {"user_id": str, "text": str})
async def send_slack_direct_message(args):
    # TODO: send a Slack DM to the rep (Web API chat.postMessage to the rep's user id).
    raise NotImplementedError("Wire to Slack")


async def run_once(call_id: str):
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[get_call, send_slack_direct_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__get_call",
            "mcp__gtm_tools__send_slack_direct_message",
        ],
        permission_mode="acceptEdits",
    )
    prompt = f"A customer call (id: {call_id}) was just analyzed. Draft the follow-up and DM it to the rep as a draft."
    async for _ in query(prompt=prompt, options=options):
        pass


if __name__ == "__main__":
    # Invoke from your recorder's "conversation analyzed" webhook with the call id.
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    asyncio.run(run_once(call_id))
