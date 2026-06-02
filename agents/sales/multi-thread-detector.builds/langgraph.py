"""Multi Thread Detector — LangGraph build.

A 4-node graph: fetch the triggering call -> fetch the deal's prior calls -> Claude analysis ->
post to the channel. Swap the TODO bodies for your recorder / chat tool. The reasoning is one
Anthropic call whose system prompt is the agent's operating logic
(mirrors agents/sales/multi-thread-detector.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py <CALL_ID>     # or call build_graph().invoke({"call_id": ...}) from your webhook
"""
from __future__ import annotations

import sys
from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Multi Thread Detector agent. Given the triggering call and the deal's
prior calls: build a cumulative stakeholder map (each prospect-side participant's name, title/role
where stated, and MEDDPICC role - Champion, Economic Buyer, Technical Evaluator, Coach, End User).
Score threading risk: Critical (1 stakeholder or 1 role), High (2 but no Economic Buyer or no
Champion), Medium (3+ but 2+ roles uncovered), Low (4+ covering Champion, Economic Buyer, Technical
Evaluator). First call on a new deal -> "Early Stage - monitor"; inbound/intro-only -> no alert;
titles not stated -> note "Roles inferred - confirm titles with the rep". For each missing role,
give one specific action tied to the pain discussed. Only emit an alert when risk is Medium or
higher; otherwise return exactly "Threading healthy - no alert needed.". Never fabricate
stakeholders. Use single stars for emphasis, never double stars. Humanizer rules: no em dashes, no
AI throat-clearing, no hype, one clear ask. Output the alert exactly per the canonical spec,
including the Deal Threading Score (roles covered/5)."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    prior_calls: list[dict[str, Any]]
    report: str


def fetch_call(state: State) -> State:
    # TODO: fetch the triggering call (account, deal, participants) from your recorder by call_id,
    # or load it via the gtmsi adapters: from gtmsi.adapters import load_transcript
    return {"call": {}}


def fetch_prior_calls(state: State) -> State:
    # TODO: fetch every prior call on the same deal/account from your recorder.
    return {"prior_calls": []}


def analyze(state: State) -> State:
    if not state.get("call"):
        return {"report": "Threading healthy - no alert needed."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALL:\n{state['call']}\n\nPRIOR CALLS:\n{state.get('prior_calls', [])}"}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to your team channel only when it is an alert (Medium+).
    if state.get("report") and "no alert needed" not in state["report"].lower():
        print(state["report"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("fetch_prior_calls", fetch_prior_calls)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "fetch_prior_calls")
    g.add_edge("fetch_prior_calls", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({"call_id": sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"})
