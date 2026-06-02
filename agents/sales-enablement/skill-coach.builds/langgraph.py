"""Skill Coach — LangGraph build.

A 3-node graph: fetch this week's calls -> Claude skill evaluation -> post to Slack.
Swap the TODO bodies for your recorder / Slack. The reasoning is one Anthropic call whose system
prompt is the agent's operating logic (mirrors agents/sales-enablement/skill-coach.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Skill Coach agent. Given this week's calls grouped by rep: evaluate
each rep on five skills (Discovery Depth, Presentation Clarity, Objection Recovery, Rapport Building,
Closing Technique) and decide proficient or gap; for each gap extract one specific call moment (call
name/date, what happened, what the rep should have done instead) and assign one concrete coaching
exercise; produce one alert per rep with at least one gap (up to 3 gap blocks per rep), then a short
'No coaching gaps detected' summary for the rest. Tie every gap and moment to a specific call and
quote. Humanizer rules: no em dashes, no AI throat-clearing, no hype, one clear ask. Output exactly
per the canonical spec."""


class State(TypedDict, total=False):
    calls: list[dict[str, Any]]
    report: str


def fetch_calls(state: State) -> State:
    # TODO: fetch this week's team calls from your recorder, or load transcripts via the
    # gtmsi adapters: from gtmsi.adapters import load_transcript
    return {"calls": []}


def analyze(state: State) -> State:
    if not state.get("calls"):
        return {"report": "No calls recorded this week. Coaching alerts skipped."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"THIS WEEK (grouped by rep):\n{state['calls']}"}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to your Slack channel (Web API or webhook).
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
