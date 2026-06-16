#!/usr/bin/env python3
"""Generate a combined iCalendar (.ics) file of City of Fort Lauderdale
advisory board / committee meetings.

The schedules below were compiled from public sources on the City Clerk's
"Advisory Boards, Committees, and Authorities" hub and individual board pages
on fortlauderdale.gov. They are best-effort and may be out of date — the City
changes, reschedules, and cancels meetings. Always confirm against the
authoritative Legistar calendar (https://fortlauderdale.legistar.com/) or the
City Clerk's Office (954-828-5288) before attending.

No third-party dependencies — stdlib only. Run:

    python3 generate_calendar.py

writes: fort-lauderdale-advisory-boards.ics
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

OUTPUT_FILE = "fort-lauderdale-advisory-boards.ics"
TZID = "America/New_York"
COMPILED_ON = "2026-06-16"

# First occurrences are computed on/after this date.
SEARCH_START = date(2026, 7, 1)
# Single-shot "verify schedule" reminders are anchored here.
REMINDER_DATE = date(2026, 6, 30)

# RRULE weekday tokens, Monday=0 .. Sunday=6
WEEKDAY_TOKEN = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
WEEKDAY_NAME = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
ORDINAL_NAME = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", -1: "last"}

DISCLAIMER = (
    f"Schedule auto-compiled from public web sources on {COMPILED_ON} - "
    "confirm date/time/location with the City Clerk (954-828-5288) or the "
    "Legistar calendar (https://fortlauderdale.legistar.com/) before attending."
)


@dataclass
class Board:
    """One advisory board / committee.

    For boards with a known recurrence, set `ordinal` (1..4 or -1 for last),
    `weekday` (0=Mon..6=Sun) and `start`/`end` times. For boards whose schedule
    is unknown / as-needed, leave `ordinal` as None to emit a single
    "verify schedule" reminder instead of a recurring event.
    """

    name: str
    source: str
    slug: str
    ordinal: int | None = None
    weekday: int | None = None
    start_hour: int = 0
    start_min: int = 0
    end_hour: int | None = None
    end_min: int = 0
    location: str = ""
    contact: str = ""
    note: str = ""

    @property
    def recurring(self) -> bool:
        return self.ordinal is not None and self.weekday is not None


# Common locations
DSD = "Development Services Department, 700 NW 19th Avenue, Fort Lauderdale, FL 33311"
CITY_HALL = "City Hall, 100 N Andrews Avenue, Fort Lauderdale, FL 33301"

CLERK_HUB = (
    "https://www.fortlauderdale.gov/government/departments-a-h/city-clerk-s-office/"
    "advisory-boards-committees-authorities-agendas-and-minutes"
)


def clerk(path: str) -> str:
    return f"{CLERK_HUB}/{path}"


BOARDS: list[Board] = [
    # ---- Known recurring schedules -------------------------------------
    Board(
        name="Planning and Zoning Board",
        slug="planning-zoning-board",
        ordinal=3,
        weekday=2,  # Wednesday
        start_hour=18,
        end_hour=20,
        location=DSD,
        contact="planning@fortlauderdale.gov",
        source=(
            "https://www.fortlauderdale.gov/government/departments-a-h/"
            "development-services/urban-design-and-planning/development-applications-"
            "boards-and-committees/planning-and-zoning-board"
        ),
    ),
    Board(
        name="Board of Adjustment",
        slug="board-of-adjustment",
        ordinal=2,
        weekday=2,  # Wednesday
        start_hour=18,
        end_hour=20,
        location=DSD,
        contact="planning@fortlauderdale.gov",
        source=clerk("board-of-adjustment"),
    ),
    Board(
        name="Economic Development Advisory Board",
        slug="economic-development-advisory-board",
        ordinal=2,
        weekday=2,  # Wednesday
        start_hour=15,
        end_hour=17,
        location=DSD,
        contact="",
        source=clerk("economic-development-advisory-board"),
    ),
    Board(
        name="Beach Business Improvement District Advisory Committee",
        slug="beach-bid-advisory-committee",
        ordinal=2,
        weekday=0,  # Monday
        start_hour=13,
        start_min=30,
        end_hour=15,
        location="Beach Community Center / City Hall, Fort Lauderdale, FL",
        contact="BeachBusinessImprovementDistrictAdvisoryCommittee@fortlauderdale.gov",
        source=clerk("beach-business-improvement-district-advisory-committee"),
    ),
    Board(
        name="Historic Preservation Board",
        slug="historic-preservation-board",
        ordinal=1,
        weekday=0,  # Monday
        start_hour=18,
        end_hour=20,
        location=DSD,
        contact="HistoricPreservationBoard@fortlauderdale.gov",
        note="Meets 1st Monday with exceptions; some months differ. Verify each month.",
        source=(
            "https://www.fortlauderdale.gov/government/departments-a-h/"
            "development-services/urban-design-and-planning/development-applications-"
            "boards-and-committees/historic-preservation-board"
        ),
    ),
    Board(
        name="Sustainability Advisory Board",
        slug="sustainability-advisory-board",
        ordinal=4,
        weekday=0,  # Monday
        start_hour=18,
        end_hour=20,
        location=CITY_HALL,
        contact="",
        note="4th Monday inferred from 2026 dates; time approximate. Verify each month.",
        source=clerk("sustainability-advisory-board"),
    ),
    Board(
        name="Budget Advisory Board",
        slug="budget-advisory-board",
        ordinal=3,
        weekday=2,  # Wednesday
        start_hour=17,
        end_hour=19,
        location=CITY_HALL,
        contact="BudgetAdvisoryBoard@fortlauderdale.gov",
        note="Meets roughly monthly (often 3rd Wednesday) but dates vary widely. Verify each month.",
        source=clerk("budget-advisory-board"),
    ),
    # ---- Unknown / as-needed schedules (single verify reminder) ---------
    Board(
        name="Marine Advisory Board",
        slug="marine-advisory-board",
        location=CITY_HALL,
        contact="MarineAdvisoryBoard@fortlauderdale.gov",
        source=clerk("marine-advisory-board"),
    ),
    Board(
        name="Parks, Recreation, and Beaches Board",
        slug="parks-recreation-beaches-board",
        location="Fire Station 2, 528 NW 2nd Street, 3rd Floor, Fort Lauderdale, FL 33311",
        contact="",
        source=clerk("parks-recreation-and-beaches-board"),
    ),
    Board(
        name="Affordable Housing Advisory Committee",
        slug="affordable-housing-advisory-committee",
        contact="AffordableHousingAdvisoryCommittee@fortlauderdale.gov",
        source=clerk("affordable-housing-advisory-committee"),
    ),
    Board(
        name="Fire Rescue Advisory Committee",
        slug="fire-rescue-advisory-committee",
        contact="Fire-rescueadvisorycommittee@fortlauderdale.gov",
        source=clerk("fire-rescue-advisory-committee"),
    ),
    Board(
        name="Education Advisory Board",
        slug="education-advisory-board",
        contact="EducationAdvisoryBoard@fortlauderdale.gov",
        source=clerk("education-advisory-board"),
    ),
    Board(
        name="Infrastructure Advisory Board",
        slug="infrastructure-advisory-board",
        contact="infrastructureAdvisoryBoard@fortlauderdale.gov",
        source=clerk("infrastructure-advisory-board"),
    ),
    Board(
        name="Infrastructure Task Force Advisory Committee",
        slug="infrastructure-task-force-advisory-committee",
        contact="infrastructureAdvisoryBoard@fortlauderdale.gov",
        source=clerk("infrastructure-task-force-advisory-committee"),
    ),
    Board(
        name="Noise Control Advisory Committee",
        slug="noise-control-advisory-committee",
        source=clerk("noise-control-advisory-committee"),
    ),
    Board(
        name="Nuisance Abatement Board",
        slug="nuisance-abatement-board",
        source=clerk("nuisance-abatement-board"),
    ),
    Board(
        name="Community Appearance Board",
        slug="community-appearance-board",
        contact="communityappearanceboard@fortlauderdale.gov",
        location=DSD,
        source=clerk("community-appearance-board"),
    ),
    Board(
        name="Public Art and Placemaking Advisory Board",
        slug="public-art-placemaking-advisory-board",
        contact="PublicArtAndPlacementBoard@fortlauderdale.gov",
        source=clerk("public-art-and-placemaking-advisory-board"),
    ),
    Board(
        name="Homeless Advisory Committee",
        slug="homeless-advisory-committee",
        contact="HomelessAdvisoryCommittee@fortlauderdale.gov",
        source=clerk("homeless-advisory-committee"),
    ),
    Board(
        name="Housing Authority",
        slug="housing-authority",
        source=clerk("housing-authority"),
    ),
    Board(
        name="Northwest-Progresso-Flagler Heights Redevelopment Advisory Board",
        slug="nw-progresso-flagler-heights-rac",
        source=CLERK_HUB,
    ),
    Board(
        name="Development Review Committee",
        slug="development-review-committee",
        contact="planning@fortlauderdale.gov",
        location=DSD,
        source=clerk("development-review-committee"),
    ),
    Board(
        name="Code Enforcement Board",
        slug="code-enforcement-board",
        contact="cenforcement@fortlauderdale.gov",
        source=clerk("code-enforcement-board/code-enforcement-board-archives"),
    ),
    Board(
        name="Civil Service Board",
        slug="civil-service-board",
        source=clerk("civil-service-board"),
    ),
    Board(
        name="Insurance Advisory Board",
        slug="insurance-advisory-board",
        source=CLERK_HUB,
    ),
    Board(
        name="Charter Revision Board",
        slug="charter-revision-board",
        source=CLERK_HUB,
    ),
]


def nth_weekday_on_or_after(start: date, ordinal: int, weekday: int) -> date:
    """Return the first date >= `start` that is the `ordinal`-th `weekday`
    of its month (ordinal: 1..4, or -1 for the last weekday of the month)."""
    year, month = start.year, start.month
    for _ in range(24):  # search forward up to two years; always resolves quickly
        candidate = _nth_weekday_of_month(year, month, ordinal, weekday)
        if candidate >= start:
            return candidate
        month += 1
        if month > 12:
            month = 1
            year += 1
    raise RuntimeError("could not resolve recurrence start")


def _nth_weekday_of_month(year: int, month: int, ordinal: int, weekday: int) -> date:
    if ordinal == -1:
        last_day = calendar.monthrange(year, month)[1]
        d = date(year, month, last_day)
        offset = (d.weekday() - weekday) % 7
        return d - timedelta(days=offset)
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + (ordinal - 1) * 7)


def fold(line: str) -> str:
    """Fold a content line to <=75 octets per RFC 5545 (continuation lines
    begin with a single space)."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line
    out = []
    chunk = b""
    for ch in line:
        b = ch.encode("utf-8")
        # 75 for first line; continuation lines effectively 74 (leading space)
        limit = 75 if not out else 74
        if len(chunk) + len(b) > limit:
            out.append(chunk.decode("utf-8"))
            chunk = b
        else:
            chunk += b
    out.append(chunk.decode("utf-8"))
    return "\r\n ".join(out)


def esc(text: str) -> str:
    """Escape TEXT values per RFC 5545."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def dt_local(d: date, hour: int, minute: int) -> str:
    return f"{d.year:04d}{d.month:02d}{d.day:02d}T{hour:02d}{minute:02d}00"


def vtimezone() -> list[str]:
    """A static VTIMEZONE for America/New_York (US Eastern, post-2007 DST rules)."""
    return [
        "BEGIN:VTIMEZONE",
        f"TZID:{TZID}",
        "X-LIC-LOCATION:America/New_York",
        "BEGIN:DAYLIGHT",
        "TZOFFSETFROM:-0500",
        "TZOFFSETTO:-0400",
        "TZNAME:EDT",
        "DTSTART:19700308T020000",
        "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU",
        "END:DAYLIGHT",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:-0400",
        "TZOFFSETTO:-0500",
        "TZNAME:EST",
        "DTSTART:19701101T020000",
        "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU",
        "END:STANDARD",
        "END:VTIMEZONE",
    ]


def schedule_summary(board: Board) -> str:
    if not board.recurring:
        return "Schedule: as-needed / not published - verify with the City."
    when = (
        f"Meets the {ORDINAL_NAME[board.ordinal]} {WEEKDAY_NAME[board.weekday]} "
        f"of each month at {board.start_hour % 12 or 12}:{board.start_min:02d} "
        f"{'PM' if board.start_hour >= 12 else 'AM'}."
    )
    return when


def description_lines(board: Board) -> str:
    parts = [schedule_summary(board)]
    if board.note:
        parts.append(f"Note: {board.note}")
    if board.contact:
        parts.append(f"Contact: {board.contact}")
    parts.append(f"Source: {board.source}")
    parts.append("")
    parts.append(DISCLAIMER)
    return "\\n".join(esc(p) for p in parts)


def event(board: Board, dtstamp: str) -> list[str]:
    lines = ["BEGIN:VEVENT"]
    lines.append(f"DTSTAMP:{dtstamp}")
    lines.append("STATUS:TENTATIVE")
    lines.append("TRANSP:OPAQUE")

    if board.recurring:
        first = nth_weekday_on_or_after(SEARCH_START, board.ordinal, board.weekday)
        end_hour = board.end_hour if board.end_hour is not None else board.start_hour + 1
        end_min = board.end_min if board.end_hour is not None else board.start_min
        lines.append(f"UID:{board.slug}-recurring@fortlauderdale-boards")
        lines.append(f"SUMMARY:{esc(board.name)}")
        lines.append(
            f"DTSTART;TZID={TZID}:{dt_local(first, board.start_hour, board.start_min)}"
        )
        lines.append(f"DTEND;TZID={TZID}:{dt_local(first, end_hour, end_min)}")
        token = f"{board.ordinal}{WEEKDAY_TOKEN[board.weekday]}"
        lines.append(f"RRULE:FREQ=MONTHLY;BYDAY={token}")
    else:
        # All-day single reminder to verify the schedule.
        nxt = REMINDER_DATE + timedelta(days=1)
        lines.append(f"UID:{board.slug}-verify@fortlauderdale-boards")
        lines.append(f"SUMMARY:{esc('Verify schedule - ' + board.name)}")
        lines.append(
            f"DTSTART;VALUE=DATE:{REMINDER_DATE.year:04d}"
            f"{REMINDER_DATE.month:02d}{REMINDER_DATE.day:02d}"
        )
        lines.append(
            f"DTEND;VALUE=DATE:{nxt.year:04d}{nxt.month:02d}{nxt.day:02d}"
        )

    if board.location:
        lines.append(f"LOCATION:{esc(board.location)}")
    lines.append(f"DESCRIPTION:{description_lines(board)}")
    lines.append(f"URL:{board.source}")
    lines.append("END:VEVENT")
    return lines


def build() -> str:
    dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Fort Lauderdale Advisory Boards//Calendar Generator//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Fort Lauderdale Advisory Boards",
        f"X-WR-TIMEZONE:{TZID}",
    ]
    lines += vtimezone()
    for board in BOARDS:
        lines += event(board, dtstamp)
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in lines) + "\r\n"


def main() -> None:
    ics = build()
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        f.write(ics)
    recurring = sum(1 for b in BOARDS if b.recurring)
    reminders = len(BOARDS) - recurring
    print(
        f"Wrote {OUTPUT_FILE}: {len(BOARDS)} boards "
        f"({recurring} recurring, {reminders} verify-reminders)."
    )


if __name__ == "__main__":
    main()
