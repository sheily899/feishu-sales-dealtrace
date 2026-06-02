"""Validate — Claude managed agent (Claude Agent SDK).

Per-call agent: runs once per analyzed customer call. The agent's logic lives in SYSTEM_PROMPT
(mirrors agents/operations/validate.md). Custom tools wrap your stack: get_call, query_crm,
update_crm, send_slack_direct_message. Claude extracts the CRM-impacting fields, reads current CRM
state, builds a before/after review card, and DMs it to the call owner. It writes to the CRM ONLY
after the rep approves; it never writes unattended.

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

SYSTEM_PROMPT = """You are the Validate agent, triggered once per analyzed customer call. On each run:
1. Use get_call to fetch the analyzed call by its id. If it is internal/non-customer, DM the call
   owner a one-line note that no review card was generated and why, then stop.
2. Extract every CRM-impacting field present in the conversation, each backed by a verbatim quote
   and a confidence score where possible: participants and roles/emails (to resolve the Contact and
   the owner), the account and any domain, and deal signals (stage movement, next steps with owners
   and dates, budget or contract value, decision timeline, competitors named, pain points,
   commitments). Normalize values: dates to ISO, currency to the org default, picklists to canonical
   labels. Drop null/empty keys. If no CRM-impacting fields are detected, DM 'No CRM-impacting fields
   detected on this call.' and stop.
3. Map each field to its CRM target { object, field, upsert_key? }. With query_crm, resolve the
   record (Contact by participant email or ContactId; Account by domain or AccountId; Opportunity by
   OpportunityId, else open opp(s) on the Account for the Contact, else a 'Pending Validation' draft
   opp NOT created until approved) and read its current value. Build a per-field diff of
   { current, proposed, confidence, evidence }.
4. DM the call owner a review card with send_slack_direct_message: header 'Validate CRM Fields for
   <Account | Contact | Opportunity>'; a diff table (one row per field: Field | Current -> Proposed |
   Confidence% | Evidence quote+timecode); a link to the call; and actions Approve & Push / Edit
   Fields / Skip / Remind me later, with per-field checkboxes for partial approval.
5. ONLY after the rep approves (or edits + approves), use update_crm to upsert in order Account ->
   Contact -> Opportunity, writing ONLY the approved/edited fields and leaving everything else
   untouched, then log a Call/Task/Activity summarizing the changes with a transcript link and
   confirm with links to the updated records. NEVER write to the CRM without approval.
Apply humanizer rules to the review-card message: no em dashes, no 'I hope this finds you well' or
'I wanted to reach out', no hype adjectives, one clear ask, keep the owner's real voice."""


@tool("get_call", "Fetch an analyzed call (transcript + metadata) by its id.", {"call_id": str})
async def get_call(args):
    # TODO: call your recorder's API, or load the transcript via the gtmsi adapters (load_transcript).
    raise NotImplementedError("Wire to your call recorder / gtmsi adapters")


@tool("query_crm", "Read current CRM record state to build the before/after diff.", {"soql_or_filter": str})
async def query_crm(args):
    # TODO: call your CRM (Salesforce/HubSpot/...) and return the matching records' current field values.
    raise NotImplementedError("Wire to your CRM API")


@tool("update_crm", "Write approved fields to the CRM. Call ONLY after the rep approves.", {"object": str, "record_id": str, "fields": dict})
async def update_crm(args):
    # TODO: upsert the approved fields to the CRM. Must be gated behind rep approval of the review card.
    raise NotImplementedError("Wire to your CRM API")


@tool("send_slack_direct_message", "DM the review card to the call owner.", {"user_id": str, "text": str})
async def send_slack_direct_message(args):
    # TODO: send a Slack DM to the call owner (Web API chat.postMessage to the owner's user id).
    raise NotImplementedError("Wire to Slack")


async def run_once(call_id: str):
    tools = create_sdk_mcp_server(name="gtm_tools", version="1.0.0",
                                  tools=[get_call, query_crm, update_crm, send_slack_direct_message])
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"gtm_tools": tools},
        allowed_tools=[
            "mcp__gtm_tools__get_call",
            "mcp__gtm_tools__query_crm",
            "mcp__gtm_tools__update_crm",
            "mcp__gtm_tools__send_slack_direct_message",
        ],
        permission_mode="acceptEdits",
    )
    prompt = f"A customer call (id: {call_id}) was just analyzed. Build the CRM review card and DM it to the call owner. Write to the CRM only after approval."
    async for _ in query(prompt=prompt, options=options):
        pass


if __name__ == "__main__":
    # Invoke from your recorder's "conversation analyzed" webhook with the call id.
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    asyncio.run(run_once(call_id))
