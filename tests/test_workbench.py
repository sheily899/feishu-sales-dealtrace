import json
import pytest
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

from gtmsi.workbench import (
    _PAGE,
    build_evidence_map,
    build_standard_transcript,
    create_workbench_server,
    display_call_type,
    LiveWorkbench,
    MultiChatWorkbench,
    normalize_events,
)
from gtmsi.feishu import FeishuConfig
from gtmsi.workbench_store import SQLiteWorkbenchStore
from gtmsi.models import CustomerState, StateChange, StateTodo


ROLE_MAP = {"customer-1": "customer", "sales-1": "sales", "bot-1": "bot"}


def test_normalize_events_deduplicates_sorts_and_filters_bot_messages():
    events = [
        {"message_id": "m2", "chat_id": "chat-1", "sender_id": "sales-1", "sender_name": "销售", "timestamp": "2026-08-22T10:03:00+08:00", "text": "可以安排技术确认接口。"},
        {"message_id": "m1", "chat_id": "chat-1", "sender_id": "customer-1", "sender_name": "客户", "timestamp": "2026-08-22T10:01:00+08:00", "text": "CRM 对接会不会很麻烦？"},
        {"message_id": "m3", "chat_id": "chat-1", "sender_id": "bot-1", "sender_name": "机器人", "timestamp": "2026-08-22T10:04:00+08:00", "text": "分析已更新。"},
        {"message_id": "m2", "chat_id": "chat-1", "sender_id": "sales-1", "sender_name": "销售", "timestamp": "2026-08-22T10:03:00+08:00", "text": "重复事件。"},
    ]

    messages = normalize_events(events, ROLE_MAP)

    assert [message["messageId"] for message in messages] == ["m1", "m2"]
    assert [message["role"] for message in messages] == ["customer", "sales"]
    assert [message["senderName"] for message in messages] == ["客户", "销售"]


def test_normalize_events_displays_all_timestamps_in_beijing_time():
    messages = normalize_events([
        {"message_id": "m1", "chat_id": "chat-1", "sender_id": "customer-1", "sender_name": "客户",
         "timestamp": "2026-08-22T02:01:00+00:00", "text": "测试"},
    ], ROLE_MAP)

    assert messages[0]["sentAt"] == "2026-08-22T10:01:00+08:00"


def test_workbench_page_polls_for_new_group_messages():
    assert "setInterval(load, 3000)" in _PAGE


def test_build_standard_transcript_retains_message_evidence_ids():
    messages = [
        {"messageId": "m1", "role": "customer", "text": "CRM 对接会不会很麻烦？", "sentAt": "2026-08-22T10:01:00+08:00"},
        {"messageId": "m2", "role": "sales", "text": "可以安排技术确认接口。", "sentAt": "2026-08-22T10:03:00+08:00"},
    ]

    transcript, segments = build_standard_transcript(messages)

    assert transcript == "客户：CRM 对接会不会很麻烦？\n\n销售：可以安排技术确认接口。"
    assert segments == [
        {"segmentId": "seg_m1", "messageId": "m1"},
        {"segmentId": "seg_m2", "messageId": "m2"},
    ]


def test_build_evidence_map_links_quotes_to_normalized_chat_messages():
    messages = [
        {"messageId": "m1", "role": "customer", "text": "CRM 对接会不会很麻烦？"},
        {"messageId": "m2", "role": "sales", "text": "可以安排技术同事确认接口。"},
    ]
    report = {
        "group_chat": {
            "customer_concerns": [
                {"evidence": [{"speaker": "客户", "text": "CRM 对接会不会很麻烦？"}]}
            ]
        },
        "coaching": {"strengths": [{"evidence": [{"speaker": "销售", "text": "安排技术同事确认"}]}]},
    }

    evidence_map = build_evidence_map(report, messages)

    assert evidence_map["客户\nCRM 对接会不会很麻烦？"] == ["m1"]
    assert evidence_map["销售\n安排技术同事确认"] == ["m2"]


def test_display_call_type_uses_business_friendly_chinese_label():
    assert display_call_type("discovery") == "需求探索（Discovery）"
    assert display_call_type("unknown-stage") == "unknown-stage"


def test_live_workbench_uses_the_same_normalizer_for_feishu_messages():
    workbench = LiveWorkbench({"ou-customer": "customer", "ou-sales": "sales"})

    workbench.ingest({
        "message_id": "om-2", "chat_id": "oc-live", "sender_id": "ou-sales",
        "sender_name": "语安", "timestamp": "2026-08-22T10:03:00+08:00", "text": "我下周一前发案例。",
    })
    workbench.ingest({
        "message_id": "om-1", "chat_id": "oc-live", "sender_id": "ou-customer",
        "sender_name": "amily", "timestamp": "2026-08-22T10:01:00+08:00", "text": "能否对接现有 CRM？",
    })
    workbench.ingest({
        "message_id": "om-bot", "chat_id": "oc-live", "sender_id": "ou-bot",
        "sender_name": "机器人", "timestamp": "2026-08-22T10:04:00+08:00", "text": "分析已更新。",
    })

    snapshot = workbench.snapshot()

    assert snapshot["sourceLabel"] == "飞书测试群同步"
    assert [message["messageId"] for message in snapshot["messages"]] == ["om-1", "om-2"]
    assert [message["senderName"] for message in snapshot["messages"]] == ["客户", "销售"]
    assert workbench.transcript == "客户：能否对接现有 CRM？\n\n销售：我下周一前发案例。"


def test_live_workbench_restores_group_messages_and_latest_report_after_restart(tmp_path):
    store = SQLiteWorkbenchStore(tmp_path / "workbench.sqlite3")
    workbench = LiveWorkbench({"ou-customer": "customer", "ou-sales": "sales"}, store=store)
    workbench.ingest({
        "message_id": "om-1", "chat_id": "oc-live", "sender_id": "ou-customer",
        "sender_name": "amily", "timestamp": "2026-08-22T10:01:00+08:00", "text": "能否对接现有 CRM？",
    })
    store.save_report("oc-live", {"classification": {"call_type": "discovery"}, "summary": "已保存报告"}, {})

    restarted = LiveWorkbench({"ou-customer": "customer", "ou-sales": "sales"}, store=store, chat_id="oc-live")

    assert restarted.snapshot()["messages"][0]["text"] == "能否对接现有 CRM？"
    assert restarted.snapshot()["analysis"]["summary"] == "已保存报告"

    restarted.ingest({
        "message_id": "om-2", "chat_id": "oc-live", "sender_id": "ou-sales",
        "sender_name": "语安", "timestamp": "2026-08-22T10:03:00+08:00", "text": "我安排技术确认。",
    })

    assert restarted.snapshot()["analysis"] is None


class _Report:
    def model_dump(self):
        return {"classification": {"call_type": "discovery"}, "summary": "分析完成"}


class _StateLLM:
    def __init__(self):
        self.calls = 0

    def complete_json(self, system, cached_blocks, user_text, max_tokens=None):
        self.calls += 1
        return {
            "state": {"stage": "需求探索", "todos": [{"title": "发送客户案例", "status": "pending"}]},
            "change": {"added": [{"category": "todo", "title": "发送客户案例", "evidence": [{"speaker": "销售", "text": "下周一前发给您"}]}]},
        }


def test_live_workbench_skips_all_model_calls_when_state_has_no_new_messages(tmp_path):
    store = SQLiteWorkbenchStore(tmp_path / "workbench.sqlite3")
    event = {"message_id": "m-1", "chat_id": "oc-live", "sender_id": "ou-sales", "sender_name": "语安",
             "timestamp": "2026-08-22T10:01:00+08:00", "text": "我下周一前发给您。"}
    store.save_event(event)
    store.save_state_version("oc-live", CustomerState(), StateChange(), ["m-1"])
    store.save_report("oc-live", {"classification": {"call_type": "discovery"}, "summary": "历史报告"}, {})

    def unexpected_coach(_):
        raise AssertionError("没有新增消息时不得调用销售分析模型")

    state_llm = _StateLLM()
    workbench = LiveWorkbench({"ou-sales": "sales"}, store=store, chat_id="oc-live",
                              coach_runner=unexpected_coach, state_llm=state_llm)

    snapshot = workbench.analyze()

    assert snapshot["noNewMessages"] is True
    assert snapshot["customerState"]["version"] == 1
    assert snapshot["analysis"]["summary"] == "历史报告"
    assert state_llm.calls == 0


def test_live_workbench_saves_a_new_state_version_only_when_new_messages_arrive(tmp_path):
    store = SQLiteWorkbenchStore(tmp_path / "workbench.sqlite3")
    workbench = LiveWorkbench({"ou-sales": "sales"}, store=store, coach_runner=lambda _: _Report(), state_llm=_StateLLM())
    workbench.ingest({"message_id": "m-1", "chat_id": "oc-live", "sender_id": "ou-sales", "sender_name": "语安",
                      "timestamp": "2026-08-22T10:01:00+08:00", "text": "我下周一前发给您。"})

    first = workbench.analyze()
    second = workbench.analyze()

    assert first["customerState"]["version"] == 1
    assert second["noNewMessages"] is True
    assert [state.version for state in store.list_state_versions("oc-live")] == [1]


def test_multi_chat_workbench_keeps_messages_reports_and_state_versions_isolated(tmp_path):
    store = SQLiteWorkbenchStore(tmp_path / "workbench.sqlite3")
    workbench = MultiChatWorkbench(
        {"ou-sales": "sales"}, ["oc-a", "oc-b"], store=store,
        coach_runner=lambda _: _Report(), state_llm=_StateLLM(),
    )
    workbench.ingest({
        "message_id": "m-a", "chat_id": "oc-a", "sender_id": "ou-sales", "sender_name": "语安",
        "timestamp": "2026-08-22T10:01:00+08:00", "text": "我下周一前发给您。",
    })
    workbench.ingest({
        "message_id": "m-b", "chat_id": "oc-b", "sender_id": "ou-sales", "sender_name": "语安",
        "timestamp": "2026-08-22T10:02:00+08:00", "text": "我下周一前发给您。",
    })

    first = workbench.analyze("oc-a")
    second = workbench.snapshot("oc-b")

    assert [message["messageId"] for message in first["messages"]] == ["m-a"]
    assert first["customerState"]["version"] == 1
    assert [message["messageId"] for message in second["messages"]] == ["m-b"]
    assert second["analysis"] is None
    assert second["customerState"] is None
    assert store.list_state_versions("oc-b") == []


def test_multi_chat_workbench_rejects_a_group_outside_the_allowlist(tmp_path):
    workbench = MultiChatWorkbench({"ou-sales": "sales"}, ["oc-a"], store=SQLiteWorkbenchStore(tmp_path / "workbench.sqlite3"))

    with pytest.raises(KeyError, match="未配置"):
        workbench.snapshot("oc-other")


def test_workbench_http_api_reads_only_the_requested_configured_group(tmp_path):
    store = SQLiteWorkbenchStore(tmp_path / "workbench.sqlite3")
    for chat_id, message_id, text in [("oc-a", "m-a", "客户 A"), ("oc-b", "m-b", "客户 B")]:
        store.save_event({
            "message_id": message_id, "chat_id": chat_id, "sender_id": "ou-sales", "sender_name": "语安",
            "timestamp": "2026-08-22T10:01:00+08:00", "text": text,
        })
    config = FeishuConfig("cli_demo", "not-a-real-secret", {"ou-sales": "sales"}, ["oc-a", "oc-b"])
    server = create_workbench_server("127.0.0.1", 0, config, store=store, start_listener=False)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(f"{base_url}/api/workbench?chatId=oc-b") as response:
            selected = json.load(response)
        with urlopen(f"{base_url}/api/workbench") as response:
            default = json.load(response)
        with urlopen(f"{base_url}/api/chats") as response:
            chats = json.load(response)
        with pytest.raises(HTTPError) as error:
            urlopen(f"{base_url}/api/workbench?chatId=oc-other")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()

    assert [message["messageId"] for message in selected["messages"]] == ["m-b"]
    assert [message["messageId"] for message in default["messages"]] == ["m-a"]
    assert [chat["chatId"] for chat in chats["chats"]] == ["oc-a", "oc-b"]
    assert error.value.code == 404


def test_workbench_page_includes_customer_state_and_change_timeline():
    from gtmsi.workbench import _PAGE

    assert 'id="customer-state"' in _PAGE
    assert "当前客户状态" in _PAGE
    assert "本次变化" in _PAGE
    assert "版本时间线" in _PAGE
    assert "暂无新消息" in _PAGE
