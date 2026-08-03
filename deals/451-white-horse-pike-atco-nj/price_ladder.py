import importlib.util,sys,io,contextlib
spec=importlib.util.spec_from_file_location("om","ONE_MODEL.py")
om=importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(om)
rows=[]
for P in (1_000_000,1_100_000,1_150_000,1_200_000,1_250_000,1_300_000,1_400_000,1_600_000):
    om.PRICE=P
    cs={n:om.run(*a,**k) for n,a,k in [
      ("floor",("f",18.00,18,35,False,0.0900),{}),
      ("base",("b",22.00,12,45,False,0.0875),{}),
      ("growth",("g",24.00,12,60,True,0.0800),{}),
      ("renew",("r",0.00,0,0,False,0.0925),{"renew":True})]}
    rows.append((P,P/4400,132000/P,cs["floor"],cs["base"],cs["renew"],cs["growth"]))
print(f"{'Price':>10}{'$/SF':>7}{'cap':>8}{'floorU':>9}{'floorL':>9}{'baseU':>9}{'baseL':>9}{'renU':>9}{'renL':>9}{'grU':>9}{'grL':>9}")
for P,psf,cap,f,b,r,g in rows:
    print(f"{P:>10,.0f}{psf:>7.0f}{cap:>8.2%}{f['u']:>9.2%}{f['l']:>9.2%}{b['u']:>9.2%}{b['l']:>9.2%}{r['u']:>9.2%}{r['l']:>9.2%}{g['u']:>9.2%}{g['l']:>9.2%}")
