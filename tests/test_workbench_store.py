from gtmsi.workbench_store import SQLiteWorkbenchStore
from gtmsi.models import CustomerState, StateChange, StateChangeItem, StateItem, StateTodo


def test_store_keeps_messages_scoped_to_each_group_and_deduplicated(tmp_path):
    store = SQLiteWorkbenchStore(tmp_path / "workbench.sqlite3")
    first = {
        "message_id": "om-1", "chat_id": "oc-a", "sender_id": "ou-customer",
        "sender_name": "ou-customer", "timestamp": "2026-08-22T10:01:00+08:00", "text": "需要 CRM 对接。",
    }

    assert store.save_event(first) is True
    assert store.save_event(first) is False
    assert store.save_event({**first, "message_id": "om-2", "chat_id": "oc-b", "text": "另一客户群消息。"}) is True

    assert store.load_events("oc-a") == [first]
    assert [event["message_id"] for event in store.load_events("oc-b")] == ["om-2"]


def test_store_replaces_only_the_latest_report_for_a_group(tmp_path):
    store = SQLiteWorkbenchStore(tmp_path / "workbench.sqlite3")

    store.save_report("oc-a", {"summary": "第一版"}, {"客户\\n需要 CRM": ["om-1"]})
    store.save_report("oc-a", {"summary": "第二版"}, {"销售\\n安排评估": ["om-2"]})

    assert store.load_report("oc-a") == ({"summary": "第二版"}, {"销售\\n安排评估": ["om-2"]})
    assert store.load_report("oc-b") is None


def test_store_appends_customer_state_versions_without_overwriting_history(tmp_path):
    store = SQLiteWorkbenchStore(tmp_path / "workbench.sqlite3")
    first = CustomerState(
        stage="需求探索",
        needs=[StateItem(title="对接现有 CRM")],
        todos=[StateTodo(title="发送客户案例", status="pending")],
    )
    second = CustomerState(
        stage="方案评估",
        needs=[StateItem(title="对接现有 CRM")],
        todos=[StateTodo(title="发送客户案例", status="completed")],
    )

    saved_first = store.save_state_version("oc-a", first, StateChange(), ["m-1"])
    saved_second = store.save_state_version("oc-a", second, StateChange(), ["m-2"])

    assert saved_first.version == 1
    assert saved_second.version == 2
    assert store.load_latest_state("oc-a").version == 2
    assert store.load_state_version("oc-a", 1).todos[0].status == "pending"
    assert [state.version for state in store.list_state_versions("oc-a")] == [1, 2]
    assert store.load_latest_state("oc-b") is None


def test_store_keeps_state_change_and_analyzed_message_boundary_per_version(tmp_path):
    store = SQLiteWorkbenchStore(tmp_path / "workbench.sqlite3")
    change = StateChange(added=[StateChangeItem(category="concern", title="预算范围")], current_focus="补充初步报价")

    saved = store.save_state_version("oc-a", CustomerState(), change, ["m-3", "m-4"])

    assert store.load_state_change("oc-a", saved.version) == change
    assert store.load_analyzed_message_ids("oc-a", saved.version) == ["m-3", "m-4"]


def test_store_returns_lightweight_summaries_scoped_to_requested_groups(tmp_path):
    store = SQLiteWorkbenchStore(tmp_path / "workbench.sqlite3")
    store.save_event({
        "message_id": "m-a", "chat_id": "oc-a", "sender_id": "ou-customer",
        "sender_name": "客户", "timestamp": "2026-08-22T10:01:00+08:00", "text": "请发案例。",
    })
    store.save_event({
        "message_id": "m-b", "chat_id": "oc-b", "sender_id": "ou-customer",
        "sender_name": "客户", "timestamp": "2026-08-22T11:01:00+08:00", "text": "需要报价。",
    })
    store.save_report("oc-b", {"classification": {"call_type": "discovery"}}, {})
    store.save_state_version("oc-a", CustomerState(
        stage="方案评估", todos=[StateTodo(title="发送案例", status="pending")],
    ), StateChange(), ["m-a"])

    assert store.load_chat_summaries(["oc-b", "oc-a", "oc-empty", "oc-b"]) == [
        {"chatId": "oc-b", "displayName": "oc-b", "latestMessageAt": "2026-08-22T11:01:00+08:00", "stage": "discovery", "todoCount": 0},
        {"chatId": "oc-a", "displayName": "oc-a", "latestMessageAt": "2026-08-22T10:01:00+08:00", "stage": "方案评估", "todoCount": 1},
        {"chatId": "oc-empty", "displayName": "oc-empty", "latestMessageAt": None, "stage": None, "todoCount": 0},
    ]
