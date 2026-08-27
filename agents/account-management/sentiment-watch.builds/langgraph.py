"""Sentiment Watch — LangGraph build.

A 3-node graph: fetch the analyzed call -> Claude sentiment analysis -> alert the owner (only on an
extreme). Swap the TODO bodies for your recorder / Slack. The reasoning is one Anthropic call whose
system prompt is the agent's operating logic (mirrors agents/account-management/sentiment-watch.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({"call_id": "..."}) from your webhook handler
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Sentiment Watch agent. Given one analyzed call: read overall and
customer sentiment, top emotion tags, roles (customer vs rep/owner), and the most revealing quote.
Classify HIGHLY POSITIVE / HIGHLY NEGATIVE / NEUTRAL (routine politeness does NOT count; when in
doubt, NEUTRAL). If NEUTRAL, output exactly 'NEUTRAL - no alert'. Otherwise output: 'Sentiment:
<POSITIVE|NEGATIVE>', 'Account / Owner', 'Why' (1-2 sentences tied to the call), 'Quote' (verbatim),
'Suggested next step', 'Call' (link). Tie every flag to a verbatim quote. Humanizer rules: no em
dashes, no AI throat-clearing, no hype, one clear ask."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    alert: str


def fetch_call(state: State) -> State:
    # TODO: fetch the analyzed call from your recorder, or load it via the dealtrace adapters:
    # from dealtrace.adapters import load_transcript
    return {"call": {}}


def analyze(state: State) -> State:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALL:\n{state.get('call', {})}"}],
    )
    return {"alert": msg.content[0].text}


def alert_owner(state: State) -> State:
    text = state.get("alert", "")
    if text.strip().startswith("NEUTRAL"):
        return {}  # not an extreme: stay silent
    # TODO: DM state["alert"] to the account owner via Slack (Web API or webhook).
    print(text)
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("analyze", analyze)
    g.add_node("alert_owner", alert_owner)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "analyze")
    g.add_edge("analyze", "alert_owner")
    g.add_edge("alert_owner", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({"call_id": "<CALL_ID>"})
