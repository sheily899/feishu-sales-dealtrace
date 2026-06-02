"""Compliance Checker — LangGraph build.

A 3-node graph: fetch the analyzed call -> Claude scans for violations -> post to Slack only if a
violation is found. Swap the TODO bodies for your recorder / Slack. The reasoning is one Anthropic
call whose system prompt is the agent's operating logic (mirrors agents/operations/compliance-checker.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    # invoke per analyzed call from your recorder's "conversation analyzed" webhook:
    #   build_graph().invoke({"call_id": "<CALL_ID>"})
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Compliance Checker agent reviewing one analyzed customer call. Scan the
transcript against five categories: A) unauthorized commercial commitments; B) data handling and
privacy; C) regulatory and legal claims; D) competitor disparagement (factual public comparisons are
NOT violations); E) sales conduct. Assign severity to each violation: CRITICAL, HIGH, or MEDIUM. If
there is NO violation, output exactly 'NO_VIOLATIONS'. Otherwise output the alert: ":rotating_light:
COMPLIANCE ALERT - [highest severity]"; Call, Rep, Account; a numbered list, each with "[Category]:
[label]", 'Transcript evidence: "[exact quote, max 2-3 sentences]"', "Risk: [one sentence]",
"Recommended action: [step]"; then "Overall recommendation". For any CRITICAL, prepend ":warning:
This alert is CRITICAL and may require immediate management review." Back every flag with a verbatim
quote. Humanizer rules: no em dashes, no AI throat-clearing, no hype, one clear ask."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    alert: str


def fetch_call(state: State) -> State:
    # TODO: fetch the transcript + metadata for state["call_id"] from your recorder,
    # or load it via the gtmsi adapters: from gtmsi.adapters import load_transcript
    return {"call": {}}


def scan(state: State) -> State:
    if not state.get("call"):
        return {"alert": "NO_VIOLATIONS"}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"CALL:\n{state['call']}"}],
    )
    return {"alert": msg.content[0].text}


def post_alert(state: State) -> State:
    alert = state.get("alert", "").strip()
    if not alert or alert == "NO_VIOLATIONS":
        return {}  # clean call: post nothing
    # TODO: post alert to your compliance Slack channel (Web API or webhook).
    print(alert)
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("scan", scan)
    g.add_node("post_alert", post_alert)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "scan")
    g.add_edge("scan", "post_alert")
    g.add_edge("post_alert", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({"call_id": "<CALL_ID>"})
