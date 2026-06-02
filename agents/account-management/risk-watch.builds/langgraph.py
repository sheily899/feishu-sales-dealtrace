"""Risk Watch — LangGraph build.

Per-call graph: fetch the analyzed call -> pull the account's recent history -> read CRM account
metadata -> Claude evaluates risk and drafts a tiered alert -> post to the CS channel ONLY when a
risk is present. Swap the TODO bodies for your recorder / CRM / Slack. The reasoning is one Anthropic
call whose system prompt is the agent's operating logic (mirrors agents/account-management/risk-watch.md).

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    # invoke per analyzed call, passing the call id from your recorder webhook:
    python langgraph.py <CALL_ID>      # or build_graph().invoke({"call_id": "..."}) from your handler
"""
from __future__ import annotations

import sys
from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Risk Watch agent, evaluating one analyzed customer call for account
risk. The CSM is the rep-equivalent; the customer is the account on the other side. Using the call,
the account's recent history (last 30 days vs prior 30), and the account metadata, evaluate these risk
indicators: engagement drop (fewer calls than the prior period, or key stakeholders absent), negative
sentiment ('not happy', 'frustrated', 'reconsider'), competitor mentions, escalation language
(manager/legal/SLA/termination), usage challenges (bugs, adoption struggles), relationship risk
(champion leaving or gone silent, new stakeholder with no context). Assign severity. CRITICAL:
explicit cancellation/non-renewal/termination, active competitor evaluation, escalation to legal/exec,
or 2+ indicators at once. HIGH: negative sentiment with an unresolved issue, engagement down 50%+,
competitor in passing, or champion departure. MEDIUM: single mild frustration, minor dip, a workable
usage challenge, or one carried-over action item. Highest tier wins if indicators span tiers. If NO
indicators are present, reply with exactly NO_RISK and nothing else. Otherwise output the tiered alert
in the per-tier format from the spec (CRITICAL :red_circle:, HIGH :large_orange_circle:, MEDIUM
:yellow_circle:) with the indicators and their evidence quotes, the account context, and the
recommended next actions. Tie every indicator to a transcript quote or a baseline metric; no
speculation. Apply humanizer rules: no em dashes, no AI throat-clearing, no hype adjectives, one clear ask."""


class State(TypedDict, total=False):
    call_id: str
    call: dict[str, Any]
    history: list[dict[str, Any]]
    account_meta: dict[str, Any]
    alert: str


def fetch_call(state: State) -> State:
    # TODO: fetch the analyzed call by state["call_id"] from your recorder, or load_transcript via gtmsi adapters.
    return {"call": {}}


def fetch_history(state: State) -> State:
    # TODO: pull the same account's recent calls (last ~60 days) for the engagement baseline.
    return {"history": []}


def fetch_account_meta(state: State) -> State:
    # TODO: read account metadata (owner/CSM, contract value, renewal date, open cases) from your CRM.
    return {"account_meta": {}}


def evaluate_risk(state: State) -> State:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": (
            f"CALL:\n{state.get('call', {})}\n\n"
            f"ACCOUNT HISTORY:\n{state.get('history', [])}\n\n"
            f"ACCOUNT METADATA:\n{state.get('account_meta', {})}"
        )}],
    )
    return {"alert": msg.content[0].text}


def post_alert(state: State) -> State:
    alert = state.get("alert", "")
    if "NO_RISK" in alert:
        return {}  # no risk indicators: stay silent
    # TODO: post alert to your account-risk / CS-alerts Slack channel (Web API or webhook).
    print(alert)
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_call", fetch_call)
    g.add_node("fetch_history", fetch_history)
    g.add_node("fetch_account_meta", fetch_account_meta)
    g.add_node("evaluate_risk", evaluate_risk)
    g.add_node("post_alert", post_alert)
    g.add_edge(START, "fetch_call")
    g.add_edge("fetch_call", "fetch_history")
    g.add_edge("fetch_history", "fetch_account_meta")
    g.add_edge("fetch_account_meta", "evaluate_risk")
    g.add_edge("evaluate_risk", "post_alert")
    g.add_edge("post_alert", END)
    return g.compile()


if __name__ == "__main__":
    call_id = sys.argv[1] if len(sys.argv) > 1 else "<CALL_ID>"
    build_graph().invoke({"call_id": call_id})
