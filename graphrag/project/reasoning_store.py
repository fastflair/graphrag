"""SQLite-backed persistence for reasoning traces captured during chats."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List

from .models import ReasoningStep


class ReasoningStore:
    """Stores reasoning traces for audit and replay purposes."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialise(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reasoning (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scope TEXT NOT NULL,
                    scope_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    input_text TEXT NOT NULL,
                    output_text TEXT NOT NULL,
                    tool TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()

    def append(self, scope: str, scope_id: str, reasoning: Iterable[ReasoningStep]) -> None:
        steps = list(reasoning)
        if not steps:
            return

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO reasoning (
                    scope,
                    scope_id,
                    step_index,
                    name,
                    input_text,
                    output_text,
                    tool,
                    metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        scope,
                        scope_id,
                        index,
                        step.name,
                        step.input_text,
                        step.output_text,
                        step.tool,
                        json.dumps(step.metadata, sort_keys=True, ensure_ascii=False)
                        if step.metadata
                        else None,
                    )
                    for index, step in enumerate(steps)
                ],
            )
            connection.commit()

    def get_reasoning(self, scope: str, scope_id: str) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT step_index, name, input_text, output_text, tool, metadata
                FROM reasoning
                WHERE scope = ? AND scope_id = ?
                ORDER BY step_index ASC
                """,
                (scope, scope_id),
            )
            rows = cursor.fetchall()

        results: List[Dict[str, Any]] = []
        for index, name, input_text, output_text, tool, metadata in rows:
            payload = {
                "step_index": index,
                "name": name,
                "input_text": input_text,
                "output_text": output_text,
                "tool": tool,
            }
            if metadata:
                payload["metadata"] = json.loads(metadata)
            results.append(payload)
        return results

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        try:
            yield connection
        finally:
            connection.close()
