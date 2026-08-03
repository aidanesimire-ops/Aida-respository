SF=4400; tax=39_402; ins=12_000; cam=10_000; carry=tax+ins+cam
def irr(cf):
    lo,hi=-0.9,1.5
    f=lambda r: sum(c/(1+r)**i for i,c in enumerate(cf))
    for _ in range(400):
        m=(lo+hi)/2
        if f(lo)*f(m)<=0: hi=m
        else: lo=m
    return (lo+hi)/2

# ---- Reversion at lease expiry 1/31/2033, net of re-tenanting cost ----
S=[
 ("Tenant renews (option @ $154,000)", 0.40, 154_000, 0.0925,   25_000),
 ("New NJ cannabis licensee @ $30/SF", 0.10, 132_000, 0.0950,  325_000),
 ("Bank / credit union / retail @ $22",0.20,  96_800, 0.0875,  275_000),
 ("Medical / urgent care / vet @ $24", 0.20, 105_600, 0.0825,  500_000),
 ("QSR pad rebuild @ $42 on 2,200 SF", 0.05,  92_400, 0.0700,  330_000),
 ("Extended vacancy -> land + shell",  0.05,       0, 0.0000,  123_000),
]
tot=0
print(f"{'Reversion scenario at Jan-2033':38s}{'Prob':>6s}{'NOI':>10s}{'Cap':>8s}{'Stab val':>12s}{'Re-let cost':>13s}{'Net':>12s}")
for n,p,noi,cap,cost in S:
    stab = 750_000 if cap==0 else noi/cap
    net=stab-cost; tot+=p*net
    print(f"{n:38s}{p:6.0%}{noi:10,.0f}{cap if cap else 0:8.2%}{stab:12,.0f}{cost:13,.0f}{net:12,.0f}")
print(f"\n{'PROBABILITY-WEIGHTED REVERSION':38s}{'':6s}{'':10s}{'':8s}{'':12s}{'':13s}{tot:12,.0f}")

print("\n=== UNLEVERED IRR — hold to lease expiry (6.5 yrs), sell at weighted reversion ===")
for price in [1_600_000,1_500_000,1_425_000,1_375_000,1_325_000,1_250_000]:
    cf=[-price]+[132_000]*6+[66_000+tot]
    print(f"  ${price:,} (going-in {132_000/price:.2%})  ->  IRR {irr(cf):.2%}")

print("\n=== PRICE FOR TARGET UNLEVERED IRR (same structure) ===")
fl=[132_000]*6+[66_000+tot]
for t in [0.08,0.09,0.10,0.11,0.12]:
    pv=sum(c/(1+t)**(i+1) for i,c in enumerate(fl))
    print(f"  {t:.0%} IRR -> ${pv:,.0f}  (${pv/SF:,.0f}/SF, going-in cap {132_000/pv:.2%})")

print("\n=== SCENARIO IRRs AT ASK vs AT $1.35M (hold to expiry) ===")
print(f"{'Scenario':38s}{'@ $1,600,000':>14s}{'@ $1,350,000':>14s}")
for n,p,noi,cap,cost in S:
    stab = 750_000 if cap==0 else noi/cap
    net=stab-cost
    a=irr([-1_600_000]+[132_000]*6+[66_000+net])
    b=irr([-1_350_000]+[132_000]*6+[66_000+net])
    print(f"{n:38s}{a:13.2%} {b:13.2%}")
