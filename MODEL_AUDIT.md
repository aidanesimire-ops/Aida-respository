# Model Audit — E Sunrise Blvd Assemblage

**Prepared for:** DAWN RE Enterprises Corp. · **Date:** 2026-07-22 · **Status:** internal review
**Workbook:** `Shahidi_Assemblage_Model.xlsx` (13 tabs) · **Engine:** `model_src/` (Python/openpyxl)

This is a back-to-basics review of the math, the formulas, and the facts. It states
plainly what is built correctly, what is a modeling choice you should be aware of,
what is a defect (and whether it is fixed), and — most importantly — **what data is
still missing** before this is a decision-grade underwrite rather than a screening model.

---

## 1. How this was verified

- **Headless recalculation** of every formula with the `formulas` engine (not Excel):
  **4,335 cells solved, 0 formula errors.** (`python3 validate.py`.) This proves no
  `#REF`/`#DIV0`/`#NUM` breaks — it does **not** prove the math models the right thing.
- **Hand re-computation** of each asset's NOI, cap, reversion, and returns from the
  raw inputs, checked against the recalc.
- **Tie checks** on the integrity claims the model makes (below).

### Integrity checks that PASS (verified, not asserted)

| Check | Result |
|---|---|
| Sources & Uses balance (sources − uses) | **0.00** (ties to the penny) |
| Consolidated as-is NOI = Σ each asset's as-is NOI | **$4,560,414 = $4,560,414** ✓ |
| Debt sized to lesser-of LTV/DSCR/DY | LTV binds: **min($42.1M, $46.3M, $53.7M) = $42.1M** ✓ |
| Return-attribution bridge = actual consolidated unlevered cash flow | **Δ = $0.00** (algebraically exact) ✓ |
| Per-asset NOI (Shahidi $1.00M, Publix $0.83M, Office $1.81M, Land $0.43M) | reproduced by hand ✓ |
| Break-even exit-cap formula (return-of-capital) | algebra confirmed correct ✓ |
| Redevelopment residual (−$15.5M, HOLD) | reproduced by hand ✓ |
| Office full buy-out (168,807 SF × $225) = $37.98M; fragmentation premium | reproduced ✓ |

The core engine is sound. The findings below are about **methodology and inputs**, not broken cells.

---

## 2. Findings — ranked

### 🔴 F1 — The headline income price rests on one assumed blended cap, not the parts
The concluded income price is `as-is NOI ÷ 6.5%` = **$70.2M**. But if you value **each
asset at its own going-in cap** (Shahidi 6.0%, Publix 6.0%, Sunrise 7.5%, Office 8.0%,
Land 8.0%) and sum, you get **$65.1M** — the headline is **+7.8% ($5.1M) richer** than
the sum of the parts, purely because the single 6.5% blend is tighter than the
asset-weighted average. **The blended cap is an independent input; it is not derived
from, or reconciled to, the individual asset caps.**
→ *Recommendation:* either (a) drive the blended cap from a weighted average of the
asset caps, or (b) keep 6.5% as a deliberate "portfolio" view and show the $65.1M
sum-of-parts income value next to it so the $5M gap is explicit. Right now a reviewer
who sums the parts will not reproduce the headline.

### 🟠 F2 — Levered-return sensitivity grids did not tie to the headline *(FIXED this turn)*
The Income tab's Sensitivity ② (and the new Review Board grids) reconstructed the exit
as `forward NOI ÷ exit cap`. But **two of five parcels exit at LAND VALUE** (Publix
≈$24.5M, Land ≈$15.5M), so the real reversion is **$99M**, not the ~$54M an income-cap
reversion implies. The grids therefore showed a base levered multiple of ~1.3× against a
**true 2.31×** headline. Fixed by anchoring the grids to the actual consolidated
reversion (`REV_BASE`), scaled by exit cap. The covered-land row now correctly reproduces
the 0.81× HBU multiple, and the base case reproduces 2.31×.

### 🟠 F3 — The Assemblage blended cap uses Year-1 pro-forma NOI, not as-is
The Assemblage roll-up (`TOT_NOI`, `BLEND_CAP2` = 4.63%) uses each asset's **Year-1
pro-forma NOI** (`NOI1`), which for Sunrise and Office already includes half of the
lease-up ramp. On an as-is basis the blended cap is **~4.49%** (~14 bps lower). Small,
but the "in-place cap" label overstates going-in income by ~$138k of NOI.
→ *Recommendation:* switch the roll-up's NOI source to the as-is names for a true
in-place cap, or relabel it "Year-1 pro-forma cap."

### 🟠 F4 — Covered-land price produces a *negative* income return (by design — make sure it's understood)
At the $121.9M covered-land price the income case returns **−4.4% levered IRR / 0.81×
equity** — you lose ~19% of equity over the hold on current income alone. That is the
covered-land thesis (you pay for dirt + optionality, not yield), and it is now stated on
the Review Board. But it is the number a capital partner will challenge first: **the deal
only works if land compounds at ≥ the break-even land CAGR** shown on the Income tab.

### 🟡 F5 — Publix Year-5 books reimbursement income after the tenant has vacated
The leaseback base rent correctly cliffs at the entitlement term (Year 4), but
reimbursements, occupancy, and management fee continue through Year 5 (the hold year).
After Publix vacates at Year 4 the center is dark, yet Year-5 NOI still includes NNN
recoveries. Impact is small (the parcel exits at land value regardless), but Year-5
NOI is modestly overstated.
→ *Recommendation:* cliff reimbursements/occupancy at the term too, or set hold = term.

### 🟡 F6 — Office control basis is dual ($21.7M income vs. $37.98M buy-out) — intentional, document it
The office contributes **income cash flows built off a $21.7M basis** to the consolidated
Income tab, but enters the covered-land assemblage at its **$37.98M full buy-out**
(168,807 SF × $225/SF). Both are deliberate (income value vs. cost-to-control a fractured
condo), and the income price keys off NOI not basis, so nothing double-counts. But the two
numbers for "the office" should be labeled so no one reconciles them incorrectly.

### 🟡 F7 — Assembled-land value excludes the office parcel's land
Because the office is a condominium, the assemblage counts **zero land** for it and values
the assembled dirt on the other four parcels only (7.16 ac). Buying out **every** unit does
give you control of the land under the building (via the association), and that parcel sits
on the hard corner — arguably the most valuable dirt in the block. The current treatment is
**conservative** (understates assembled land), which is defensible, but it should be a
stated choice, not a silent omission.

### 🟡 F8 — Returns exclude any promote / GP-LP waterfall
An 8% pref / 90-10 / 70-30 waterfall is defined in the code (`WF`) but **not wired into the
returns**. All IRRs/multiples are project-level. Fine for screening; add the waterfall before
you show LP-level economics.

### 🟡 F9 — Property tax is modeled uniformly and to each asset's own price
Every asset reassesses to its own purchase price at a flat 0.0191 millage. An actual
assemblage reallocates basis across parcels, and Florida's non-homestead 10% assessment cap
and any portability are not modeled. Reasonable for screening; refine with the county's
actual TRIM data at diligence.

---

## 3. Missing data — the foundational gaps

The model **fills every gap with an adjustable assumption**, which is correct for a screen.
But the following are the facts that must be obtained before this is decision-grade. Grouped
by how much they move the answer.

### A. Moves the valuation materially
1. **Real leases / rent rolls (all assets).** There are no lease abstracts anywhere — every
   `$/SF`, suite SF, expiration, renewal option, escalation, and recovery structure (NNN vs.
   gross) is estimated from corridor comps and Yelp/LoopNet. No WALT, no rollover schedule,
   no co-tenancy or kick-out clauses. **This is the single biggest gap.** Get estoppels /
   the actual rent roll and T-12 operating statements in diligence.
2. **Sunrise Plaza (Kar Luen) value.** The $8.5M is **reported/unverified** — the last
   recorded sale is Oct 2000 for $128k (stale). Building SF (25,105), land SF (30,928),
   occupancy (80.1%), and the entire tenant list are estimated. No arm's-length evidence.
3. **Office condo per-unit roster.** ~57.4% (Grove Gate/Main Street Fund) is identified;
   the **42.6% balance is ~40 individual owners grouped into one 63,155 SF line.** Exact
   per-unit SF, ownership, and cost basis need a **BCPA folio pull** (blocked from this
   build environment). Without it the buy-out is an aggregate, not a negotiation map.
4. **Publix sale-leaseback is hypothetical.** Publix is a **fee owner, not a seller.** The
   $25M is a verified 2025 deed, but the leaseback (would they do it? at what rent/term?) is
   entirely modeled. The whole covered-land structure depends on Publix agreeing to lease back.
5. **1040 Bayview entitlement + basis.** Land SF (104,108), office SF (84,495), the 259-unit
   entitlement, and the $6.69M BCPA value are all **press-sourced** (Florida YIMBY, BBX,
   Procacci). The $13M acquisition basis is modeled; the site is **not for sale.**

### B. Moves the operating numbers
6. **Operating statements (T-12s).** Insurance, CAM, R&M are estimates. **Florida AE-flood
   insurance is a genuine wildcard** and can swing NOI meaningfully — get actual bindable quotes.
7. **Actual debt quotes.** Rate, LTV, IO period, amortization, and recourse are modeled at
   mid-2026 market. Get term sheets.
8. **Property tax detail.** Actual TRIM notices, millage by parcel, and reassessment mechanics
   (see F9).

### C. Physical / legal diligence (none reflected yet)
9. **Title** — liens, easements, encroachments, deed restrictions, and (critically) the office
   **condo declaration** (does it permit a single-owner buy-out / termination? super-majority?).
10. **Survey, Phase I ESA, Property Condition Assessment, flood elevation certificates.** The
    AE flood zone is material to both insurance and redevelopment cost.
11. **Entitlement specifics** — Live Local eligibility, approved density, height, parking,
    concurrency, and impact fees. The redevelopment residual uses generic $500/SF hard cost,
    $600k/unit value, 950 SF/unit — all modeled.
12. **Assemblage / holdout reality** — the 15/20/25% premium is a placeholder; real holdout
    leverage (who must sell, who can wait) is unknown until you approach owners.

### What is genuinely VERIFIED today (✅)
Shahidi and Publix parcel facts (BCPA/deed): folios, land/building SF, last-sale prices and
dates, 2024–25 taxes. Ownership entities via Sunbiz/press. Everything else is ⚠️ reported or
🔶 modeled — flagged as such on the **Data-Gap Register** (Assumptions tab) and the **Notes**
tab, which is the correct posture for a screening model.

---

## 4. Bottom line

- **The engine is trustworthy.** Cash flows, debt sizing, consolidation, the attribution
  bridge, and the return math tie out exactly. Two grid bugs were found and one is now fixed.
- **The answer is only as good as five reported facts** (Sunrise value, office roster, Publix
  leaseback, Bayview entitlement, and — everywhere — real leases). Until those are confirmed,
  treat the outputs as a **screen**, not an appraisal.
- **Two methodology calls deserve a decision:** (F1) reconcile the blended cap to the parts,
  and (F4) make the negative covered-land income return explicit to any capital partner.

*All ⚠️ items are county-confirmable. BCPA, the Broward Clerk, and Sunbiz were egress-blocked
from the build environment, so reported data came from web mirrors and press and must be
verified at the source before reliance.*
