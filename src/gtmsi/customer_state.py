"""Evidence-guarded customer state generation from incremental group messages."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from .llm import CachedBlock
from .models import CustomerState, Quote, StateChange, StateChangeItem, StateItem, StateTodo, StateTransition


class StateLLM(Protocol):
    def complete_json(self, system: str, cached_blocks: list[CachedBlock], user_text: str, max_tokens: int | None = None): ...


@dataclass(frozen=True)
class CustomerStateResult:
    state: CustomerState
    change: StateChange
    rejected_changes: list[str]


_COLLECTIONS = {
    "need": "needs",
    "concern": "unresolved_concerns",
    "commitment": "commitments",
    "stakeholder": "stakeholders",
    "risk": "risks",
    "next_step": "scheduled_next_steps",
}

_SYSTEM = """You maintain a factual sales customer state. Return only JSON with `state` and `change`.
`state` must be the complete current state, not a summary. `change` must describe only changes caused
by the NEW messages. Every added, resolved, or status transition requires one or more exact or quoted
evidence entries containing speaker and text from NEW messages. Do not mark a todo completed or a
concern resolved unless a NEW message explicitly supports it. Write all generated text in Simplified Chinese."""


def _key(title: str) -> str:
    return "".join(title.casefold().split())


def _new_message_evidence(evidence: list[Quote], messages: list[Mapping[str, str]]) -> bool:
    if not evidence:
        return False
    texts = [str(message.get("text", "")) for message in messages]
    return all(quote.text and any(quote.text in text for text in texts) for quote in evidence)


def _matching_change(items: list[StateChangeItem], category: str, title: str) -> StateChangeItem | None:
    target = _key(title)
    return next((item for item in items if item.category == category and _key(item.title) == target), None)


def _matching_transition(items: list[StateTransition], category: str, title: str, target_status: str) -> StateTransition | None:
    target = _key(title)
    return next(
        (
            item for item in items
            if item.category == category and _key(item.title) == target and item.to_status == target_status
        ),
        None,
    )


def _render_messages(messages: list[Mapping[str, str]]) -> str:
    labels = {"customer": "客户", "sales": "销售"}
    return "\n".join(
        f"[{message.get('messageId', '')}] {labels.get(message.get('role', ''), '未知')}：{message.get('text', '')}"
        for message in messages
    )


def _merge_state(previous: CustomerState | None, candidate: CustomerState, change: StateChange,
                 messages: list[Mapping[str, str]]) -> CustomerStateResult:
    if previous is None:
        previous = CustomerState()
    rejected: list[str] = []
    accepted_added: list[StateChangeItem] = []
    accepted_resolved: list[StateChangeItem] = []
    accepted_transitions: list[StateTransition] = []

    # Only evidence-backed additions may enter a state collection. Existing items are retained
    # by default so a partial or malformed LLM response cannot silently delete business context.
    values: dict[str, list[StateItem]] = {}
    for category, attribute in _COLLECTIONS.items():
        old_items = list(getattr(previous, attribute))
        old_keys = {_key(item.title) for item in old_items}
        combined = list(old_items)
        for item in getattr(candidate, attribute):
            if _key(item.title) in old_keys:
                continue
            evidence_change = _matching_change(change.added, category, item.title)
            if evidence_change and _new_message_evidence(evidence_change.evidence, messages):
                combined.append(item.model_copy(update={"evidence": evidence_change.evidence}))
                accepted_added.append(evidence_change)
            else:
                rejected.append(f"新增 {item.title} 缺少本轮原文依据")
        values[attribute] = combined

    # Concerns are the one retained collection that can be resolved. Removal must be explicit
    # and grounded in a newly arrived message; otherwise the prior concern remains unresolved.
    candidate_concern_keys = {_key(item.title) for item in candidate.unresolved_concerns}
    for old in previous.unresolved_concerns:
        if _key(old.title) in candidate_concern_keys:
            continue
        resolved = _matching_change(change.resolved, "concern", old.title)
        if resolved and _new_message_evidence(resolved.evidence, messages):
            values["unresolved_concerns"] = [item for item in values["unresolved_concerns"] if _key(item.title) != _key(old.title)]
            accepted_resolved.append(resolved)
        else:
            rejected.append(f"解决 {old.title} 缺少本轮原文依据")

    previous_todos = {_key(todo.title): todo for todo in previous.todos}
    candidate_todos = {_key(todo.title): todo for todo in candidate.todos}
    todos: list[StateTodo] = []
    for title, old in previous_todos.items():
        proposed = candidate_todos.get(title, old)
        if proposed.status == old.status:
            todos.append(old)
            continue
        transition = _matching_transition(change.status_transitions, "todo", old.title, proposed.status)
        if transition and _new_message_evidence(transition.evidence, messages):
            todos.append(proposed.model_copy(update={"evidence": transition.evidence}))
            accepted_transitions.append(transition)
        else:
            todos.append(old)
            rejected.append(f"迁移 {old.title} 缺少本轮原文依据")
    for title, proposed in candidate_todos.items():
        if title in previous_todos:
            continue
        added = _matching_change(change.added, "todo", proposed.title)
        if added and _new_message_evidence(added.evidence, messages):
            todos.append(proposed.model_copy(update={"evidence": added.evidence}))
            accepted_added.append(added)
        else:
            rejected.append(f"新增 {proposed.title} 缺少本轮原文依据")

    state = candidate.model_copy(update={**values, "todos": todos, "version": 0, "updated_at": None, "analyzed_message_ids": []})
    safe_change = change.model_copy(update={
        "added": accepted_added,
        "resolved": accepted_resolved,
        "status_transitions": accepted_transitions,
        "evidence": [quote for quote in change.evidence if _new_message_evidence([quote], messages)],
    })
    return CustomerStateResult(state=state, change=safe_change, rejected_changes=rejected)


def generate_customer_state(
    previous: CustomerState | None,
    new_messages: list[Mapping[str, str]],
    llm: StateLLM,
) -> CustomerStateResult:
    """Generate a candidate state then deterministically reject unsupported mutations."""
    if not new_messages:
        raise ValueError("new_messages is required to generate a customer state")
    user_text = (
        "PREVIOUS_STATE:\n"
        f"{previous.model_dump_json(indent=2) if previous else '{}'}\n\n"
        "NEW_MESSAGES:\n"
        f"{_render_messages(new_messages)}\n\n"
        "Return JSON: {\"state\": CustomerState, \"change\": StateChange}."
    )
    raw = llm.complete_json(system=_SYSTEM, cached_blocks=[], user_text=user_text, max_tokens=4096)
    if not isinstance(raw, dict):
        raise ValueError("customer state model output must be a JSON object")
    candidate = CustomerState.model_validate(raw.get("state", {}))
    change = StateChange.model_validate(raw.get("change", {}))
    return _merge_state(previous, candidate, change, new_messages)
