"""Objection Catcher — LangGraph build.

A 4-node graph: fetch the week's calls -> fetch CRM outcomes -> Claude analysis -> email the digest.
Swap the TODO bodies for your recorder / CRM / email. The reasoning is one Anthropic call whose
system prompt is the agent's operating logic (mirrors agents/sales-enablement/objection-catcher.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Objection Catcher agent. Given the week's calls (with transcripts) and
optional CRM outcomes: extract every objection (quote, timestamp mm:ss, category, rep response quote,
response-pattern label); normalize into the fixed taxonomy (Pricing, Timing/Priority, Competitor,
Feature Gap, Security/Legal, Integration, Authority, ROI/Proof, Contract/Procurement, Other); score
each objection/response pair 0-100 on clarity, empathy, proof, next step, weighting by deal outcomes
where available (meeting booked / stage advanced / won/lost); rank categories by frequency and impact
and pick the 1-3 highest-scoring rebuttals per top category with why each worked; compute weekly stats
(counts, % of calls with objections, WoW change, best patterns, low-score coaching opportunities) and
2-4 coaching tips per top category. Unanswered objections are coaching opportunities. Keep a
constructive tone. Tie every example to a call quote and timestamp. Humanizer rules: no em dashes, no
AI throat-clearing, no hype, one clear ask. Output the digest exactly per the canonical spec as plain
text."""


class State(TypedDict, total=False):
    calls: list[dict[str, Any]]
    outcomes: list[dict[str, Any]]
    digest: str


def fetch_calls(state: State) -> State:
    # TODO: pull the last 7 days of calls with transcripts from your recorder, or load transcripts via
    # the dealtrace adapters: from dealtrace.adapters import load_transcript
    return {"calls": []}


def fetch_outcomes(state: State) -> State:
    # TODO: optional - query your CRM for deal outcomes per call (stage/advanced/won/lost) to weight.
    return {"outcomes": []}


def analyze(state: State) -> State:
    if not state.get("calls"):
        return {"digest": "Objection Catcher ran. No recorded calls with transcripts were found this week."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALLS:\n{state['calls']}\n\nCRM OUTCOMES:\n{state.get('outcomes', [])}"}],
    )
    return {"digest": msg.content[0].text}


def send_email(state: State) -> State:
    # TODO: email state["digest"] to the enablement owner(s) (Gmail/Outlook API or SMTP).
    print(state["digest"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("fetch_outcomes", fetch_outcomes)
    g.add_node("analyze", analyze)
    g.add_node("send_email", send_email)
    g.add_edge(START, "fetch_calls")
    g.add_edge("fetch_calls", "fetch_outcomes")
    g.add_edge("fetch_outcomes", "analyze")
    g.add_edge("analyze", "send_email")
    g.add_edge("send_email", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
