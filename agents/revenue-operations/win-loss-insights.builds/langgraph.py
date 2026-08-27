"""Win Loss Insights — LangGraph build.

A 4-node graph: fetch closed deals -> fetch their calls -> Claude analysis -> post to Slack.
Swap the TODO bodies for your CRM / recorder / Slack. The reasoning is one Anthropic call whose
system prompt is the agent's operating logic (mirrors agents/revenue-operations/win-loss-insights.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Win Loss Insights agent. Given the closed deals (won and lost) over the
trailing 30 days and their calls: analyze the WON and LOST cohorts SEPARATELY across five dimensions
(Win Themes, Loss Themes, Competitive Dynamics, Sales Cycle Patterns, Pricing Sensitivity); compare
to the prior 30-day window for trend (win rate, theme shifts, competitive shifts, cycle length);
produce 3-5 strategic recommendations with rationale. Tie every theme and number to CRM data or a
call quote. Humanizer rules: no em dashes, no AI throat-clearing, no hype, one clear ask. Output the
report exactly per the canonical spec (executive summary, win/loss themes, competitive table,
sales-cycle patterns, pricing insights, recommendations, trend vs prior period, source line)."""


class State(TypedDict, total=False):
    deals: list[dict[str, Any]]
    prior_deals: list[dict[str, Any]]
    calls: list[dict[str, Any]]
    report: str


def fetch_closed_deals(state: State) -> State:
    # TODO: query your CRM for closed-won/closed-lost opportunities in the last 30 days (and 31-60 for trend).
    return {"deals": [], "prior_deals": []}


def fetch_calls(state: State) -> State:
    # TODO: for each deal, fetch its calls from your recorder, or load transcripts via the
    # dealtrace adapters: from dealtrace.adapters import load_transcript
    return {"calls": []}


def analyze(state: State) -> State:
    if not state.get("deals"):
        return {"report": "Win Loss Insights ran. No deals closed in the last 30 days. Report will resume when data is available."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"CLOSED DEALS (last 30d):\n{state['deals']}\n\n"
            f"PRIOR PERIOD (31-60d):\n{state.get('prior_deals', [])}\n\n"
            f"CALLS:\n{state.get('calls', [])}"
        )}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to your Slack channel (Web API or webhook).
    print(state["report"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_closed_deals", fetch_closed_deals)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_closed_deals")
    g.add_edge("fetch_closed_deals", "fetch_calls")
    g.add_edge("fetch_calls", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
