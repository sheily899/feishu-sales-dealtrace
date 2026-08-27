"""Content Gaps — LangGraph build.

A 3-node graph: fetch the week's calls -> Claude analysis -> post to the channel. Swap the TODO
bodies for your recorder / chat tool. The reasoning is one Anthropic call whose system prompt is the
agent's operating logic (mirrors agents/sales-enablement/content-gaps.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Content Gaps agent. Given the week's analyzed calls: extract every
prospect question/objection, the rep's answer (and whether it resolved it), and rep uncertainty
signals (filler, deflection, hedging, promises to follow up); cluster the questions into recurring
themes, merging variants; score each theme by frequency (calls and distinct reps) and impact (stalled
or negative-sentiment deals) and rank by frequency then impact; for each top theme recommend one
concrete enablement action (one-pager, FAQ, demo clip, battlecard update, micro-training) and call
out broader training needs. If reps answered confidently across the board, say so and skip
recommendations rather than inventing gaps. Keep a constructive tone. Use single stars for emphasis,
never double stars. Humanizer rules: no em dashes, no AI throat-clearing, no hype, one clear ask.
Output the report exactly per the canonical spec."""


class State(TypedDict, total=False):
    calls: list[dict[str, Any]]
    report: str


def fetch_calls(state: State) -> State:
    # TODO: pull the last 7 days of analyzed calls from your recorder (with account/product/rep/
    # sentiment), or load transcripts via the dealtrace adapters: from dealtrace.adapters import load_transcript
    return {"calls": []}


def analyze(state: State) -> State:
    if not state.get("calls"):
        return {"report": "Weekly Content Gap Report ran. No analyzed calls were found this week."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"THIS WEEK'S CALLS:\n{state['calls']}"}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to your team channel (Slack/Teams Web API or webhook).
    print(state["report"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_calls")
    g.add_edge("fetch_calls", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
