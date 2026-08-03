def irr(cf):
    lo,hi=-0.95,3.0
    f=lambda r: sum(c/(1+r)**i for i,c in enumerate(cf))
    for _ in range(500):
        m=(lo+hi)/2
        if f(lo)*f(m)<=0: hi=m
        else: lo=m
    return (lo+hi)/2
def pmt(pv,rate,years):
    i=rate/12; n=years*12
    return pv*i/(1-(1+i)**-n)*12
def bal(pv,rate,years,after):
    i=rate/12; n=years*12; k=after*12
    return pv*((1+i)**n-(1+i)**k)/((1+i)**n-1)

P,ASK,SF,RENT=1_100_000,1_600_000,4400,132_000
TAX,INS,CAM=39_402,12_000,10_000
W=1_165_500

print("="*76); print("A.  FINANCING  —  cannabis collateral: private debt 9-11%, 50-60% LTV"); print("="*76)
print(f"{'Price':>11s}{'LTV':>7s}{'Loan':>11s}{'Rate':>7s}{'Ann. DS':>11s}{'DSCR':>7s}{'Equity':>11s}{'Cash flow':>11s}{'CoC':>8s}")
rows=[]
for px in (P,1_250_000,ASK):
    for ltv,rate in ((0.55,0.10),(0.60,0.095)):
        loan=px*ltv; ds=pmt(loan,rate,25); eq=px-loan; cfl=RENT-ds
        rows.append((px,ltv,loan,rate,ds,RENT/ds,eq,cfl,cfl/eq))
        print(f"{px:>11,.0f}{ltv:>7.0%}{loan:>11,.0f}{rate:>7.2%}{ds:>11,.0f}{RENT/ds:>7.2f}{eq:>11,.0f}{cfl:>11,.0f}{cfl/eq:>8.2%}")
print("\n  Levered IRR (55% LTV, 10%, 25-yr am, hold to expiry, weighted reversion):")
for px in (P,1_250_000,ASK):
    loan=px*0.55; ds=pmt(loan,0.10,25); eq=px-loan
    b=bal(loan,0.10,25,6.5)
    cf=[-eq]+[RENT-ds]*6+[(RENT-ds)*0.5 + W - b]
    print(f"    ${px:,.0f}: equity ${eq:,.0f}, loan bal at exit ${b:,.0f} -> levered IRR {irr(cf):.2%}")

print("\n"+"="*76); print("B.  TENANT HEALTH  —  can they carry the rent for 6.5 years?"); print("="*76)
occ=RENT+TAX+INS+CAM
print(f"  Base rent {RENT:,} + taxes {TAX:,} + insurance {INS:,} + CAM {CAM:,}")
print(f"  GROSS OCCUPANCY COST: ${occ:,}  (${occ/SF:.2f}/SF)")
print(f"\n{'Store sales':>14s}{'Occ % of sales':>17s}{'Verdict':>16s}")
for s in (1_500_000,2_000_000,2_500_000,3_000_000,3_900_000,5_000_000):
    pc=occ/s
    v = "Distressed" if pc>0.09 else ("Tight" if pc>0.07 else ("Workable" if pc>0.055 else "Healthy"))
    print(f"{s:>14,.0f}{pc:>17.1%}{v:>16s}")
print(f"\n  NJ context: $1.164bn certified 2025 sales / ~300 stores = ${1_164_000_000/300:,.0f} average per store")
print(f"  Rent-only as % of sales at $2.5M: {RENT/2_500_000:.1%}   (rent-only is the lease test; occupancy is the business test)")
print(f"  Breakeven sales for a 9% occupancy ceiling: ${occ/0.09:,.0f}")

print("\n"+"="*76); print("C.  SENSITIVITY  —  expected IRR at $1,100,000"); print("="*76)
RENEW=1_639_865
OTH=[(0.10,1_064_474),(0.20,831_286),(0.20,780_000),(0.05,990_000),(0.05,627_000)]
base_o=sum(p*v for p,v in OTH); w_o=sum(p for p,_ in OTH)
print(f"{'P(renew)':>10s}{'Wtd reversion':>16s}{'IRR @1.10M':>13s}{'IRR @1.25M':>13s}{'IRR @1.60M':>13s}")
for pr in (0.20,0.25,0.40,0.50,0.60,0.75,0.90):
    rev=pr*RENEW+(1-pr)*(base_o/w_o)
    f=lambda px:[-px]+[RENT]*6+[RENT*0.5+rev]
    print(f"{pr:>10.0%}{rev:>16,.0f}{irr(f(P)):>13.2%}{irr(f(1_250_000)):>13.2%}{irr(f(ASK)):>13.2%}")
print("\n  Market-rent sensitivity (yield on cost at $1.1M, and value at an 8.75% exit cap):")
print(f"{'Mkt rent/SF':>13s}{'NOI':>11s}{'Yield on cost':>15s}{'Value @8.75%':>14s}{'vs our basis':>14s}")
for psf in (16,18,20,22,24,26):
    noi=psf*SF; val=noi/0.0875
    print(f"{psf:>13.2f}{noi:>11,.0f}{noi/P:>15.2%}{val:>14,.0f}{val/P-1:>14.0%}")

print("\n"+"="*76); print("D.  EXIT  —  who buys it from us in 2033"); print("="*76)
for name,noi,cap,note in [
  ("Renewed cannabis lease, 5 yrs term",154_000,0.0925,"Cannabis net-lease buyer; all-cash, limited pool"),
  ("Re-let to bank/credit union, 10-15 yr NNN w/ bumps",105_600,0.0800,"NON-cannabis: financeable, national net-lease buyer pool"),
  ("Re-let to medical, 10-15 yr NNN w/ bumps",105_600,0.0775,"Medical net lease trades tighter still"),
  ("Vacant / land + shell",0,0,"Local owner-user or developer"),
]:
    v = 750_000 if cap==0 else noi/cap
    print(f"  {name:52s} ${v:>10,.0f}  {note}")
print("\n  KEY: re-tenanting to a NON-cannabis covenant removes the financing constraint,")
print("  which widens the buyer pool and compresses the exit cap by roughly 75-125 bps.")
