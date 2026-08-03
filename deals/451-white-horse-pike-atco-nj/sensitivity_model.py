def irr(cf):
    lo,hi=-0.9,1.5
    f=lambda r: sum(c/(1+r)**i for i,c in enumerate(cf))
    for _ in range(400):
        m=(lo+hi)/2
        if f(lo)*f(m)<=0: hi=m
        else: lo=m
    return (lo+hi)/2
RENEW=1_639_865
OTHER=[(0.10,1_064_474),(0.20,831_286),(0.20,780_000),(0.05,990_000),(0.05,627_000)]
base_other=sum(p*v for p,v in OTHER); base_w=sum(p for p,_ in OTHER)  # 0.60
print("Renewal-probability sensitivity (all else equal)\n")
print(f"{'P(renew)':>9s}{'Wtd reversion':>15s}{'IRR @1.60M':>12s}{'IRR @1.45M':>12s}{'IRR @1.35M':>12s}{'Px @8% IRR':>13s}")
for pr in [0.25,0.40,0.50,0.60,0.75,0.90]:
    rev = pr*RENEW + (1-pr)*(base_other/base_w)
    fl=[132_000]*6+[66_000+rev]
    px8=sum(c/1.08**(i+1) for i,c in enumerate(fl))
    print(f"{pr:9.0%}{rev:15,.0f}{irr([-1_600_000]+fl):12.2%}{irr([-1_450_000]+fl):12.2%}{irr([-1_350_000]+fl):12.2%}{px8:13,.0f}")

print("\n\nRE-RENT MATRIX — what the box supports by use (NNN, on 4,400 SF unless noted)")
uses=[("Cannabis — new NJ licensee",28,34,4400),("Bank / credit union",22,26,4400),
      ("Medical / urgent care / dental / vet",22,26,4400),("Conventional retail / service",18,22,4400),
      ("Daycare / early education",18,22,4400),("QSR / coffee drive-thru (reduced box)",38,48,2200)]
print(f"{'Use':40s}{'Rent PSF':>16s}{'Annual rent':>22s}{'vs in-place $132k':>20s}")
for n,lo,hi,sf in uses:
    a,b=lo*sf,hi*sf
    print(f"{n:40s}{f'${lo}–${hi}':>16s}{f'${a:,.0f} – ${b:,.0f}':>22s}{f'{a/132000-1:+.0%} to {b/132000-1:+.0%}':>20s}")
