"""Scorecard per Rep — LangGraph build.

A 4-node graph: fetch this week's calls -> fetch the prior week's calls -> Claude scoring ->
post to Slack. Swap the TODO bodies for your recorder / Slack. The reasoning is one Anthropic call
whose system prompt is the agent's operating logic (mirrors
agents/sales-enablement/scorecard-per-rep.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Scorecard per Rep agent. Given this week's calls (grouped by rep) and
last week's: score each rep 1-5 on Discovery Quality, Objection Handling, Value Articulation,
Next-Step Setting, Talk Ratio (5 = rep talks 30-45%, 3 = 50-60%, 1 = over 70%), Question Quality,
and compute each rep's average; compare each dimension to last week and mark improved / declined /
stable; pick the 3 lowest-scoring dimensions per rep, cite one specific call example (timestamp or
quote) each, and give one concrete coaching suggestion; add a team summary (highest performer, most
improved, team average, total calls). Tie every score and priority to a specific call and quote.
Humanizer rules: no em dashes, no AI throat-clearing, no hype, one clear ask. Output the report
exactly per the canonical spec."""


class State(TypedDict, total=False):
    calls: list[dict[str, Any]]
    prior_calls: list[dict[str, Any]]
    report: str


def fetch_calls(state: State) -> State:
    # TODO: fetch this week's team calls from your recorder, or load transcripts via the
    # dealtrace adapters: from dealtrace.adapters import load_transcript
    return {"calls": []}


def fetch_prior_calls(state: State) -> State:
    # TODO: fetch the prior 7-day window's calls for the trend comparison.
    return {"prior_calls": []}


def analyze(state: State) -> State:
    if not state.get("calls"):
        return {"report": "No calls recorded this period. Scorecard generation skipped."}
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
