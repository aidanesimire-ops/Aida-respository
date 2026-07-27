"""Command-line entry point.

    python -m aida init                     # check your setup
    python -m aida apply <url>              # fill an application (review before submit)
    python -m aida apply <url> --submit     # fill AND auto-submit (use with care)
    python -m aida tailor <url>             # just write a tailored cover letter
    python -m aida list                     # show the tracker
"""

from __future__ import annotations

import argparse
import os
import sys

from .fetcher import fetch
from .models import ApplicationRecord, Status
from .profile import Profile
from .tailor import tailor_cover_letter
from .tracker import Tracker

DEFAULT_PROFILE = "private/profile.yaml"
COVER_DIR = "private/cover_letters"


def _load_profile(path: str) -> Profile:
    if not os.path.exists(path):
        sys.exit(
            f"No profile at {path}.\n"
            "Copy profile.example.yaml to private/profile.yaml and fill it in."
        )
    return Profile.load(path)


def cmd_init(args) -> None:
    print("Aida setup check")
    print("-" * 40)
    ok = True
    if os.path.exists(args.profile):
        profile = Profile.load(args.profile)
        print(f"[ok] profile loaded: {profile.full_name or '(name missing)'}")
        for key, path in profile.document_paths().items():
            if path and os.path.exists(path):
                print(f"[ok] {key}: {path}")
            elif path:
                print(f"[!!] {key}: path set but file NOT found -> {path}")
            else:
                print(f"[--] {key}: not set")
    else:
        ok = False
        print(f"[!!] no profile at {args.profile}")
    for mod in ("requests", "bs4", "yaml", "playwright"):
        try:
            __import__(mod)
            print(f"[ok] dependency: {mod}")
        except ImportError:
            ok = False
            print(f"[!!] missing dependency: {mod}")
    print("-" * 40)
    print("Ready." if ok else "Fix the [!!] items above, then re-run init.")


def cmd_tailor(args) -> None:
    profile = _load_profile(args.profile)
    posting = fetch(args.url)
    print(f"Role: {posting.short()}")
    letter = tailor_cover_letter(profile, posting)
    os.makedirs(COVER_DIR, exist_ok=True)
    safe = (posting.company or "job").lower().replace(" ", "_")[:40]
    out = os.path.join(COVER_DIR, f"{safe}.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(letter)
    print(f"\n{letter}\n")
    print(f"[saved] {out}")
    Tracker().upsert(ApplicationRecord(
        url=args.url, company=posting.company, title=posting.title,
        ats=posting.ats.value, status=Status.TAILORED.value,
        cover_letter_path=out,
    ))


def cmd_apply(args) -> None:
    from .filler import fill_application  # lazy: only import Playwright when needed

    profile = _load_profile(args.profile)
    posting = fetch(args.url)
    print(f"Role: {posting.short()}  [{posting.ats.value}]")
    if args.submit:
        print("!! --submit is ON: the form will be sent automatically.")
    result = fill_application(posting, profile, submit=args.submit)
    print(f"\nFilled {len(result.filled)} field(s); skipped {len(result.skipped)}.")
    for line in result.filled:
        print(f"  + {line}")
    for line in result.skipped:
        print(f"  - {line}")
    Tracker().upsert(ApplicationRecord(
        url=args.url, company=posting.company, title=posting.title,
        ats=posting.ats.value, status=result.status,
        screenshot_path=result.screenshot_path,
        notes="auto-submitted" if result.submitted else "filled; reviewed manually",
    ))
    print(f"\nStatus: {result.status}")
    if result.screenshot_path:
        print(f"Screenshot: {result.screenshot_path}")


def cmd_list(args) -> None:
    rows = Tracker().all()
    if not rows:
        print("No applications tracked yet.")
        return
    print(f"{'STATUS':<14} {'COMPANY':<24} {'TITLE':<34} UPDATED")
    print("-" * 90)
    for r in rows:
        print(f"{r.status:<14} {r.company[:23]:<24} {r.title[:33]:<34} {r.updated_at}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="aida", description="Personal job-application assistant")
    parser.add_argument("--profile", default=DEFAULT_PROFILE, help="path to profile YAML")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="check your setup").set_defaults(func=cmd_init)

    p_apply = sub.add_parser("apply", help="fill an application in the browser")
    p_apply.add_argument("url")
    p_apply.add_argument("--submit", action="store_true", help="auto-submit (default: review first)")
    p_apply.set_defaults(func=cmd_apply)

    p_tailor = sub.add_parser("tailor", help="write a tailored cover letter")
    p_tailor.add_argument("url")
    p_tailor.set_defaults(func=cmd_tailor)

    sub.add_parser("list", help="show tracked applications").set_defaults(func=cmd_list)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
