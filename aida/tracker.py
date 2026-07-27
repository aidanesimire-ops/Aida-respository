"""A tiny SQLite-backed application tracker so nothing slips."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from .models import ApplicationRecord


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Tracker:
    def __init__(self, db_path: str = "applications.db"):
        self.db_path = db_path
        self._init()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init(self):
        with self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS applications (
                    url TEXT PRIMARY KEY,
                    company TEXT, title TEXT, ats TEXT, status TEXT,
                    cover_letter_path TEXT, screenshot_path TEXT, notes TEXT,
                    created_at TEXT, updated_at TEXT
                )
                """
            )

    def upsert(self, rec: ApplicationRecord):
        with self._conn() as c:
            existing = c.execute(
                "SELECT created_at FROM applications WHERE url=?", (rec.url,)
            ).fetchone()
            rec.created_at = existing[0] if existing else _now()
            rec.updated_at = _now()
            c.execute(
                """
                INSERT INTO applications
                    (url, company, title, ats, status, cover_letter_path,
                     screenshot_path, notes, created_at, updated_at)
                VALUES (:url,:company,:title,:ats,:status,:cover_letter_path,
                        :screenshot_path,:notes,:created_at,:updated_at)
                ON CONFLICT(url) DO UPDATE SET
                    company=excluded.company, title=excluded.title, ats=excluded.ats,
                    status=excluded.status, cover_letter_path=excluded.cover_letter_path,
                    screenshot_path=excluded.screenshot_path, notes=excluded.notes,
                    updated_at=excluded.updated_at
                """,
                rec.to_dict(),
            )

    def all(self) -> list[ApplicationRecord]:
        with self._conn() as c:
            c.row_factory = sqlite3.Row
            rows = c.execute(
                "SELECT * FROM applications ORDER BY updated_at DESC"
            ).fetchall()
        return [ApplicationRecord(**dict(r)) for r in rows]
