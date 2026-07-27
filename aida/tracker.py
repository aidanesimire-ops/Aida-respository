"""A tiny CSV-backed application tracker.

CSV (not a database) on purpose: you can open it in Excel or Google Sheets
any time, and it's trivial to eyeball what's been applied to.
"""

from __future__ import annotations

import csv
import datetime
import os
from typing import Optional

from .models import ApplicationRecord

DEFAULT_PATH = "applications.csv"


class Tracker:
    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        self._rows: dict[str, ApplicationRecord] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                rec = ApplicationRecord(
                    **{k: row.get(k, "") for k in ApplicationRecord.fields()}
                )
                self._rows[rec.url] = rec

    def _now(self) -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    def upsert(self, record: ApplicationRecord) -> ApplicationRecord:
        existing = self._rows.get(record.url)
        if existing:
            # Only overwrite non-empty incoming fields.
            for f in ApplicationRecord.fields():
                val = getattr(record, f)
                if val not in ("", None):
                    setattr(existing, f, val)
            record = existing
        record.updated_at = self._now()
        self._rows[record.url] = record
        self._save()
        return record

    def get(self, url: str) -> Optional[ApplicationRecord]:
        return self._rows.get(url)

    def all(self) -> list[ApplicationRecord]:
        return sorted(self._rows.values(), key=lambda r: r.updated_at, reverse=True)

    def _save(self) -> None:
        with open(self.path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=ApplicationRecord.fields())
            writer.writeheader()
            for rec in self._rows.values():
                writer.writerow({f: getattr(rec, f) for f in ApplicationRecord.fields()})
