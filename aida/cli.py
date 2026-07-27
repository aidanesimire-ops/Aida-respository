"""Command-line entry point.

    python -m aida fetch  <url>            # pull + show the posting
    python -m aida tailor <url>            # write a tailored cover letter -> outputs/
    python -m aida apply  <url>            # fetch + tailor + fill the form (review mode)
    python -m aida apply  <url> --submit   # ...and submit it
    python -m aida list                    # show tracked applications
"""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .models import ApplicationRecord, Status
from .profile import Profile
from .tailor import tailor_cover_letter, slugify
from .tracker import Tracker

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_PATH = os.path.join(REPO_ROOT, "config", "profile.yaml")
OUTPUT_DIR = os.path.join(REPO_ROOT, "outputs")


def _load_profile() -> Profile:
    return Profile.load(PROFILE_PATH)


def _print_posting(p):
    print(f"\n  {p.label()}")
    print(f"  ATS:      {p.ats.value}")
    print(f"  Location: {p.location or '—'}")
    print(f"  Apply:    {p.apply_url}")
    desc = (p.description or "").strip()
    if desc:
        print("\n  --- description (first 1200 chars) ---")
        print("  " + desc[:1200].replace("\n", "\n  "))
    print()


def _save_cover_letter(profile: Profile, posting, text: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    name = f"cover-letter_{slugify(posting.company)}_{slugify(posting.title)}.txt"
    path = os.path.join(OUTPUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def cmd_fetch(args):
    from .fetcher import fetch
    posting = fetch(args.url)
    _print_posting(posting)


def cmd_tailor(args):
    from .fetcher import fetch
    profile = _load_profile()
    posting = fetch(args.url)
    _print_posting(posting)
    letter = tailor_cover_letter(profile, posting)
    path = _save_cover_letter(profile, posting, letter)
    print("  --- tailored cover letter ---\n")
    print(letter)
    print(f"\n  saved: {path}")
    Tracker(os.path.join(REPO_ROOT, "applications.db")).upsert(
        ApplicationRecord(
            url=posting.url, company=posting.company, title=posting.title,
            ats=posting.ats.value, status=Status.TAILORED.value,
            cover_letter_path=path,
        )
    )


def cmd_apply(args):
    from .fetcher import fetch
    from .filler import fill_application
    profile = _load_profile()
    tracker = Tracker(os.path.join(REPO_ROOT, "applications.db"))

    posting = fetch(args.url)
    _print_posting(posting)

    letter = tailor_cover_letter(profile, posting)
    cover_path = _save_cover_letter(profile, posting, letter)
    print(f"  tailored cover letter -> {cover_path}")

    docs = profile.document_paths(REPO_ROOT)
    print(f"  documents available to attach: {', '.join(docs) or 'NONE (add files to documents/)'}")

    if not docs.get("resume"):
        print("\n  WARNING: no resume found at the path in config/profile.yaml.")

    print("\n  opening browser to fill the form"
          + (" and SUBMIT" if args.submit else " (review mode — you submit)") + " ...")
    result = fill_application(
        profile, posting, REPO_ROOT,
        cover_letter_text=letter,
        submit=args.submit,
        headless=args.headless,
        screenshot_path=os.path.join(OUTPUT_DIR, f"form_{slugify(posting.company)}.png"),
    )

    print(f"\n  status: {result.get('status')}")
    if result.get("error"):
        print(f"  note:   {result['error']}")
    for f in result.get("filled", []):
        print(f"    filled: {f}")
    for s in result.get("skipped", []):
        print(f"    skipped: {s}")
    if result.get("screenshot"):
        print(f"  screenshot: {result['screenshot']}")

    tracker.upsert(ApplicationRecord(
        url=posting.url, company=posting.company, title=posting.title,
        ats=posting.ats.value, status=result.get("status", Status.FILLED.value),
        cover_letter_path=cover_path, screenshot_path=result.get("screenshot", ""),
        notes="; ".join(result.get("skipped", [])),
    ))


def cmd_list(args):
    tracker = Tracker(os.path.join(REPO_ROOT, "applications.db"))
    rows = tracker.all()
    if not rows:
        print("  no applications tracked yet.")
        return
    print(f"\n  {len(rows)} tracked application(s):\n")
    for r in rows:
        print(f"  [{r.status:12}] {r.title or '—'} @ {r.company or '—'}")
        print(f"               {r.url}")
        if r.updated_at:
            print(f"               updated {r.updated_at}")
    print()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aida", description="Personal job-application assistant.")
    p.add_argument("--version", action="version", version=f"aida {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch", help="fetch and show a posting")
    f.add_argument("url")
    f.set_defaults(func=cmd_fetch)

    t = sub.add_parser("tailor", help="write a tailored cover letter")
    t.add_argument("url")
    t.set_defaults(func=cmd_tailor)

    a = sub.add_parser("apply", help="fetch + tailor + fill the form")
    a.add_argument("url")
    a.add_argument("--submit", action="store_true", help="actually submit (default: review only)")
    a.add_argument("--headless", action="store_true", help="run browser headless")
    a.set_defaults(func=cmd_apply)

    l = sub.add_parser("list", help="list tracked applications")
    l.set_defaults(func=cmd_list)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
