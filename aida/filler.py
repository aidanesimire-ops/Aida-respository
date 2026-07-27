"""Drive a real browser to fill a job-application form.

Uses Playwright. This runs on YOUR machine against YOUR logged-in browser
session. It fills standard fields, attaches your documents, and by default
STOPS so you can review before submitting. Pass submit=True to submit.

No CAPTCHA-solving and no stealth/anti-detection tricks: those get accounts
banned. On sites where honest automation can't complete the form, it fills what
it can, screenshots the page, and hands off to you.
"""

from __future__ import annotations

import os
from typing import Optional

from .models import JobPosting, ATS
from .profile import Profile

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


# Common field name/label fragments -> profile value getter
def _field_map(profile: Profile) -> list[tuple[list[str], str]]:
    """Return [(selectors_or_label_fragments, value)] best-effort."""
    return [
        (["first_name", "first name", "firstname", "given name"], profile.first_name),
        (["last_name", "last name", "lastname", "family name", "surname"], profile.last_name),
        (["full name", "your name", 'name"', "name]"], profile.full_name),
        (["email"], profile.email),
        (["phone", "mobile", "telephone"], profile.phone),
        (["linkedin"], profile.linkedin),
        (["website", "portfolio", "personal site"], profile.website),
        (["city", "location", "current location"], profile.location),
    ]


def _log(msg: str):
    print(f"  {msg}")


def fill_application(
    profile: Profile,
    posting: JobPosting,
    repo_root: str,
    cover_letter_text: str = "",
    submit: bool = False,
    headless: bool = False,
    screenshot_path: Optional[str] = None,
) -> dict:
    """Fill the application form. Returns a result dict.

    result = {status, screenshot, filled: [...], skipped: [...]}
    """
    if sync_playwright is None:
        return {
            "status": "needs_manual",
            "error": "Playwright not installed. Run: pip install playwright && playwright install chromium",
        }

    docs = profile.document_paths(repo_root)
    resume_path = docs.get("resume")
    filled: list[str] = []
    skipped: list[str] = []
    apply_url = posting.apply_url or posting.url

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(apply_url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1500)

        # 1) Standard text fields — try by name attr, id, and placeholder.
        for fragments, value in _field_map(profile):
            if not value:
                continue
            done = False
            for frag in fragments:
                for sel in (
                    f'input[name*="{frag}" i]',
                    f'input[id*="{frag}" i]',
                    f'input[placeholder*="{frag}" i]',
                    f'input[aria-label*="{frag}" i]',
                ):
                    try:
                        loc = page.locator(sel).first
                        if loc.count() and loc.is_visible():
                            loc.fill(value, timeout=3000)
                            filled.append(f"{fragments[0]} = {value}")
                            done = True
                            break
                    except Exception:
                        continue
                if done:
                    break

        # 2) Resume upload — the most valuable single attachment.
        if resume_path:
            for sel in (
                'input[type="file"][name*="resume" i]',
                'input[type="file"][id*="resume" i]',
                'input[type="file"]',
            ):
                try:
                    fi = page.locator(sel).first
                    if fi.count():
                        fi.set_input_files(resume_path, timeout=5000)
                        filled.append(f"resume -> {os.path.basename(resume_path)}")
                        break
                except Exception:
                    continue
            else:
                skipped.append("resume upload (no file input found)")

        # 3) Cover letter — paste text if there's a textarea for it.
        if cover_letter_text:
            for sel in (
                'textarea[name*="cover" i]',
                'textarea[id*="cover" i]',
                'textarea[aria-label*="cover" i]',
            ):
                try:
                    ta = page.locator(sel).first
                    if ta.count() and ta.is_visible():
                        ta.fill(cover_letter_text, timeout=3000)
                        filled.append("cover letter (pasted)")
                        break
                except Exception:
                    continue

        page.wait_for_timeout(800)
        shot = screenshot_path or "outputs/last_form.png"
        os.makedirs(os.path.dirname(shot) or ".", exist_ok=True)
        try:
            page.screenshot(path=shot, full_page=True)
        except Exception:
            shot = ""

        status = "filled"
        if submit:
            clicked = False
            for sel in (
                'button:has-text("Submit Application")',
                'button:has-text("Submit application")',
                'button:has-text("Submit")',
                'button[type="submit"]',
                'input[type="submit"]',
            ):
                try:
                    btn = page.locator(sel).first
                    if btn.count() and btn.is_visible():
                        btn.click(timeout=5000)
                        clicked = True
                        break
                except Exception:
                    continue
            status = "submitted" if clicked else "filled"
            page.wait_for_timeout(2500)
            if clicked:
                try:
                    page.screenshot(path=shot, full_page=True)
                except Exception:
                    pass
        else:
            # Leave the browser open briefly so the user can take over.
            if not headless:
                _log("Form filled. Review it in the browser window, then submit yourself.")
                _log("Closing this automated browser in 60s (your review copy stays in the screenshot).")
                page.wait_for_timeout(60000)

        context.close()
        browser.close()

    return {
        "status": status,
        "screenshot": shot,
        "filled": filled,
        "skipped": skipped,
    }
