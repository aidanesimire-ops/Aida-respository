"""Tailor a cover letter to a specific posting.

If ANTHROPIC_API_KEY is set and the `anthropic` package is installed, this uses
Claude to write a genuinely role-specific letter. Otherwise it falls back to a
solid template built from the profile + posting.
"""

from __future__ import annotations

import os
import re

from .models import JobPosting
from .profile import Profile

DEFAULT_MODEL = os.environ.get("AIDA_MODEL", "claude-opus-5")


def _company_from(posting: JobPosting) -> str:
    return posting.company or "your organization"


def _template_letter(profile: Profile, posting: JobPosting) -> str:
    company = _company_from(posting)
    role = posting.title or "the position"
    skills = ", ".join(profile.skills[:5]) if profile.skills else "real estate development and investment"
    return f"""{profile.full_name}
{profile.email} | {profile.phone} | {profile.location}

Dear Hiring Manager,

I am writing to apply for {role} at {company}. {profile.summary.strip()}

Across my career I have led projects through every stage of the development
lifecycle — acquisition analysis, financial modeling, investment underwriting,
due diligence, financing, entitlement, and asset repositioning — working
alongside developers, institutional investors, lenders, municipalities, and
counsel. My strengths in {skills} map directly to what {company} is building,
and I would bring disciplined analysis and accountable execution to the role
from day one.

I would welcome the chance to discuss how my background aligns with {company}'s
goals. Thank you for your time and consideration.

Sincerely,
{profile.full_name}
"""


def _llm_letter(profile: Profile, posting: JobPosting) -> str:
    import anthropic  # imported lazily

    client = anthropic.Anthropic()
    desc = (posting.description or "")[:6000]
    system = (
        "You write concise, specific, executive cover letters. One page max. "
        "No clichés, no filler, no invented facts. Ground every claim in the "
        "candidate's real background provided below. Match the letter to the "
        "specific role and company. Return only the letter body text."
    )
    user = f"""Write a tailored cover letter.

CANDIDATE:
Name: {profile.full_name}
Contact: {profile.email} | {profile.phone} | {profile.location}
Title: {profile.current_title}
Years experience: {profile.years_experience}
Summary: {profile.summary}
Key skills: {", ".join(profile.skills)}

ROLE:
Company: {_company_from(posting)}
Title: {posting.title}
Location: {posting.location}
Posting:
{desc}
"""
    msg = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    parts = [b.text for b in msg.content if getattr(b, "type", "") == "text"]
    return "\n".join(parts).strip()


def tailor_cover_letter(profile: Profile, posting: JobPosting) -> str:
    """Return cover-letter text tailored to the posting.

    Prefers Claude when available; always falls back to the template so this
    never blocks an application.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # noqa: F401
            letter = _llm_letter(profile, posting)
            if letter:
                return letter
        except Exception:
            pass  # fall through to template
    return _template_letter(profile, posting)


def slugify(text: str, maxlen: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", (text or "").lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:maxlen] or "role"
