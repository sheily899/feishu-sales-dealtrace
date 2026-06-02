"""Validate — LangGraph build.

Per-call graph: fetch the analyzed call -> read current CRM state -> Claude builds the before/after
review card -> DM the call owner -> (only on approval) write the approved fields to the CRM. Swap the
TODO bodies for your recorder / CRM / Slack. The reasoning is one Anthropic call whose system prompt
is the agent's operating logic (mirrors agents/operations/validate.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    # invoke per analyzed call, passing the call id from your recorder webhook:
    python langgraph.py <CALL_ID>      # or build_graph().invoke({"call_id": "..."}) from your handler
"""
from __future__ import annotations

import sys
from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Validate agent, building a CRM review card for one analyzed customer
call. If the call is internal/non-customer, output a one-line note that no review card was generated
and why. Otherwise extract every CRM-impacting field present (each backed by a verbatim quote and a
confidence score where possible): participants and roles/emails, the account and any domain, and deal
signals (stage movement, next steps with owners/dates, budget or contract value, decision timeline,
competitors named, pain points, commitments). Normalize values: dates to ISO, currency to org
default, picklists to canonical labels; drop null/empty. If no CRM-impacting fields are detected,
output 'No CRM-impacting fields detected on this call.' Otherwise, against the supplied current CRM
state, build a per-field diff and render the review card EXACTLY as: a header 'Validate CRM Fields for
<record>', a diff table (Field | Current -> Proposed | Confidence% | Evidence quote+timecode), and the
actions line 'Actions: Approve & Push | Edit Fields | Skip | Remind me later'. Apply humanizer rules:
no em dashes, no 'I hope this finds you well' or 'I wanted to reach out', no hype adjectives, one clear
ask. The CRM write happens only after the rep approves; never write unattended. Every proposed field
must trace to a quote, timecode, or confidence score; no invented values."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    crm_state: dict[str, Any]
    review_card: str
    approved_fields: dict[str, Any]


def fetch_call(state: State) -> State:
    # TODO: fetch the analyzed call by state["call_id"] from your recorder, or load_transcript via gtmsi adapters.
    return {"call": {}}


def read_crm(state: State) -> State:
    # TODO: resolve Account/Contact/Opportunity (by email/domain/id) and read current field values.
    return {"crm_state": {}}


def build_review_card(state: State) -> State:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALL:\n{state.get('call', {})}\n\nCURRENT CRM STATE:\n{state.get('crm_state', {})}"}],
    )
    return {"review_card": msg.content[0].text}


def dm_owner(state: State) -> State:
    # TODO: DM state["review_card"] to the call owner via Slack. Never send to the customer.
    print(state["review_card"])
    return {}


def write_crm_on_approval(state: State) -> State:
    # TODO: gate on the rep's approval (interactive step / callback). Then upsert ONLY the approved
    # fields in order Account -> Contact -> Opportunity, log a Call/Task/Activity, and confirm.
    # NEVER write to the CRM without approval. Left as a no-op placeholder for the approval callback.
    if not state.get("approved_fields"):
        return {}
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("read_crm", read_crm)
    g.add_node("build_review_card", build_review_card)
    g.add_node("dm_owner", dm_owner)
    g.add_node("write_crm_on_approval", write_crm_on_approval)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "read_crm")
    g.add_edge("read_crm", "build_review_card")
    g.add_edge("build_review_card", "dm_owner")
    g.add_edge("dm_owner", "write_crm_on_approval")
    g.add_edge("write_crm_on_approval", END)
    return g.compile()


if __name__ == "__main__":
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    build_graph().invoke({"call_id": call_id})
