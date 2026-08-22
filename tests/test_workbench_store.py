from gtmsi.workbench_store import SQLiteWorkbenchStore


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
