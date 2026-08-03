"""ONE model. One hold period. One set of cases. Every number in the deck must come from here."""
def irr(cf):
    lo,hi=-0.95,3.0
    f=lambda r: sum(c/(1+r)**i for i,c in enumerate(cf))
    for _ in range(600):
        m=(lo+hi)/2
        if f(lo)*f(m)<=0: hi=m
        else: lo=m
    return (lo+hi)/2
def pmt(pv,r,y):
    i=r/12; n=y*12; return pv*i/(1-(1+i)**-n)*12
def bal(pv,r,y,after):
    i=r/12; n=y*12; k=after*12
    return pv*((1+i)**n-(1+i)**k)/((1+i)**n-1)

# ---------- FIXED INPUTS ----------
PRICE   = 1_100_000
SF      = 4_400
RENT    = 132_000      # in place, flat, to Jan-2033 (year 6.5)
OPTION  = 154_000      # if tenant renews
CARRY   = 61_402       # taxes+ins+maint if vacant
LAND_CAP= 150_000      # cost to entitle/build the pad
LAND_NOI= 100_000      # pad ground rent + EV licence
HOLD    = 10
LTV,RATE,AM = 0.55,0.10,25

def run(name, relet_psf, void_months, ti_psf, land, exit_cap, renew=False):
    cf=[-PRICE]+[0.0]*HOLD
    for yr in range(1,HOLD+1):
        x=0.0
        if renew:
            x += RENT if yr<=6 else (RENT*0.5+OPTION*0.5 if yr==7 else OPTION)
        else:
            if yr<=6: x+=RENT
            elif yr==7:
                x+=RENT*0.5
                v=min(void_months,6)/12.0
                x-=CARRY*v
            elif yr==8:
                v=max(0,void_months-6)/12.0
                x-=CARRY*v
                x-=(ti_psf*SF + 0.05*relet_psf*SF*10)
                x+=relet_psf*SF*max(0,(12-max(0,void_months-6))/12.0)
            else:
                x+=relet_psf*SF*(1.025**(yr-9))
        if land:
            if yr==2: x-=LAND_CAP
            if yr>=3: x+=LAND_NOI
        cf[yr]+=x
    # exit
    if renew: noi_exit=OPTION
    else:     noi_exit=relet_psf*SF*(1.025**(HOLD-9))
    if land: noi_exit+=LAND_NOI
    exitval=noi_exit/exit_cap
    cf[HOLD]+=exitval
    u=irr(cf)
    loan=PRICE*LTV; ds=pmt(loan,RATE,AM); eq=PRICE-loan; b=bal(loan,RATE,AM,HOLD)
    cfl=[-eq]+[c-ds for c in cf[1:]]; cfl[-1]-=b
    l=irr(cfl)
    return dict(name=name,cf=cf,u=u,l=l,exitval=exitval,noi_exit=noi_exit)

cases=[
 run("FLOOR  - tenant fails, weak re-let, no land", 18.00, 18, 35, False, 0.0900),
 run("BASE   - re-let at market, no land",          22.00, 12, 45, False, 0.0875),
 run("GROWTH - land built + quality re-let",        24.00, 12, 60, True,  0.0800),
 run("RENEWAL- tenant exercises the option",         0.00,  0,  0, False, 0.0925, renew=True),
]
print("="*92); print("ONE MODEL — $1,100,000 purchase, 10-year hold, all cases on the same basis"); print("="*92)
print(f"{'Case':46s}{'Exit NOI':>10s}{'Exit value':>12s}{'Unlevered':>11s}{'Levered':>10s}")
print("-"*92)
for c in cases:
    print(f"{c['name']:46s}{c['noi_exit']:>10,.0f}{c['exitval']:>12,.0f}{c['u']:>11.2%}{c['l']:>10.2%}")
print("-"*92)
print(f"\nGoing-in cap rate (a yield, NOT an IRR): ${RENT:,} / ${PRICE:,} = {RENT/PRICE:.2%}")
print(f"Cash-on-cash year 1, 55% LTV: (${RENT:,} - ${pmt(PRICE*LTV,RATE,AM):,.0f}) / ${PRICE*(1-LTV):,.0f} = {(RENT-pmt(PRICE*LTV,RATE,AM))/(PRICE*(1-LTV)):.1%}")

print("\n"+"="*92); print("CASH FLOW, SIDE BY SIDE  (so every IRR above is auditable)"); print("="*92)
print(f"{'Year':>5s}" + "".join(f"{c['name'].split()[0]:>15s}" for c in cases))
for y in range(0,HOLD+1):
    print(f"{y:>5d}" + "".join(f"{c['cf'][y]:>15,.0f}" for c in cases))
print("-"*92)
print(f"{'IRR':>5s}" + "".join(f"{c['u']:>15.2%}" for c in cases))

print("\n"+"="*92); print("CONTRADICTIONS IN THE CURRENT DECK"); print("="*92)
print("  Deck says            This model says   Why they differ")
print("  " + "-"*86)
print(f"  Floor  +5.4%         {cases[0]['u']:>6.2%}            old floor used a 12-mo void and a different exit cap")
print(f"  Base   +8.7%         {cases[1]['u']:>6.2%}            old base re-let at $24, not market $22")
print(f"  Growth +18.2%        {cases[2]['u']:>6.2%}            same shape, small timing differences")
print(f"  'Expected 12.0%'     n/a               that was a 6.5-YEAR hold, not 10 — different metric entirely")
print(f"  'Worst case +6.2%'   n/a               also the 6.5-year model. Two 'worst cases' in one deck.")
print(f"  Going-in cap 12.0%   {RENT/PRICE:>6.2%}            correct, but it is a YIELD not a return — easily confused with IRR")
