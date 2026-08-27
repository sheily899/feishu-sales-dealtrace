"""Upsell Alert — LangGraph build.

Per-call graph: fetch the analyzed call -> Claude detect+classify -> confirm in CRM -> post to Slack.
Swap the TODO bodies for your recorder / CRM / Slack. The reasoning is one Anthropic call whose
system prompt is the agent's operating logic (mirrors agents/revenue-operations/upsell-alert.md).

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

SYSTEM_PROMPT = """You are the Upsell Alert agent screening one analyzed customer call. If the call is
internal/non-customer, output a one-line skip note. Otherwise detect any expansion signal (budget
increase, seat/headcount growth, new use case, higher-tier interest, multi-year/renewal intent),
back each with a verbatim quote and the speaker, and classify the primary (and any secondary) from
BUDGET-INCREASE, SEAT-GROWTH, NEW-USE-CASE, TIER-UPGRADE, MULTI-YEAR/RENEWAL-INTENT. If no genuine
signal, output 'reviewed, no expansion signal detected'. If a signal exists, output the alert in the
canonical format: header, account/owner/ACV line, fields table (signal type, secondary signals,
speaker, confidence HIGH/MEDIUM/LOW), the most revealing quote, why it matters, and a specific
recommended next move. Do not inflate hypothetical language into commitment (mark it LOW). Tie every
claim to a call quote or the provided CRM match. Humanizer rules: no em dashes, no AI throat-clearing,
no hype, one clear ask."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    crm_match: dict[str, Any]
    report: str


def fetch_call(state: State) -> State:
    # TODO: fetch the analyzed call by state["call_id"] from your recorder, or load_transcript via dealtrace adapters.
    return {"call": {}}


def confirm_crm(state: State) -> State:
    # TODO: look up the speaker/account in your CRM to confirm the contact, account, ACV, and owner.
    return {"crm_match": {}}


def analyze(state: State) -> State:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"CALL:\n{state.get('call', {})}\n\nCRM MATCH:\n{state.get('crm_match', {})}"
        )}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to your Slack channel (Web API or webhook).
    print(state["report"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("confirm_crm", confirm_crm)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "confirm_crm")
    g.add_edge("confirm_crm", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    build_graph().invoke({"call_id": call_id})
