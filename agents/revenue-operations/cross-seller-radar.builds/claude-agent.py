"""Cross Seller Radar — Claude managed agent (Claude Agent SDK).

Per-call agent: runs once per analyzed existing-customer call. The agent's logic lives in
SYSTEM_PROMPT (mirrors agents/revenue-operations/cross-seller-radar.md). Custom tools wrap your
stack: get_call, query_crm, send_channel_message. Claude scores the five cross-sell signal
categories, reads what the account already owns from the CRM, maps signals to unowned products, and
posts the alert (only for HIGH and MEDIUM opportunities).

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

SYSTEM_PROMPT = """You are the Cross Seller Radar agent, triggered once per analyzed existing-customer
call. On each run:
1. Use get_call to fetch the analyzed call by its id. If it is a prospect call (not an existing
   customer), skip; cross-sell applies only to existing customers.
2. Use query_crm to read what the account already owns: current products, current ACV, and renewal
   date, so you only pitch what they lack.
3. Scan the transcript for cross-sell signals across five categories, scoring each: A explicit pain
   matching an unowned product (3 pts each), B questions about additional capabilities (2 pts each),
   C expansion signals like new teams, growth, volume pricing (2 pts each), D dissatisfaction with a
   third-party tool you could replace (3 pts each), E advocacy / strong satisfaction (1 pt each,
   enablers). Total = sum of points.
4. Qualify: HIGH (8+), MEDIUM (4-7), LOW (1-3), NONE (0). Alert ONLY on HIGH and MEDIUM; below that
   send nothing and stop.
5. Map each signal to a specific product the customer does not own, each with a confidence (HIGH
   direct / MEDIUM likely / LOW possible) and what they use today, if anything.
6. Post the alert with send_channel_message in the canonical format: header table (account, current
   products, current ACV, renewal date, opportunity score, rep, call date), signals detected (each
   with quote, product match, confidence), recommended approach (ordered next steps), estimated
   expansion value (or 'requires scoping call to estimate'), and the most compelling key quotes.
If the dissatisfaction is with the CURRENT product (not a third-party tool), do not flag as
cross-sell; note it may need a retention intervention and suggest involving customer success. If the
product catalog is unknown, list the raw signals for manual review and flag that mapping was not
possible. Every signal ties to something the customer actually said; every product match is one they
do not already own. Humanizer rules on the message: no em dashes, no AI throat-clearing, no hype
adjectives, one clear ask."""


@tool("get_call", "Fetch an analyzed call (transcript + metadata) by its id.", {"call_id": str})
async def get_call(args):
    # TODO: call your recorder's API, or load the transcript via the dealtrace adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / dealtrace adapters")


@tool("query_crm", "Read what the account already owns: products, ACV, renewal date.", {"account": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return current products, ACV, and renewal date.
    raise NotImplementedError("Wire to your CRM API")


@tool("send_channel_message", "Post the expansion-opportunity alert to a team channel.", {"channel": str, "text": str})
async def send_channel_message(args):
    # TODO: post to Slack/Teams (Web API or webhook).
    raise NotImplementedError("Wire to your chat tool")


async def run_once(call_id: str):
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[get_call, query_crm, send_channel_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__get_call",
            "mcp__gtm_tools__query_crm",
            "mcp__gtm_tools__send_channel_message",
        ],
        permission_mode="acceptEdits",
    )
    prompt = f"An existing-customer call (id: {call_id}) was just analyzed. Score it for cross-sell signals and post the alert if the opportunity is HIGH or MEDIUM."
    async for _ in query(prompt=prompt, options=options):
        pass


if __name__ == "__main__":
    # Invoke from your recorder's "conversation analyzed" webhook with the call id.
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    asyncio.run(run_once(call_id))
