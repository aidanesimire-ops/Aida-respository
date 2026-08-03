"""
export_inputs.py — emit the model's INPUT CONTRACT as machine-readable JSON.

Run:  python3 export_inputs.py   ->   writes ../model_inputs.json

This is the integration surface for a developer plugging the model into their own
systems: one structured, typed, source-flagged document of every input the model
consumes, plus the key named outputs it produces. It is GENERATED FROM THE SAME
SOURCE the workbook builder reads (tab_assumptions.GLOBAL_SECTIONS, the per-asset
_blocks(), configs, data, the office roster, the land block), so it can never drift
from the model. Regenerate it whenever inputs change; diff it in code review.
"""
import json, os
import tab_assumptions
from tab_assumptions import GLOBAL_SECTIONS, _blocks
from mblib import (F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM, F_NUM2, F_YR)
from data import PARCELS, SH, MKT
from configs import PUBLIX_CFG, KARLUEN_CFG
from tab_office import A as OFFICE_A, OWNERS
from tab_land import A as LAND_A

OUT = "../model_inputs.json"
TEMPLATE = "../overrides.template.json"
OVERRIDES = "../overrides.json"

# The fill-in-the-blanks list: inputs we do NOT yet have solid data for, or that are
# modeled and worth confirming. Each becomes an entry in overrides.json with its
# current value + a status telling you what it is and where to get the real number.
# scope is "global" (patch by driver name) or "asset:<name>" (patch by dict key).
GAP_STATUS = [
    ("global", "SUN_ACQ", "⚠️ REPORTED — Kar Luen last recorded sale (Oct 2000, $128k — implausibly low, likely nominal). Get a recent basis/appraisal at BCPA / Clerk."),
    ("global", "OFF_ACQ", "✅ VERIFIED — Main St Fund (Grove Gate) 57.4% / 96,930 SF for $10M, 09/23/2019 (Daily Business Review). Confirm current sub-folios at BCPA."),
    ("global", "LND_ACQ", "✅ VERIFIED — Procacci/BBX bought 2014 for ~$7.9–8.0M; BBX exited 2022 (Florida YIMBY). Confirm the recorded deed."),
    ("global", "CAP", "🔶 MODELED — blended going-in cap. Set from an appraisal / broker BOV, or derive from the individual asset caps."),
    ("global", "SCAP", "🔶 MODELED — blended stabilized / exit cap. Set from sale comps."),
    ("global", "RATE", "🔶 MODELED — senior rate. Replace with a lender term sheet."),
    ("global", "LTV", "🔶 MODELED — max senior LTV. Replace with a lender term sheet."),
    ("global", "PREM_BASE", "🔶 MODELED — assemblage premium (base). Refine from holdout negotiations."),
    ("global", "ELIFT", "🔶 MODELED — entitlement lift %. Confirm after Live Local approval."),
    ("global", "LPSF_BASE", "🔶 MODELED — land $/SF (base). Confirm with recent land comps."),
    ("global", "UNIT_BASE", "🔶 MODELED — value per entitled unit (base). Confirm with entitled-land comps."),
    ("global", "REVUNIT", "🔶 MODELED — achievable value per finished unit. Confirm with sellout / rental comps."),
    ("global", "HARDPSF", "🔶 MODELED — hard cost $/GBA SF (AE-zone coastal). Confirm with a GC / estimator."),
    ("asset:sunrise", "price", "⚠️ REPORTED ~$8.5M — no recent arm's-length sale. VERIFY at BCPA / broker."),
    ("asset:sunrise", "gla", "⚠️ REPORTED (LoopNet) — confirm building SF at BCPA."),
    ("asset:sunrise", "land_sf", "⚠️ REPORTED — confirm land SF at BCPA."),
    ("asset:sunrise", "occ0", "🔶 ESTIMATED occupancy — confirm from the actual rent roll."),
    ("asset:sunrise", "market_rent", "🔶 ESTIMATED $/SF NNN — confirm from leases / corridor comps."),
    ("asset:office", "gla", "✅ VERIFIED 168,807 SF, 13-story (Avison Young / LoopNet). Confirm aggregate of Grove Gate sub-folios at BCPA."),
    ("asset:office", "occ0", "🔶 ESTIMATED occupancy — confirm from the rent roll."),
    ("asset:office", "market_rent", "✅ ~$25–26/SF Modified Gross (LoopNet listing). Confirm from actual leases."),
    ("asset:office", "opex_psf", "🔶 MODELED office opex $/SF — confirm from operating statements."),
    ("asset:office", "sale_comp_psf", "⚠️ REPORTED ~$300/SF (historical) — confirm from recent unit sales."),
    ("asset:office", "price", "🔶 MODELED income basis — confirm the underwritten target."),
    ("asset:land", "price", "⚠️ Bayview SOLD to Willow Bridge for $24.7M (~Aug 2026) — basis reset to that trade; now a JV target, not a fee purchase. Verify at the county."),
    ("asset:land", "land_sf", "⚠️ REPORTED — confirm at BCPA."),
    ("asset:land", "office_sf", "⚠️ CONFLICT — 84,495 SF (Redfin, leasable) vs 101,803 SF (BCPA living area). Confirm rentable SF."),
    ("asset:land", "units", "✅ 259 units (247 market + 12 affordable), case UDP-Z25002 'The Residences at Bayview' (Florida YIMBY / City staff report). Confirm FINAL P&Z / Commission approval."),
    ("asset:land", "bcpa_value", "⚠️ 2015 assessed ~$8.25M (stale mirror); current just value NOT confirmed — verify at BCPA."),
    ("asset:land", "interim_occ", "🔶 MODELED interim occupancy — confirm from the rent roll."),
    ("asset:land", "interim_rent", "🔶 MODELED interim office rent — confirm from leases."),
    ("asset:publix", "price", "✅ VERIFIED 2025 deed $25M — but the leaseback structure below is hypothetical."),
    ("asset:publix", "slb_rent", "🔶 HYPOTHETICAL leaseback rent — Publix is a fee owner, not a seller. Confirm any real leaseback terms."),
    ("asset:publix", "slb_sf", "🔶 Publix leaseback SF — confirm."),
    ("asset:publix", "sbux_rent", "🔶 ESTIMATED Starbucks pad rent — confirm."),
    ("asset:publix", "term", "🔶 ASSUMED leaseback / entitlement term (years) — confirm."),
]

_OVR_README = ("FILL-IN-THE-BLANKS for real data. Put a confirmed number in any 'value' "
               "field, then rebuild: cd model_src && python3 build_model.py. The 'status' "
               "text says what each field is and where to get it. Ratios are decimals "
               "(0.065 = 6.5%). Unlisted or unchanged fields keep the model's current "
               "assumption — nothing breaks if you leave a field alone. This file is yours: "
               "regenerating overrides.template.json never overwrites it. Add any other "
               "input here too — 'global' patches by driver name (see model_inputs.json), "
               "'assets.<asset>' patches by input key.")

# number-format string -> (unit label, json type)
UNIT = {
    F_ACCT: ("USD", "number"), F_ACCT_TOP: ("USD", "number"),
    F_PCT1: ("ratio (0-1)", "number"), F_PCT2: ("ratio (0-1)", "number"),
    F_MULT: ("multiple (x)", "number"), F_PSF: ("USD/SF", "number"),
    F_NUM: ("count/SF", "number"), F_NUM2: ("count/SF", "number"),
    F_YR: ("years", "number"),
}
FLAG = {"✅": "VERIFIED", "⚠️": "REPORTED", "🔶": "MODELED", "🟢": "LINK"}

CONF = {  # confidence per confidence code, for the conventions block
    "VERIFIED": "public record — BCPA / FL Sunbiz / recorded deed",
    "REPORTED": "counterparty / broker listing / press — unconfirmed at the county",
    "MODELED": "assumption from market research; moves with the inputs",
    "ESTIMATED": "market-research triangulation",
}

# per-asset value-driver confidence hints (keys that are county-verifiable vs modeled)
ASSET_META = {
    "shahidi": ("Shahidi Retail (Galleria Plaza)", "Shahidi Retail", "VERIFIED"),
    "publix":  ("Publix + Starbucks (sale-leaseback)", "Publix & Starbucks", "VERIFIED"),
    "sunrise": ("Sunrise Plaza (Kar Luen)", "Sunrise Plaza", "REPORTED"),
    "office":  ("Galleria Corporate Centre (office condo)", "Office Condo", "REPORTED"),
    "land":    ("1040 Bayview (JV upside)", "Bayview JV", "REPORTED"),
}

# key OUTPUT cells the model produces (named registry cell -> plain-English meaning)
OUTPUTS = {
    "Income Valuation": {
        "PX_INCOME": "concluded income-based purchase price (as-is NOI ÷ blended cap)",
        "ASIS_NOI": "consolidated as-is in-place NOI",
        "STAB_NOI": "consolidated stabilized NOI",
        "LOAN": "sized senior loan (lesser of LTV/DSCR/DY)",
        "EQ_I": "sponsor equity at the income price",
        "IRRL_I": "levered portfolio IRR at income price",
        "IRRU_I": "unlevered portfolio IRR at income price",
        "EML_I": "levered equity multiple at income price",
        "DSCR_I": "year-1 DSCR at income price",
        "BE_EXITCAP": "break-even exit cap (return of capital)",
        "PREMIUM": "covered-land price − income price (dirt + optionality)",
        "IRRL_H": "levered IRR at the covered-land price (negative by design)",
    },
    "Assemblage": {
        "RAW_COST": "sum of per-asset control costs (sum-of-parts)",
        "ACQ": "covered-land acquisition price (sum-of-parts × (1+premium))",
        "TOT_NOI": "total in-place NOI across the block",
        "BLEND_CAP2": "blended in-place cap (NOI ÷ control cost)",
        "TOT_AC": "total land assembled (acres)",
        "BLEND_LANDPSF": "blended land basis ($/SF)",
    },
    "Highest & Best Use": {
        "SUM_PARTS": "sum-of-parts control cost",
        "LAND_FRAG": "land value as fragmented parcels",
        "LAND_ASM": "land value assembled (plottage)",
        "PLOTTAGE": "plottage premium (assembled − fragmented)",
        "LAND_ENTITLED": "post-Live-Local entitled land value",
        "RESID": "redevelopment residual land value (negative → HOLD)",
    },
    "Office Condo": {
        "BUYOUT_TOTAL": "full condo buy-out at unit-market $/SF",
        "FRAG_PREM": "fragmentation premium (buy-out − income value)",
    },
}


def _driver(name, label, val, fmt, flag=None, note=""):
    unit, jtype = UNIT.get(fmt, ("", "number"))
    d = {"key": name, "label": label.strip(), "value": val,
         "unit": unit, "type": jtype}
    if flag:
        d["confidence"] = FLAG.get(flag, flag)
    if note:
        d["drives"] = note
    return d


def build():
    doc = {
        "meta": {
            "model": "E Sunrise Blvd Assemblage — covered land play",
            "owner": "DAWN RE Enterprises Corp.",
            "location": "Fort Lauderdale, FL 33304 · Galleria hard corner · plat 49-42-36-12",
            "generated_by": "export_inputs.py",
            "note": "Generated from the model source; regenerate after any input change.",
        },
        "conventions": {
            "confidence": CONF,
            "ratios": "all caps/rates/percentages are decimals (0.065 = 6.5%)",
            "control_surface": "the 'global' block + per-asset 'inputs' are the Assumptions "
                               "control tab (single input surface). 'detail_inputs' live on each "
                               "asset tab. Change a value here + regenerate the workbook to reprice.",
        },
        "global": [],
        "assets": {},
        "office_owner_roster": [],
        "market_research": MKT,
        "outputs": OUTPUTS,
    }

    # ---- global drivers (from the shared GLOBAL_SECTIONS structure) ----
    for title, drivers in GLOBAL_SECTIONS:
        doc["global"].append({
            "section": title,
            "drivers": [_driver(n, l, v, f, flag, note) for (n, l, v, f, flag, note) in drivers],
        })

    # ---- per-asset headline inputs (authoritative: the same _blocks() the control tab renders) ----
    block_by_prefix = {p: (title, rows) for p, title, rows in _blocks()}
    prefix_for = {"shahidi": "SHA", "publix": "PUB", "sunrise": "SUN", "office": "OFF", "land": "LND"}

    # source dicts for facts + the full detail inputs (growth, TI/LC, reserves, closing, etc.)
    src = {
        "shahidi": dict(SH), "publix": dict(PUBLIX_CFG["inp"]),
        "sunrise": dict(KARLUEN_CFG["inp"]), "office": dict(OFFICE_A), "land": dict(LAND_A),
    }
    facts = {
        "shahidi": PARCELS["shahidi"], "publix": PARCELS["publix"],
    }

    for akey, (label, sheet, conf) in ASSET_META.items():
        prefix = prefix_for[akey]
        title, rows = block_by_prefix[prefix]
        headline = [_driver(n, l, v, f) for (n, l, v, f) in rows]
        headline_keys = {n for (n, *_ ) in rows}
        # detail inputs that live on the asset tab (present in the source dict, not on the control tab)
        detail = {k: v for k, v in src[akey].items()
                  if k not in {"_landsf_name"} and not k.startswith("_")}
        entry = {
            "label": label,
            "workbook_tab": sheet,
            "parcel_confidence": conf,
            "control_tab_inputs": headline,
            "detail_inputs": detail,
        }
        if akey in facts:
            entry["verified_facts"] = facts[akey]
        doc["assets"][akey] = entry

    # ---- office owner roster (fractured condo buy-out map) ----
    for i, (nm, sf, basis, bdate, note) in enumerate(OWNERS):
        doc["office_owner_roster"].append({
            "unit_index": i + 1, "owner": nm, "sf": sf,
            "original_basis": basis, "bought": bdate, "note": note,
        })

    with open(OUT, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    n_global = sum(len(s["drivers"]) for s in doc["global"])
    n_asset = sum(len(a["control_tab_inputs"]) + len(a["detail_inputs"]) for a in doc["assets"].values())
    print(f"wrote {OUT}: {n_global} global inputs, {n_asset} asset inputs, "
          f"{len(doc['office_owner_roster'])} owner rows, "
          f"{sum(len(v) for v in OUTPUTS.values())} documented outputs")


def _current_global(name):
    for _title, drivers in GLOBAL_SECTIONS:
        for (n, _l, v, *_rest) in drivers:
            if n == name:
                return v
    return None


def build_overrides():
    """Emit overrides.template.json (always) and seed overrides.json (only if missing,
    so a user's filled-in values are never clobbered)."""
    asset_src = {"shahidi": SH, "publix": PUBLIX_CFG["inp"], "sunrise": KARLUEN_CFG["inp"],
                 "office": OFFICE_A, "land": LAND_A}
    doc = {"_README": _OVR_README, "global": {}, "assets": {}}
    for scope, key, status in GAP_STATUS:
        if scope == "global":
            doc["global"][key] = {"value": _current_global(key), "status": status}
        else:
            asset = scope.split(":", 1)[1]
            doc["assets"].setdefault(asset, {})[key] = {"value": asset_src[asset].get(key), "status": status}
    with open(TEMPLATE, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    seeded = False
    if not os.path.exists(OVERRIDES):
        with open(OVERRIDES, "w") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        seeded = True
    n = len(GAP_STATUS)
    print(f"wrote {TEMPLATE}: {n} fill-in fields" + (f"; seeded {OVERRIDES}" if seeded else f"; kept your {OVERRIDES}"))


if __name__ == "__main__":
    build()
    build_overrides()
