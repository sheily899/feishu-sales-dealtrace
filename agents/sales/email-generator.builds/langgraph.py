"""Email Generator — LangGraph build.

Per-call graph: fetch the analyzed call -> Claude draft (in the rep's voice, humanized) -> DM the
draft to the rep. Swap the TODO bodies for your recorder / Slack. The reasoning is one Anthropic call
whose system prompt is the agent's operating logic (mirrors agents/sales/email-generator.md).

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

SYSTEM_PROMPT = """You are the Email Generator agent drafting a post-call follow-up for the REP on one
analyzed customer call. If the call is internal/non-customer, output a one-line note that no follow-up
was generated and why. Otherwise extract (each backed by a verbatim quote where possible): attendees
and roles (rep vs buyer), the buyer's pain and any number attached, commitments by either side, agreed
action items with owner and due date, open questions, the single most important next step, and the
call type (which sets tone). Then draft a short follow-up in the rep's voice: a specific subject
(company + topic, not 'Great meeting you'); a one-line opening; 2-4 recap bullets tied to real call
content; agreed actions as 'owner - action - date'; one clear next step with a concrete proposed time;
a sign-off. Body under ~150 words, skimmable. Apply humanizer rules: no em dashes, no 'I hope this
finds you well' or 'I wanted to reach out', no hype adjectives, one clear ask, keep the rep's real
voice. Return plain text EXACTLY as: 'Subject: ...' then 'Body: ...' then '---' then 'Action items:'
(one owner - action - date per line). This is a DRAFT for the rep to review and send. NEVER address or
send it to the customer. If no next step was agreed, propose one from the call type and label it as
proposed, not agreed."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    draft: str


def fetch_call(state: State) -> State:
    # TODO: fetch the analyzed call by state["call_id"] from your recorder, or load_transcript via gtmsi adapters.
    return {"call": {}}


def draft_email(state: State) -> State:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALL:\n{state.get('call', {})}"}],
    )
    return {"draft": msg.content[0].text}


def dm_rep(state: State) -> State:
    # TODO: DM state["draft"] to the rep (the deal owner) via Slack. Never send to the customer.
    print(state["draft"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("draft_email", draft_email)
    g.add_node("dm_rep", dm_rep)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "draft_email")
    g.add_edge("draft_email", "dm_rep")
    g.add_edge("dm_rep", END)
    return g.compile()


if __name__ == "__main__":
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    build_graph().invoke({"call_id": call_id})
