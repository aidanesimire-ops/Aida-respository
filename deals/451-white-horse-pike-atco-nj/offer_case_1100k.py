SF=4400; NOI=132_000; tax=39_402; ins=12_000; cam=10_000
def irr(cf):
    lo,hi=-0.95,2.0
    f=lambda r: sum(c/(1+r)**i for i,c in enumerate(cf))
    for _ in range(500):
        m=(lo+hi)/2
        if f(lo)*f(m)<=0: hi=m
        else: lo=m
    return (lo+hi)/2

P=1_100_000
print("=== THE $1.1M BASIS ===")
print(f"Price ${P:,} | ${P/SF:.2f}/SF | going-in cap {NOI/P:.2%}")
print(f"Discount to $1.6M ask: {P/1_600_000-1:+.1%}  (${1_600_000-P:,} below)")
print(f"Discount to $1.30M value indication: {P/1_300_000-1:+.1%}")
print(f"Discount to assessor implied value $1,271,025: {P/1_271_025-1:+.1%}")
print(f"Discount to market-rent value $1,106,286: {P/1_106_286-1:+.1%}")
print(f"Land + shell floor $750,000 = {750_000/P:.0%} of purchase price")
print(f"  -> implied price for the INCOME + upside: ${P-750_000:,}")

print("\n=== PAYBACK BEFORE THE LEASE EVEN EXPIRES ===")
cum=132_000*6.5
print(f"Contracted rent to 1/31/2033 (6.5 yrs): ${cum:,.0f} = {cum/P:.0%} of the purchase price")
print(f"Years of rent to full return of capital: {P/132_000:.1f} yrs")
print(f"If option exercised, contracted rent to 2038: ${cum+154_000*5:,.0f} = {(cum+154_000*5)/P:.0%} of price")

print("\n=== DOWNSIDE PROTECTION: YIELD ON COST AT $1.1M IF RE-LET ===")
for psf in [16,18,20,22,24,26,30]:
    r=psf*SF
    print(f"  Re-let @ ${psf}/SF -> ${r:,} NOI -> {r/P:.2%} yield on a $1.1M basis")

print("\n=== BREAK-EVEN: HOW BAD CAN IT GET AND STILL RETURN CAPITAL ===")
for cap in [0.085,0.0875,0.09,0.095]:
    be=P*cap
    print(f"  Rent needed to hold $1.1M value @ {cap:.2%} exit cap: ${be:,.0f} = ${be/SF:.2f}/SF")

print("\n=== REVERSION SCENARIOS (unchanged) vs A $1.1M BASIS ===")
S=[("Tenant renews at option rent",0.40,1_639_865),
   ("New NJ cannabis licensee",0.10,1_064_474),
   ("Bank / credit union / retail",0.20,831_286),
   ("Medical / urgent care / vet",0.20,780_000),
   ("QSR pad rebuild",0.05,990_000),
   ("Extended vacancy -> land+shell",0.05,627_000)]
w=sum(p*v for _,p,v in S)
print(f"{'Scenario':34s}{'Prob':>6s}{'Net value':>12s}{'IRR @1.1M':>11s}{'IRR @1.6M':>11s}")
for n,p,v in S:
    a=irr([-P]+[132_000]*6+[66_000+v]); b=irr([-1_600_000]+[132_000]*6+[66_000+v])
    print(f"{n:34s}{p:6.0%}{v:12,.0f}{a:11.2%}{b:11.2%}")
print(f"{'PROBABILITY-WEIGHTED':34s}{'100%':>6s}{w:12,.0f}{irr([-P]+[132_000]*6+[66_000+w]):11.2%}{irr([-1_600_000]+[132_000]*6+[66_000+w]):11.2%}")

print("\n=== NEGOTIATION LADDER ===")
print(f"{'Price':>12s}{'$/SF':>8s}{'Cap':>8s}{'Exp IRR':>10s}{'Renewal case':>14s}{'Worst case':>12s}")
for px in [1_100_000,1_150_000,1_200_000,1_250_000,1_300_000,1_400_000,1_600_000]:
    e=irr([-px]+[132_000]*6+[66_000+w])
    b=irr([-px]+[132_000]*6+[66_000+1_639_865])
    wc=irr([-px]+[132_000]*6+[66_000+627_000])
    tag=" <- OFFER" if px==1_100_000 else (" <- ask" if px==1_600_000 else "")
    print(f"{px:12,.0f}{px/SF:8.0f}{132_000/px:8.2%}{e:10.2%}{b:14.2%}{wc:12.2%}{tag}")
