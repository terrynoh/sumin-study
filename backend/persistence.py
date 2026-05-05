from __future__ import annotations

import sqlite3
import json
from datetime import date, datetime
from pathlib import Path

from backend.models import AttemptRecord, ParentSummary, Reflection, Track, UnmatchedPathRecord


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    concept_ids TEXT NOT NULL,
    track TEXT NOT NULL,
    correct INTEGER NOT NULL,
    hint_level_used INTEGER NOT NULL,
    attempted_at TEXT NOT NULL,
    error_category TEXT,
    diagnostic_target TEXT,
    diagnostic_sentence TEXT,
    repair_node_ids TEXT NOT NULL DEFAULT '',
    transfer_variation_of TEXT,
    articulation_ok INTEGER,
    path_match_status TEXT NOT NULL DEFAULT 'n/a'
);

CREATE INDEX IF NOT EXISTS idx_attempts_student_time
ON attempts(student_id, attempted_at);

CREATE TABLE IF NOT EXISTS reflections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    reflection_text TEXT NOT NULL,
    articulation_ok INTEGER,
    submitted_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reflections_student_time
ON reflections(student_id, submitted_at);

CREATE TABLE IF NOT EXISTS parent_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    week_start TEXT NOT NULL,
    week_end TEXT NOT NULL,
    improving TEXT NOT NULL,
    still_developing TEXT NOT NULL,
    one_thing_that_would_help TEXT NOT NULL,
    sent_at TEXT,
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_parent_summaries_week
ON parent_summaries(student_id, week_start);

CREATE TABLE IF NOT EXISTS unmatched_path_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL,
    student_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    submitted_steps TEXT NOT NULL,
    attempted_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_unmatched_path_steps_student_time
ON unmatched_path_steps(student_id, attempted_at);
"""


class LearningStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init(self) -> None:
        con = self._connect()
        try:
            con.executescript(SCHEMA_SQL)
            self._ensure_optional_columns(con)
            con.commit()
        finally:
            con.close()

    def _ensure_optional_columns(self, con: sqlite3.Connection) -> None:
        columns = {
            row[1] for row in con.execute("PRAGMA table_info(attempts)").fetchall()
        }
        optional_columns = {
            "diagnostic_target": "TEXT",
            "diagnostic_sentence": "TEXT",
            "path_match_status": "TEXT NOT NULL DEFAULT 'n/a'",
        }
        for column_name, column_type in optional_columns.items():
            if column_name not in columns:
                con.execute(f"ALTER TABLE attempts ADD COLUMN {column_name} {column_type}")

    def add_attempt(self, student_id: str, attempt: AttemptRecord) -> int:
        con = self._connect()
        try:
            cursor = con.execute(
                """
                INSERT INTO attempts (
                    student_id, item_id, concept_ids, track, correct, hint_level_used,
                    attempted_at, error_category, diagnostic_target, diagnostic_sentence,
                    repair_node_ids, transfer_variation_of, articulation_ok, path_match_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    attempt.item_id,
                    ",".join(attempt.concept_ids),
                    attempt.track.value,
                    int(attempt.correct),
                    attempt.hint_level_used,
                    attempt.attempted_at.isoformat(),
                    attempt.error_category,
                    attempt.diagnostic_target,
                    attempt.diagnostic_sentence,
                    ",".join(attempt.repair_node_ids),
                    attempt.transfer_variation_of,
                    None if attempt.articulation_ok is None else int(attempt.articulation_ok),
                    attempt.path_match_status,
                ),
            )
            con.commit()
            return int(cursor.lastrowid)
        finally:
            con.close()

    def list_attempts(self, student_id: str) -> list[AttemptRecord]:
        con = self._connect()
        try:
            rows = con.execute(
                """
                SELECT id, item_id, concept_ids, track, correct, hint_level_used, attempted_at,
                       error_category, diagnostic_target, diagnostic_sentence, repair_node_ids,
                       transfer_variation_of, articulation_ok, path_match_status
                FROM attempts
                WHERE student_id = ?
                ORDER BY attempted_at ASC, id ASC
                """,
                (student_id,),
            ).fetchall()
        finally:
            con.close()
        return [
            AttemptRecord(
                item_id=row[1],
                concept_ids=tuple(filter(None, row[2].split(","))),
                track=Track(row[3]),
                correct=bool(row[4]),
                hint_level_used=int(row[5]),
                attempted_at=datetime.fromisoformat(row[6]),
                error_category=row[7],
                diagnostic_target=row[8],
                diagnostic_sentence=row[9],
                repair_node_ids=tuple(filter(None, row[10].split(","))),
                transfer_variation_of=row[11],
                articulation_ok=None if row[12] is None else bool(row[12]),
                id=int(row[0]),
                path_match_status=row[13] or "n/a",
            )
            for row in rows
        ]

    def list_unmatched_paths(self, student_id: str, since: datetime | None = None) -> list[AttemptRecord]:
        con = self._connect()
        try:
            params: list[object] = [student_id]
            where = "student_id = ? AND correct = 1 AND path_match_status = 'unmatched'"
            if since is not None:
                where += " AND attempted_at >= ?"
                params.append(since.isoformat())
            rows = con.execute(
                f"""
                SELECT id, item_id, concept_ids, track, correct, hint_level_used, attempted_at,
                       error_category, diagnostic_target, diagnostic_sentence, repair_node_ids,
                       transfer_variation_of, articulation_ok, path_match_status
                FROM attempts
                WHERE {where}
                ORDER BY attempted_at ASC, id ASC
                """,
                tuple(params),
            ).fetchall()
        finally:
            con.close()
        return [
            AttemptRecord(
                item_id=row[1],
                concept_ids=tuple(filter(None, row[2].split(","))),
                track=Track(row[3]),
                correct=bool(row[4]),
                hint_level_used=int(row[5]),
                attempted_at=datetime.fromisoformat(row[6]),
                error_category=row[7],
                diagnostic_target=row[8],
                diagnostic_sentence=row[9],
                repair_node_ids=tuple(filter(None, row[10].split(","))),
                transfer_variation_of=row[11],
                articulation_ok=None if row[12] is None else bool(row[12]),
                id=int(row[0]),
                path_match_status=row[13] or "n/a",
            )
            for row in rows
        ]

    def add_unmatched_path_steps(
        self,
        student_id: str,
        attempt_id: int,
        item_id: str,
        submitted_steps: tuple[str, ...],
        attempted_at: datetime,
    ) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                INSERT INTO unmatched_path_steps (
                    attempt_id, student_id, item_id, submitted_steps, attempted_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    student_id,
                    item_id,
                    json.dumps(list(submitted_steps), ensure_ascii=False),
                    attempted_at.isoformat(),
                ),
            )
            con.commit()
        finally:
            con.close()

    def list_unmatched_path_steps(
        self,
        student_id: str,
        since: datetime | None = None,
    ) -> list[UnmatchedPathRecord]:
        con = self._connect()
        try:
            params: list[object] = [student_id]
            where = "student_id = ?"
            if since is not None:
                where += " AND attempted_at >= ?"
                params.append(since.isoformat())
            rows = con.execute(
                f"""
                SELECT id, attempt_id, item_id, submitted_steps, attempted_at
                FROM unmatched_path_steps
                WHERE {where}
                ORDER BY attempted_at ASC, id ASC
                """,
                tuple(params),
            ).fetchall()
        finally:
            con.close()
        return [
            UnmatchedPathRecord(
                id=int(row[0]),
                attempt_id=int(row[1]),
                item_id=row[2],
                submitted_steps=tuple(json.loads(row[3])),
                attempted_at=datetime.fromisoformat(row[4]),
            )
            for row in rows
        ]

    def add_reflection(
        self,
        student_id: str,
        item_id: str,
        reflection_text: str,
        articulation_ok: bool | None,
        submitted_at: datetime,
    ) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                INSERT INTO reflections (
                    student_id, item_id, reflection_text, articulation_ok, submitted_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    student_id,
                    item_id,
                    reflection_text,
                    None if articulation_ok is None else int(articulation_ok),
                    submitted_at.isoformat(),
                ),
            )
            con.commit()
        finally:
            con.close()

    def update_latest_attempt_articulation(
        self,
        student_id: str,
        item_id: str,
        articulation_ok: bool,
    ) -> bool:
        con = self._connect()
        try:
            cursor = con.execute(
                """
                UPDATE attempts
                SET articulation_ok = ?
                WHERE id = (
                    SELECT id
                    FROM attempts
                    WHERE student_id = ? AND item_id = ?
                    ORDER BY attempted_at DESC, id DESC
                    LIMIT 1
                )
                """,
                (int(articulation_ok), student_id, item_id),
            )
            con.commit()
            return cursor.rowcount > 0
        finally:
            con.close()

    def list_reflections(self, student_id: str, since: datetime | None = None) -> list[Reflection]:
        con = self._connect()
        try:
            params: list[object] = [student_id]
            where = "student_id = ?"
            if since is not None:
                where += " AND submitted_at >= ?"
                params.append(since.isoformat())
            rows = con.execute(
                f"""
                SELECT id, student_id, item_id, reflection_text, articulation_ok, submitted_at
                FROM reflections
                WHERE {where}
                ORDER BY submitted_at ASC, id ASC
                """,
                tuple(params),
            ).fetchall()
        finally:
            con.close()
        return [
            Reflection(
                id=int(row[0]),
                student_id=row[1],
                item_id=row[2],
                reflection_text=row[3],
                articulation_ok=None if row[4] is None else bool(row[4]),
                submitted_at=datetime.fromisoformat(row[5]),
            )
            for row in rows
        ]

    def upsert_parent_summary(
        self,
        student_id: str,
        week_start: date,
        week_end: date,
        sections: dict[str, str],
        *,
        created_at: datetime | None = None,
    ) -> None:
        created_at = created_at or datetime.now()
        con = self._connect()
        try:
            con.execute(
                """
                INSERT INTO parent_summaries (
                    student_id, week_start, week_end, improving, still_developing,
                    one_thing_that_would_help, sent_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
                ON CONFLICT(student_id, week_start) DO UPDATE SET
                    week_end = excluded.week_end,
                    improving = excluded.improving,
                    still_developing = excluded.still_developing,
                    one_thing_that_would_help = excluded.one_thing_that_would_help
                """,
                (
                    student_id,
                    week_start.isoformat(),
                    week_end.isoformat(),
                    sections["improving"],
                    sections["still_developing"],
                    sections["one_thing_that_would_help"],
                    created_at.isoformat(),
                ),
            )
            con.commit()
        finally:
            con.close()

    def get_parent_summary(self, student_id: str, week_start: date) -> ParentSummary | None:
        con = self._connect()
        try:
            row = con.execute(
                """
                SELECT id, student_id, week_start, week_end, improving, still_developing,
                       one_thing_that_would_help, sent_at, created_at
                FROM parent_summaries
                WHERE student_id = ? AND week_start = ?
                """,
                (student_id, week_start.isoformat()),
            ).fetchone()
        finally:
            con.close()
        if row is None:
            return None
        return ParentSummary(
            id=int(row[0]),
            student_id=row[1],
            week_start=date.fromisoformat(row[2]),
            week_end=date.fromisoformat(row[3]),
            improving=row[4],
            still_developing=row[5],
            one_thing_that_would_help=row[6],
            sent_at=None if row[7] is None else datetime.fromisoformat(row[7]),
            created_at=datetime.fromisoformat(row[8]),
        )

    def mark_summary_sent(self, student_id: str, week_start: date, sent_at: datetime) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                UPDATE parent_summaries
                SET sent_at = ?
                WHERE student_id = ? AND week_start = ?
                """,
                (sent_at.isoformat(), student_id, week_start.isoformat()),
            )
            con.commit()
        finally:
            con.close()
