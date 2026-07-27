"""Plain data structures shared across the tool."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class ATS(str, Enum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    WORKDAY = "workday"
    GENERIC = "generic"
    UNKNOWN = "unknown"


class Status(str, Enum):
    FETCHED = "fetched"          # posting pulled + parsed
    TAILORED = "tailored"        # cover letter written
    FILLED = "filled"            # form filled, awaiting your review
    SUBMITTED = "submitted"      # application submitted
    NEEDS_MANUAL = "needs_manual"  # site can't be automated safely
    ERROR = "error"


@dataclass
class JobPosting:
    url: str
    ats: ATS = ATS.UNKNOWN
    company: str = ""
    title: str = ""
    location: str = ""
    description: str = ""
    apply_url: str = ""

    def label(self) -> str:
        t = self.title or "Unknown role"
        c = self.company or "Unknown company"
        return f"{t} @ {c}"


@dataclass
class ApplicationRecord:
    url: str
    company: str = ""
    title: str = ""
    ats: str = ATS.UNKNOWN.value
    status: str = Status.FETCHED.value
    cover_letter_path: str = ""
    screenshot_path: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
