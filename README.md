# Aida — personal job-application assistant

A tool that helps **Aida Nesimi** apply to jobs faster. You give it a job link;
it pulls the posting, writes a cover letter tailored to that exact role, opens
the application form in your browser, fills your details, and attaches your
documents. By default it **stops so you can review before submitting**.

> **Important:** this runs on *your* computer and drives *your* browser. It can't
> be run "for you" from the cloud — driving a browser requires being on the same
> machine as the browser. Setup is a one-time ~10 minutes.

## What it does / doesn't do

- ✅ Fetches and summarizes a posting (Greenhouse & Lever get clean structured data)
- ✅ Writes a role-specific cover letter (uses Claude if `ANTHROPIC_API_KEY` is set, else a strong template)
- ✅ Fills standard application fields and uploads your resume
- ✅ Tracks every application so nothing slips
- ✅ Review-before-submit by default; `--submit` when you want it to submit
- ❌ No CAPTCHA-solving, no stealth/anti-bot tricks (those get accounts banned)
- ❌ Can't reliably automate every site — some (heavy Workday/LinkedIn flows) it
  fills what it can, screenshots, and hands off to you

## One-time setup

```bash
# 1. Get the code
git clone <this repo>            # or download it
cd Aida-respository

# 2. Install dependencies
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# 3. Add your profile + documents
cp config/profile.example.yaml config/profile.yaml   # then edit it
#   (a real profile.yaml for Aida is already included and is gitignored)
# put your files in documents/ — see documents/README.md for the names

# 4. (Optional) Claude-written cover letters
export ANTHROPIC_API_KEY=sk-ant-...     # Windows: set ANTHROPIC_API_KEY=...
```

## Daily use

```bash
# See what a posting is before doing anything
python -m aida fetch  "https://jobs.lever.co/acme/1234"

# Just write me a tailored cover letter for this role
python -m aida tailor "https://boards.greenhouse.io/acme/jobs/5678"

# Full run: fetch + tailor + fill the form, then let me review & submit
python -m aida apply  "https://boards.greenhouse.io/acme/jobs/5678"

# Same, but submit automatically (only where the site allows it)
python -m aida apply  "https://boards.greenhouse.io/acme/jobs/5678" --submit

# What have I applied to?
python -m aida list
```

Generated cover letters and form screenshots land in `outputs/` (gitignored).
The application log lives in `applications.db` (gitignored).

## Privacy

`config/profile.yaml`, everything in `documents/`, `outputs/`, `applications.db`,
and `.env` are all **gitignored** — your phone number, email, resume, and
recommendation letter never get pushed to GitHub.
