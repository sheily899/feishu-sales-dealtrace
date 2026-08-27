"""Case Builder — LangGraph build.

A 4-node graph: fetch the triggering call -> fetch the deal's prior calls -> Claude analysis ->
post to the channel. Swap the TODO bodies for your recorder / chat tool. The reasoning is one
Anthropic call whose system prompt is the agent's operating logic (mirrors agents/sales/case-builder.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py <CALL_ID>     # or call build_graph().invoke({"call_id": ...}) from your webhook
"""
from __future__ import annotations

import sys
from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Case Builder agent. Given the triggering call and the deal's prior
calls: first check eligibility (proceed only if there is business pain, a demo/solution walkthrough,
a pricing/investment discussion, or an ROI/value conversation; otherwise return exactly
"No business case generated - call had no substantive business discussion."). Then extract six
sections: (1) Current State and Pain + quantified impact (mark "Needs quantification" if absent),
(2) Desired Future State + KPIs, (3) Solution Mapping (capability -> pain, interest High/Med/Low),
(4) Investment (or "Not yet discussed"), (5) ROI and Payback estimate
(ROI = ((annual value - annual investment)/annual investment) x 100%; payback = annual investment /
monthly value; give the framework if pain is not quantified, never invent a number), (6) Risks and
Mitigations (flag unaddressed as "Open"). Label any section the call did not cover. Use single stars
for emphasis, never double stars. Humanizer rules: no em dashes, no AI throat-clearing, no hype, one
clear ask. Output the business case exactly per the canonical spec. It is a draft for the rep, never
sent to the customer."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    prior_calls: list[dict[str, Any]]
    report: str


def fetch_call(state: State) -> State:
    # TODO: fetch the triggering call's transcript + metadata from your recorder by state["call_id"],
    # or load it via the dealtrace adapters: from dealtrace.adapters import load_transcript
    return {"call": {}}


def fetch_prior_calls(state: State) -> State:
    # TODO: fetch the deal's/account's prior calls from your recorder for cumulative context.
    return {"prior_calls": []}


def analyze(state: State) -> State:
    if not state.get("call"):
        return {"report": "No business case generated - no call data available."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALL:\n{state['call']}\n\nPRIOR CALLS:\n{state.get('prior_calls', [])}"}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to your team channel (Slack/Teams Web API or webhook).
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
