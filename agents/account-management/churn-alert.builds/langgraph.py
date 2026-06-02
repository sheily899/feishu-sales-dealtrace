"""Churn Alert — LangGraph build.

A 4-node graph: scope active customers -> fetch their calls -> Claude analysis -> post to Slack.
Swap the TODO bodies for your CRM / recorder / Slack. The reasoning is one Anthropic call whose
system prompt is the agent's operating logic (mirrors agents/account-management/churn-alert.md).
The CSM is the rep-equivalent; the customer is the account on the other side.

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Churn Alert agent. Given the active customer accounts (with CRM health
data) and their calls over the last ~90 days: per account, report call frequency and any drop versus
the prior period, average sentiment and the trend, unresolved issues, competitor or alternative
mentions, expressed dissatisfaction, and any expansion signals. Fuse CRM health, usage trends, and
conversation signals and assign severity. HIGH: multiple strong signals at once. MEDIUM: one clear
signal or a few mild ones. LOW (monitor): minor fluctuations or early signals. For each at-risk
account, give the key risk drivers and one specific proactive retention tactic for this week.
Anonymize company names with a stable alias per account. This report covers ACTIVE customers, not
live deals. Tie every rating to CRM health data or a call signal. If no churn signals are detected,
output 'No churn signals detected this week. Customer base is stable.' Apply humanizer rules: no em
dashes, no AI throat-clearing, no hype, one clear ask. Output the report exactly per the canonical
spec, with High / Medium / Low (Monitor) sections and a summary line of the counts by category."""


class State(TypedDict, total=False):
    accounts: list[dict[str, Any]]
    calls: list[dict[str, Any]]
    report: str


def fetch_active_accounts(state: State) -> State:
    # TODO: query your CRM for ACTIVE customer accounts (exclude open/live deals) and their health data.
    return {"accounts": []}


def fetch_calls(state: State) -> State:
    # TODO: for each account, fetch its calls over the last ~90 days from your recorder, or load
    # transcripts via the gtmsi adapters: from gtmsi.adapters import load_transcript
    return {"calls": []}


def analyze(state: State) -> State:
    if not state.get("accounts"):
        return {"report": "Churn Alert ran. No active customers were found to analyze."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"ACTIVE CUSTOMERS:\n{state['accounts']}\n\nCALLS:\n{state.get('calls', [])}"}],
    )
    return {"report": msg.content[0].text}


def post_report(state: State) -> State:
    # TODO: post state["report"] to your CS / account-management Slack channel (Web API or webhook).
    print(state["report"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_active_accounts", fetch_active_accounts)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("analyze", analyze)
    g.add_node("post_report", post_report)
    g.add_edge(START, "fetch_active_accounts")
    g.add_edge("fetch_active_accounts", "fetch_calls")
    g.add_edge("fetch_calls", "analyze")
    g.add_edge("analyze", "post_report")
    g.add_edge("post_report", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
