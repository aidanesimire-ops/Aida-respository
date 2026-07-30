# Institutional Audit — E Sunrise Blvd Assemblage

**Prepared for:** DAWN RE Enterprises Corp. · **Purpose:** deal-readiness review · **Basis:** the 17-tab
model as built (4,981 cells, 0 formula errors, headless-recalc verified). This supersedes the earlier audit.

The goal here is the standard an LP's investment committee and a lender's credit desk would hold: not "does
it compute" (it does), but "does it model the right thing, are the assumptions defensible, and will the
numbers survive diligence." Read the verdict first.

---

## Verdict

**The engine is institutionally sound and every internal tie holds.** The issue is not arithmetic — it is
**framing and a handful of assumption risks that change the story.**

The one thing that must change before you show this to a partner: **returns are headlined at the income-value
price ($65.1M), which is a valuation floor you cannot actually acquire at.** At the realistic acquisition cost
(sum-of-parts ≈ $105.8M — what each owner will actually take), the levered IRR is **0.4% / 1.02×**, and at the
covered-land price it is **negative**. This is a **land-appreciation / redevelopment play in which the income
barely covers the carry** — not a 20% income deal. Underwrite and pitch it as that, and it is a credible,
well-built covered-land bet. Pitch the $65M-price return and it fails diligence on the first question a buyer
asks: *"can you actually buy it for that?"*

---

## 1. What is bankable — verified, not asserted

Re-computed by hand and cross-checked against the recalc:

| Check | Result |
|---|---|
| Concluded income price = sum of each asset at its own cap (reconciles to the tabs) | $65,095,361 ✓ |
| Implied blended going-in cap (now an **output**, not a guessed input) | 7.01% ✓ |
| Return-attribution bridge = actual consolidated unlevered cash flow | **Δ = $0.00** ✓ |
| Sources & Uses balance | **$0.00** ✓ |
| Senior debt = lesser of LTV / DSCR / debt-yield (LTV-bound at income price) | $39.06M; DSCR 1.48× ✓ |
| **LP/GP waterfall** — pref accrues 8% on unreturned capital; tiers reconcile; LP + GP = project | ✓ |
| Waterfall directionality — LP 20.4% < project 23.1% < GP 40.6% (promote transfers return to GP) | ✓ |
| GP promote = 30% × excess above pref ($33.6M) | $10.09M ✓ |
| Redevelopment residual, office buy-out, plottage, break-even exit cap | reproduced ✓ |

The math you can rely on. The waterfall is a clean **European (whole-deal) pari-passu-pref-then-70/30-promote**
structure — see §4 for what it does *not* yet model.

---

## 2. The finding that reframes the deal 🔴

The model prices the block three ways and — correctly — shows the income return at two of them. The **third,
and most important, price is missing from the returns: the price you will actually pay.**

| Purchase basis | Going-in cap | Yr-1 DSCR | Levered IRR | Equity multiple |
|---|---|---|---|---|
| Income value $65.1M — *a floor; not achievable for a fragmented assemblage* | 7.0% | 1.48× | **23.1%** | 2.63× |
| **Sum-of-parts ≈ $105.8M — *the realistic acquisition cost*** | 4.3% | **1.25×** | **0.4%** | **1.02×** |
| Covered-land $127.0M — *ceiling (sum-of-parts + 20% premium)* | 3.7% | ~1.0× | **≈ −4%** | <1× |

You cannot buy Publix ($25M fee), the office ($42M buy-out), or the land ($13M) at their income value — those
prices already embed control premiums. So the blended purchase is **~$106M–$127M**, where the income return
is **roughly zero-to-negative** and the DSCR is thin (1.25× falling toward 1.0×). **The return is entirely the
dirt.** That is a legitimate covered-land thesis — but it must be stated, and the LP waterfall (which currently
runs on the $65M floor, yielding LP 20.4%) should be re-based on the realistic price, where LP economics are far
thinner.

→ **Fix (recommended, I can do it now):** add a **"realistic acquisition" returns column at sum-of-parts** as
the primary case on Income Valuation, re-base the Partner Returns waterfall on it, and reframe Start Here / the
Exec dashboard / the marketing page around "income covers the carry; the return is the land." This is the single
highest-value change for making a real deal.

---

## 3. Assumption risks — ranked against the comps we now have

1. **🔴 Publix leaseback rent $22/SF vs. market $8–14/SF (grocery NNN).** Research (Boulder Group /
   investmentgrade.com) puts grocery-anchor base rent at $8–14/SF. The model's $22 is a *bridge rate* set to
   cover carry — 1.6–2.7× market. At a realistic $13/SF, Publix NOI falls ~$300k/yr and the "income covers the
   carry" claim weakens materially. The **dark case** (Publix won't lease back at all → −$422k/yr, ~$5M extra
   equity carry) is now modeled — good — but the *base* case should be stress-tested at market leaseback rent.
2. **🟠 Office exit cap 8.25%.** Research: Fort Lauderdale Class B/C office caps are **8%+ and "double-digit
   commonplace."** An 8.25% exit on a fractured Class B condo is optimistic; at 10% the office reversion drops
   ~$3–4M. Flex it in the downside.
3. **🟠 Office tax basis inconsistency.** The office income cash flow reassesses tax to its **$21.7M income
   basis**, but you would pay **$42.2M** (the buy-out). Florida reassesses to price, so office taxes would ~2×,
   cutting office NOI ~$0.4M/yr. The model understates office opex in the acquisition case.
4. **🟠 Premium stacking.** The covered-land price adds a **20% assemblage premium on top of** a sum-of-parts
   that already includes the office **fragmentation premium** ($42.2M buy-out vs ~$22M income value). Confirm
   these two premiums are compensating different risks (intra-condo holdouts vs cross-parcel holdouts) and not
   double-counting the same one.
5. **🟡 Insurance likely light.** Coastal Broward commercial runs **1.2–4.5% of value** (2–3× within a mile of
   water); the model carries flat ~$45–65k/asset (~0.2%). Passed through NNN on the retail, but it hits the
   office (modified-gross) and land NOI directly. Get bindable quotes.
6. **🟡 Assemblage premium (15/20/25%) has no transaction basis** — it is a placeholder. Tie it to holdout
   reality once you've approached owners.
7. **🟢 Well-supported by the research:** retail rents ($25–50/SF NNN on the corridor), strip caps (6.25–8.5%),
   land basis ($125/SF ≈ the $129/SF closed comp), the office SF and Grove Gate 57.4%/$10M, and the Bayview
   entitlement (259 units, UDP-Z25002). Construction at $500/SF is *conservative* vs the $300–450/SF AE-coastal
   band — meaning the redevelopment residual is closer to break-even than the base case shows.

---

## 4. Model / methodology notes

- **Waterfall is a screening structure.** European whole-deal, one 8% pref tier, then 70/30. It does **not**
  model a GP catch-up, multiple IRR hurdles (e.g., 8% → 15% → higher promote), acquisition / asset-management /
  disposition fees, or capital calls for interim shortfalls. Interim levered CF is currently **positive** every
  year (+$1.4–2.4M) at the income price, so no calls arise there — but at the realistic price and thinner DSCR,
  confirm that holds. Add the fee/catch-up tiers before an LP close.
- **Reversion mixes exit types** — income assets sell at forward NOI ÷ exit cap; Publix and the land exit at
  land value. That is correct for a covered-land play, but ~$40M of the $99M reversion is *land value*, so the
  exit is a land-price bet, not a cap-rate bet. Frame it that way.
- **Single 5-year hold, single exit.** No phasing, no partial sales, no refinance/recapitalization — reasonable
  for a screen; a real covered-land hold is likely longer and lumpier.
- **No entitlement probability or timing.** The premium is optionality on a redevelopment that (a) isn't the
  current base case and (b) needs ~14% annual land appreciation to justify. A probability/timing overlay would
  make the optionality honest.

---

## 5. Data that gates the deal (still outstanding)

The four-agent research sweep confirmed folios, ownership, SF, sale prices, and the entitlement, and narrowed the
comps — but the county portals (BCPA / Clerk / Sunbiz) were egress-blocked, and the following remain **required
before hard money.** They are tracked with sources in `overrides.json`.

1. **Publix leaseback appetite + terms** — binary; the thesis depends on it. A call to Publix RE (Lakeland).
2. **The office condo declaration** — does it permit a single-owner buy-out / termination, and at what vote?
   Plus the full per-unit BCPA folio roster (the 42.6% is ~40 owners, still grouped).
3. **Real leases + T-12s** — every rent and expense is estimated; this is what diligence attacks first.
4. **Current BCPA just values + tax bills** — none could be pulled; taxes drive NOI (see §3.3).
5. **Bindable insurance quotes** (§3.5), a **lender term sheet**, and **final entitlement approval** status.

Verified today (✅): Shahidi & Publix parcel facts and deeds; office 168,807 SF and Grove Gate's 57.4%/$10M;
Bayview 259-unit case UDP-Z25002 and the $7.9M 2014 basis. Everything else is ⚠️ reported or 🔶 modeled.

---

## 6. Recommended fixes — in priority order

1. **Re-base returns on the realistic (sum-of-parts) price** and reframe the whole story as a land play with the
   income covering carry (§2). *Highest value; I can implement now.*
2. **Stress Publix at market leaseback rent** ($13/SF) as the base, keep $22 as the upside (§3.1).
3. **Reassess office tax to the $42.2M buy-out** in the acquisition case (§3.3).
4. **Widen the office exit cap** toward 9–10% in the downside (§3.2).
5. **Add waterfall fee + catch-up tiers** before an LP close (§4).
6. **Add an entitlement probability/timing overlay** to the redevelopment upside (§4).

Items 1–4 I can build immediately and they change the numbers a partner sees; 5–6 are for the LP-close version.
Tell me which to implement and I'll do them and re-verify.
