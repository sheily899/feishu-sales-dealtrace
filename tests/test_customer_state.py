from gtmsi.customer_state import generate_customer_state
from gtmsi.models import CustomerState, StateItem, StateTodo


class FakeLLM:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def complete_json(self, system, cached_blocks, user_text, max_tokens=None):
        self.calls += 1
        return self.response


NEW_MESSAGES = [
    {"messageId": "m-2", "role": "sales", "text": "案例已经发给您了，您可以先看看。"},
    {"messageId": "m-3", "role": "customer", "text": "不过老板比较关心预算，最好能先给一个大概范围。"},
]


def test_state_generation_accepts_evidence_backed_new_concern_and_todo_completion():
    previous = CustomerState(
        stage="方案评估",
        todos=[StateTodo(title="提供客户案例", status="pending")],
    )
    llm = FakeLLM({
        "state": {
            "stage": "方案评估",
            "unresolved_concerns": [{"title": "预算范围", "evidence": [{"speaker": "客户", "text": "老板比较关心预算"}]}],
            "todos": [{"title": "提供客户案例", "status": "completed"}],
        },
        "change": {
            "added": [{"category": "concern", "title": "预算范围", "evidence": [{"speaker": "客户", "text": "老板比较关心预算"}]}],
            "status_transitions": [{"category": "todo", "title": "提供客户案例", "from_status": "pending", "to_status": "completed", "evidence": [{"speaker": "销售", "text": "案例已经发给您了"}]}],
            "current_focus": "提供初步报价",
        },
    })

    result = generate_customer_state(previous, NEW_MESSAGES, llm)

    assert result.state.todos[0].status == "completed"
    assert [item.title for item in result.state.unresolved_concerns] == ["预算范围"]
    assert result.rejected_changes == []


def test_state_generation_rejects_todo_completion_without_new_message_evidence():
    previous = CustomerState(todos=[StateTodo(title="提供客户案例", status="pending")])
    llm = FakeLLM({
        "state": {"todos": [{"title": "提供客户案例", "status": "completed"}]},
        "change": {
            "status_transitions": [{"category": "todo", "title": "提供客户案例", "from_status": "pending", "to_status": "completed", "evidence": [{"speaker": "销售", "text": "案例已发送"}]}],
        },
    })

    result = generate_customer_state(previous, NEW_MESSAGES, llm)

    assert result.state.todos[0].status == "pending"
    assert result.change.status_transitions == []
    assert "提供客户案例" in result.rejected_changes[0]


def test_state_generation_rejects_unresolved_concern_removal_without_evidence():
    previous = CustomerState(unresolved_concerns=[StateItem(title="CRM 接入复杂度")])
    llm = FakeLLM({
        "state": {"unresolved_concerns": []},
        "change": {"resolved": [{"category": "concern", "title": "CRM 接入复杂度", "evidence": []}]},
    })

    result = generate_customer_state(previous, NEW_MESSAGES, llm)

    assert [item.title for item in result.state.unresolved_concerns] == ["CRM 接入复杂度"]
    assert result.change.resolved == []
    assert "CRM 接入复杂度" in result.rejected_changes[0]
