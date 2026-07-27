"""Plain data structures shared across the tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ATS(str, Enum):
    """Applicant Tracking System behind a job posting."""

    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    WORKDAY = "workday"
    GENERIC = "generic"
    UNKNOWN = "unknown"


class Status(str, Enum):
    """Where an application is in the pipeline."""

    FOUND = "found"            # link saved, nothing done yet
    TAILORED = "tailored"      # cover letter / materials prepared
    FILLED = "filled"          # form filled in browser, awaiting your review
    SUBMITTED = "submitted"    # you (or --submit) sent it
    NEEDS_MANUAL = "needs_manual"  # site can't be automated; do it by hand
    ERROR = "error"


@dataclass
class JobPosting:
    """A parsed job posting."""

    url: str
    ats: ATS = ATS.UNKNOWN
    company: str = ""
    title: str = ""
    location: str = ""
    description: str = ""
    apply_url: str = ""

    def short(self) -> str:
        title = self.title or "Unknown role"
        company = self.company or "Unknown company"
        return f"{title} @ {company}"


@dataclass
class ApplicationRecord:
    """One row in the tracker."""

    url: str
    company: str = ""
    title: str = ""
    status: str = Status.FOUND.value
    ats: str = ATS.UNKNOWN.value
    cover_letter_path: str = ""
    screenshot_path: str = ""
    notes: str = ""
    updated_at: str = ""  # stamped by the tracker at write time

    @classmethod
    def fields(cls) -> list[str]:
        return [
            "url", "company", "title", "status", "ats",
            "cover_letter_path", "screenshot_path", "notes", "updated_at",
        ]
