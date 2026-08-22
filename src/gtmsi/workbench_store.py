"""Local SQLite persistence for the Feishu sales-analysis workbench."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Mapping


class SQLiteWorkbenchStore:
    """Persist raw group events and the newest analysis report per group.

    The store is deliberately local-only for the MVP. Queries are parameterized
    because event text and sender identifiers originate outside the application.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS group_events (
                    message_id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    sender_name TEXT NOT NULL,
                    sent_at TEXT NOT NULL,
                    text TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS group_events_chat_sent
                    ON group_events(chat_id, sent_at, message_id);
                CREATE TABLE IF NOT EXISTS group_reports (
                    chat_id TEXT PRIMARY KEY,
                    report_json TEXT NOT NULL,
                    evidence_map_json TEXT NOT NULL
                );
                """
            )

    def _connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=5)

    def save_event(self, event: Mapping[str, str]) -> bool:
        required = ("message_id", "chat_id", "sender_id", "sender_name", "timestamp", "text")
        if any(not isinstance(event.get(key), str) or not event[key].strip() for key in required):
            raise ValueError("group event is missing a required text field")
        if len(event["text"]) > 10_000:
            raise ValueError("group event text exceeds the 10,000 character limit")
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO group_events
                    (message_id, chat_id, sender_id, sender_name, sent_at, text)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event["message_id"], event["chat_id"], event["sender_id"], event["sender_name"],
                 event["timestamp"], event["text"]),
            )
        return cursor.rowcount == 1

    def load_events(self, chat_id: str) -> list[dict[str, str]]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT message_id, chat_id, sender_id, sender_name, sent_at, text
                FROM group_events WHERE chat_id = ? ORDER BY sent_at, message_id
                """,
                (chat_id,),
            ).fetchall()
        return [
            {"message_id": row[0], "chat_id": row[1], "sender_id": row[2], "sender_name": row[3],
             "timestamp": row[4], "text": row[5]}
            for row in rows
        ]

    def save_report(self, chat_id: str, report: Mapping, evidence_map: Mapping[str, list[str]]) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO group_reports (chat_id, report_json, evidence_map_json) VALUES (?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    report_json = excluded.report_json,
                    evidence_map_json = excluded.evidence_map_json
                """,
                (chat_id, json.dumps(report, ensure_ascii=False), json.dumps(evidence_map, ensure_ascii=False)),
            )

    def load_report(self, chat_id: str) -> tuple[dict, dict[str, list[str]]] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT report_json, evidence_map_json FROM group_reports WHERE chat_id = ?", (chat_id,)
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0]), json.loads(row[1])
