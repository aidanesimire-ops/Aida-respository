"""Entity (LLC/trust) detection and absentee-owner flagging."""

from __future__ import annotations

import re

import pandas as pd

from .config import Market

# Ordered strongest-signal first: an owner like "PALM HOLDINGS LLC" should be
# typed as LLC, not HOLDINGS, so we rank matches instead of taking the first hit.
ENTITY_TOKENS: tuple[tuple[str, str], ...] = (
    ("LLC", r"L\.?\s?L\.?\s?C\.?"),
    ("LLLP", r"L\.?L\.?L\.?P\.?"),
    ("LLP", r"L\.?L\.?P\.?"),
    ("LP", r"L\.?P\.?"),
    ("INC", r"INC(?:ORPORATED)?\.?"),
    ("CORP", r"CORP(?:ORATION)?\.?"),
    ("LTD", r"LTD\.?|LIMITED"),
    ("TRUST", r"TRUST|TRUSTEE(?:S)?|\bTR\b|\bTRS\b"),
    ("FOUNDATION", r"FOUNDATION"),
    ("PARTNERS", r"PARTNERS(?:HIP)?"),
    ("HOLDINGS", r"HOLDINGS?"),
    ("PROPERTIES", r"PROPERTIES|PROPERTY CO"),
    ("INVESTMENTS", r"INVESTMENTS?"),
    ("ENTERPRISES", r"ENTERPRISES?"),
    ("GROUP", r"GROUP"),
    ("ASSOCIATES", r"ASSOCIATES|ASSN|ASSOCIATION"),
    ("VENTURES", r"VENTURES?"),
    ("REALTY", r"REALTY"),
    ("MANAGEMENT", r"MANAGEMENT|MGMT"),
    ("CAPITAL", r"CAPITAL"),
    ("DEVELOPMENT", r"DEVELOPMENT|DEVELOPERS?"),
    ("CHURCH", r"CHURCH|MINISTRIES|TEMPLE|SYNAGOGUE"),
    ("GOVERNMENT", r"CITY OF|COUNTY OF|STATE OF|DISTRICT|AUTHORITY|SCHOOL BOARD|UNITED STATES"),
    ("COMPANY", r"\bCO\b|COMPANY"),
)

_COMPILED = [(label, re.compile(rf"(?<![A-Z0-9]){pat}(?![A-Z0-9])")) for label, pat in ENTITY_TOKENS]

# Entity types that are institutional rather than an investor to cold-call.
NON_TARGET_TYPES = frozenset({"GOVERNMENT", "CHURCH"})

FLAG_COLS = ["Entity_Type", "Entity_YN", "Absentee_YN", "Owner_Normalized"]


def entity_type(name: object) -> str:
    """Best-matching entity token for an owner name, or ``""`` for a person."""
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return ""
    text = re.sub(r"[^A-Z0-9&\s\.]", " ", str(name).upper())
    for label, pattern in _COMPILED:
        if pattern.search(text):
            return label
    return ""


def normalize_owner(name: object) -> str:
    """Upper-cased, punctuation-stripped owner name for matching/de-duping.

    Periods close up rather than split, so ``L.L.C.`` normalizes to ``LLC`` and
    matches a filing recorded as ``LLC``; every other separator becomes a space.
    """
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return ""
    text = str(name).upper().replace(".", "")
    text = re.sub(r"[^A-Z0-9&\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def absentee_flag(city: object, local_cities: tuple[str, ...]) -> str:
    """``N`` local, ``Y`` out of area, ``Unknown`` when the record has no city."""
    if city is None or (isinstance(city, float) and pd.isna(city)):
        return "Unknown"
    value = str(city).upper().strip()
    if not value:
        return "Unknown"
    return "N" if value in local_cities else "Y"


def add_flags(df: pd.DataFrame, market: Market) -> pd.DataFrame:
    """Attach entity/absentee columns. Safe to run on any stage's frame."""
    out = df.copy()
    owner_field = market.f("owner1")
    owners = out[owner_field] if owner_field in out.columns else pd.Series("", index=out.index)

    out["Owner_Normalized"] = owners.map(normalize_owner)
    out["Entity_Type"] = owners.map(entity_type)
    out["Entity_YN"] = out["Entity_Type"].map(lambda t: "Y" if t else "N")

    city_field = market.f("mailcity")
    cities = out[city_field] if city_field in out.columns else pd.Series(None, index=out.index)
    local = market.local_cities
    out["Absentee_YN"] = cities.map(lambda c: absentee_flag(c, local))
    return out


def callable_entities(df: pd.DataFrame) -> pd.Series:
    """Mask of entity-owned rows worth resolving (skips city/church-owned)."""
    if "Entity_YN" not in df.columns:
        return pd.Series(False, index=df.index)
    return (df["Entity_YN"] == "Y") & ~df["Entity_Type"].isin(NON_TARGET_TYPES)
