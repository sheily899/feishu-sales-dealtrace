"""Lost-Deal Intel — LangGraph build.

A 4-node graph: fetch lost deals -> fetch their calls -> Claude analysis -> post to Slack.
Swap the TODO bodies for your CRM / recorder / Slack. The reasoning is one Anthropic call whose
system prompt is the agent's operating logic (mirrors agents/revenue-operations/lost-deal-intel.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Lost-Deal Intel agent. Given the lost deals and their calls:
classify each loss into one primary reason plus up to two contributing (with evidence) from
PRICING, COMPETITION, PRODUCT-GAP, TIMING, SALES-EXECUTION, CHAMPION-LOSS, NO-DECISION,
LEGAL-SECURITY; write a per-deal post-mortem (timeline + turning-point call, customer perspective +
key quote, competitive intel if relevant, sales-execution STRONG/ADEQUATE/WEAK, product-fit signal);
if 3+ losses add cross-deal patterns; end with 2-3 org-level recommendations. Tie every claim to CRM
data or a call quote. Humanizer rules: no em dashes, no AI throat-clearing, no hype, one clear ask.
Output the report exactly per the canonical spec."""


class State(TypedDict, total=False):
    deals: list[dict[str, Any]]
    calls: list[dict[str, Any]]
    report: str


def fetch_lost_deals(state: State) -> State:
    # TODO: query your CRM for Closed-Lost opportunities in the last 7 days.
    return {"deals": []}


def fetch_calls(state: State) -> State:
    # TODO: for each deal, fetch its calls from your recorder, or load transcripts via the
    # dealtrace adapters: from dealtrace.adapters import load_transcript
    return {"calls": []}


def analyze(state: State) -> State:
    if not state.get("deals"):
        return {"report": "Lost-Deal Intel ran. No deals were marked lost. Pipeline health is stable."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"LOST DEALS:\n{state['deals']}\n\nCALLS:\n{state.get('calls', [])}"}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to your Slack channel (Web API or webhook).
    print(state["report"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_lost_deals", fetch_lost_deals)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_lost_deals")
    g.add_edge("fetch_lost_deals", "fetch_calls")
    g.add_edge("fetch_calls", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
