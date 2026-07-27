# Aida — Personal Job-Application Assistant

A small tool that helps apply to jobs faster. It runs **on your own computer**,
drives **your own browser**, fills application forms from your saved profile and
documents, and pauses for you to review before anything is submitted.

## What it can and can't do (read this first)

**It can:**
- Read a job posting from a link (Greenhouse, Lever, and most public postings).
- Write a cover letter tailored to that specific role.
- Open the application page in a real browser and fill the fields it recognizes
  (name, email, phone, LinkedIn, etc.).
- Attach your resume, cover letter, recommendation letter, and work samples.
- Keep a tracker (`applications.csv`) of everything, openable in Excel/Sheets.

**It can't (by design or reality):**
- **Be run from the cloud against your accounts.** It has to run locally,
  because that's the only way it can use *your* logged-in browser sessions.
- **Beat CAPTCHAs, login walls, or bot-detection.** On sites that use those
  (many big boards), it fills what it can and hands off to you — it does not try
  to evade detection, which is what gets accounts banned.
- **Answer legal attestations for you.** Work authorization, sponsorship, and
  EEO questions are left blank unless *you* set them in your profile.

**Auto-submit is off by default.** `aida apply <url>` fills the form and waits
for you to review and submit. Pass `--submit` only when you want it to click
submit for you.

## Setup (one time)

```bash
pip install -r requirements.txt
playwright install chromium

cp profile.example.yaml private/profile.yaml   # then edit it
# put your resume/cover letter/etc. in private/documents/
python -m aida init                            # verify everything is wired up
```

Your profile and documents live under `private/`, which is **gitignored** —
nothing personal is ever committed.

## Everyday use

```bash
# Just write a tailored cover letter for a posting
python -m aida tailor "https://boards.greenhouse.io/acme/jobs/123"

# Fill the application in your browser, then review + submit yourself
python -m aida apply "https://jobs.lever.co/acme/abc-123"

# Fill AND auto-submit (use with care, only where you trust it)
python -m aida apply "https://jobs.lever.co/acme/abc-123" --submit

# See everything you've applied to
python -m aida list
```

## Layout

```
aida/            the tool (committed)
  fetcher.py     read + parse a posting
  tailor.py      write a cover letter
  filler.py      drive the browser and fill the form
  tracker.py     applications.csv read/write
  cli.py         command-line interface
profile.example.yaml   template (committed)
private/         YOUR profile + documents + tracker (gitignored, never pushed)
```
