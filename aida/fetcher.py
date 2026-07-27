"""Fetch and parse a job posting from a URL.

Uses the public JSON APIs of common ATS platforms (Greenhouse, Lever) when it
can, and falls back to scraping page text otherwise. This only READS a posting
— it never submits anything.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from .models import ATS, JobPosting

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None

UA = "Mozilla/5.0 (compatible; AidaJobAssistant/0.1; personal use)"


def detect_ats(url: str) -> ATS:
    host = urlparse(url).netloc.lower()
    if "greenhouse.io" in host or "grnh.se" in host:
        return ATS.GREENHOUSE
    if "lever.co" in host:
        return ATS.LEVER
    if "ashbyhq.com" in host:
        return ATS.ASHBY
    if "myworkdayjobs.com" in host or "workday" in host:
        return ATS.WORKDAY
    return ATS.GENERIC


def _require_requests():
    if requests is None:
        raise RuntimeError("The 'requests' package is required: pip install requests")


def fetch(url: str) -> JobPosting:
    ats = detect_ats(url)
    if ats == ATS.GREENHOUSE:
        return _fetch_greenhouse(url)
    if ats == ATS.LEVER:
        return _fetch_lever(url)
    return _fetch_generic(url, ats)


def _fetch_greenhouse(url: str) -> JobPosting:
    _require_requests()
    # https://boards.greenhouse.io/<board>/jobs/<id>
    m = re.search(r"greenhouse\.io/(?:embed/job_app\?token=|.*?/jobs/)?([^/?&]+)", url)
    board = re.search(r"greenhouse\.io/(?:embed/[^/]+/)?([^/]+)/jobs/", url)
    job_id = re.search(r"/jobs/(\d+)", url) or re.search(r"token=(\d+)", url)
    posting = JobPosting(url=url, ats=ATS.GREENHOUSE, apply_url=url)
    if board and job_id:
        api = (
            f"https://boards-api.greenhouse.io/v1/boards/"
            f"{board.group(1)}/jobs/{job_id.group(1)}?content=true"
        )
        try:
            data = requests.get(api, headers={"User-Agent": UA}, timeout=20).json()
            posting.title = data.get("title", "")
            posting.company = board.group(1).replace("-", " ").title()
            loc = data.get("location") or {}
            posting.location = loc.get("name", "")
            posting.description = _strip_html(data.get("content", ""))
            posting.apply_url = data.get("absolute_url", url)
            return posting
        except Exception:
            pass
    return _fetch_generic(url, ATS.GREENHOUSE)


def _fetch_lever(url: str) -> JobPosting:
    _require_requests()
    # https://jobs.lever.co/<company>/<id>
    m = re.search(r"lever\.co/([^/]+)/([0-9a-f-]+)", url)
    posting = JobPosting(url=url, ats=ATS.LEVER, apply_url=url.rstrip("/") + "/apply")
    if m:
        company, job_id = m.group(1), m.group(2)
        api = f"https://api.lever.co/v0/postings/{company}/{job_id}"
        try:
            data = requests.get(api, headers={"User-Agent": UA}, timeout=20).json()
            posting.title = data.get("text", "")
            posting.company = company.replace("-", " ").title()
            cats = data.get("categories") or {}
            posting.location = cats.get("location", "")
            posting.description = data.get("descriptionPlain", "")
            posting.apply_url = data.get("applyUrl") or posting.apply_url
            return posting
        except Exception:
            pass
    return _fetch_generic(url, ATS.LEVER)


def _fetch_generic(url: str, ats: ATS) -> JobPosting:
    _require_requests()
    posting = JobPosting(url=url, ats=ats, apply_url=url)
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        html = resp.text
    except Exception as exc:  # noqa: BLE001
        posting.description = f"(could not fetch: {exc})"
        return posting
    if BeautifulSoup is None:
        posting.description = _strip_html(html)[:8000]
        return posting
    soup = BeautifulSoup(html, "html.parser")
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        posting.title = og_title["content"]
    elif soup.title:
        posting.title = soup.title.get_text(strip=True)
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        posting.company = og_site["content"]
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    posting.description = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n")).strip()[:8000]
    return posting


def _strip_html(html: str) -> str:
    if not html:
        return ""
    if BeautifulSoup is not None:
        return BeautifulSoup(html, "html.parser").get_text("\n").strip()
    return re.sub(r"<[^>]+>", "", html).strip()
