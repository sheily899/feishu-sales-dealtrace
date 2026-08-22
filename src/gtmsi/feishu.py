"""Feishu event parsing at the boundary of the sales-chat adapter.

The parser is SDK-independent so recorded events can be unit tested without
network access or Feishu credentials.
"""
from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class FeishuConfig:
    """Non-secret runtime configuration for the local Feishu group listener."""

    app_id: str
    app_secret: str
    role_map: dict[str, str]
    group_allowlist: list[str]

    @classmethod
    def from_env(cls, environment: Mapping[str, str] | None = None) -> "FeishuConfig":
        values = environment if environment is not None else os.environ
        app_id = values.get("FEISHU_APP_ID", "").strip()
        app_secret = values.get("FEISHU_APP_SECRET", "").strip()
        if not app_id:
            raise ValueError("FEISHU_APP_ID is required when starting Feishu mode")
        if not app_secret:
            raise ValueError("FEISHU_APP_SECRET is required when starting Feishu mode")
        try:
            role_map = json.loads(values.get("FEISHU_ROLE_MAP", "{}"))
        except json.JSONDecodeError as error:
            raise ValueError("FEISHU_ROLE_MAP must be a JSON object") from error
        if not isinstance(role_map, dict) or any(role not in {"customer", "sales"} for role in role_map.values()):
            raise ValueError("FEISHU_ROLE_MAP values must be customer or sales")
        if any(not isinstance(sender_id, str) for sender_id in role_map):
            raise ValueError("FEISHU_ROLE_MAP keys must be sender open IDs")
        groups = [chat_id.strip() for chat_id in values.get("FEISHU_GROUP_ALLOWLIST", "").split(",") if chat_id.strip()]
        return cls(app_id=app_id, app_secret=app_secret, role_map=role_map, group_allowlist=groups)


def parse_message_event(payload: Mapping[str, Any]) -> dict[str, str] | None:
    """Return a raw text message from an ``im.message.receive_v1`` group event.

    Non-group and non-text messages are intentionally ignored in the MVP. The
    raw result matches ``workbench.normalize_events``' input contract.
    """
    if payload.get("header", {}).get("event_type") != "im.message.receive_v1":
        return None
    event = payload.get("event", {})
    message = event.get("message", {})
    if message.get("chat_type") != "group" or message.get("message_type") != "text":
        return None
    sender_id = event.get("sender", {}).get("sender_id", {}).get("open_id")
    message_id, chat_id = message.get("message_id"), message.get("chat_id")
    if not all(isinstance(value, str) and value for value in (sender_id, message_id, chat_id)):
        return None
    try:
        text = json.loads(message.get("content", "{}"))["text"].strip()
        created_ms = int(message.get("create_time") or payload.get("header", {}).get("create_time"))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if not text:
        return None
    timestamp = datetime.fromtimestamp(created_ms / 1000, UTC).isoformat()
    return {
        "message_id": message_id,
        "chat_id": chat_id,
        "sender_id": sender_id,
        "sender_name": sender_id,
        "timestamp": timestamp,
        "text": text,
    }
