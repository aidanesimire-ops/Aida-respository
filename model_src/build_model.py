"""
build_model.py — assemble the full E Sunrise Blvd Assemblage underwriting workbook.
Run:  python3 build_model.py
"""
import json, os
from openpyxl.utils import get_column_letter, column_index_from_string
from mblib import new_book, add_sheet, NAVY, GOLD
import tab_assumptions, tab_shahidi, tab_asset, tab_office, tab_land, tab_assemblage, tab_income, tab_scenarios, tab_hbu, tab_exec, tab_notes, tab_review, tab_capital, tab_dealbook, tab_partners, tab_starthere, tab_comps, tab_devt
import configs, data

OUT = "../Shahidi_Assemblage_Model.xlsx"
OVERRIDES = "../overrides.json"


def _ov_value(entry):
    """An override entry may be a bare value or {'value': x, 'status': '...'}."""
    return entry["value"] if isinstance(entry, dict) and "value" in entry else entry


def apply_overrides(path=OVERRIDES):
    """Patch the default inputs with real/corrected data from overrides.json BEFORE
    the workbook is built. Absent file (or absent key) → defaults are used unchanged,
    so this can never break the build. This is the single fill-in-the-blanks surface:
    drop a confirmed value in overrides.json, rerun build_model.py, and it flows through
    every tab. Global drivers patch by name; per-asset inputs patch by dict key."""
    if not os.path.exists(path):
        return []
    with open(path) as f:
        ov = json.load(f)
    applied = []

    # global drivers (GLOBAL_SECTIONS is a list of (title, [(name,label,val,fmt,flag,note)...]))
    g = ov.get("global", {})
    if g:
        new_sections = []
        for title, drivers in tab_assumptions.GLOBAL_SECTIONS:
            nd = []
            for (name, label, val, fmt, flag, note) in drivers:
                if name in g:
                    val = _ov_value(g[name])
                    f2 = g[name].get("confidence", flag) if isinstance(g[name], dict) else flag
                    nd.append((name, label, val, fmt, f2, note)); applied.append(name)
                else:
                    nd.append((name, label, val, fmt, flag, note))
            new_sections.append((title, nd))
        tab_assumptions.GLOBAL_SECTIONS = new_sections

    # per-asset inputs (mutate the source dicts in place — every tab reads the same object)
    asset_dicts = {"shahidi": data.SH, "publix": configs.PUBLIX_CFG["inp"],
                   "sunrise": configs.KARLUEN_CFG["inp"], "office": tab_office.A, "land": tab_land.A}
    for asset, kv in ov.get("assets", {}).items():
        d = asset_dicts.get(asset)
        if not isinstance(d, dict) or not isinstance(kv, dict):
            continue
        for k, entry in kv.items():
            if k in d:
                d[k] = _ov_value(entry); applied.append(f"{asset}.{k}")
    return applied


def fit_row_heights(ws):
    """Bump row heights so wrapped text in merged cells doesn't clip (Excel
    does not auto-fit merged-cell row height)."""
    # map top-left cell -> (min_col,max_col) of its merged range
    span = {}
    for mr in ws.merged_cells.ranges:
        span[(mr.min_row, mr.min_col)] = (mr.min_col, mr.max_col)
    def colw(ci):
        w = ws.column_dimensions[get_column_letter(ci)].width
        return w if w else 8.43
    for row in ws.iter_rows():
        need = 0
        for c in row:
            if not isinstance(c.value, str) or c.value.startswith("="):
                continue
            al = c.alignment
            if not (al and al.wrap_text):
                continue
            c1, c2 = span.get((c.row, c.column), (c.column, c.column))
            width_chars = sum(colw(ci) for ci in range(c1, c2 + 1))
            sz = (c.font.size or 8)
            cpr = max(6, width_chars * (11.0 / sz))   # chars per line, font-scaled
            lines = max(1, -(-len(c.value) // int(cpr)))
            need = max(need, lines * (sz + 4) + 3)
        if need:
            cur = ws.row_dimensions[row[0].row].height or 15
            ws.row_dimensions[row[0].row].height = min(64, max(cur, need))


def main():
    applied = apply_overrides()
    if applied:
        print(f"applied {len(applied)} override(s):", ", ".join(applied[:12]) + (" …" if len(applied) > 12 else ""))
    wb = new_book()
    sh = {}

    # ---- assumptions control panel first (pure inputs, no deps) ----
    sh["Assumptions"] = add_sheet(wb, "Assumptions", tabcolor=GOLD)
    a_free = tab_assumptions.build_inputs(sh["Assumptions"])
    areg = sh["Assumptions"].reg
    A = {"Assumptions": areg}

    def amap(prefix):
        p = prefix + "_"
        return {k[len(p):]: v for k, v in areg.items() if k.startswith(p)}

    # ---- asset tabs (populate registries; each reads its block from Assumptions) ----
    sh["Shahidi Retail"] = add_sheet(wb, "Shahidi Retail", tabcolor=NAVY)
    tab_shahidi.build(sh["Shahidi Retail"], amap("SHA"))

    sh["Publix & Starbucks"] = add_sheet(wb, "Publix & Starbucks", tabcolor=NAVY)
    tab_asset.build(sh["Publix & Starbucks"], configs.PUBLIX_CFG, amap("PUB"))

    sh["Sunrise Plaza"] = add_sheet(wb, "Sunrise Plaza", tabcolor=NAVY)
    tab_asset.build(sh["Sunrise Plaza"], configs.KARLUEN_CFG, amap("SUN"))

    sh["Office Condo"] = add_sheet(wb, "Office Condo", tabcolor=NAVY)
    tab_office.build(sh["Office Condo"], amap("OFF"))

    sh["Bayview JV"] = add_sheet(wb, "Bayview JV", tabcolor=NAVY)
    tab_land.build(sh["Bayview JV"], A, amap("LND"))

    # ---- assemblage HBU (links to assets + assumptions premium) ----
    asset_regs = {name: s.reg for name, s in sh.items()}
    asm_regs = dict(asset_regs); asm_regs.update(A)
    sh["Assemblage"] = add_sheet(wb, "Assemblage", tabcolor=GOLD)
    tab_assemblage.build(sh["Assemblage"], asm_regs)

    # ---- income valuation (links to assets + assemblage + assumptions) ----
    inc_regs = dict(asm_regs)
    inc_regs["Assemblage"] = sh["Assemblage"].reg
    sh["Income Valuation"] = add_sheet(wb, "Income Valuation", tabcolor=GOLD)
    tab_income.build(sh["Income Valuation"], inc_regs)

    # ---- scenarios (links to income valuation) ----
    scen_regs = dict(inc_regs)
    scen_regs["Income Valuation"] = sh["Income Valuation"].reg
    sh["Scenarios"] = add_sheet(wb, "Scenarios", tabcolor=GOLD)
    tab_scenarios.build(sh["Scenarios"], scen_regs)

    # ---- review board (interactive sensitivities; links to income + assemblage + scenarios) ----
    review_regs = dict(scen_regs)
    review_regs["Scenarios"] = sh["Scenarios"].reg
    sh["Review Board"] = add_sheet(wb, "Review Board", tabcolor=GOLD)
    tab_review.build(sh["Review Board"], review_regs)

    # ---- highest & best use (links to assets + assemblage + assumptions) ----
    hbu_regs = dict(scen_regs)
    hbu_regs["Scenarios"] = sh["Scenarios"].reg
    sh["Highest & Best Use"] = add_sheet(wb, "Highest & Best Use", tabcolor=GOLD)
    tab_hbu.build(sh["Highest & Best Use"], hbu_regs)

    # ---- capital stack & affordability (links to income + assemblage) ----
    cap_regs = dict(hbu_regs)
    cap_regs["Highest & Best Use"] = sh["Highest & Best Use"].reg
    sh["Capital Stack"] = add_sheet(wb, "Capital Stack", tabcolor=GOLD)
    tab_capital.build(sh["Capital Stack"], cap_regs)

    # ---- deal book (acquisition & execution package; links to income + assemblage + HBU) ----
    sh["Deal Book"] = add_sheet(wb, "Deal Book", tabcolor=GOLD)
    tab_dealbook.build(sh["Deal Book"], cap_regs)

    # ---- partner returns (LP/GP waterfall + downside; links to income + scenarios) ----
    sh["Partner Returns"] = add_sheet(wb, "Partner Returns", tabcolor=GOLD)
    tab_partners.build(sh["Partner Returns"], cap_regs)

    # ---- comps & pricing (the quotable factual basis; links to assets + assemblage + HBU) ----
    sh["Comps & Pricing"] = add_sheet(wb, "Comps & Pricing", tabcolor=GOLD)
    tab_comps.build(sh["Comps & Pricing"], cap_regs)

    # ---- development pro forma (quantifying the vision; links to assemblage) ----
    sh["Development Pro Forma"] = add_sheet(wb, "Development Pro Forma", tabcolor=GOLD)
    tab_devt.build(sh["Development Pro Forma"], cap_regs)

    # ---- executive summary (links to everything) ----
    all_regs = dict(cap_regs)
    all_regs["Highest & Best Use"] = sh["Highest & Best Use"].reg
    sh["Executive Summary"] = add_sheet(wb, "Executive Summary", tabcolor=GOLD)
    tab_exec.build(sh["Executive Summary"], all_regs)

    # ---- start here (the reading map; links to a few headline cells) ----
    start_regs = dict(all_regs); start_regs["Partner Returns"] = sh["Partner Returns"].reg
    sh["Start Here"] = add_sheet(wb, "Start Here", tabcolor=GOLD)
    tab_starthere.build(sh["Start Here"], start_regs)

    # ---- notes / sources / methodology ----
    sh["Notes & Sources"] = add_sheet(wb, "Notes & Sources", tabcolor=GOLD)
    tab_notes.build(sh["Notes & Sources"])

    # ---- append the live data-gap register to the Assumptions tab (needs all regs) ----
    tab_assumptions.build_index(sh["Assumptions"], all_regs, a_free)

    # ---- reorder ----
    order = ["Start Here", "Executive Summary", "Comps & Pricing", "Development Pro Forma", "Deal Book",
             "Assumptions", "Income Valuation", "Scenarios", "Assemblage", "Highest & Best Use",
             "Review Board", "Capital Stack", "Partner Returns", "Shahidi Retail", "Publix & Starbucks",
             "Sunrise Plaza", "Office Condo", "Bayview JV", "Notes & Sources"]
    wb._sheets = [sh[t].ws for t in order]
    wb.active = 0

    # ---- tab colours grouped by reading section (makes the 17 tabs scannable) ----
    C_SEE, C_MAKE, C_PLAY = GOLD, "2E7D74", "3B6EA5"
    C_CTRL, C_MATH, C_REF, C_VISION = "C77D2E", "4A5A6A", "6B7280", "2E7D4F"
    tabcolor = {
        "Start Here": C_SEE, "Executive Summary": C_SEE, "Comps & Pricing": C_SEE,
        "Development Pro Forma": C_VISION,
        "Deal Book": C_MAKE, "Partner Returns": C_MATH,
        "Review Board": C_PLAY, "Capital Stack": C_PLAY,
        "Assumptions": C_CTRL,
        "Income Valuation": C_MATH, "Scenarios": C_MATH, "Assemblage": C_MATH, "Highest & Best Use": C_MATH,
        "Shahidi Retail": NAVY, "Publix & Starbucks": NAVY, "Sunrise Plaza": NAVY, "Office Condo": NAVY, "Bayview JV": C_VISION,
        "Notes & Sources": C_REF,
    }

    # ---- print setup on every tab ----
    for t in order:
        ws = sh[t].ws
        ws.sheet_properties.tabColor = tabcolor.get(t, GOLD)
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = True
        ws.page_margins.left = ws.page_margins.right = 0.3
        ws.page_margins.top = ws.page_margins.bottom = 0.4
        fit_row_heights(ws)

    wb.save(OUT)
    print("saved", OUT)

    import json
    reg = {t: s.reg for t, s in sh.items()}
    with open("registry.json", "w") as f:
        json.dump(reg, f, indent=1)


if __name__ == "__main__":
    main()
