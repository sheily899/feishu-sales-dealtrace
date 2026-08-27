"""Cross Team Handoff — LangGraph build.

A 4-node graph: detect transitioned accounts -> fetch their calls -> Claude writes the handoff ->
post to Slack. Swap the TODO bodies for your CRM / recorder / Slack. The reasoning is one Anthropic
call whose system prompt is the agent's operating logic (mirrors agents/operations/cross-team-handoff.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Cross-Team Handoff agent. Given the transitioned accounts and their
calls, write a handoff for the receiving team. For each account reconstruct: a chronological call
history, a stakeholder map (name, title, role, disposition), and every commitment the team made with
who, when, and fulfilled-or-outstanding status. Write the handoff with sections: ":arrow_right:
Account Handoff Summary - [Account]" with the transition/value/stage/date header; "1. Deal Context";
"2. Stakeholder Map" (table + primary contact going forward); "3. Conversation History Highlights"
(5-10 calls); "4. Commitments and Promises Made" (:white_check_mark: fulfilled, :hourglass:
outstanding, flag overdue); "5. Open Items and Risks"; "6. Recommended Next Steps for the receiving
team" (numbered). Tie every claim to CRM data or a call quote. Humanizer rules: no em dashes, no AI
throat-clearing, no hype, one clear ask. Output the handoff exactly per the canonical spec."""


class State(TypedDict, total=False):
    accounts: list[dict[str, Any]]
    calls: list[dict[str, Any]]
    report: str


def detect_transitions(state: State) -> State:
    # TODO: query your CRM for accounts whose stage or owner changed in the window.
    return {"accounts": []}


def fetch_calls(state: State) -> State:
    # TODO: for each account, fetch its calls from your recorder, or load transcripts via the
    # dealtrace adapters: from dealtrace.adapters import load_transcript
    return {"calls": []}


def analyze(state: State) -> State:
    if not state.get("accounts"):
        return {"report": "Cross-Team Handoff ran. No transitions detected."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"TRANSITIONED ACCOUNTS:\n{state['accounts']}\n\nCALLS:\n{state.get('calls', [])}"}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to the receiving team's Slack channel (Web API or webhook).
    print(state["report"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("detect_transitions", detect_transitions)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "detect_transitions")
    g.add_edge("detect_transitions", "fetch_calls")
    g.add_edge("fetch_calls", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
