"""Competitor Ping — LangGraph build.

Per-call graph: fetch the analyzed call -> Claude detect+extract -> post to Slack (only when
competitors are found). Swap the TODO bodies for your recorder / Slack. The reasoning is one
Anthropic call whose system prompt is the agent's operating logic (mirrors
agents/revenue-operations/competitor-ping.md).

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

SYSTEM_PROMPT = """You are the Competitor Ping agent scanning one analyzed call for competitor
mentions. Detect explicit competitor names, implicit references ('another vendor', 'the other tool
we're looking at', 'the incumbent'), and competitor product references. If no competitor comes up in
a competitive or evaluative context, output exactly 'No competitor mentions detected.' Otherwise, for
each competitor extract: mention context (PROSPECT-INITIATED / REP-INITIATED / ACTIVE-EVALUATION /
INCUMBENT / PAST-USER), strengths cited (with quotes), weaknesses cited (with quotes), prospect
sentiment (POSITIVE / NEUTRAL / NEGATIVE), the rep's positioning response and whether it landed, and
win/loss risk (HIGH / MODERATE / LOW). Output the alert in the canonical format: header table (deal,
rep, call date, competitors detected), one intelligence block per competitor with the most revealing
quote, then 2-3 recommended actions. A mention only in passing is not flagged. Tie every strength,
weakness, and risk call to a transcript quote; no invented competitor claims. Humanizer rules: no em
dashes, no AI throat-clearing, no hype, one clear ask."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    report: str


def fetch_call(state: State) -> State:
    # TODO: fetch the analyzed call by state["call_id"] from your recorder, or load_transcript via dealtrace adapters.
    return {"call": {}}


def analyze(state: State) -> State:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALL:\n{state.get('call', {})}"}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    report = state.get("report", "")
    if "No competitor mentions detected" in report:
        return {}  # silent when nothing to report
    # TODO: post report to your Slack channel (Web API or webhook).
    print(report)
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    build_graph().invoke({"call_id": call_id})
