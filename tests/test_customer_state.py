import pytest

from dealtrace.customer_state import _SYSTEM, generate_customer_state
from dealtrace.models import CustomerIssue, CustomerState


class FakeLLM:
    def __init__(self, response):
        self.response = response

    def complete_json(self, system, cached_blocks, user_text, max_tokens=None):
        return self.response


def _message(text, role="customer", message_id="m-1"):
    return {"messageId": message_id, "role": role, "text": text}


def test_prompt_uses_operations_as_single_mutation_source():
    assert "Never return a complete\nstate snapshot" in _SYSTEM
    assert "create|update|resolve|reopen" in _SYSTEM
    assert "copy the exact issue_id" in _SYSTEM
    assert "pending approval is a concern, not a next_step" in _SYSTEM
    assert "only relay, consider, discuss, or seek approval" in _SYSTEM
    assert "resolved within the same NEW_MESSAGES" in _SYSTEM


def test_explicit_sales_future_action_can_create_todo():
    text = "我明天会发送技术文档。"
    result = generate_customer_state(
        None,
        [_message(text, role="sales")],
        FakeLLM(
            {
                "operations": [
                    {
                        "operation": "create",
                        "category": "todo",
                        "business_object": "technical_document",
                        "title": "发送技术文档",
                        "evidence": [{"speaker": "销售", "text": text}],
                    }
                ]
            }
        ),
    )

    assert result.state.todos[0].status == "pending"
    assert result.change.operations[0].operation == "create"


def test_non_core_current_focus_shape_is_downgraded_without_aborting_round():
    result = generate_customer_state(
        None,
        [_message("销售明天发送方案。", role="sales", message_id="tolerant-focus")],
        FakeLLM({
            "operations": [{
                "operation": "create", "category": "todo", "business_object": "proposal",
                "title": "发送方案", "detail": {"bad": "shape"},
                "executor": "销售", "action": "发送方案", "temporal_status": "future",
                "source_type": "sales_commitment",
                "evidence": [{"speaker": "销售", "text": "销售明天发送方案。"}],
            }],
            "current_focus": {"bad": "shape"},
        }),
    )
    assert result.state.todos
    assert result.change.current_focus is None
    assert any("current_focus" in item for item in result.conflicts)


def test_invalid_core_operation_is_rejected_while_valid_operation_survives():
    result = generate_customer_state(
        None,
        [_message("销售明天发送方案。", role="sales", message_id="tolerant-core")],
        FakeLLM({
            "operations": [
                {"operation": "create", "category": "not_a_category", "business_object": "bad",
                 "title": "无效事项", "evidence": []},
                {"operation": "create", "category": "todo", "business_object": "proposal",
                 "title": "发送方案", "executor": "销售", "action": "发送方案",
                 "temporal_status": "future", "source_type": "sales_commitment",
                 "evidence": [{"speaker": "销售", "text": "销售明天发送方案。"}]},
            ],
            "current_focus": None,
        }),
    )
    assert len(result.state.todos) == 1
    assert any("operations[0]" in item for item in result.conflicts)


def test_ai_recommendation_cannot_enter_todo():
    text = "具体需求我还没想太清楚。"
    result = generate_customer_state(
        None,
        [_message(text)],
        FakeLLM(
            {
                "operations": [
                    {
                        "operation": "create",
                        "category": "todo",
                        "business_object": "discovery_followup",
                        "title": "进一步探索客户需求",
                        "evidence": [{"speaker": "客户", "text": text}],
                    }
                ]
            }
        ),
    )

    assert result.state.todos == []
    assert any("未来行动承诺" in reason for reason in result.rejected_changes)


def test_question_or_recommendation_cannot_enter_next_step():
    text = "您这边大概什么时候能有结果？"
    result = generate_customer_state(
        None,
        [_message(text, role="sales")],
        FakeLLM(
            {
                "operations": [
                    {
                        "operation": "create",
                        "category": "next_step",
                        "business_object": "结果跟进",
                        "title": "跟进结果",
                        "evidence": [{"speaker": "销售", "text": text}],
                    }
                ]
            }
        ),
    )

    assert result.state.scheduled_next_steps == []
    assert any("未来行动承诺" in reason for reason in result.rejected_changes)


def test_already_delivered_fact_cannot_enter_future_commitment():
    text = "报价已经发给您了。"
    result = generate_customer_state(
        None,
        [_message(text, role="sales")],
        FakeLLM(
            {
                "operations": [
                    {
                        "operation": "create",
                        "category": "commitment",
                        "business_object": "delivered_fact",
                        "title": "销售已发送报价",
                        "evidence": [{"speaker": "销售", "text": text}],
                    }
                ]
            }
        ),
    )

    assert result.state.commitments == []


def test_no_operation_preserves_historical_issue():
    previous = CustomerState(
        issues=[
            CustomerIssue(
                issue_id="issue-1",
                category="concern",
                business_object="technical_integration",
                status="open",
                title="接口兼容性",
                created_message_id="old",
                updated_message_id="old",
            )
        ]
    )
    result = generate_customer_state(
        previous,
        [_message("今天讨论合同寄送地址。")],
        FakeLLM({"operations": []}),
    )

    assert result.state.issues[0].status == "open"
    assert result.state.unresolved_concerns[0].issue_id == "issue-1"


def test_transition_requires_real_old_stage_and_evidence():
    text = "我们可以进入技术评估。"
    transition = {
        "category": "opportunity",
        "title": "商机阶段",
        "from_status": "需求确认",
        "to_status": "技术评估",
        "evidence": [{"speaker": "客户", "text": text}],
    }
    accepted = generate_customer_state(
        CustomerState(stage="需求确认"),
        [_message(text)],
        FakeLLM({"operations": [], "status_transitions": [transition]}),
    )
    rejected = generate_customer_state(
        CustomerState(stage="unknown"),
        [_message(text)],
        FakeLLM({"operations": [], "status_transitions": [transition]}),
    )

    assert accepted.state.stage == "技术评估"
    assert len(accepted.change.status_transitions) == 1
    assert rejected.state.stage == "unknown"
    assert rejected.change.status_transitions == []


@pytest.mark.parametrize(
    ("response", "message"),
    [
        ({}, "missing required 'operations' array"),
        ({"operations": {}}, "'operations' must be a JSON array"),
        ("[]", "must be a JSON object"),
    ],
)
def test_invalid_top_level_response_is_not_silent_noop(response, message):
    with pytest.raises(ValueError, match=message):
        generate_customer_state(None, [_message("测试")], FakeLLM(response))


def test_legacy_change_only_addition_is_supported_but_state_is_ignored():
    text = "客户明确需要导出审计日志。"
    result = generate_customer_state(
        None,
        [_message(text)],
        FakeLLM(
            {
                "state": {"needs": []},
                "change": {
                    "added": [
                        {
                            "category": "need",
                            "title": "导出审计日志",
                            "evidence": [{"speaker": "客户", "text": text}],
                        }
                    ]
                },
            }
        ),
    )

    assert [item.title for item in result.state.needs] == ["导出审计日志"]
    assert any("legacy adapter" in conflict for conflict in result.conflicts)


def test_legacy_ambiguous_title_resolution_is_rejected():
    previous = CustomerState(
        issues=[
            CustomerIssue(
                issue_id=f"issue-{index}",
                category="concern",
                business_object=f"object-{index}",
                status="open",
                title="待确认事项",
                created_message_id=f"old-{index}",
                updated_message_id=f"old-{index}",
            )
            for index in range(2)
        ]
    )
    result = generate_customer_state(
        previous,
        [_message("该事项已经确认。")],
        FakeLLM(
            {
                "state": {},
                "change": {
                    "resolved": [
                        {
                            "category": "concern",
                            "title": "待确认事项",
                            "evidence": [{"speaker": "客户", "text": "该事项已经确认。"}],
                        }
                    ]
                },
            }
        ),
    )

    assert all(issue.status == "open" for issue in result.state.issues)
    assert any("不存在可关联" in reason for reason in result.rejected_changes)


def test_empty_operations_retry_uses_seed_plus_one():
    class SeedLLM:
        seed = 42

        def __init__(self):
            self.calls = []

        def complete_json(self, **kwargs):
            self.calls.append(self.seed)
            if len(self.calls) == 1:
                return {"operations": []}
            return {"operations": [{
                "operation": "create", "category": "need", "business_object": "需求",
                "title": "明确需求", "evidence": [
                    {"speaker": "customer", "text": "客户需要明确需求"}
                ],
            }]}

    llm = SeedLLM()
    result = generate_customer_state(
        None, [_message("客户需要明确需求", message_id="retry-1")], llm
    )
    assert llm.calls == [42, 43]
    assert result.state.issues[0].category == "need"
    assert llm.seed == 42
