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
import json
import tab_assumptions
from tab_assumptions import GLOBAL_SECTIONS, _blocks
from mblib import (F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM, F_NUM2, F_YR)
from data import PARCELS, SH, MKT
from configs import PUBLIX_CFG, KARLUEN_CFG
from tab_office import A as OFFICE_A, OWNERS
from tab_land import A as LAND_A

OUT = "../model_inputs.json"

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
    "land":    ("1040 Bayview (covered land)", "Land", "REPORTED"),
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


if __name__ == "__main__":
    build()
