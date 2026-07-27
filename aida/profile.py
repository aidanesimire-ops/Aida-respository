"""Load and validate the user's profile from config/profile.yaml."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from typing import Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


@dataclass
class Profile:
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    locations: list = field(default_factory=list)
    linkedin: str = ""
    website: str = ""
    github: str = ""
    current_title: str = ""
    years_experience: int = 0
    summary: str = ""
    work_authorized_us: Optional[bool] = None
    requires_sponsorship: Optional[bool] = None
    willing_to_relocate: Optional[bool] = None
    salary_expectation: str = ""
    skills: list = field(default_factory=list)
    documents: dict = field(default_factory=dict)
    default_answers: dict = field(default_factory=dict)
    references: list = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def document_paths(self, repo_root: str) -> dict:
        """Return {label: absolute_path} for documents that exist on disk."""
        out = {}
        for label, rel in (self.documents or {}).items():
            if not rel:
                continue
            path = rel if os.path.isabs(rel) else os.path.join(repo_root, rel)
            if os.path.exists(path):
                out[label] = path
        return out

    @classmethod
    def load(cls, path: str) -> "Profile":
        if yaml is None:
            raise RuntimeError(
                "PyYAML is required to load the profile. Install with: pip install pyyaml"
            )
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Profile not found: {path}\n"
                "Copy config/profile.example.yaml to config/profile.yaml and fill it in."
            )
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        known = {fld.name for fld in fields(cls)}
        clean = {k: v for k, v in data.items() if k in known}
        return cls(**clean)
