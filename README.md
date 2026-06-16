# Fort Lauderdale Advisory Board Meetings — Calendar

A ready-to-import calendar of the **City of Fort Lauderdale, FL** advisory
boards, committees, and authorities and their meeting schedules.

- **`fort-lauderdale-advisory-boards.ics`** — the combined calendar file. Import
  this into Google Calendar, Apple Calendar, or Outlook.
- **`generate_calendar.py`** — the generator that produces the `.ics` (stdlib
  Python only, no dependencies). Edit the `BOARDS` list and re-run to update.

## ⚠️ Accuracy disclaimer

These schedules were **auto-compiled from public web sources on 2026-06-16** and
are **best-effort, not authoritative**. The City reschedules and cancels
meetings frequently, and several boards meet "as needed." Every event is marked
**TENTATIVE**. Always confirm date, time, and location before attending:

- **Legistar calendar (authoritative):** https://fortlauderdale.legistar.com/
- **City Clerk — Advisory Boards hub:** https://www.fortlauderdale.gov/government/departments-a-h/city-clerk-s-office/advisory-boards-committees-authorities-agendas-and-minutes
- **City Clerk's Office:** (954) 828-5288

## What's in the calendar

All times are **America/New_York** (Eastern, with correct EST/EDT handling).

### Recurring meetings (ongoing monthly rules)

| Board | When | Time |
|---|---|---|
| Planning and Zoning Board | 3rd Wednesday | 6:00–8:00 PM |
| Board of Adjustment | 2nd Wednesday | 6:00–8:00 PM |
| Economic Development Advisory Board | 2nd Wednesday | 3:00–5:00 PM |
| Beach BID Advisory Committee | 2nd Monday | 1:30–3:00 PM |
| Historic Preservation Board | 1st Monday* | 6:00–8:00 PM |
| Sustainability Advisory Board | 4th Monday* | 6:00–8:00 PM |
| Budget Advisory Board | ~3rd Wednesday* | 5:00–7:00 PM |

\* Schedule has known exceptions or was inferred from 2026 dates — verify each month.

### Verify-schedule reminders (as-needed / unpublished)

These boards don't publish a fixed recurrence, so the calendar includes a single
all-day **"Verify schedule — …"** reminder (2026-06-30) with each board's contact
and source link, instead of a fabricated recurring time:

Marine Advisory Board · Parks, Recreation, and Beaches Board · Affordable Housing
Advisory Committee · Fire Rescue Advisory Committee · Education Advisory Board ·
Infrastructure Advisory Board · Infrastructure Task Force Advisory Committee ·
Noise Control Advisory Committee · Nuisance Abatement Board · Community Appearance
Board · Public Art and Placemaking Advisory Board · Homeless Advisory Committee ·
Housing Authority · NW-Progresso-Flagler Heights Redevelopment Advisory Board ·
Development Review Committee · Code Enforcement Board · Civil Service Board ·
Insurance Advisory Board · Charter Revision Board

## How to import

**Google Calendar:** Settings → *Import & export* → *Import* → choose
`fort-lauderdale-advisory-boards.ics` → pick a target calendar (tip: create a
dedicated "Fort Lauderdale Boards" calendar so you can delete it in one click).

**Apple Calendar (macOS):** *File → Import…* → select the `.ics` → choose a calendar.

**Apple Calendar (iOS):** open the `.ics` from Files/Mail → *Add All*.

**Outlook:** *File → Open & Export → Import/Export → Import an iCalendar (.ics)*.

## Regenerating

```bash
python3 generate_calendar.py   # writes fort-lauderdale-advisory-boards.ics
```

To correct a schedule, edit the matching entry in the `BOARDS` list in
`generate_calendar.py`. For a recurring board set `ordinal` (1–4, or -1 for the
last), `weekday` (0=Mon … 6=Sun), and the start/end times; leave `ordinal`
unset to emit a verify-reminder instead.
