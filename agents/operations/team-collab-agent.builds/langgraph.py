"""Team Collab Agent — LangGraph build.

A 3-node graph: fetch the analyzed call -> Claude picks the teams -> post to Slack only if a team is
needed. Swap the TODO bodies for your recorder / Slack. The reasoning is one Anthropic call whose
system prompt is the agent's operating logic (mirrors agents/operations/team-collab-agent.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    # invoke per analyzed call from your recorder's "conversation analyzed" webhook:
    #   build_graph().invoke({"call_id": "<CALL_ID>"})
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Team Collaboration agent reviewing one analyzed customer call. Scan the
transcript against routing rules for six teams and flag every team genuinely needed (a call can need
several): SALES ENGINEERING, LEGAL, FINANCE/DEAL DESK, PROFESSIONAL SERVICES/IMPLEMENTATION, PRODUCT,
EXECUTIVE. Do NOT flag a team if the rep already fully resolved the question on the call. If no team
is needed, output exactly 'NO_SIGNALS'. Otherwise, for EACH flagged team output a separate block:
":handshake: Cross-Team Collaboration Needed - [Team]"; Account; Deal stage (or N/A); Call; Rep;
"Why [Team] is needed" (1-2 sentences); "Key quotes" (customer quote, rep response if relevant);
"Suggested next step" (specific); "Urgency" (High/Medium/Low). Separate each team's block clearly.
Back every alert with a verbatim quote. Humanizer rules: no em dashes, no AI throat-clearing, no
hype, one clear ask."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    alerts: str


def fetch_call(state: State) -> State:
    # TODO: fetch the transcript + metadata for state["call_id"] from your recorder,
    # or load it via the dealtrace adapters: from dealtrace.adapters import load_transcript
    return {"call": {}}


def route(state: State) -> State:
    if not state.get("call"):
        return {"alerts": "NO_SIGNALS"}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALL:\n{state['call']}"}],
    )
    return {"alerts": msg.content[0].text}


def post_alerts(state: State) -> State:
    alerts = state.get("alerts", "").strip()
    if not alerts or alerts == "NO_SIGNALS":
        return {}  # no team needed: post nothing
    # TODO: split alerts into per-team blocks and post each to its team Slack channel.
    print(alerts)
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("route", route)
    g.add_node("post_alerts", post_alerts)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "route")
    g.add_edge("route", "post_alerts")
    g.add_edge("post_alerts", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({"call_id": "<CALL_ID>"})
