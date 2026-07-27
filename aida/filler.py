"""Drive a real browser to fill an application form.

Design principles:
  * Runs a VISIBLE browser so you can watch, log in, and take over any time.
  * Fills only what it can confidently match; leaves the rest for you.
  * NEVER clicks submit unless you pass submit=True.
  * Screenshots the filled form so there's always a record.

This uses Playwright. Install once with:  playwright install chromium
"""

from __future__ import annotations

import os
import time

from .models import ATS, JobPosting, Status
from .profile import Profile

# Field label/name substrings -> profile attribute name.
TEXT_FIELD_MAP = {
    "first name": "first_name",
    "last name": "last_name",
    "full name": "full_name",
    "email": "email",
    "phone": "phone",
    "address": "address",
    "city": "city",
    "state": "state",
    "zip": "zip_code",
    "postal": "zip_code",
    "linkedin": "linkedin",
    "website": "website",
    "portfolio": "portfolio",
    "current company": "current_company",
    "current title": "current_title",
    "desired salary": "desired_salary",
    "salary": "desired_salary",
}


class FillResult:
    def __init__(self):
        self.filled: list[str] = []
        self.skipped: list[str] = []
        self.screenshot_path: str = ""
        self.submitted: bool = False
        self.status: str = Status.FILLED.value


def _profile_value(profile: Profile, attr: str) -> str:
    if attr == "full_name":
        return profile.full_name
    val = getattr(profile, attr, "")
    return "" if val is None else str(val)


def fill_application(
    posting: JobPosting,
    profile: Profile,
    submit: bool = False,
    screenshot_dir: str = "screenshots",
) -> FillResult:
    """Open the apply page and fill what we can. Returns a FillResult."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Playwright is required. Install with:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        ) from exc

    result = FillResult()
    os.makedirs(screenshot_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(posting.apply_url or posting.url, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        _fill_text_fields(page, profile, result)
        _upload_documents(page, profile, result)

        # Screenshot the filled state before doing anything irreversible.
        safe = (posting.company or "job").lower().replace(" ", "_")[:40]
        shot = os.path.join(screenshot_dir, f"{safe}_{int(time.time())}.png")
        try:
            page.screenshot(path=shot, full_page=True)
            result.screenshot_path = shot
        except Exception:
            pass

        if submit:
            result.submitted = _click_submit(page)
            result.status = (
                Status.SUBMITTED.value if result.submitted else Status.FILLED.value
            )
            page.wait_for_timeout(2000)
        else:
            print(
                "\n>>> Form filled. Review it in the browser window, finish any "
                "remaining fields, then submit yourself.\n>>> Press Enter here "
                "when you're done to close the browser..."
            )
            try:
                input()
            except EOFError:
                page.wait_for_timeout(60000)

        context.close()
        browser.close()

    if not result.filled:
        result.status = Status.NEEDS_MANUAL.value
    return result


def _fill_text_fields(page, profile: Profile, result: FillResult) -> None:
    inputs = page.query_selector_all("input, textarea")
    for el in inputs:
        try:
            itype = (el.get_attribute("type") or "text").lower()
            if itype in ("hidden", "file", "checkbox", "radio", "submit", "button"):
                continue
            label = _label_for(page, el)
            attr = _match_field(label)
            if not attr:
                continue
            value = _profile_value(profile, attr)
            if not value:
                result.skipped.append(f"{label} (no profile value)")
                continue
            el.fill(value)
            result.filled.append(f"{label} -> {value}")
        except Exception:
            continue


def _label_for(page, el) -> str:
    """Best-effort human label for a field."""
    for attr in ("aria-label", "placeholder", "name", "id"):
        val = el.get_attribute(attr)
        if val:
            return val.lower().replace("_", " ").replace("-", " ")
    return ""


def _match_field(label: str) -> str:
    if not label:
        return ""
    for needle, attr in TEXT_FIELD_MAP.items():
        if needle in label:
            return attr
    return ""


def _upload_documents(page, profile: Profile, result: FillResult) -> None:
    """Attach resume (and cover letter where a second upload exists)."""
    file_inputs = page.query_selector_all("input[type=file]")
    docs = profile.document_paths()
    order = ["resume", "cover_letter", "recommendation_letter", "case_study"]
    available = [(k, docs[k]) for k in order if docs.get(k) and os.path.exists(docs[k])]
    for idx, el in enumerate(file_inputs):
        if idx >= len(available):
            break
        key, path = available[idx]
        try:
            el.set_input_files(path)
            result.filled.append(f"uploaded {key}: {os.path.basename(path)}")
        except Exception:
            result.skipped.append(f"{key} upload failed")


def _click_submit(page) -> bool:
    for selector in (
        "button[type=submit]",
        "input[type=submit]",
        "button:has-text('Submit')",
        "button:has-text('Submit application')",
        "button:has-text('Apply')",
    ):
        try:
            btn = page.query_selector(selector)
            if btn and btn.is_visible():
                btn.click()
                page.wait_for_timeout(3000)
                return True
        except Exception:
            continue
    print("[filler] Could not find a submit button — submit manually.")
    return False
