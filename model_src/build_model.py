"""
build_model.py — assemble the full E Sunrise Blvd Assemblage underwriting workbook.
Run:  python3 build_model.py
"""
from openpyxl.utils import get_column_letter, column_index_from_string
from mblib import new_book, add_sheet, NAVY, GOLD
import tab_assumptions, tab_shahidi, tab_asset, tab_office, tab_land, tab_assemblage, tab_income, tab_scenarios, tab_hbu, tab_exec, tab_notes
import configs

OUT = "../Shahidi_Assemblage_Model.xlsx"


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

    sh["Land"] = add_sheet(wb, "Land", tabcolor=NAVY)
    tab_land.build(sh["Land"], A, amap("LND"))

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

    # ---- highest & best use (links to assets + assemblage + assumptions) ----
    hbu_regs = dict(scen_regs)
    hbu_regs["Scenarios"] = sh["Scenarios"].reg
    sh["Highest & Best Use"] = add_sheet(wb, "Highest & Best Use", tabcolor=GOLD)
    tab_hbu.build(sh["Highest & Best Use"], hbu_regs)

    # ---- executive summary (links to everything) ----
    all_regs = dict(hbu_regs)
    all_regs["Highest & Best Use"] = sh["Highest & Best Use"].reg
    sh["Executive Summary"] = add_sheet(wb, "Executive Summary", tabcolor=GOLD)
    tab_exec.build(sh["Executive Summary"], all_regs)

    # ---- notes / sources / methodology ----
    sh["Notes & Sources"] = add_sheet(wb, "Notes & Sources", tabcolor=GOLD)
    tab_notes.build(sh["Notes & Sources"])

    # ---- append the live data-gap register to the Assumptions tab (needs all regs) ----
    tab_assumptions.build_index(sh["Assumptions"], all_regs, a_free)

    # ---- reorder ----
    order = ["Executive Summary", "Assumptions", "Income Valuation", "Scenarios", "Assemblage",
             "Highest & Best Use", "Shahidi Retail", "Publix & Starbucks", "Sunrise Plaza",
             "Office Condo", "Land", "Notes & Sources"]
    wb._sheets = [sh[t].ws for t in order]
    wb.active = 0

    # ---- print setup on every tab ----
    for t in order:
        ws = sh[t].ws
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
