import pytest

from dealtrace.feishu import FeishuConfig, inbound_message_to_raw, parse_message_event


def test_parse_message_event_converts_group_text_to_raw_message():
    payload = {
        "header": {"event_type": "im.message.receive_v1", "create_time": "1787543700000"},
        "event": {
            "sender": {"sender_type": "user", "sender_id": {"open_id": "ou-customer"}},
            "message": {
                "message_id": "om_001",
                "chat_id": "oc_demo",
                "chat_type": "group",
                "message_type": "text",
                "create_time": "1787543700000",
                "content": '{"text":"CRM 对接会不会很麻烦？"}',
            },
        },
    }

    assert parse_message_event(payload) == {
        "message_id": "om_001",
        "chat_id": "oc_demo",
        "sender_id": "ou-customer",
        "sender_name": "ou-customer",
        "timestamp": "2026-08-24T03:55:00+00:00",
        "text": "CRM 对接会不会很麻烦？",
    }


def test_parse_message_event_ignores_non_group_and_non_text_events():
    payload = {
        "header": {"event_type": "im.message.receive_v1"},
        "event": {
            "sender": {"sender_id": {"open_id": "ou-customer"}},
            "message": {"chat_type": "p2p", "message_type": "image", "content": "{}"},
        },
    }

    assert parse_message_event(payload) is None


def test_feishu_config_reads_role_and_group_allowlists_from_environment():
    config = FeishuConfig.from_env({
        "FEISHU_APP_ID": "cli_demo",
        "FEISHU_APP_SECRET": "not-a-real-secret",
        "FEISHU_ROLE_MAP": '{"ou-customer":"customer","ou-sales":"sales"}',
        "FEISHU_GROUP_ALLOWLIST": "oc_demo,oc_backup",
    })

    assert config.role_map == {"ou-customer": "customer", "ou-sales": "sales"}
    assert config.group_allowlist == ["oc_demo", "oc_backup"]


def test_feishu_config_deduplicates_groups_and_requires_at_least_one_group():
    environment = {
        "FEISHU_APP_ID": "cli_demo",
        "FEISHU_APP_SECRET": "not-a-real-secret",
        "FEISHU_ROLE_MAP": '{"ou-customer":"customer"}',
    }

    assert FeishuConfig.from_env({
        **environment,
        "FEISHU_GROUP_ALLOWLIST": "oc_demo, oc_backup,oc_demo, ,oc_backup",
    }).group_allowlist == ["oc_demo", "oc_backup"]
    with pytest.raises(ValueError, match="FEISHU_GROUP_ALLOWLIST"):
        FeishuConfig.from_env(environment)


def test_feishu_config_requires_app_credentials_and_valid_roles():
    with pytest.raises(ValueError, match="FEISHU_APP_ID"):
        FeishuConfig.from_env({})
    with pytest.raises(ValueError, match="customer or sales"):
        FeishuConfig.from_env({
            "FEISHU_APP_ID": "cli_demo",
            "FEISHU_APP_SECRET": "not-a-real-secret",
            "FEISHU_ROLE_MAP": '{"ou-demo":"bot"}',
        })


class _InboundMessage:
    chat_type = "group"
    message_id = "om_live_001"
    chat_id = "oc_live"
    sender_id = "ou-sales"
    sender_name = "语安"
    sender_is_bot = False
    content_text = "可以安排技术同事确认接口。"
    create_time = 1787543700000


def test_inbound_message_to_raw_converts_sdk_message_without_sdk_network_access():
    assert inbound_message_to_raw(_InboundMessage()) == {
        "message_id": "om_live_001",
        "chat_id": "oc_live",
        "sender_id": "ou-sales",
        "sender_name": "语安",
        "timestamp": "2026-08-24T03:55:00+00:00",
        "text": "可以安排技术同事确认接口。",
    }


def test_inbound_message_to_raw_filters_bot_and_non_group_messages():
    message = _InboundMessage()
    message.sender_is_bot = True
    assert inbound_message_to_raw(message) is None
    message.sender_is_bot = False
    message.chat_type = "p2p"
    assert inbound_message_to_raw(message) is None
