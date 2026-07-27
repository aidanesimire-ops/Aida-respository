"""Fetch and parse a job posting from a URL.

Uses the public Greenhouse and Lever APIs where possible (structured, reliable),
and falls back to plain HTML parsing for everything else.
"""

from __future__ import annotations

import html
import re
from urllib.parse import urlparse

from .models import JobPosting, ATS

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None

USER_AGENT = (
    "Mozilla/5.0 (compatible; AidaJobAssistant/0.1; personal job-search use)"
)


def _require_requests():
    if requests is None:
        raise RuntimeError("The 'requests' package is required. pip install requests")


def detect_ats(url: str) -> ATS:
    host = (urlparse(url).hostname or "").lower()
    if "greenhouse.io" in host:
        return ATS.GREENHOUSE
    if "lever.co" in host:
        return ATS.LEVER
    if "ashbyhq.com" in host:
        return ATS.ASHBY
    if "myworkdayjobs.com" in host or "workday" in host:
        return ATS.WORKDAY
    return ATS.GENERIC


def _strip_html(raw: str) -> str:
    if not raw:
        return ""
    if BeautifulSoup is not None:
        text = BeautifulSoup(raw, "html.parser").get_text("\n")
    else:
        text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _fetch_greenhouse(url: str) -> JobPosting:
    # e.g. https://boards.greenhouse.io/{board}/jobs/{id}
    #      https://job-boards.greenhouse.io/{board}/jobs/{id}
    m = re.search(r"greenhouse\.io/(?:embed/job_app\?token=|[^/]*/)?([^/]+)/jobs/(\d+)", url)
    board = job_id = None
    if m:
        board, job_id = m.group(1), m.group(2)
    else:
        m2 = re.search(r"token=(\d+)", url)
        if m2:
            job_id = m2.group(1)
    if not (board and job_id):
        return _fetch_generic(url, ATS.GREENHOUSE)
    _require_requests()
    api = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}?content=true"
    r = requests.get(api, headers={"User-Agent": USER_AGENT}, timeout=20)
    r.raise_for_status()
    d = r.json()
    return JobPosting(
        url=url,
        ats=ATS.GREENHOUSE,
        company=board.replace("-", " ").title(),
        title=d.get("title", ""),
        location=(d.get("location") or {}).get("name", ""),
        description=_strip_html(d.get("content", "")),
        apply_url=d.get("absolute_url", url),
    )


def _fetch_lever(url: str) -> JobPosting:
    # e.g. https://jobs.lever.co/{company}/{id}
    m = re.search(r"lever\.co/([^/]+)/([0-9a-f\-]{6,})", url)
    if not m:
        return _fetch_generic(url, ATS.LEVER)
    company, job_id = m.group(1), m.group(2)
    _require_requests()
    api = f"https://api.lever.co/v0/postings/{company}/{job_id}"
    r = requests.get(api, headers={"User-Agent": USER_AGENT}, timeout=20)
    r.raise_for_status()
    d = r.json()
    cats = d.get("categories", {}) or {}
    return JobPosting(
        url=url,
        ats=ATS.LEVER,
        company=company.replace("-", " ").title(),
        title=d.get("text", ""),
        location=cats.get("location", ""),
        description=d.get("descriptionPlain") or _strip_html(d.get("description", "")),
        apply_url=d.get("applyUrl") or (url.rstrip("/") + "/apply"),
    )


def _fetch_generic(url: str, ats: ATS = ATS.GENERIC) -> JobPosting:
    _require_requests()
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=25)
    r.raise_for_status()
    title = ""
    description = ""
    if BeautifulSoup is not None:
        soup = BeautifulSoup(r.text, "html.parser")
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            title = og["content"].strip()
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        main = soup.find("main") or soup.body or soup
        description = _strip_html(str(main))
    else:
        m = re.search(r"<title[^>]*>(.*?)</title>", r.text, re.I | re.S)
        title = m.group(1).strip() if m else ""
        description = _strip_html(r.text)
    return JobPosting(
        url=url, ats=ats, title=title,
        description=description[:8000], apply_url=url,
    )


def fetch(url: str) -> JobPosting:
    """Fetch a posting, dispatching on the detected ATS."""
    ats = detect_ats(url)
    if ats == ATS.GREENHOUSE:
        return _fetch_greenhouse(url)
    if ats == ATS.LEVER:
        return _fetch_lever(url)
    return _fetch_generic(url, ats)
