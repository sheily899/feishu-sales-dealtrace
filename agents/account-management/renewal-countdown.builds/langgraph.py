"""Renewal Countdown — LangGraph build.

A 4-node graph: fetch upcoming renewals -> fetch their calls -> Claude grades health + builds the
digest -> post to Slack. Swap the TODO bodies for your CRM / recorder / Slack. The reasoning is one
Anthropic call whose system prompt is the agent's operating logic (mirrors
agents/account-management/renewal-countdown.md). The CSM is the rep-equivalent; the customer is the
account on the other side.

    pip install langgraph anthropic
    export ANTHROPIC_API_KEY=...
    python langgraph.py        # or call build_graph().invoke({}) from your scheduler (cron, Airflow, ...)
"""
from __future__ import annotations

from typing import Any, TypedDict

import anthropic
from langgraph.graph import END, START, StateGraph

SYSTEM_PROMPT = """You are the Renewal Countdown agent. Given the accounts renewing in the next
30/60/90 days (with renewal date, contract value, owner, last-call date) and their calls over the last
~90 days: per account, report total calls, average sentiment, unresolved issues, competitor mentions,
expansion signals, and any dissatisfaction. Grade each renewal. HEALTHY: 3+ calls in 90 days, mostly
positive sentiment, no unresolved issues, no competitor mentions. AT RISK: 1-2 calls, OR mixed
sentiment, OR 1+ unresolved issues. CRITICAL: 0 calls in 90 days, OR a negative sentiment trend, OR
competitor mentions, OR explicit dissatisfaction. No call data -> CRITICAL with an 'immediate outreach
recommended' note. Size a prep action to the health and horizon (CRITICAL: urgent check-in this week;
AT RISK: value-recap + renewal discussion within two weeks; HEALTHY: renewal proposal with expansion
options). Output the digest exactly per the canonical spec, with 30-DAY / 60-DAY / 90-DAY sections
(each account: name, renewal date, value, owner, health, recent engagement, risk factors, prep
actions), a summary line of the counts, and an 'OVERDUE -- Needs Status Update' section for any
past-due, not-renewed account. Tie every health grade to a call count or a conversation signal. Apply
humanizer rules: no em dashes, no AI throat-clearing, no hype, one clear ask."""


class State(TypedDict, total=False):
    renewals: list[dict[str, Any]]
    calls: list[dict[str, Any]]
    digest: str


def fetch_renewals(state: State) -> State:
    # TODO: query your CRM for accounts with renewals in the next 30/60/90 days (resolve the real
    # renewal-date field, do not hardcode a label).
    return {"renewals": []}


def fetch_calls(state: State) -> State:
    # TODO: for each renewing account, fetch its calls over the last ~90 days from your recorder, or
    # load transcripts via the dealtrace adapters: from dealtrace.adapters import load_transcript
    return {"calls": []}


def build_digest(state: State) -> State:
    if not state.get("renewals"):
        return {"digest": "No upcoming renewals in the next 90 days. Next scan scheduled for the next run."}
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"RENEWALS (next 90d):\n{state['renewals']}\n\nCALLS:\n{state.get('calls', [])}"}],
    )
    return {"digest": msg.content[0].text}


def post_digest(state: State) -> State:
    # TODO: post state["digest"] to your renewals / account-management Slack channel (Web API or webhook).
    print(state["digest"])
    return {}


def build_graph():
    g = StateGraph(State)
    g.add_node("fetch_renewals", fetch_renewals)
    g.add_node("fetch_calls", fetch_calls)
    g.add_node("build_digest", build_digest)
    g.add_node("post_digest", post_digest)
    g.add_edge(START, "fetch_renewals")
    g.add_edge("fetch_renewals", "fetch_calls")
    g.add_edge("fetch_calls", "build_digest")
    g.add_edge("build_digest", "post_digest")
    g.add_edge("post_digest", END)
    return g.compile()


if __name__ == "__main__":
    build_graph().invoke({})
