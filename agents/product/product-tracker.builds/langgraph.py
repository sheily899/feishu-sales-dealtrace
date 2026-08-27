"""Product Tracker — LangGraph build.

A 3-node graph: fetch the week's calls -> Claude extracts and prioritizes product signals -> post the
digest to Slack. Swap the TODO bodies for your recorder / Slack. The reasoning is one Anthropic call
whose system prompt is the agent's operating logic (mirrors agents/product/product-tracker.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Product Tracker agent. Given the week's customer-facing calls: extract
every product signal (FEATURE REQUESTS, BUG REPORTS, WORKAROUND MENTIONS, COMPETITIVE FEATURE GAPS,
PRAISE, USABILITY COMPLAINTS), each with account, customer name and title, exact quote, and rep
response. Categorize into UX / Usability, Performance, Integrations, Missing Features, Bugs, or
Workflow Gaps. Prioritize by frequency (3+ = High, 2 = Medium, 1 = Low) and customer tier (enterprise
outweighs SMB) into P1-P4. Group duplicates with a count. Output a digest: header (calls analyzed,
signals extracted, accounts), P1-P4 blocks, Positive Feedback, Competitive Intel, Trends vs last
week. If one request dominates (5+), call it out as a Top Signal at the top. Every signal ties to a
verbatim quote and a named account. Humanizer rules: no em dashes, no AI throat-clearing, no hype."""


class State(TypedDict, total=False):
    calls: list[dict[str, Any]]
    digest: str


def fetch_calls(state: State) -> State:
    # TODO: fetch the last 7 days of customer-facing calls from your recorder, or load transcripts via
    # the dealtrace adapters: from dealtrace.adapters import load_transcript
    return {"calls": []}


def extract_feedback(state: State) -> State:
    if not state.get("calls"):
        return {"digest": "No customer calls recorded this week. No product feedback to report."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALLS:\n{state['calls']}"}],
    )
    return {"digest": msg.content[0].text}


def post_digest(state: State) -> State:
    # TODO: post state["digest"] to your product Slack channel (Web API or webhook).
    print(state["digest"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("extract_feedback", extract_feedback)
    g.add_node("post_digest", post_digest)
    g.add_edge(START, "fetch_calls")
    g.add_edge("fetch_calls", "extract_feedback")
    g.add_edge("extract_feedback", "post_digest")
    g.add_edge("post_digest", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
