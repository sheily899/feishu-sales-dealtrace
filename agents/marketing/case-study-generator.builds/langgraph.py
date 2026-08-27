"""Case Study Generator — LangGraph build.

A 4-node graph: fetch the analyzed call -> fetch CRM facts -> Claude drafts the case study -> DM the
draft to marketing. Swap the TODO bodies for your recorder / CRM / Slack. The reasoning is one
Anthropic call whose system prompt is the agent's operating logic (mirrors
agents/marketing/case-study-generator.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({"call_id": "..."}) from your webhook handler
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Case Study Generator agent. Given one analyzed call and its CRM facts:
first confirm it is a success story (strong outcome, measurable result, satisfied customer, or
closed-won). If not, output exactly 'Not a success story - no case study drafted.'. Otherwise draft
a structured case study with sections Title, Client Overview, Challenge, Solution, Results, Customer
Quote (verbatim), Why it matters, then a '---' and a Review checklist (source call link, quotes
needing customer approval, unverified facts to confirm). Do not invent numbers, quotes, or outcomes.
This is a DRAFT; never publish, never address the customer. Humanizer rules: no em dashes, no AI
throat-clearing, no hype."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    crm: dict[str, Any]
    draft: str


def fetch_call(state: State) -> State:
    # TODO: fetch the analyzed call from your recorder, or load it via the dealtrace adapters:
    # from dealtrace.adapters import load_transcript
    return {"call": {}}


def fetch_crm(state: State) -> State:
    # TODO: query your CRM for the account/opportunity facts (account, industry, size, value, contacts, dates).
    return {"crm": {}}


def draft_case_study(state: State) -> State:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALL:\n{state.get('call', {})}\n\nCRM FACTS:\n{state.get('crm', {})}"}],
    )
    return {"draft": msg.content[0].text}


def send_draft(state: State) -> State:
    # TODO: DM state["draft"] to the marketing owner via Slack (Web API or webhook). Never publish.
    print(state["draft"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("fetch_crm", fetch_crm)
    g.add_node("draft_case_study", draft_case_study)
    g.add_node("send_draft", send_draft)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "fetch_crm")
    g.add_edge("fetch_crm", "draft_case_study")
    g.add_edge("draft_case_study", "send_draft")
    g.add_edge("send_draft", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({"call_id": "<CALL_ID>"})
