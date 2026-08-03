exec(open('ONE_MODEL.py').read().split('cases=[')[0])
PRICE,SF,RENT,HOLD=1_100_000,4_400,132_000,10
LTV,RATE,AM=0.55,0.10,25
LOAN=PRICE*LTV; EQ=PRICE-LOAN; DS=pmt(LOAN,RATE,AM); BAL10=bal(LOAN,RATE,AM,HOLD)
MKT=22.0

C=[("Floor",   run("f",18.00,18,35,False,0.0900)),
   ("Base",    run("b",22.00,12,45,False,0.0875)),
   ("Renewal", run("r", 0.00, 0, 0,False,0.0925,renew=True)),
   ("Growth",  run("g",24.00,12,60,True, 0.0800))]

print("="*98); print("ACQUISITION METRICS  —  fixed, identical in every case"); print("="*98)
rows=[("Purchase price",f"${PRICE:,}"),("Price per square foot",f"${PRICE/SF:,.2f}"),
 ("Gross leasable area",f"{SF:,} SF"),("Year-1 NOI (in place, absolute NNN)",f"${RENT:,}"),
 ("Rent per square foot, in place",f"${RENT/SF:,.2f}"),
 ("GOING-IN CAP RATE",f"{RENT/PRICE:.2%}"),
 ("Cap rate on MARKET rent ($22.00/SF)",f"{MKT*SF/PRICE:.2%}"),
 ("Cap rate at their $1,600,000 ask",f"{RENT/1_600_000:.2%}"),
 ("Replacement-cost check",f"${PRICE/SF:,.0f}/SF vs $300-350/SF to build")]
for a,b in rows: print(f"  {a:52s}{b:>22s}")

print("\n"+"="*98); print("DEBT METRICS  —  55% LTV, 10.0%, 25-year amortisation"); print("="*98)
rows=[("Loan amount",f"${LOAN:,.0f}"),("Equity required",f"${EQ:,.0f}"),
 ("Loan-to-value",f"{LTV:.0%}"),("Loan constant",f"{DS/LOAN:.2%}"),
 ("Annual debt service",f"${DS:,.0f}"),
 ("DSCR, year 1",f"{RENT/DS:.2f}x"),
 ("DEBT YIELD (NOI / loan)",f"{RENT/LOAN:.1%}"),
 ("Break-even occupancy",f"{DS/RENT:.0%} of current rent"),
 ("Loan balance at year 10",f"${BAL10:,.0f}")]
for a,b in rows: print(f"  {a:52s}{b:>22s}")

print("\n"+"="*98); print("CASH-ON-CASH  —  year 1"); print("="*98)
cf1=RENT-DS
print(f"  {'Unlevered cash flow (= NOI)':52s}{f'${RENT:,}':>22s}")
print(f"  {'Unlevered cash-on-cash (= going-in cap)':52s}{f'{RENT/PRICE:.2%}':>22s}")
print(f"  {'Levered cash flow after debt service':52s}{f'${cf1:,.0f}':>22s}")
print(f"  {'LEVERED CASH-ON-CASH':52s}{f'{cf1/EQ:.2%}':>22s}")
print(f"  {'Simple payback, unlevered':52s}{f'{PRICE/RENT:.1f} years':>22s}")
print(f"  {'Simple payback, levered':52s}{f'{EQ/cf1:.1f} years':>22s}")

print("\n"+"="*98); print("RETURN METRICS BY CASE  —  10-year hold"); print("="*98)
hdr=f"{'Metric':40s}" + "".join(f"{n:>14s}" for n,_ in C)
print(hdr); print("-"*98)
def row(label, vals): print(f"{label:40s}" + "".join(f"{v:>14s}" for v in vals))
row("Exit NOI",            [f"${c['noi_exit']:,.0f}" for _,c in C])
row("Exit cap rate",       ["9.00%","8.75%","9.25%","8.00%"])
row("Sale price, year 10", [f"${c['exitval']:,.0f}" for _,c in C])
print("-"*98)
row("UNLEVERED IRR",       [f"{c['u']:.2%}" for _,c in C])
tot=[sum(c['cf'][1:]) for _,c in C]
row("Total cash returned", [f"${t:,.0f}" for t in tot])
row("Equity multiple",     [f"{t/PRICE:.2f}x" for t in tot])
row("Profit",              [f"${t-PRICE:,.0f}" for t in tot])
print("-"*98)
lev=[]
for _,c in C:
    l=[x-DS for x in c['cf'][1:]]; l[-1]-=BAL10; lev.append(l)
row("LEVERED IRR",         [f"{c['l']:.2%}" for _,c in C])
row("Levered cash returned",[f"${sum(l):,.0f}" for l in lev])
row("Levered equity multiple",[f"{sum(l)/EQ:.2f}x" for l in lev])
row("Avg cash-on-cash, yrs 1-9",[f"{sum(l[:9])/9/EQ:.1%}" for l in lev])
print("-"*98)
row("Yield on cost at stabilisation",
    [f"{c['noi_exit']/(PRICE+(150_000 if n=='Growth' else 0)):.1%}" for n,c in C])

print("\n"+"="*98); print("THE SAME METRICS AT THEIR $1,600,000 ASK"); print("="*98)
P2=1_600_000; L2=P2*LTV; E2=P2-L2; D2=pmt(L2,RATE,AM); B2=bal(L2,RATE,AM,HOLD)
print(f"  {'Going-in cap rate':52s}{f'{RENT/P2:.2%}':>22s}")
print(f"  {'DSCR, year 1':52s}{f'{RENT/D2:.2f}x':>22s}")
print(f"  {'Debt yield':52s}{f'{RENT/L2:.1%}':>22s}")
print(f"  {'Levered cash-on-cash, year 1':52s}{f'{(RENT-D2)/E2:.2%}':>22s}")
print(f"  {'Simple payback, unlevered':52s}{f'{P2/RENT:.1f} years':>22s}")
for n,c in C:
    cf=[-P2]+c['cf'][1:]
    l=[-E2]+[x-D2 for x in c['cf'][1:]]; l[-1]-=B2
    print(f"  {n+' case — unlevered / levered IRR':52s}{f'{irr(cf):.2%} / {irr(l):.2%}':>22s}")
