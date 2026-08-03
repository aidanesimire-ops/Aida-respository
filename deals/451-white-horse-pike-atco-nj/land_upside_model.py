P=1_100_000; SF=4400; NOI=132_000
print("=== SITE CAPACITY ===")
tot=3.13; bldg_ac=SF/43560
print(f"Site {tot} AC = {tot*43560:,.0f} SF | building {SF:,} SF = {bldg_ac:.2f} AC")
print(f"Building coverage: {SF/(tot*43560):.1%}")
park=0.55  # ac for existing parking/drive aisles/drive-thru stacking
print(f"Est. land committed to existing use (bldg+parking+drive-thru): {bldg_ac+park:.2f} AC")
print(f"ESTIMATED DEVELOPABLE EXCESS: {tot-bldg_ac-park:.2f} AC\n")

print("=== EV FAST CHARGING — REVENUE SHARE STRUCTURE ===")
print("Benchmark: highway-corridor DCFC $2,200-3,500/stall/mo gross.")
print("Atco is a secondary corridor (15,370 VPD) -> discount to $1,000-1,800/stall/mo.\n")
for stalls in (6,8):
    for permo in (1000,1400,1800):
        gross=stalls*permo*12
        print(f"  {stalls} stalls @ ${permo:,}/mo -> ${gross:,}/yr gross | owner @10% ${gross*.10:,.0f} | @25% ${gross*.25:,.0f}")
print("\n  Operator funds 100% of capex. Land required ~0.30-0.40 AC.")
ev_lo,ev_base,ev_hi=12_000,20_000,34_000
print(f"  UNDERWRITE: ${ev_lo:,} low / ${ev_base:,} base / ${ev_hi:,} high per year\n")

print("=== OUTPARCEL GROUND LEASE (QSR / car wash / medical pad) ===")
print("Method: entitled pad land value x ground-lease yield (8-9%).")
for lv in (500_000,650_000,800_000):
    for y in (0.08,0.09):
        print(f"  Pad land value ${lv:,} @ {y:.0%} -> ${lv*y:,.0f}/yr ground rent")
pad_lo,pad_base,pad_hi=40_000,55_000,75_000
print(f"  UNDERWRITE: ${pad_lo:,} low / ${pad_base:,} base / ${pad_hi:,} high per year (0.75-1.0 AC)\n")

print("=== COMBINED UPSIDE — INCREMENTAL NOI AND VALUE CREATED ===")
print(f"{'Case':10s}{'EV':>12s}{'Pad':>12s}{'Total NOI':>13s}{'@9.0% cap':>13s}{'@9.5% cap':>13s}{'% of $1.1M basis':>18s}")
for name,ev,pad in [("Low",ev_lo,pad_lo),("Base",ev_base,pad_base),("High",ev_hi,pad_hi)]:
    t=ev+pad
    print(f"{name:10s}{ev:12,.0f}{pad:12,.0f}{t:13,.0f}{t/0.09:13,.0f}{t/0.095:13,.0f}{t/0.09/P:18.0%}")

print("\n=== EFFECT ON THE DEAL IF EXECUTED (base case) ===")
t=ev_base+pad_base
print(f"Stabilized NOI: ${NOI:,} + ${t:,} = ${NOI+t:,}")
print(f"Yield on cost at $1.1M basis: {(NOI+t)/P:.2%}  (vs {NOI/P:.2%} today)")
print(f"Value @ 9.25% cap: ${(NOI+t)/0.0925:,.0f}  vs $1.1M basis = {((NOI+t)/0.0925)/P-1:+.0%}")
print(f"Net of est. $150,000 owner cost (subdivision, entitlement, site work):")
print(f"   Value created: ${(NOI+t)/0.0925 - NOI/0.0925 - 150_000:,.0f}")

print("\n=== DOWNSIDE RE-TEST: DOES THE PAD RESCUE A DARK BUILDING? ===")
for psf in (18,20,22):
    r=psf*SF
    print(f"  Building re-let @ ${psf}/SF (${r:,}) + pad/EV ${t:,} = ${r+t:,} -> {(r+t)/P:.2%} on $1.1M")
