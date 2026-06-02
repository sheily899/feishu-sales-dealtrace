"""Revenue Sentry — LangGraph build.

A 4-node graph: fetch open deals -> fetch their calls -> Claude risk analysis -> post to Slack.
Swap the TODO bodies for your CRM / recorder / Slack. The reasoning is one Anthropic call whose
system prompt is the agent's operating logic (mirrors agents/revenue-operations/revenue-sentry.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Revenue Sentry agent. Given the open deals and their recent calls:
score each deal 0-3 on five risk dimensions (higher = riskier), each backed by call evidence:
Engagement Cadence, Sentiment Trajectory, Unresolved Objections, Competitive Pressure,
Timeline Slippage; Total Risk = sum out of 15 (if close date is today or past due, set Timeline
Slippage to 3). Classify each deal RED ALERT (10-15), ORANGE WARNING (6-9), YELLOW WATCH (3-5),
GREEN HEALTHY (0-2); include only RED, ORANGE, YELLOW; omit GREEN. Attach a specific recommended
intervention to every RED and ORANGE deal. Tie every score to CRM data or a call quote. Humanizer
rules: no em dashes, no AI throat-clearing, no hype, one clear ask. Output the alert exactly per the
canonical spec, with a pipeline health summary and total revenue at risk."""


class State(TypedDict, total=False):
    deals: list[dict[str, Any]]
    calls: list[dict[str, Any]]
    report: str


def fetch_open_deals(state: State) -> State:
    # TODO: query your CRM for open opportunities (name, stage, amount, close date, owner, last activity).
    return {"deals": []}


def fetch_calls(state: State) -> State:
    # TODO: for each deal, fetch its last 14 days of calls from your recorder, or load transcripts via
    # the gtmsi adapters: from gtmsi.adapters import load_transcript
    return {"calls": []}


def analyze(state: State) -> State:
    if not state.get("deals"):
        return {"report": "Revenue Sentry ran. No open deals to scan. Pipeline is empty or all closed."}
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
