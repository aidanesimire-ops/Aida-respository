"""
build_model.py — assemble the full E Sunrise Blvd Assemblage underwriting workbook.
Run:  python3 build_model.py
"""
from mblib import new_book, add_sheet, NAVY, GOLD
import tab_shahidi, tab_asset, tab_office, tab_land, tab_assemblage, tab_exec
import configs

OUT = "../Shahidi_Assemblage_Model.xlsx"


def main():
    wb = new_book()
    sh = {}

    # ---- asset tabs first (populate registries) ----
    sh["Shahidi Retail"] = add_sheet(wb, "Shahidi Retail", tabcolor=NAVY)
    tab_shahidi.build(sh["Shahidi Retail"])

    sh["Publix & Starbucks"] = add_sheet(wb, "Publix & Starbucks", tabcolor=NAVY)
    tab_asset.build(sh["Publix & Starbucks"], configs.PUBLIX_CFG)

    sh["Sunrise Plaza"] = add_sheet(wb, "Sunrise Plaza", tabcolor=NAVY)
    tab_asset.build(sh["Sunrise Plaza"], configs.KARLUEN_CFG)

    sh["Office Condo"] = add_sheet(wb, "Office Condo", tabcolor=NAVY)
    tab_office.build(sh["Office Condo"])

    sh["Land"] = add_sheet(wb, "Land", tabcolor=NAVY)
    tab_land.build(sh["Land"])

    # ---- assemblage (links to assets) ----
    asset_regs = {name: s.reg for name, s in sh.items()}
    sh["Assemblage"] = add_sheet(wb, "Assemblage", tabcolor=GOLD)
    tab_assemblage.build(sh["Assemblage"], asset_regs)

    # ---- executive summary (links to assemblage + assets) ----
    all_regs = dict(asset_regs)
    all_regs["Assemblage"] = sh["Assemblage"].reg
    sh["Executive Summary"] = add_sheet(wb, "Executive Summary", tabcolor=GOLD)
    tab_exec.build(sh["Executive Summary"], all_regs)

    # ---- reorder: Exec, Assemblage, then the five assets ----
    order = ["Executive Summary", "Assemblage", "Shahidi Retail", "Publix & Starbucks",
             "Sunrise Plaza", "Office Condo", "Land"]
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

    wb.save(OUT)
    print("saved", OUT)

    import json
    reg = {t: s.reg for t, s in sh.items()}
    with open("registry.json", "w") as f:
        json.dump(reg, f, indent=1)


if __name__ == "__main__":
    main()
