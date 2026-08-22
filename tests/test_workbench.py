from gtmsi.workbench import (
    _PAGE,
    build_evidence_map,
    build_standard_transcript,
    display_call_type,
    LiveWorkbench,
    normalize_events,
)
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


def test_workbench_server_exposes_configured_chat_summaries_endpoint():
    import inspect

    assert 'path == "/api/chats"' in inspect.getsource(__import__("gtmsi.workbench", fromlist=["run_workbench"]).run_workbench)


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


def test_workbench_page_includes_customer_state_and_change_timeline():
    from gtmsi.workbench import _PAGE

    assert 'id="customer-state"' in _PAGE
    assert "当前客户状态" in _PAGE
    assert "本次变化" in _PAGE
    assert "版本时间线" in _PAGE
    assert "暂无新消息" in _PAGE
