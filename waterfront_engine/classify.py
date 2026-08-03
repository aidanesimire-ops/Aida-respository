"""Split a parcel set into asset classes by DOR use code + keyword rules."""

from __future__ import annotations

import logging

import pandas as pd

from .config import AssetClass, Market

log = logging.getLogger(__name__)


def normalize_use(series: pd.Series) -> pd.Series:
    """Use codes come back as ``1``, ``01``, ``01.0``, ``'0100'`` — normalize.

    Numeric-looking codes are zero-padded to two digits so ``1`` and ``01``
    compare equal; longer detail codes (``0100``) keep their full value and are
    matched by prefix.
    """
    s = series.astype("string").fillna("").str.strip().str.upper()
    s = s.str.replace(r"\.0+$", "", regex=True)  # 1.0 -> 1
    return s.where(~s.str.fullmatch(r"\d"), s.str.zfill(2))


def match_codes(use: pd.Series, codes: list[str] | tuple[str, ...], match: str = "exact") -> pd.Series:
    """Boolean mask of rows whose use code is in ``codes``."""
    norm = normalize_use(use)
    wanted = [str(c).strip().upper() for c in codes if str(c).strip()]
    if not wanted:
        return pd.Series(False, index=use.index)

    if match == "prefix":
        pattern = "|".join(f"(?:{c})" for c in sorted(set(wanted)))
        return norm.str.match(pattern).fillna(False)

    expanded: set[str] = set()
    for code in wanted:
        expanded.add(code)
        if code.isdigit():
            expanded.add(code.zfill(2))
            expanded.add(code.lstrip("0") or "0")
    return norm.isin(expanded)


def use_text(df: pd.DataFrame, market: Market) -> pd.Series:
    """Concatenated use description + detail, upper-cased, for keyword rules."""
    parts: list[pd.Series] = []
    for key in ("f_usedesc", "f_usedetail"):
        name = market.fields.get(key)
        if name and name in df.columns:
            parts.append(df[name].astype("string").fillna(""))
    if not parts:
        return pd.Series("", index=df.index, dtype="string")
    text = parts[0]
    for extra in parts[1:]:
        text = text.str.cat(extra, sep=" ")
    return text.str.upper()


def class_mask(df: pd.DataFrame, asset: AssetClass, market: Market) -> pd.Series:
    """Rows belonging to one asset class, including the medical/office carve-out."""
    use = df[market.f("use")]
    mask = match_codes(use, asset.codes, market.code_match)

    if asset.include_kw_from and asset.include_kw:
        text = use_text(df, market)
        borrowed = match_codes(use, asset.include_kw_from, market.code_match) & text.str.contains(
            asset.include_kw, regex=True, na=False
        )
        mask = mask | borrowed

    if asset.exclude_kw:
        text = use_text(df, market)
        mask = mask & ~text.str.contains(asset.exclude_kw, regex=True, na=False)

    return mask.fillna(False)


def split_asset_classes(
    df: pd.DataFrame,
    asset_classes: dict[str, AssetClass],
    market: Market,
) -> dict[str, pd.DataFrame]:
    """Split parcels into ``{class_key: frame}``, tagging group/class columns."""
    out: dict[str, pd.DataFrame] = {}
    for key, asset in asset_classes.items():
        bucket = df[class_mask(df, asset, market)].copy()
        bucket["Asset_Class"] = asset.label
        bucket["Asset_Group"] = asset.group
        out[key] = bucket
        log.info("%-18s %6d parcels", asset.label, len(bucket))
    return out


def overlap_report(
    buckets: dict[str, pd.DataFrame],
    asset_classes: dict[str, AssetClass],
    market: Market,
) -> pd.DataFrame:
    """Parcels landing in more than one asset class (QA: de-dupe by folio)."""
    folio = market.f("folio")
    rows: list[dict[str, object]] = []
    for key, frame in buckets.items():
        if folio not in frame.columns:
            continue
        label = asset_classes[key].label
        for value in frame[folio].dropna().astype(str):
            rows.append({"Folio": value, "Asset Class": label})
    if not rows:
        return pd.DataFrame(columns=["Folio", "Asset Classes", "Count"])

    tidy = pd.DataFrame(rows).drop_duplicates()
    grouped = (
        tidy.groupby("Folio")["Asset Class"]
        .agg(lambda s: " | ".join(sorted(set(s))))
        .reset_index()
        .rename(columns={"Asset Class": "Asset Classes"})
    )
    grouped["Count"] = grouped["Asset Classes"].str.count(r"\|") + 1
    return (
        grouped[grouped["Count"] > 1]
        .sort_values(["Count", "Folio"], ascending=[False, True])
        .reset_index(drop=True)
    )


def use_code_census(df: pd.DataFrame, market: Market) -> pd.DataFrame:
    """Value-count of use codes with descriptions — the 'did a code move buckets?' QA."""
    use = normalize_use(df[market.f("use")])
    desc_field = market.opt("usedesc")
    frame = pd.DataFrame({"DOR Use": use})
    if desc_field and desc_field in df.columns:
        frame["Use Description"] = df[desc_field].astype("string").fillna("")
    else:
        frame["Use Description"] = ""
    census = (
        frame.groupby("DOR Use")
        .agg(Parcels=("Use Description", "size"), Example=("Use Description", "first"))
        .reset_index()
        .sort_values("Parcels", ascending=False)
        .reset_index(drop=True)
    )
    return census
