"""Local demo workbench for normalized Feishu-style sales chat events."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime


def normalize_events(events: Iterable[Mapping[str, str]], role_map: Mapping[str, str]) -> list[dict[str, str]]:
    """Deduplicate and order text events before creating sales-analysis input."""
    unique: dict[str, dict[str, str]] = {}
    for event in events:
        message_id = event["message_id"]
        if message_id in unique:
            continue
        role = role_map.get(event["sender_id"], "unknown")
        if role not in {"customer", "sales"} or not event.get("text", "").strip():
            continue
        unique[message_id] = {
            "messageId": message_id,
            "chatId": event["chat_id"],
            "senderName": event.get("sender_name", role),
            "role": role,
            "sentAt": event["timestamp"],
            "text": event["text"].strip(),
        }
    return sorted(unique.values(), key=lambda message: (message["sentAt"], message["messageId"]))


def build_standard_transcript(messages: Iterable[Mapping[str, str]]) -> tuple[str, list[dict[str, str]]]:
    """Convert normalized messages to the engine's role-labelled text contract."""
    labels = {"customer": "客户", "sales": "销售"}
    lines: list[str] = []
    segments: list[dict[str, str]] = []
    for message in messages:
        label = labels.get(message["role"])
        if not label:
            continue
        lines.append(f"{label}：{message['text']}")
        segments.append({"segmentId": f"seg_{message['messageId']}", "messageId": message["messageId"]})
    return "\n\n".join(lines), segments
