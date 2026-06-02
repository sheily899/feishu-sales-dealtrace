"""Pre-Call Prep — LangGraph build.

A 5-node graph: read calendar -> match CRM -> fetch prior calls -> Claude briefing -> DM the rep.
Swap the TODO bodies for your calendar / CRM / recorder / Slack. The reasoning is one Anthropic call
whose system prompt is the agent's operating logic (mirrors agents/sales-enablement/pre-call-prep.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Pre-Call Prep agent. Given today's meetings, their matched CRM
accounts/opportunities, and prior-call summaries: for each meeting write a rich block with a
human-style TL;DR, attendee context, relationship summary, opportunity context, recent activity
recap, risks/challenges, competitive landscape, recommended focus for today, strategic tips, and
useful artifacts. List meetings in chronological order. If there are no customer meetings, output
'Good morning! You have no customer meetings on your calendar today.' Use emojis and clean headings,
NO markdown bold or '*' symbols. Every fact comes from the calendar, CRM, or a prior call. Humanizer
rules: no em dashes, no AI throat-clearing, no hype, one clear ask."""


class State(TypedDict, total=False):
    meetings: list[dict[str, Any]]
    crm: list[dict[str, Any]]
    calls: list[dict[str, Any]]
    briefing: str


def read_calendar(state: State) -> State:
    # TODO: read today's meetings (7:00 AM - 7:00 PM) from your calendar API.
    return {"meetings": []}


def match_crm(state: State) -> State:
    # TODO: match attendees to a CRM account + most relevant opportunity.
    return {"crm": []}


def fetch_calls(state: State) -> State:
    # TODO: for each matched account/opportunity, fetch prior-call summaries from your recorder,
    # or load transcripts via the gtmsi adapters: from gtmsi.adapters import load_transcript
    return {"calls": []}


def analyze(state: State) -> State:
    if not state.get("meetings"):
        return {"briefing": "Good morning! You have no customer meetings on your calendar today."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"MEETINGS:\n{state['meetings']}\n\nCRM:\n{state.get('crm', [])}\n\nPRIOR CALLS:\n{state.get('calls', [])}"}],
    )
    return {"briefing": msg.content[0].text}


def dm_rep(state: State) -> State:
    # TODO: DM state["briefing"] to the rep on Slack (Web API or webhook).
    print(state["briefing"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("read_calendar", read_calendar)
    g.add_node("match_crm", match_crm)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("analyze", analyze)
    g.add_node("dm_rep", dm_rep)
    g.add_edge(START, "read_calendar")
    g.add_edge("read_calendar", "match_crm")
    g.add_edge("match_crm", "fetch_calls")
    g.add_edge("fetch_calls", "analyze")
    g.add_edge("analyze", "dm_rep")
    g.add_edge("dm_rep", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
