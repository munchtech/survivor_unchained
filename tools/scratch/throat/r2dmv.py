from lib import *
a=load(sys.argv[1]); U0=a[1]; th,r=cyl(U0); dh=cKDTree(a[5]).query(U0)[0]
for f in sys.argv[2:]:
    U=load(f)[1]; d=np.linalg.norm(U-U0,axis=1)*1e3; print(f[-8:])
    for lo,hi in ((0,.005),(.005,.01),(.01,.015),(.015,.02),(.02,.03),(.03,.045),(.045,.07),(.07,.1),(.1,.14)):
        m=(dh>=lo)&(dh<hi)&(r<0.17)&(U0[:,1]>1.4)
        print("  dh %.3f-%.3f max %.1f mean %.2f  front(|th|<40) max %.1f side(40-110) max %.1f"%(lo,hi,d[m].max(),d[m].mean(),d[m&(np.abs(th)<40)].max(),d[m&(np.abs(th)>40)&(np.abs(th)<110)].max()))
