"""Social Proof Finder — LangGraph build.

A 3-node graph: fetch the week's calls -> Claude finds social proof -> post the report to Slack. Swap
the TODO bodies for your recorder / Slack. The reasoning is one Anthropic call whose system prompt is
the agent's operating logic (mirrors agents/marketing/social-proof-finder.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Social Proof Finder agent. Given the week's customer-facing calls:
flag moments of genuine customer satisfaction, success, or positive outcomes. PRIORITIZE specific,
authentic quotes that mention a measurable result; AVOID false positives (routine politeness, neutral
status talk). Group by account, lead with a one-line header (count of stories), then per story output
call title, one-line summary, verbatim quote, account / speaker + title, call link. Sort the
strongest, results-backed quotes first. Note that quotes are unverified draft material and need
customer approval before public use. Humanizer rules: no em dashes, no AI throat-clearing, no hype,
one clear ask."""


class State(TypedDict, total=False):
    calls: list[dict[str, Any]]
    report: str


def fetch_calls(state: State) -> State:
    # TODO: fetch the last 7 days of customer-facing calls from your recorder, or load transcripts via
    # the gtmsi adapters: from gtmsi.adapters import load_transcript
    return {"calls": []}


def find_social_proof(state: State) -> State:
    if not state.get("calls"):
        return {"report": "Social Proof Finder ran. No customer calls recorded this week, so no social proof to report."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALLS:\n{state['calls']}"}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to your marketing/sales Slack channel (Web API or webhook).
    print(state["report"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("find_social_proof", find_social_proof)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_calls")
    g.add_edge("fetch_calls", "find_social_proof")
    g.add_edge("find_social_proof", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
