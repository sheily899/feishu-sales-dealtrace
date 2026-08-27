"""Inbound Qualifier — LangGraph build.

Per-call graph: fetch the analyzed call -> read firmographics from the CRM -> Claude score BANT + ICP
fit -> post to Slack. Swap the TODO bodies for your recorder / CRM / Slack. The reasoning is one
Anthropic call whose system prompt is the agent's operating logic (mirrors
agents/revenue-operations/inbound-qualifier.md).

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

SYSTEM_PROMPT = """You are the Inbound Qualifier agent qualifying one analyzed inbound call. If no
transcript is available, output a one-line note that qualification could not be completed and
recommend manual review. Otherwise score BANT (0-3 per dimension, 12 max), each with one line of
transcript evidence: Budget, Authority, Need, Timeline (3 CONFIRMED / 2 PARTIAL / 1 IMPLIED / 0
MISSING). Using the provided firmographics, rate ICP fit against the configured profile (industry,
company size, use-case match, tech-stack fit, geography): GOOD (4-5 criteria), PARTIAL (2-3), POOR
(0-1). Determine disposition: HOT (BANT 10-12, ICP Good), WARM (BANT 7-9, or 10+ with Partial ICP),
COOL (BANT 4-6), DISQUALIFIED (BANT 0-3, or ICP Poor regardless of BANT). Output the report in the
canonical format: header table (lead, call date, rep, lead score, BANT score, ICP fit), BANT
breakdown (one line of evidence per dimension), ICP fit notes, recommended next steps, and the key
quotes that justify it. If the call is under 5 minutes, score what you can and mark unaddressed
dimensions 0 with 'Not discussed, call too short'; if it is an existing customer asking about a new
product, flag it EXPANSION not inbound. Tie every BANT score and the disposition to a transcript quote
or CRM firmographic. Humanizer rules: no em dashes, no AI throat-clearing, no hype, one clear ask."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    firmographics: dict[str, Any]
    report: str


def fetch_call(state: State) -> State:
    # TODO: fetch the analyzed call by state["call_id"] from your recorder, or load_transcript via dealtrace adapters.
    return {"call": {}}


def fetch_firmographics(state: State) -> State:
    # TODO: read company size, industry, and the existing-customer flag from your CRM for ICP fit.
    return {"firmographics": {}}


def analyze(state: State) -> State:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"CALL:\n{state.get('call', {})}\n\nFIRMOGRAPHICS:\n{state.get('firmographics', {})}"
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
    g.add_node("fetch_firmographics", fetch_firmographics)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "fetch_firmographics")
    g.add_edge("fetch_firmographics", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    build_graph().invoke({"call_id": call_id})
