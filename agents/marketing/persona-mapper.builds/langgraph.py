"""Persona Mapper — LangGraph build.

A 3-node graph: fetch the analyzed call -> Claude maps the personas -> post the brief to a channel.
Swap the TODO bodies for your recorder / Slack. The reasoning is one Anthropic call whose system
prompt is the agent's operating logic (mirrors agents/marketing/persona-mapper.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({"call_id": "..."}) from your webhook handler
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Persona Mapper agent. Given one analyzed call: identify every persona
mentioned or speaking (title, department, inferred buyer role), pull each one's goals, challenges,
and marketing-relevant priorities, and map the buying-group shape. Then translate into concrete
marketing opportunities. Output a brief with three sections: Personas Identified (one line each),
Key Priorities, Opportunities for Marketing. Label inferred roles as inferred. Do not invent
personas, titles, or priorities. This is a working draft. Humanizer rules: no em dashes, no AI
throat-clearing, no hype."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    brief: str


def fetch_call(state: State) -> State:
    # TODO: fetch the analyzed call from your recorder, or load it via the dealtrace adapters:
    # from dealtrace.adapters import load_transcript
    return {"call": {}}


def map_personas(state: State) -> State:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALL:\n{state.get('call', {})}"}],
    )
    return {"brief": msg.content[0].text}


def post_brief(state: State) -> State:
    # TODO: post state["brief"] to your marketing Slack channel (Web API or webhook).
    print(state["brief"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("map_personas", map_personas)
    g.add_node("post_brief", post_brief)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "map_personas")
    g.add_edge("map_personas", "post_brief")
    g.add_edge("post_brief", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({"call_id": "<CALL_ID>"})
