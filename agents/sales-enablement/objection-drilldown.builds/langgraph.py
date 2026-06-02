"""Objection Drilldown — LangGraph build.

A 4-node graph: fetch this week's calls -> fetch the prior week's calls -> Claude analysis ->
post to Slack. Swap the TODO bodies for your recorder / Slack. The reasoning is one Anthropic call
whose system prompt is the agent's operating logic (mirrors
agents/sales-enablement/objection-drilldown.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Objection Drilldown agent. Given this week's calls and last week's:
classify every prospect objection into ONE category (PRICING/BUDGET, TIMING/URGENCY, COMPETITION,
FEATURE-GAPS, AUTHORITY/DECISION-PROCESS, SECURITY/LEGAL/COMPLIANCE, INTEGRATION/TECHNICAL,
ROI/PROOF) with the rep, call id, and a paraphrase; score each rep response Effective (3) /
Partial (2) / Ineffective (1); extract the top-scoring rebuttal per category as a reusable template;
compare frequency by category to last week and flag rising, declining, and new categories; flag the
categories most tied to calls with no next step as high-risk. Tie every objection, score, and
rebuttal to a specific call and quote. Humanizer rules: no em dashes, no AI throat-clearing, no
hype, one clear ask. Output the report exactly per the canonical spec."""


class State(TypedDict, total=False):
    calls: list[dict[str, Any]]
    prior_calls: list[dict[str, Any]]
    report: str


def fetch_calls(state: State) -> State:
    # TODO: fetch this week's team calls from your recorder, or load transcripts via the
    # gtmsi adapters: from gtmsi.adapters import load_transcript
    return {"calls": []}


def fetch_prior_calls(state: State) -> State:
    # TODO: fetch the prior 7-day window's calls for the trend comparison.
    return {"prior_calls": []}


def analyze(state: State) -> State:
    if not state.get("calls"):
        return {"report": "No calls recorded this week. Objection drilldown skipped."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"THIS WEEK:\n{state['calls']}\n\nLAST WEEK:\n{state.get('prior_calls', [])}"}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to your Slack channel (Web API or webhook).
    print(state["report"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("fetch_prior_calls", fetch_prior_calls)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_calls")
    g.add_edge("fetch_calls", "fetch_prior_calls")
    g.add_edge("fetch_prior_calls", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
