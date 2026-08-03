"""Entity resolution — Sunbiz (FL) live lookup, disk cache, and bulk-file match.

Two ways to fill the manager / registered-agent columns:

* :class:`SunbizClient` — polite live lookups against ``search.sunbiz.org``.
  Fine for a few thousand entities; every result is cached to disk so a rerun
  costs nothing.
* :class:`BulkEntityIndex` — match against a pre-parsed export of the free
  Sunbiz corporate data file. No rate limit, and the right answer at volume.

Swap in another state by writing a class with the same ``lookup(name) -> dict``
shape (OpenCorporates, a Secretary of State search, …) and passing it to the
pipeline; nothing else in the engine is Florida-specific.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Iterable, Protocol

import pandas as pd
import requests

from .flags import normalize_owner

log = logging.getLogger(__name__)

BASE = "https://search.sunbiz.org"
SEARCH_URL = f"{BASE}/Inquiry/CorporationSearch/SearchResults"

ENRICHMENT_COLS = [
    "Sunbiz_Entity",
    "Sunbiz_Status",
    "Sunbiz_DocNumber",
    "Registered_Agent",
    "Managers_Members",
    "Sunbiz_Principal_Address",
    "Sunbiz_URL",
]

_MANAGER_HEADINGS = ("authorized person", "officer/director", "officer / director", "general partner")
_AGENT_HEADINGS = ("registered agent",)


class EntityResolver(Protocol):
    """Anything that can turn an owner name into enrichment columns."""

    def lookup(self, name: str) -> dict[str, str]: ...


class SunbizClient:
    """Live Sunbiz search with on-disk caching and a fixed request delay."""

    def __init__(
        self,
        cache_path: str | Path = "data/sunbiz_cache.json",
        *,
        delay: float = 1.6,
        timeout: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.cache_path = Path(cache_path)
        self.delay = delay
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.setdefault(
            "User-Agent", "Mozilla/5.0 (compatible; DAWNRE-research/1.0)"
        )
        self.cache: dict[str, dict[str, str]] = {}
        if self.cache_path.exists():
            try:
                self.cache = json.loads(self.cache_path.read_text())
                log.info("sunbiz cache: %d entries", len(self.cache))
            except json.JSONDecodeError:
                log.warning("sunbiz cache unreadable, starting fresh: %s", self.cache_path)
        self._last_call = 0.0

    # -- public ----------------------------------------------------------
    def lookup(self, name: str) -> dict[str, str]:
        key = normalize_owner(name)
        if not key:
            return {}
        if key in self.cache:
            return self.cache[key]
        result = self._lookup_live(name)
        self.cache[key] = result
        return result

    def save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=1, sort_keys=True))

    def enrich(self, names: Iterable[str], *, save_every: int = 25) -> dict[str, dict[str, str]]:
        """Resolve many names, checkpointing the cache as it goes."""
        results: dict[str, dict[str, str]] = {}
        pending = [n for n in dict.fromkeys(names) if normalize_owner(n)]
        for i, name in enumerate(pending, start=1):
            results[name] = self.lookup(name)
            if i % save_every == 0:
                self.save_cache()
                log.info("sunbiz %d/%d", i, len(pending))
        self.save_cache()
        return results

    # -- internals -------------------------------------------------------
    def _throttle(self) -> None:
        wait = self.delay - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()

    def _lookup_live(self, name: str) -> dict[str, str]:
        try:
            self._throttle()
            resp = self.session.get(
                SEARCH_URL,
                params={"inquiryType": "EntityName", "searchTerm": name},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            candidate = pick_candidate(parse_search_results(resp.text), name)
            if not candidate:
                return {"Sunbiz_Entity": "NO MATCH"}

            url = candidate["url"]
            self._throttle()
            detail = self.session.get(url, timeout=self.timeout)
            detail.raise_for_status()
            parsed = parse_detail(detail.text)
            parsed.setdefault("Sunbiz_Entity", candidate.get("name", ""))
            parsed.setdefault("Sunbiz_Status", candidate.get("status", ""))
            parsed.setdefault("Sunbiz_DocNumber", candidate.get("doc_number", ""))
            parsed["Sunbiz_URL"] = url
            return parsed
        except requests.RequestException as exc:
            log.warning("sunbiz lookup failed for %r: %s", name, exc)
            return {"Sunbiz_Entity": f"ERROR: {exc}"}


class BulkEntityIndex:
    """Name-matched index over a pre-parsed Sunbiz corporate data export.

    Point it at a CSV/parquet with an entity-name column plus whichever of
    manager / registered-agent / status / document-number columns you have; the
    match is on the normalized name, same normalization the parcel side uses.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        name_col: str = "entity_name",
        managers_col: str | None = "managers",
        agent_col: str | None = "registered_agent",
        status_col: str | None = "status",
        doc_col: str | None = "document_number",
        address_col: str | None = None,
    ) -> None:
        path = Path(path)
        frame = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path, dtype=str)
        if name_col not in frame.columns:
            raise ValueError(f"{path} has no column {name_col!r}; found {list(frame.columns)}")
        frame = frame.assign(_key=frame[name_col].map(normalize_owner))
        frame = frame[frame["_key"] != ""].drop_duplicates("_key", keep="first")

        self._cols = {
            "Sunbiz_Entity": name_col,
            "Managers_Members": managers_col,
            "Registered_Agent": agent_col,
            "Sunbiz_Status": status_col,
            "Sunbiz_DocNumber": doc_col,
            "Sunbiz_Principal_Address": address_col,
        }
        self._index = frame.set_index("_key")
        log.info("bulk entity index: %d entities from %s", len(self._index), path)

    def lookup(self, name: str) -> dict[str, str]:
        key = normalize_owner(name)
        if not key or key not in self._index.index:
            return {"Sunbiz_Entity": "NO MATCH"}
        row = self._index.loc[key]
        out: dict[str, str] = {}
        for out_col, src in self._cols.items():
            if src and src in self._index.columns:
                value = row[src]
                out[out_col] = "" if pd.isna(value) else str(value)
        return out


# -- HTML parsing --------------------------------------------------------
def parse_search_results(html: str) -> list[dict[str, str]]:
    """Rows from a Sunbiz search-results page."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []
    for tr in soup.select("table tbody tr"):
        link = tr.find("a", href=True)
        if not link:
            continue
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        href = link["href"]
        rows.append(
            {
                "name": link.get_text(" ", strip=True),
                "url": href if href.startswith("http") else BASE + href,
                "doc_number": cells[1] if len(cells) > 1 else "",
                "status": cells[2] if len(cells) > 2 else "",
            }
        )
    return rows


def pick_candidate(rows: list[dict[str, str]], name: str) -> dict[str, str] | None:
    """Exact normalized name wins; then an ACTIVE filing; then the first row."""
    if not rows:
        return None
    key = normalize_owner(name)
    exact = [r for r in rows if normalize_owner(r["name"]) == key]
    pool = exact or rows
    # equality, not substring: "INACTIVE" contains "ACTIVE"
    active = [r for r in pool if r.get("status", "").strip().upper() == "ACTIVE"]
    return (active or pool)[0]


def parse_detail(html: str) -> dict[str, str]:
    """Pull agent / managers / status / address off a Sunbiz detail page.

    Sunbiz renders each block as ``div.detailSection`` with the heading in the
    first ``span``. Headings drift, so anything unrecognised is ignored rather
    than mis-filed, and a regex fallback catches status/document number.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    out: dict[str, str] = {}
    sections = soup.select("div.detailSection") or soup.select("div.searchResultDetail div")

    for section in sections:
        text_lines = [ln.strip() for ln in section.get_text("\n").split("\n") if ln.strip()]
        if not text_lines:
            continue
        heading = text_lines[0].lower().rstrip(":")
        body = text_lines[1:]
        if any(h in heading for h in _AGENT_HEADINGS):
            out["Registered_Agent"] = " | ".join(body[:6])
        elif any(h in heading for h in _MANAGER_HEADINGS):
            out["Managers_Members"] = " | ".join(body[:20])
        elif heading.startswith("principal address"):
            out["Sunbiz_Principal_Address"] = " | ".join(body[:4])
        elif heading.startswith("filing information") or heading.startswith("detail"):
            paired = _pairs(body)
            if "document number" in paired:
                out["Sunbiz_DocNumber"] = paired["document number"]
            if "status" in paired:
                out["Sunbiz_Status"] = paired["status"]

    full = soup.get_text("\n")
    if "Sunbiz_DocNumber" not in out:
        m = re.search(r"Document Number\s*\n?\s*([A-Z0-9-]+)", full)
        if m:
            out["Sunbiz_DocNumber"] = m.group(1)
    if "Sunbiz_Status" not in out:
        m = re.search(r"\bStatus\s*\n?\s*(ACTIVE|INACTIVE|[A-Z ]{3,20})", full)
        if m:
            out["Sunbiz_Status"] = m.group(1).strip()

    title = soup.select_one("div.detailSection span, h2, h3")
    if title and "Sunbiz_Entity" not in out:
        candidate = title.get_text(" ", strip=True)
        if candidate and "detail" not in candidate.lower():
            out["Sunbiz_Entity"] = candidate
    return out


def _pairs(lines: list[str]) -> dict[str, str]:
    """``[label, value, label, value]`` → ``{label.lower(): value}``."""
    known = {"document number", "fei/ein number", "date filed", "state", "status", "last event"}
    out: dict[str, str] = {}
    for i, line in enumerate(lines[:-1]):
        if line.lower().rstrip(":") in known:
            out[line.lower().rstrip(":")] = lines[i + 1]
    return out


def apply_enrichment(
    df: pd.DataFrame,
    resolver: EntityResolver,
    *,
    mask: pd.Series | None = None,
    owner_field: str = "OWNERNME1",
) -> pd.DataFrame:
    """Add Sunbiz columns for the masked rows, one lookup per distinct owner."""
    out = df.copy()
    for col in ENRICHMENT_COLS:
        if col not in out.columns:
            out[col] = ""

    if owner_field not in out.columns:
        log.warning("owner field %r missing — skipping enrichment", owner_field)
        return out

    target = out if mask is None else out[mask]
    names = [n for n in target[owner_field].dropna().astype(str).unique() if n.strip()]
    if not names:
        return out

    log.info("resolving %d distinct entity owners", len(names))
    resolved = {name: resolver.lookup(name) for name in names}
    if hasattr(resolver, "save_cache"):
        resolver.save_cache()  # type: ignore[attr-defined]

    for col in ENRICHMENT_COLS:
        values = target[owner_field].astype(str).map(lambda n: resolved.get(n, {}).get(col, ""))
        out.loc[target.index, col] = values
    return out
