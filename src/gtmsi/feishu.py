"""Feishu event parsing at the boundary of the sales-chat adapter.

The parser is SDK-independent so recorded events can be unit tested without
network access or Feishu credentials.
"""
from __future__ import annotations

from datetime import UTC, datetime
import json
from typing import Any, Mapping


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
