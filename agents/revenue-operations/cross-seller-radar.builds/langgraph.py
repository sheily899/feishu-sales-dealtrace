"""Cross Seller Radar — LangGraph build.

Per-call graph: fetch the analyzed call -> read what the account owns from the CRM -> Claude score
the cross-sell signals -> post to Slack (only for HIGH/MEDIUM opportunities). Swap the TODO bodies
for your recorder / CRM / Slack. The reasoning is one Anthropic call whose system prompt is the
agent's operating logic (mirrors agents/revenue-operations/cross-seller-radar.md).

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

SYSTEM_PROMPT = """You are the Cross Seller Radar agent scoring one analyzed existing-customer call
for expansion. If it is a prospect call (not an existing customer), output exactly 'Prospect call -
cross-sell does not apply.' Otherwise, using what the account already owns (provided), scan the
transcript for cross-sell signals across five categories and score each: A explicit pain matching an
unowned product (3 pts each), B questions about additional capabilities (2 pts each), C expansion
signals like new teams, growth, volume pricing (2 pts each), D dissatisfaction with a third-party
tool you could replace (3 pts each), E advocacy / strong satisfaction (1 pt each). Total = sum.
Qualify: HIGH (8+), MEDIUM (4-7), LOW (1-3), NONE (0). If LOW or NONE, output exactly 'No qualified
cross-sell opportunity.' If HIGH or MEDIUM, map each signal to a specific unowned product with a
confidence (HIGH/MEDIUM/LOW) and output the alert in the canonical format: header table (account,
current products, ACV, renewal date, opportunity score, rep, call date), signals detected,
recommended approach, estimated expansion value, key quotes. If dissatisfaction is with the CURRENT
product (not a third-party tool), do not flag as cross-sell; note a possible retention intervention.
Every signal ties to something the customer said; every product match is one they do not own.
Humanizer rules: no em dashes, no AI throat-clearing, no hype, one clear ask."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    account_owns: dict[str, Any]
    report: str


def fetch_call(state: State) -> State:
    # TODO: fetch the analyzed call by state["call_id"] from your recorder, or load_transcript via dealtrace adapters.
    return {"call": {}}


def fetch_account(state: State) -> State:
    # TODO: read current products, ACV, and renewal date for the account from your CRM.
    return {"account_owns": {}}


def analyze(state: State) -> State:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"CALL:\n{state.get('call', {})}\n\nACCOUNT OWNS:\n{state.get('account_owns', {})}"
        )}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    report = state.get("report", "")
    if "No qualified cross-sell opportunity" in report or "cross-sell does not apply" in report:
        return {}  # silent below threshold / for prospect calls
    # TODO: post report to your Slack channel (Web API or webhook).
    print(report)
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("fetch_account", fetch_account)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "fetch_account")
    g.add_edge("fetch_account", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    build_graph().invoke({"call_id": call_id})
