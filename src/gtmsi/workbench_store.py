"""Local SQLite persistence for the Feishu sales-analysis workbench."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Mapping
from datetime import UTC, datetime

from .models import CustomerState, StateChange


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
                CREATE TABLE IF NOT EXISTS customer_state_snapshots (
                    chat_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    state_json TEXT NOT NULL,
                    analyzed_message_ids_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (chat_id, version)
                );
                CREATE TABLE IF NOT EXISTS customer_state_changes (
                    chat_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    change_json TEXT NOT NULL,
                    PRIMARY KEY (chat_id, version),
                    FOREIGN KEY (chat_id, version)
                        REFERENCES customer_state_snapshots(chat_id, version)
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

    def delete_report(self, chat_id: str) -> None:
        with self._connection() as connection:
            connection.execute("DELETE FROM group_reports WHERE chat_id = ?", (chat_id,))

    def load_chat_summaries(self, chat_ids: list[str]) -> list[dict]:
        """Return one lightweight summary per configured group without loading transcripts."""
        chat_ids = list(dict.fromkeys(chat_id for chat_id in chat_ids if chat_id))
        if not chat_ids:
            return []
        values = ", ".join("(?)" for _ in chat_ids)
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                WITH allowed(chat_id) AS (VALUES {values}),
                latest_events AS (
                    SELECT chat_id, MAX(sent_at) AS latest_message_at
                    FROM group_events WHERE chat_id IN (SELECT chat_id FROM allowed)
                    GROUP BY chat_id
                ), latest_versions AS (
                    SELECT chat_id, MAX(version) AS version
                    FROM customer_state_snapshots
                    WHERE chat_id IN (SELECT chat_id FROM allowed)
                    GROUP BY chat_id
                )
                SELECT allowed.chat_id, latest_events.latest_message_at,
                       group_reports.report_json, customer_state_snapshots.state_json
                FROM allowed
                LEFT JOIN latest_events ON latest_events.chat_id = allowed.chat_id
                LEFT JOIN group_reports ON group_reports.chat_id = allowed.chat_id
                LEFT JOIN latest_versions ON latest_versions.chat_id = allowed.chat_id
                LEFT JOIN customer_state_snapshots
                    ON customer_state_snapshots.chat_id = latest_versions.chat_id
                    AND customer_state_snapshots.version = latest_versions.version
                """,
                chat_ids,
            ).fetchall()
        summaries = {}
        for chat_id, latest_message_at, report_json, state_json in rows:
            state = CustomerState.model_validate_json(state_json) if state_json else None
            report = json.loads(report_json) if report_json else {}
            stage = state.stage if state and state.stage != "unknown" else report.get("classification", {}).get("call_type")
            summaries[chat_id] = {
                "chatId": chat_id,
                "displayName": chat_id,
                "latestMessageAt": latest_message_at,
                "stage": stage,
                "todoCount": sum(todo.status == "pending" for todo in state.todos) if state else 0,
            }
        return [
            {**summaries[chat_id], "displayName": f"客户群 {index}"}
            for index, chat_id in enumerate(chat_ids, start=1)
        ]

    def save_state_version(
        self,
        chat_id: str,
        state: CustomerState,
        change: StateChange,
        analyzed_message_ids: list[str],
    ) -> CustomerState:
        """Append one immutable customer-state version and its matching delta."""
        if not isinstance(chat_id, str) or not chat_id.strip():
            raise ValueError("chat_id is required for a customer state")
        if any(not isinstance(message_id, str) or not message_id.strip() for message_id in analyzed_message_ids):
            raise ValueError("analyzed_message_ids must contain non-empty strings")
        if len(set(analyzed_message_ids)) != len(analyzed_message_ids):
            raise ValueError("analyzed_message_ids must not contain duplicates")
        now = datetime.now(UTC).isoformat()
        with self._connection() as connection:
            next_version = connection.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM customer_state_snapshots WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()[0]
            stored_state = state.model_copy(update={
                "version": next_version,
                "updated_at": now,
                "analyzed_message_ids": list(analyzed_message_ids),
            })
            connection.execute(
                """
                INSERT INTO customer_state_snapshots
                    (chat_id, version, state_json, analyzed_message_ids_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    chat_id,
                    stored_state.version,
                    stored_state.model_dump_json(),
                    json.dumps(analyzed_message_ids, ensure_ascii=False),
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO customer_state_changes (chat_id, version, change_json)
                VALUES (?, ?, ?)
                """,
                (chat_id, stored_state.version, change.model_dump_json()),
            )
        return stored_state

    def load_latest_state(self, chat_id: str) -> CustomerState | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT state_json FROM customer_state_snapshots
                WHERE chat_id = ? ORDER BY version DESC LIMIT 1
                """,
                (chat_id,),
            ).fetchone()
        return CustomerState.model_validate_json(row[0]) if row else None

    def load_state_version(self, chat_id: str, version: int) -> CustomerState | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT state_json FROM customer_state_snapshots WHERE chat_id = ? AND version = ?",
                (chat_id, version),
            ).fetchone()
        return CustomerState.model_validate_json(row[0]) if row else None

    def list_state_versions(self, chat_id: str) -> list[CustomerState]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT state_json FROM customer_state_snapshots WHERE chat_id = ? ORDER BY version ASC",
                (chat_id,),
            ).fetchall()
        return [CustomerState.model_validate_json(row[0]) for row in rows]

    def load_state_change(self, chat_id: str, version: int) -> StateChange | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT change_json FROM customer_state_changes WHERE chat_id = ? AND version = ?",
                (chat_id, version),
            ).fetchone()
        return StateChange.model_validate_json(row[0]) if row else None

    def load_analyzed_message_ids(self, chat_id: str, version: int) -> list[str]:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT analyzed_message_ids_json FROM customer_state_snapshots
                WHERE chat_id = ? AND version = ?
                """,
                (chat_id, version),
            ).fetchone()
        return json.loads(row[0]) if row else []
