"""Load the applicant profile from a YAML file."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Optional

try:
    import yaml
except ImportError:  # pragma: no cover - dependency hint
    yaml = None


@dataclass
class Profile:
    """Everything an application form might ask for.

    Fields left blank are simply skipped in the browser and left for you to
    review. Never invent answers to legal-attestation questions (work
    authorization, sponsorship, EEO) — fill those yourself in the YAML.
    """

    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "United States"

    linkedin: str = ""
    website: str = ""
    portfolio: str = ""

    current_title: str = ""
    current_company: str = ""
    years_experience: Optional[int] = None
    summary: str = ""

    # Legal / screening — you must set these; the tool never guesses.
    work_authorized_us: Optional[bool] = None
    requires_sponsorship: Optional[bool] = None
    willing_to_relocate: Optional[bool] = None
    desired_salary: str = ""
    notice_period: str = ""

    # File paths on YOUR machine.
    resume_path: str = ""
    cover_letter_path: str = ""
    recommendation_letter_path: str = ""
    case_study_path: str = ""
    development_plan_path: str = ""

    skills: list = field(default_factory=list)
    # Reusable answers keyed by a lowercase substring of the question.
    # e.g. {"why are you interested": "..."}
    answers: dict = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def document_paths(self) -> dict[str, str]:
        return {
            "resume": self.resume_path,
            "cover_letter": self.cover_letter_path,
            "recommendation_letter": self.recommendation_letter_path,
            "case_study": self.case_study_path,
            "development_plan": self.development_plan_path,
        }

    @classmethod
    def load(cls, path: str) -> "Profile":
        if yaml is None:
            raise RuntimeError(
                "PyYAML is required. Install with: pip install pyyaml"
            )
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            # Warn but don't fail — forward-compatible with extra keys.
            print(f"[profile] ignoring unrecognized keys: {sorted(unknown)}")
        return cls(**{k: v for k, v in data.items() if k in known})
