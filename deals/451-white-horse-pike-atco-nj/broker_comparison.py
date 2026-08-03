import math
SF=4400; RENT=132_000; MKT=22.0; ASK=1_600_000; OFFER=1_100_000
print("="*80); print("BRIDGE  —  how their $1,600,000 becomes our $1,100,000"); print("="*80)
v0=ASK
mkt_noi=MKT*SF
print(f"  Their ask: $132,000 contract rent capitalised at 8.25%            {v0:>12,.0f}")
v1=mkt_noi/0.0825
d1=v1-v0
print(f"  1. Use MARKET rent (${MKT:.2f}/SF = ${mkt_noi:,.0f}) not contract rent   {d1:>12,.0f}")
print(f"     -> value on market rent at the same 8.25%                     {v1:>12,.0f}")
v2=mkt_noi/0.0875
d2=v2-v1
print(f"  2. Widen the yield 8.25% -> 8.75% for lease + covenant quality    {d2:>12,.0f}")
print(f"     -> value                                                      {v2:>12,.0f}")
d3=OFFER-v2
print(f"  3. Rounding / negotiating margin                                 {d3:>12,.0f}")
print(f"  OUR OFFER                                                        {OFFER:>12,.0f}")
print(f"\n  Total gap ${ASK-OFFER:,.0f}  =  {abs(d1)/(ASK-OFFER):.0%} rent that is not market"
      f"  +  {abs(d2)/(ASK-OFFER):.0%} lease quality  +  {abs(d3)/(ASK-OFFER):.0%} margin")

print("\n"+"="*80); print("COMBINED COMP SET  —  ours and theirs, one list"); print("="*80)
comps=[
 ("7 Brew, Clementon","THEIRS",510,155_000,"Build-to-suit",False),
 ("501 Delsea Dr, Sewell","THEIRS",1_373,39.33*1373,"2nd generation",True),
 ("340 S White Horse Pike, Berlin","OURS",1_750,27.43*1750,"2nd generation",True),
 ("804 N White Horse Pike, Magnolia","OURS",3_035,None,"2nd generation",True),
 ("Avis Budget, Lawnside","THEIRS",3_300,27.96*3300,"2nd generation",True),
 ("Wendy's, Voorhees","THEIRS",3_321,157_659,"Build-to-suit",False),
 ("Wawa, Chesilhurst","THEIRS",5_585,325_000,"Build-to-suit",False),
 ("Walgreens, Blackwood","THEIRS",14_870,463_823,"Build-to-suit",False),
 ("ALDI, Voorhees","THEIRS",19_054,246_950,"2nd generation",True),
 ("706 N White Horse Pike, Magnolia","OURS",40_000,11.50*40000,"Flex / industrial",True),
]
print(f"{'Comparable':34s}{'Source':>8s}{'SF':>8s}{'$/SF':>9s}  {'Type':18s} Valid?")
for n,src,sf,rent,typ,valid in comps:
    psf=f"{rent/sf:8.2f}" if rent else "     n/a"
    print(f"{n:34s}{src:>8s}{sf:>8,d}{psf}  {typ:18s} {'YES' if valid else 'no - BTS'}")

print("\n"+"="*80); print("THE SIZE EFFECT  —  fit on second-generation comps only"); print("="*80)
pts=[(1373,39.33),(1750,27.43),(3300,27.96),(19054,12.96),(40000,11.50)]
n=len(pts); xs=[math.log(a) for a,_ in pts]; ys=[b for _,b in pts]
mx=sum(xs)/n; my=sum(ys)/n
b=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs)
a=my-b*mx
ss_t=sum((y-my)**2 for y in ys); ss_r=sum((y-(a+b*x))**2 for x,y in zip(xs,ys))
print(f"  rent/SF = {a:.2f} {b:+.3f} x ln(SF)     R^2 = {1-ss_r/ss_t:.2f}")
for sf in (1373,1750,3300,4400,5585,19054):
    tag="  <== OUR BUILDING" if sf==4400 else ""
    print(f"    {sf:>6,d} SF -> ${a+b*math.log(sf):5.2f}/SF{tag}")
pred=a+b*math.log(SF)
print(f"\n  Fitted value at 4,400 SF: ${pred:.2f}/SF")
print(f"  Our underwritten market rent: ${MKT:.2f}/SF  ({'conservative' if MKT<pred else 'aggressive'} by ${abs(pred-MKT):.2f})")

print("\n"+"="*80); print("CLAIM vs READ  —  the offering memorandum's selling points"); print("="*80)
rows=[
 ("Absolute NNN, zero landlord obligations","TRUE and valuable - we agree, and it is why the floor holds"),
 ("8.25% year-one cap rate","True arithmetic, wrong rent. On market rent the same price is a 6.05% cap"),
 ("Below replacement cost at $363/SF","At their price, barely. At ours ($250/SF) it is decisively true"),
 ("3-lane drive-thru","AGREE - it is the single best feature and widens the tenant pool"),
 ("+3.13 acres, room to expand","AGREE - and we value it at zero, so it is free upside"),
 ("Double personal guarantee","Two individuals is not a covenant. Worth ~75bps, not a headline"),
 ("Barrier-to-entry licensed industry","Cuts both ways - only 2 licences in the township means a THIN re-let market"),
 ("Affluent demographics, $123,940 avg HH income","TRUE - supports the medical and bank backfill, which is our base case"),
]
for c,r in rows: print(f"  THEY SAY : {c}\n  WE READ  : {r}\n")
