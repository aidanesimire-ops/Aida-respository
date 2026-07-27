"""Produce a per-role cover letter.

Two modes:

1.  Template mode (default, no API key): fills your base cover letter with the
    company/role so every application has a targeted opening line. Fast and
    free, but generic.
2.  Claude mode (if ANTHROPIC_API_KEY is set): rewrites the letter to speak
    directly to the posting. Uses the Anthropic Messages API.

In practice the best tailoring happens in conversation with Claude — this
module is the offline fallback so the tool still works on its own.
"""

from __future__ import annotations

import os

from .models import JobPosting
from .profile import Profile

BASE_OPENING = (
    "Dear Hiring Manager,\n\n"
    "I am excited to apply for the {title} role at {company}. As a real estate "
    "development executive with nearly a decade of experience and $2B+ in "
    "cumulative project capitalization — spanning underwriting, deal structuring, "
    "entitlements, and asset repositioning — I believe my background maps "
    "directly to what {company} is building."
)


def tailor_cover_letter(profile: Profile, posting: JobPosting) -> str:
    company = posting.company or "your organization"
    title = posting.title or "this position"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _tailor_with_claude(profile, posting, api_key)
        except Exception as exc:  # noqa: BLE001
            print(f"[tailor] Claude tailoring failed ({exc}); using template.")

    opening = BASE_OPENING.format(company=company, title=title)
    body = (
        "\n\nThroughout my career I have led projects across the full development "
        "lifecycle — acquisition analysis, financial modeling, investment "
        "underwriting, due diligence, financing, entitlement, and repositioning — "
        "working with developers, institutional investors, lenders, and "
        "municipalities. I combine market intelligence with disciplined financial "
        "analysis to identify high-value opportunities, structure deals, and guide "
        "capital-allocation decisions that maximize returns while managing risk.\n\n"
        "My background is reinforced by executive education from the Harvard "
        "Graduate School of Design, real estate broker licensure in three states, "
        "LEED AP Neighborhood Development accreditation, and FINRA Series 66 & SIE. "
        "I would welcome the chance to discuss how my experience can contribute to "
        f"{company}'s goals.\n\n"
        "Sincerely,\n"
        f"{profile.full_name or 'Aida Nesimi'}"
    )
    return opening + body


def _tailor_with_claude(profile: Profile, posting: JobPosting, api_key: str) -> str:
    import anthropic  # imported lazily so the tool runs without it

    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        "Write a concise, specific cover letter (max ~320 words) for this "
        "candidate applying to the role below. Ground every claim in the "
        "candidate summary; do not invent employers, titles, or facts. Return "
        "only the letter text.\n\n"
        f"CANDIDATE: {profile.full_name}\n"
        f"SUMMARY: {profile.summary}\n\n"
        f"ROLE: {posting.title}\n"
        f"COMPANY: {posting.company}\n"
        f"POSTING:\n{posting.description[:4000]}"
    )
    resp = client.messages.create(
        model=os.environ.get("AIDA_MODEL", "claude-opus-5"),
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()
