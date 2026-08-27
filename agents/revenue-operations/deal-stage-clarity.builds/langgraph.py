"""Deal Stage Clarity — LangGraph build.

A 4-node graph: fetch open deals -> fetch their calls -> Claude stage audit -> post to Slack.
Swap the TODO bodies for your CRM / recorder / Slack. The reasoning is one Anthropic call whose
system prompt is the agent's operating logic (mirrors agents/revenue-operations/deal-stage-clarity.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Deal Stage Clarity agent. Given the active open deals (with current
stage, amount, expected close date, owner, last activity) and their recent calls: map stages to
expected evidence using the six-stage framework (Prospecting; Discovery/Qualification; Demo/Solution;
Proposal/Evaluation; Negotiation/Legal; Verbal Commit), adapting the labels to whatever stages this
CRM uses. Flag each deal with a confidence rating (HIGH/MEDIUM/LOW): OVERSTAGED (stage ahead of the
evidence, inflates the forecast), UNDERSTAGED (evidence ahead of the stage), STALE (no conversation
in 14+ days and no stage change), or correctly staged. Calculate forecast impact: overstated $ /
understated $ / net adjustment. Skip deals created in the last 3 days with no calls; for deals with
only email activity, note no call data and do not validate the stage. Tie every stage call to CRM
data or a specific conversation moment. Output the report exactly per the canonical spec (header line,
flagged-deals table, per-deal detail with evidence bullets and the recommended stage move, a
correctly-staged summary, and a forecast impact summary). Humanizer rules: no em dashes, no AI
throat-clearing, no hype, one clear ask."""


class State(TypedDict, total=False):
    deals: list[dict[str, Any]]
    calls: list[dict[str, Any]]
    report: str


def fetch_open_deals(state: State) -> State:
    # TODO: query your CRM for active open opportunities with their current stages.
    return {"deals": []}


def fetch_calls(state: State) -> State:
    # TODO: for each deal, fetch its recent calls from your recorder, or load transcripts via the
    # dealtrace adapters: from dealtrace.adapters import load_transcript
    return {"calls": []}


def analyze(state: State) -> State:
    if not state.get("deals"):
        return {"report": "Deal Stage Clarity ran. No active open deals to analyze."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"OPEN DEALS:\n{state['deals']}\n\nCALLS:\n{state.get('calls', [])}"}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to your Slack channel (Web API or webhook).
    print(state["report"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_open_deals", fetch_open_deals)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_open_deals")
    g.add_edge("fetch_open_deals", "fetch_calls")
    g.add_edge("fetch_calls", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
