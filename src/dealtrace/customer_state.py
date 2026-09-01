"""Evidence-guarded, operation-based customer issue lifecycle."""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from hashlib import sha256
from typing import Any, Protocol

from .llm import CachedBlock
from .models import (
    AppliedIssueOperation,
    CustomerIssue,
    CustomerState,
    IssueOperation,
    Quote,
    StateChange,
    StateChangeItem,
    StateItem,
    StateTodo,
    StateTransition,
)


class StateLLM(Protocol):
    def complete_json(self, system: str, cached_blocks: list[CachedBlock], user_text: str,
                      max_tokens: int | None = None): ...


@dataclass(frozen=True)
class CustomerStateResult:
    state: CustomerState
    change: StateChange
    rejected_changes: list[str]
    conflicts: list[str] = field(default_factory=list)
    raw_response: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] = field(default_factory=list)
    raw_model_response: dict[str, Any] | None = None
    normalized_response: dict[str, Any] | None = None
    schema_results: list[dict[str, Any]] = field(default_factory=list)


_COLLECTIONS = {
    "need": "needs", "concern": "unresolved_concerns", "commitment": "commitments",
    "stakeholder": "stakeholders", "risk": "risks", "next_step": "scheduled_next_steps",
}
_FUTURE_ACTION_CUES = (
    "我会", "我们会", "我将", "我们将", "我来", "我们来", "我负责", "我们负责",
    "我安排", "我们安排", "我发", "我们发", "我提供", "我们提供", "我转达",
    "我们转达", "下周", "明天", "稍后",
)
_REQUEST_ACTION_CUES = ("请", "麻烦", "帮忙", "需要你", "请您", "请你")
_RECOMMENDATION_CUES = ("建议", "可以考虑", "不妨", "最好", "推荐")
_SYSTEM = """You extract proposed lifecycle operations from NEW_MESSAGES.
The application, not the model, owns the final customer state. Return only one JSON object with
`operations`, optional `status_transitions`, and optional `current_focus`. Never return a complete
state snapshot.

Each operation is:
{"operation":"create|update|resolve|reopen|accept_workaround","issue_id":null,"category":"need|concern|commitment|todo|stakeholder|risk|next_step","business_object":"stable concise object key","title":"Chinese title","detail":"optional","executor":"责任方或null","action":"具体动作或null","temporal_status":"future|pending|completed|resolved","source_type":"customer_request|sales_commitment|task_assignment|determined_arrangement|fact|recommendation","evidence":[{"speaker":"客户","text":"exact excerpt from NEW_MESSAGES"}]}

Rules:
- create: omit issue_id. Create separate issues for separate business objects even when their category
  is the same. Never merge objects merely because they appear in one conversation.
- update/resolve/reopen: copy the exact issue_id, category, and business_object from PREVIOUS_ISSUES.
  Titles may be clarified without changing identity.
- resolve: only for an open historical issue and only when NEW_MESSAGES explicitly resolve that same
  object. Silence, topic changes, relaying information, or a proposal without acceptance are not resolution.
- reopen: only for a resolved historical issue with explicit new evidence that it became active again.
- concern means an explicit unresolved obstacle, pending confirmation, or pending approval, not vague
  wording alone. A pending approval is a concern, not a next_step. When one party proposes a material
  condition and the other party will only relay, consider, discuss, or seek approval instead of accepting
  it, create a separate open concern for that business object. If a newly raised concern is explicitly
  resolved within the same NEW_MESSAGES, do not create it as an open issue; only historical open issues
  can receive a resolve operation.
- next_step is only a scheduled interaction or milestone (for example, a meeting or demo time).
  A concrete deliverable or task must be `todo`, even when it is also scheduled.
- todo is valid when NEW_MESSAGES contain a concrete action, an identifiable responsible party
  (the speaker, the named recipient, or the party assigned by the request), and evidence. This includes
  a customer request ("请/麻烦…"), a task assignment, a sales promise ("我会/我来…"), or a determined
  arrangement ("计划/安排…"). Do not downgrade these to `next_step` or `commitment`.
- commitment is a separately tracked promise only when it is not itself a concrete task to be executed;
  concrete promises with an actionable deliverable should be `todo`.
  Fill `executor`, `action`, `temporal_status`, and `source_type` for every todo candidate.
  Recommendations belong only in
  current_focus and never become customer facts, todos, commitments, resolutions, or transitions.
- a behavior already completed in NEW_MESSAGES is a fact, not a future commitment.
- need is an explicit customer goal, capability requirement, or problem to solve; risk is an explicit
  negative fact with a plausible impact on deal, delivery, adoption, or renewal; stakeholder is a
  named or clearly identified participant in decision, approval, technical, implementation, or business
  coordination. If one message contains multiple independent facts (for example a role plus a risk plus
  a task), emit separate operations with separate evidence; never collapse them into one concern or todo.
- accept_workaround records a temporary workaround accepted for an open issue; it is not resolved.
- do not emit both resolve and reopen for one issue in a single response.
- every operation and transition must quote NEW_MESSAGES exactly. Write generated text in Simplified Chinese.
"""

_SUPPLEMENTAL_SYSTEM = """Review NEW_MESSAGES for omissions from the primary customer-state analysis.
Return only JSON: {\"candidates\": []}. Each candidate is a simple fact, never a lifecycle
operation: {\"category\": \"need|risk|stakeholder|commitment\", \"business_object\": "
"stable object, \"fact\": \"fact supported by the messages\", \"evidence_message_ids\": [\"id\"]}.
Risk must include business_impact; stakeholder must include role; commitment must include
future_commitment. To close an existing issue, include its exact issue_id and status=resolved.
Do not invent objects, IDs, evidence, or categories. Return an empty candidates array when
there is no supported omission.
"""



def _key(value: str) -> str:
    return "".join(value.casefold().split())


def _message_id(message: Mapping[str, Any]) -> str:
    return str(message.get("messageId") or message.get("message_id") or "unknown")


def _message_time(message: Mapping[str, Any]) -> str | None:
    for key in ("timestamp", "createTime", "create_time", "sentAt", "sent_at"):
        if message.get(key) is not None:
            return str(message[key])
    return None


def _ground_evidence(evidence: list[Quote], messages: list[Mapping[str, Any]]) -> list[Quote] | None:
    if not evidence:
        return None
    grounded: list[Quote] = []
    for quote in evidence:
        message = next((m for m in messages if quote.text and quote.text in str(m.get("text", ""))), None)
        if message is None:
            return None
        grounded.append(quote.model_copy(update={
            "message_id": _message_id(message), "occurred_at": _message_time(message),
        }))
    return grounded


def _has_future_action(operation: IssueOperation, evidence: list[Quote]) -> bool:
    if operation.source_type in {"recommendation", "ai_suggestion"}:
        return False
    if operation.executor and operation.action and operation.temporal_status in {"future", "pending"}:
        return True
    for quote in evidence:
        text = quote.text or ""
        if any(cue in text for cue in _RECOMMENDATION_CUES):
            continue
        explicit_request = any(cue in text for cue in _REQUEST_ACTION_CUES)
        explicit_assignment = any(cue in text for cue in _FUTURE_ACTION_CUES)
        if explicit_request or explicit_assignment:
            return True
    return False


def _has_commitment(operation: IssueOperation, evidence: list[Quote]) -> bool:
    """Validate a future promise without requiring a concrete executable todo."""
    if operation.source_type in {"recommendation", "ai_suggestion", "customer_request"}:
        return False
    if operation.temporal_status == "future" and (operation.detail or operation.title):
        return True
    return any(any(cue in (quote.text or "") for cue in _FUTURE_ACTION_CUES)
               for quote in evidence)


def _has_scheduled_step(operation: IssueOperation, evidence: list[Quote]) -> bool:
    """Validate an explicitly arranged milestone, independently of todo validation."""
    if operation.source_type in {"recommendation", "ai_suggestion"}:
        return False
    schedule_cues = ("安排", "计划", "约", "会议", "演示", "上线", "培训", "明天", "下周", "本周", "本月", "号", "日")
    return operation.temporal_status in {"future", "pending"} and any(
        any(cue in (quote.text or "") for cue in schedule_cues) for quote in evidence
    )


def _bigrams(value: str) -> set[str]:
    normalized = _key(value.replace("legacy:", ""))
    if len(normalized) < 2:
        return {normalized} if normalized else set()
    return {normalized[index:index + 2] for index in range(len(normalized) - 1)}


def _evidence_refers_to_issue(issue: CustomerIssue, evidence: list[Quote]) -> bool:
    """Require grounded evidence; exact historical issue_id supplies identity.

    Business-object text is only a corroborating signal. Completion messages
    commonly use a natural-language synonym rather than the stored key, so
    rejecting them solely for missing bigram overlap caused valid closes to be
    dropped. The caller has already verified the exact issue_id/category.
    """
    anchors = _bigrams(issue.business_object)
    evidence_text = _key(" ".join(quote.text for quote in evidence))
    return bool(evidence) and (not anchors or any(anchor in evidence_text for anchor in anchors) or
                               any(cue in evidence_text for cue in ("已完成", "已确认", "已解决", "通过", "接受", "完成")))


def _legacy_issue_id(category: str, title: str) -> str:
    digest = sha256(f"{category}:{_key(title)}".encode()).hexdigest()[:16]
    return f"legacy:{category}:{digest}"


def _migrate_legacy_issues(state: CustomerState) -> list[CustomerIssue]:
    """Migrate persisted v1 collections once; ongoing correlation uses issue_id only."""
    if state.issues:
        return [issue.model_copy(deep=True) for issue in state.issues]
    issues: list[CustomerIssue] = []
    for category, attribute in _COLLECTIONS.items():
        for item in getattr(state, attribute):
            first_id = next((q.message_id for q in item.evidence if q.message_id), "legacy")
            issues.append(CustomerIssue(
                issue_id=item.issue_id or _legacy_issue_id(category, item.title), category=category,
                business_object=f"legacy:{_key(item.title)}", status="open", title=item.title,
                detail=item.detail, evidence_history=item.evidence, created_message_id=first_id,
                updated_message_id=first_id,
            ))
    for item in state.todos:
        first_id = next((q.message_id for q in item.evidence if q.message_id), "legacy")
        issues.append(CustomerIssue(
            issue_id=item.issue_id or _legacy_issue_id("todo", item.title), category="todo",
            business_object=f"legacy:{_key(item.title)}",
            status="resolved" if item.status == "completed" else "open", title=item.title,
            detail=item.detail, evidence_history=item.evidence, created_message_id=first_id,
            updated_message_id=first_id,
        ))
    return issues


def _project_state(previous: CustomerState, issues: list[CustomerIssue], stage: str) -> CustomerState:
    values: dict[str, Any] = {attribute: [] for attribute in _COLLECTIONS.values()}
    values["todos"] = []
    for issue in issues:
        item = StateItem(issue_id=issue.issue_id, title=issue.title, detail=issue.detail,
                         evidence=issue.evidence_history)
        if issue.category == "todo":
            values["todos"].append(StateTodo.model_validate(
                item.model_dump() | {"status": "completed" if issue.status == "resolved" else "pending"}
            ))
        elif issue.status in {"open", "accepted_workaround"}:
            values[_COLLECTIONS[issue.category]].append(item)
    return previous.model_copy(update={
        **values, "issues": issues, "stage": stage, "version": 0, "updated_at": None,
        "analyzed_message_ids": [],
    })


def _append_evidence(existing: list[Quote], added: list[Quote]) -> list[Quote]:
    seen = {(quote.message_id, quote.text) for quote in existing}
    return existing + [quote for quote in added if (quote.message_id, quote.text) not in seen]


def _new_issue_id(category: str, evidence: list[Quote], ordinal: int, existing: set[str]) -> str:
    message_id = evidence[0].message_id or "unknown"
    while f"issue:{category}:{message_id}:{ordinal}" in existing:
        ordinal += 1
    return f"issue:{category}:{message_id}:{ordinal}"


def _change_item(operation: AppliedIssueOperation) -> StateChangeItem:
    return StateChangeItem(issue_id=operation.issue_id, category=operation.category,
                           title=operation.title, detail=operation.detail, evidence=operation.evidence)


def apply_issue_operations(
    previous: CustomerState | None,
    operations: list[IssueOperation],
    new_messages: list[Mapping[str, Any]],
    *,
    current_focus: str | None = None,
    status_transitions: list[StateTransition] | None = None,
    conflicts: list[str] | None = None,
    initial_stage: str | None = None,
) -> CustomerStateResult:
    """Validate proposals and derive the sole canonical final state."""
    previous = previous or CustomerState()
    issues = _migrate_legacy_issues(previous)
    by_id = {issue.issue_id: issue for issue in issues}
    historical_ids = set(by_id)
    rejected: list[str] = []
    accepted: list[AppliedIssueOperation] = []
    added: list[StateChangeItem] = []
    resolved: list[StateChangeItem] = []
    conflicts = list(conflicts or [])

    terminal: dict[str, set[str]] = {}
    for operation in operations:
        if operation.issue_id and operation.operation in {"resolve", "reopen"}:
            terminal.setdefault(operation.issue_id, set()).add(operation.operation)
    contradictory = {issue_id for issue_id, kinds in terminal.items() if len(kinds) > 1}
    create_ordinals: Counter[tuple[str, str]] = Counter()

    for operation in operations:
        if operation.issue_id in contradictory:
            rejected.append(f"事项 {operation.issue_id} 同时提出 resolve/reopen，生命周期变化冲突")
            continue
        grounded = _ground_evidence(operation.evidence, new_messages)
        if grounded is None:
            rejected.append(f"{operation.operation} {operation.title} 缺少本轮原文依据")
            continue
        if operation.operation == "create":
            valid_future = {
                "todo": _has_future_action(operation, grounded),
                "commitment": _has_commitment(operation, grounded),
                "next_step": _has_scheduled_step(operation, grounded),
            }.get(operation.category, True)
            if not valid_future:
                rejected.append(f"新增 {operation.title} 缺少明确的未来行动承诺（{operation.category} 未来事项证据不足）")
                continue
            ordinal_key = (operation.category, grounded[0].message_id or "unknown")
            ordinal = create_ordinals[ordinal_key]
            create_ordinals[ordinal_key] += 1
            issue_id = _new_issue_id(operation.category, grounded, ordinal, set(by_id))
            last = grounded[-1]
            issue = CustomerIssue(
                issue_id=issue_id, category=operation.category,
                business_object=operation.business_object, status="open", title=operation.title,
                detail=operation.detail, evidence_history=grounded,
                created_at=grounded[0].occurred_at, updated_at=last.occurred_at,
                created_message_id=grounded[0].message_id or "unknown",
                updated_message_id=last.message_id or "unknown",
            )
            issues.append(issue)
            by_id[issue_id] = issue
            applied = AppliedIssueOperation.model_validate(
                operation.model_dump() | {"issue_id": issue_id, "evidence": grounded}
            )
            accepted.append(applied)
            added.append(_change_item(applied))
            continue

        issue_id = operation.issue_id
        if not issue_id or issue_id not in historical_ids:
            rejected.append(f"{operation.operation} {operation.title} 不存在可关联的历史事项")
            continue
        issue = by_id[issue_id]
        if operation.category != issue.category:
            rejected.append(f"{operation.operation} {operation.title} 的类别与历史事项不一致")
            continue
        if operation.business_object != issue.business_object:
            rejected.append(f"{operation.operation} {operation.title} 的业务对象与历史事项不一致")
            continue
        if not _evidence_refers_to_issue(issue, grounded):
            rejected.append(f"{operation.operation} {operation.title} 的证据未指向同一业务对象")
            continue
        if operation.operation in {"resolve", "accept_workaround"} and issue.status not in {"open", "accepted_workaround"}:
            rejected.append(f"{operation.operation} {operation.title} 要求历史事项当前为 open 或 accepted_workaround")
            continue
        if operation.operation == "reopen" and issue.status != "resolved":
            rejected.append(f"reopen {operation.title} 要求历史事项当前为 resolved")
            continue

        status = ("resolved" if operation.operation == "resolve" else
                  "accepted_workaround" if operation.operation == "accept_workaround" else (
            "open" if operation.operation == "reopen" else issue.status
        ))
        last = grounded[-1]
        updated = issue.model_copy(update={
            "status": status, "title": operation.title,
            "detail": operation.detail if operation.detail is not None else issue.detail,
            "evidence_history": _append_evidence(issue.evidence_history, grounded),
            "updated_at": last.occurred_at,
            "updated_message_id": last.message_id or issue.updated_message_id,
        })
        issues[issues.index(issue)] = updated
        by_id[issue_id] = updated
        applied = AppliedIssueOperation.model_validate(
            operation.model_dump() | {"issue_id": issue_id, "evidence": grounded}
        )
        accepted.append(applied)
        if operation.operation == "resolve":
            resolved.append(_change_item(applied))
        elif operation.operation in {"reopen", "accept_workaround"}:
            added.append(_change_item(applied))

    stage = previous.stage
    if stage == "unknown" and initial_stage and initial_stage != "unknown":
        stage = initial_stage
    accepted_transitions: list[StateTransition] = []
    for transition in status_transitions or []:
        grounded = _ground_evidence(transition.evidence, new_messages)
        valid_history = (transition.category == "opportunity" and stage != "unknown"
                         and _key(transition.from_status) == _key(stage))
        if grounded is None or not valid_history:
            rejected.append(f"迁移 {transition.title} 缺少可关联的历史业务状态或本轮证据")
            continue
        stage = transition.to_status
        accepted_transitions.append(transition.model_copy(update={"evidence": grounded}))

    state = _project_state(previous, issues, stage)
    change = StateChange(operations=accepted, added=added, resolved=resolved,
                         status_transitions=accepted_transitions, current_focus=current_focus)
    return CustomerStateResult(state, change, rejected, conflicts)


def _legacy_target(item: StateChangeItem, issues: list[CustomerIssue]) -> CustomerIssue | None:
    if item.issue_id:
        return next((issue for issue in issues if issue.issue_id == item.issue_id), None)
    matches = [issue for issue in issues if issue.category == item.category
               and issue.status == "open" and _key(issue.title) == _key(item.title)]
    return matches[0] if len(matches) == 1 else None


def _adapt_legacy_response(raw: dict[str, Any], previous: CustomerState):
    """Read only v1 change; deliberately ignore its duplicate state snapshot."""
    raw_change = raw.get("change")
    if not isinstance(raw_change, dict):
        raise ValueError("customer state model output 'change' must be a JSON object")
    change = StateChange.model_validate(raw_change)
    issues = _migrate_legacy_issues(previous)
    operations: list[IssueOperation] = []
    for item in change.added:
        operations.append(IssueOperation(
            operation="create", category=item.category,
            business_object=f"legacy:{_key(item.title)}", title=item.title,
            detail=item.detail, evidence=item.evidence,
        ))
    for item in change.resolved:
        target = _legacy_target(item, issues)
        operations.append(IssueOperation(
            operation="resolve", issue_id=target.issue_id if target else item.issue_id,
            category=item.category,
            business_object=target.business_object if target else f"legacy:{_key(item.title)}",
            title=item.title, detail=item.detail, evidence=item.evidence,
        ))
    raw_state = raw.get("state")
    initial_stage = raw_state.get("stage") if isinstance(raw_state, dict) else None
    return (operations, change.status_transitions, change.current_focus,
            ["legacy adapter: ignored duplicate state snapshot; change is the sole mutation source"],
            initial_stage)


def _render_messages(messages: list[Mapping[str, Any]]) -> str:
    labels = {"customer": "客户", "sales": "销售"}
    return "\n".join(
        f"[{_message_id(m)}] {labels.get(str(m.get('role', '')), '未知')}：{m.get('text', '')}"
        for m in messages
    )


def generate_customer_state(previous: CustomerState | None, new_messages: list[Mapping[str, Any]],
                            llm: StateLLM, *, system_prompt: str | None = None) -> CustomerStateResult:
    """Ask the model for operations, then deterministically build final state."""
    if not new_messages:
        raise ValueError("new_messages is required to generate a customer state")
    previous = previous or CustomerState()
    previous_json = CustomerState(
        stage=previous.stage, issues=_migrate_legacy_issues(previous)
    ).model_dump_json(indent=2)
    user_text = (
        f"PREVIOUS_ISSUES:\n{previous_json}\n\nNEW_MESSAGES:\n{_render_messages(new_messages)}\n\n"
        "Return JSON: {\"operations\": [IssueOperation], \"status_transitions\": [], \"current_focus\": null}."
    )
    call_kwargs = {"system": system_prompt or _SYSTEM, "cached_blocks": [],
                   "user_text": user_text, "max_tokens": 4096}
    raw = llm.complete_json(**call_kwargs)
    # A syntactically valid but empty analysis is a semantic failure when messages exist.
    # Retry once with an explicit independent seed, without changing the primary prompt.
    empty_analysis = isinstance(raw, dict) and (
        (isinstance(raw.get("operations"), list) and not raw["operations"])
        or (isinstance(raw.get("change"), dict)
            and not any(raw["change"].get(key) for key in ("added", "resolved", "status_transitions")))
    )
    base_seed = getattr(llm, "seed", None)
    if empty_analysis and isinstance(base_seed, int):
        llm.seed = base_seed + 1
        try:
            raw = llm.complete_json(**call_kwargs)
        finally:
            llm.seed = base_seed
    if not isinstance(raw, dict):
        raise ValueError("customer state model output must be a JSON object")
    if "operations" in raw:
        if not isinstance(raw["operations"], list):
            raise ValueError("customer state model output 'operations' must be a JSON array")
        conflicts: list[str] = []
        operations: list[IssueOperation] = []
        schema_results: list[dict[str, Any]] = []
        non_core_fields = {"detail", "executor", "action", "temporal_status", "source_type"}
        for index, item in enumerate(raw["operations"]):
            if not isinstance(item, dict):
                conflicts.append(f"operations[{index}] 核心操作不是对象，已逐项拒绝")
                schema_results.append({"index": index, "accepted": False, "reason": "not_object"})
                continue
            normalized = dict(item)
            # Optional descriptive attributes are best-effort. A malformed value must not
            # discard an otherwise evidence-bound operation.
            for field_name in non_core_fields:
                if field_name in normalized and normalized[field_name] is not None \
                        and not isinstance(normalized[field_name], str):
                    conflicts.append(f"operations[{index}].{field_name} 非字符串，已降级为空值")
                    normalized[field_name] = None
            try:
                operations.append(IssueOperation.model_validate(normalized))
            except Exception as exc:
                conflicts.append(f"operations[{index}] 核心字段校验失败，已逐项拒绝: {exc}")
                schema_results.append({"index": index, "accepted": False, "reason": str(exc)})
            else:
                schema_results.append({"index": index, "accepted": True})
        transitions: list[StateTransition] = []
        raw_transitions = raw.get("status_transitions", [])
        if not isinstance(raw_transitions, list):
            conflicts.append("status_transitions 不是数组，已忽略该字段")
            raw_transitions = []
        for index, item in enumerate(raw_transitions):
            try:
                transitions.append(StateTransition.model_validate(item))
            except Exception as exc:
                conflicts.append(f"status_transitions[{index}] 核心字段校验失败，已逐项拒绝: {exc}")
        current_focus = raw.get("current_focus")
        if current_focus is not None and not isinstance(current_focus, str):
            conflicts.append("current_focus 非字符串，已降级为空值")
            current_focus = None
        initial_stage = None
    elif "change" in raw:
        operations, transitions, current_focus, conflicts, initial_stage = _adapt_legacy_response(
            raw, previous
        )
    else:
        raise ValueError("customer state model output is missing required 'operations' array")
    result = apply_issue_operations(
        previous, operations, new_messages, current_focus=current_focus,
        status_transitions=transitions, conflicts=conflicts, initial_stage=initial_stage,
    )
    return replace(result, raw_response=raw, candidates=raw.get("candidates", []),
                   schema_results=locals().get("schema_results", []))


def generate_supplemental_review(previous: CustomerState, new_messages: list[Mapping[str, Any]],
                                 llm: StateLLM, *, review_prompt: str = _SUPPLEMENTAL_SYSTEM) -> CustomerStateResult:
    """Run the opt-in fact review; the normal primary call never uses this path."""
    class _SupplementalLLM:
        raw_model_response: dict[str, Any] | None = None
        normalized_response: dict[str, Any] | None = None
        candidate_rejections: list[str] = []

        def complete_json(self, system, cached_blocks, user_text, max_tokens=None):
            raw = llm.complete_json(system, cached_blocks, user_text, max_tokens)
            self.raw_model_response = raw if isinstance(raw, dict) else None
            self.candidate_rejections = []
            candidates = raw.get("candidates") if isinstance(raw, dict) else None
            if not isinstance(candidates, list):
                self.normalized_response = {"operations": []}
                self.candidate_rejections.append("缺少 candidates 数组")
                return self.normalized_response
            categories = {"need", "risk", "stakeholder", "commitment"}
            by_message = {_message_id(message): message for message in new_messages}
            operations: list[dict[str, Any]] = []
            for index, candidate in enumerate(candidates):
                if not isinstance(candidate, dict):
                    self.candidate_rejections.append(f"candidate[{index}] 非对象")
                    continue
                category = candidate.get("category")
                obj = candidate.get("business_object") or candidate.get("object")
                fact = candidate.get("fact")
                ids = candidate.get("evidence_message_ids")
                if category not in categories or not isinstance(obj, str) or not obj:
                    self.candidate_rejections.append(f"candidate[{index}] 缺少合法 category/business_object")
                    continue
                if not isinstance(fact, str) or not fact or not isinstance(ids, list) or not ids:
                    self.candidate_rejections.append(f"candidate[{index}] 缺少 fact/evidence_message_ids")
                    continue
                if any(str(message_id) not in by_message for message_id in ids):
                    self.candidate_rejections.append(f"candidate[{index}] evidence_message_ids 不存在于本轮消息")
                    continue
                if category == "risk" and not candidate.get("business_impact"):
                    self.candidate_rejections.append(f"candidate[{index}] risk 缺少 business_impact")
                    continue
                if category == "stakeholder" and not candidate.get("role"):
                    self.candidate_rejections.append(f"candidate[{index}] stakeholder 缺少 role")
                    continue
                if category == "commitment" and not candidate.get("future_commitment"):
                    self.candidate_rejections.append(f"candidate[{index}] commitment 缺少 future_commitment")
                    continue
                evidence = [{"speaker": by_message[str(message_id)].get("role", "未知"),
                             "text": by_message[str(message_id)].get("text", "")}
                            for message_id in ids]
                operation = "resolve" if candidate.get("status") == "resolved" else "create"
                item = {"operation": operation, "category": category,
                        "business_object": obj, "title": fact, "detail": fact,
                        "evidence": evidence}
                if category == "commitment" and operation == "create":
                    item.update({"executor": candidate.get("executor") or "销售",
                                 "action": candidate.get("future_commitment"),
                                 "temporal_status": "future",
                                 "source_type": "sales_commitment"})
                if candidate.get("issue_id") is not None:
                    item["issue_id"] = candidate["issue_id"]
                operations.append(item)
            self.normalized_response = {"operations": operations}
            return self.normalized_response

    adapter = _SupplementalLLM()
    result = generate_customer_state(previous, new_messages, adapter,
                                     system_prompt=review_prompt)
    allowed = {"need", "risk", "stakeholder", "commitment"}
    invalid = [op for op in result.change.operations if op.category not in allowed]
    if not invalid:
        return replace(result, raw_model_response=adapter.raw_model_response,
                       candidates=(adapter.raw_model_response or {}).get("candidates", []),
                       normalized_response=adapter.normalized_response,
                       conflicts=result.conflicts + adapter.candidate_rejections)
    kept = [op for op in result.change.operations if op.category in allowed]
    filtered = apply_issue_operations(
        previous, [IssueOperation.model_validate(op.model_dump()) for op in kept], new_messages,
        current_focus=result.change.current_focus, conflicts=result.conflicts + [
            f"补充复核拒绝非目标类别 {op.category}" for op in invalid
        ],
    )
    return replace(filtered, raw_response=result.raw_response,
                   candidates=(adapter.raw_model_response or {}).get("candidates", []),
                   raw_model_response=adapter.raw_model_response,
                   normalized_response=adapter.normalized_response,
                   schema_results=result.schema_results,
                   conflicts=result.conflicts + adapter.candidate_rejections)
