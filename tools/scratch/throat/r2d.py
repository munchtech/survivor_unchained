from lib import *
a=load(sys.argv[1]); U0=a[3]
for f in sys.argv[2:]:
    U=load(f)[3]; d=np.linalg.norm(U-U0,axis=1); m=d>1e-4; th,r=cyl(U0)
    print(f[-10:], m.sum(), "th %.0f..%.0f y %.3f..%.3f max %.1fmm"%(th[m].min(),th[m].max(),U0[m,1].min(),U0[m,1].max(),d.max()*1e3) if m.any() else "")
