# How to use this dashboard — a broker's guide

A plain-English guide to using the Commercial Deal Dashboard for **marketing, prospecting, and
pricing**. Open `dashboard/index.html` in any browser (nothing to install). The same "How to use"
panel is at the top of the dashboard itself.

## The one thing to understand first

Your MLS export has **price and size but no income** (no NOI, rents, cap rate, or units). So:

- **$/SqFt numbers are real** — straight from the data.
- **Everything income-based (cap rate, value, returns) comes from assumptions you control.** The
  dashboard makes those assumptions visible and adjustable so you can dial them to your read.

Where a number depends on assumptions, the tool says so. Cells tagged **Indicative** have few
sales behind them — verify before you quote them to a client.

## The five jobs it does

### 1. Find sellers to call  → *Prospects* + *Reprice inventory*
- **Prospects** lists the failure rate by asset type and (in the Excel/CSV) the actual failed
  listings — expired/cancelled/withdrawn owners who couldn't sell. That's your cold-call list.
- In **Reprice inventory**, filter the flag to **Overpriced**: live listings priced above what
  the comps and assumptions support — owners who may need a pricing conversation.

### 2. Win a listing (seller pitch)  → *Underwrite* → *Print deal sheet*
1. In **Underwrite a deal**, pick the property from the *Listing* dropdown (or type in price + size).
2. Set the audience selector to **the seller** and click **🖨 Print deal sheet**.
3. You get a one-page PDF: what the market supports at today's rents/cap, and the price that
   actually clears. Hand it to the owner.

### 3. Pitch a buyer  → *Reprice inventory* (Underpriced) → *Print deal sheet*
1. In **Reprice inventory**, filter the flag to **Underpriced** and sort by **IRR** or **Gap**.
2. Open a deal in **Underwrite**, set the audience to **a buyer**, and print the sheet: implied
   cap, value, DSCR, cash-on-cash, and projected IRR — a ready-to-send teaser.
- Ignore anything flagged **Check** — its size or rent looks off in the data; verify first.

### 4. Answer "what should I pay?"  → *Goal-seek*
Pick a variable to **Solve for** (price, rent, exit cap, LTV, market cap) and the target it must
hit (**IRR, going-in cap, DSCR, cash-on-cash, equity multiple, or asking = value**). Example:
*solve **price** so that **IRR = 18%*** → it tells you the most you can pay and still hit 18%.

### 5. Pick a market  → *Answers* + *$/SqFt map* + *Absorption*
The **Answers** band at the top always shows, live: cheapest vs. priciest basis, the
highest-yield asset type at your assumptions, and where supply is tightest. The **$/SqFt map** and
**Absorption** tables back it up.

## Making the numbers more real

- **Use market rents.** On the Assumptions card, the *Mkt rent (comps)* column is the median asking
  rent from your lease listings. Click **Use market rents (from lease comps)** to replace the
  assumed rents with real ones for every type that has lease data.
- **Set your financing once.** The **Financing & hold** panel (LTV, rate, exit cap, hold, …) drives
  every return in the tool — the inventory IRR column, the Answers band, and the underwriting.
- **Tune per asset class.** Edit any yellow cell (rent, vacancy, opex, cap) and the whole board
  recomputes. Your changes are the model.

## What to trust, and what to verify

| Reads as… | Means | Before you quote it |
|---|---|---|
| A **$/SqFt** figure | Real, from closed/active data | Fine to use; note the comp count |
| **High / Med / Indicative** badge | How many closed sales back it | "Indicative" → verify with more comps |
| An **implied cap / value / IRR** | Derived from your assumptions | Confirm rents & expenses on the actual deal |
| **Check** flag | Size or rent looks off in the data | Don't market it until you've verified the SqFt |

None of this is an appraisal. It's a fast, defensible way to price, prospect, and pitch — then you
confirm the winners with a rent roll and a T-12.
