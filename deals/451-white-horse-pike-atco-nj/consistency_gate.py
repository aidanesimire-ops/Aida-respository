from pypdf import PdfReader
import re
t="\n".join(p.extract_text() or "" for p in PdfReader("451 White Horse Pike - IC Deck.pdf").pages)
t=t.replace("−","-").replace("–","-").replace("—","--")
must = ["12.00%","6.13%","8.40%","14.95%","18.33%","-1.08%","6.29%","19.40%","24.43%",
        "$902,000","$1,133,943","$1,664,865","$2,603,000","$1,100,000","$1,250,000",
        "$1,600,000","$250.00","2.00x","21.8%","13.34%","$65,972","$605,000","$495,000",
        "$511,596","1.49x","1.75x","2.78x","3.64x","0.94x","1.53x","3.82x","5.71x",
        "$1,252,500","$22.00","8.25%","8.75%","9.00%","9.25%","8.00%","$25.74","$21.52"]
stale = ["12.0% expected","+6.2%","18.2%","24.2%","$931","$2,186,000","$2,170,000","6.5-year","$1.30M","$1,300,000 value","5.4%","8.7%"]
miss=[m for m in must if m not in t]
hit=[s for s in stale if s in t]
print("PAGES:", len(PdfReader("451 White Horse Pike - IC Deck.pdf").pages))
print("MISSING canonical:", miss or "none")
print("STALE present:", hit or "none")
# ladder cross-check against ONE_MODEL
import importlib.util,io,contextlib
spec=importlib.util.spec_from_file_location("om","ONE_MODEL.py"); om=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()): spec.loader.exec_module(om)
bad=[]
for P,exp in [(1_000_000,("7.79%","10.05%","16.65%","20.02%")),(1_100_000,("6.13%","8.40%","14.95%","18.33%")),
              (1_250_000,("4.03%","6.31%","12.78%","16.17%")),(1_600_000,("0.31%","2.59%","8.88%","12.25%"))]:
    om.PRICE=P
    got=(f"{om.run('f',18,18,35,False,.09)['u']:.2%}",f"{om.run('b',22,12,45,False,.0875)['u']:.2%}",
         f"{om.run('r',0,0,0,False,.0925,renew=True)['u']:.2%}",f"{om.run('g',24,12,60,True,.08)['u']:.2%}")
    if got!=exp: bad.append((P,exp,got))
print("LADDER mismatches:", bad or "none")
