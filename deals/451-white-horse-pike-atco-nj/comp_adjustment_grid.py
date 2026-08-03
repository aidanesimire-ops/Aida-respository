SF=4400
print("="*104); print("LEASE COMP ADJUSTMENT GRID  —  adjusted to subject: 4,400 SF, Atco, 10-15 yr term"); print("="*104)
# only attributes we actually know are adjusted; unknowns left at 0 and flagged
comps=[
 # name, city, sf, rent, size_adj, loc_adj, term_adj, note
 ("501 Delsea Dr","Sewell",1_373,39.33,-0.30,-0.10, 0.00,"Term not disclosed"),
 ("340 S White Horse Pike","Berlin",1_750,27.43,-0.20, 0.00, 0.00,"Asking rate; has drive-thru"),
 ("Avis Budget, 341 N WHP","Lawnside",3_300,27.96,-0.10,-0.10,-0.05,"Signed Jun-2025; 3-yr term"),
]
print(f"{'#':>2} {'Comparable':26s}{'City':11s}{'SF':>7s}{'Rent/SF':>9s}{'Size':>7s}{'Loc':>7s}{'Term':>7s}{'Net':>8s}{'Adjusted':>10s}  Note")
print("-"*104)
adj=[]
for i,(n,c,sf,r,a1,a2,a3,note) in enumerate(comps,1):
    net=(1+a1)*(1+a2)*(1+a3)-1
    v=r*(1+a1)*(1+a2)*(1+a3); adj.append(v)
    print(f"{i:>2} {n:26s}{c:11s}{sf:>7,d}{r:>9.2f}{a1:>7.0%}{a2:>7.0%}{a3:>7.0%}{net:>8.0%}{v:>10.2f}  {note}")
print("-"*104)
lo,hi=min(adj),max(adj); mean=sum(adj)/len(adj); med=sorted(adj)[len(adj)//2]
print(f"{'':2} {'INDICATED RANGE':26s}{'':11s}{'':7s}{'':9s}{'':7s}{'':7s}{'':7s}{'':8s}{lo:>10.2f} to {hi:.2f}")
print(f"{'':2} {'Mean / Median':26s}{'':11s}{'':7s}{'':9s}{'':7s}{'':7s}{'':7s}{'':8s}{mean:>10.2f} / {med:.2f}")
print(f"{'':2} {'CONCLUDED  (we use)':26s}{'':11s}{'':7s}{'':9s}{'':7s}{'':7s}{'':7s}{'':8s}{22.00:>10.2f}  <- low end of the range, deliberately")
print(f"\n   At $22.00/SF the subject rents for ${22*SF:,.0f}/yr.  In-place cannabis rent is $132,000 = ${132000/SF:.2f}/SF, a {132000/(22*SF)-1:.0%} premium.")

print("\n"+"="*104); print("COMPS EXCLUDED FROM THE GRID, AND WHY"); print("="*104)
ex=[("7 Brew","Clementon",510,303.92,"Build-to-suit — rent repays land + construction, not a letting"),
    ("Wendy's","Voorhees",3_321,47.47,"Build-to-suit"),
    ("Wawa","Chesilhurst",5_585,58.19,"Build-to-suit, includes fuel"),
    ("Walgreens","Blackwood",14_870,31.19,"Build-to-suit, national credit, legacy rent"),
    ("ALDI","Voorhees",19_054,12.96,"Grocery big box — 4.3x subject size, different product"),
    ("706 N WHP","Magnolia",40_000,11.50,"Flex / industrial — different use class"),
    ("804 N WHP","Magnolia",3_035,None,"Rate not published — closest analogue, worth a call"),
    ("2 S WHP","Stratford",None,None,"Rate not published")]
for n,c,sf,r,why in ex:
    print(f"   {n:14s}{c:13s}{(f'{sf:,} SF' if sf else 'n/a'):>10s}{(f'${r:.2f}' if r else '  n/a'):>10s}   {why}")

print("\n"+"="*104); print("SALE COMP SCHEDULE  —  cannabis single-tenant net lease"); print("="*104)
sales=[("LivWell","Aurora, CO",1_025_000,0.0887,"n/a","Corporate","n/a","CLOSED Apr-26"),
 ("Cookies","Kalamazoo, MI",3_100_000,0.0825,"10 yrs","Corporate","n/a","Listing"),
 ("Curaleaf","Worth, IL",None,0.0935,"n/a","Corporate","10% / 5 yrs","Listing"),
 ("Ascend","Pennsylvania",None,0.0925,"n/a","Corporate","n/a","Listing"),
 ("Jungle Boys","Naples, FL",None,0.0740,"n/a","Corporate","2% / yr","Listing"),
 ("STNL all-tenant avg","US, Q1-2026",None,0.0680,"n/a","Mixed","n/a","Benchmark"),
 ("SUBJECT at ask","Atco, NJ",1_600_000,0.0825,"6.5 yrs","2 personal","NONE","Asking"),
 ("SUBJECT at our offer","Atco, NJ",1_100_000,0.1200,"6.5 yrs","2 personal","NONE","OUR BID")]
print(f"{'Comparable':22s}{'Market':16s}{'Price':>12s}{'Cap':>8s}{'Term':>9s}{'Guarantee':>12s}{'Bumps':>13s}  Status")
print("-"*104)
for n,m,p,c,t,g,b,st in sales:
    print(f"{n:22s}{m:16s}{(f'${p:,}' if p else '—'):>12s}{c:>8.2%}{t:>9s}{g:>12s}{b:>13s}  {st}")
print("-"*104)
print("   Cannabis STNL range 7.40% – 9.35%.  Subject is the only one in the set with NO rent escalations,")
print("   NO corporate guarantee and the shortest remaining term — so it belongs at the wide end, not the tight end.")
