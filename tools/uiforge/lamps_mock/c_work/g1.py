import numpy as np, cv2
from PIL import Image
O='../shoot/out/'
A=np.asarray(Image.open(O+'u25_today_lamps.png').convert('RGB')).astype(np.float32)
W=np.asarray(Image.open(O+'u25_today_wicks.png').convert('RGB')).astype(np.float32)
N=np.asarray(Image.open(O+'u25_today_lamps_night.png').convert('RGB')).astype(np.float32)
x0,y0,x1,y1=1016,145,1891,1010
a=A[y0:y1,x0:x1]; w=W[y0:y1,x0:x1]; n=N[y0:y1,x0:x1]
H=y1-y0; yw=772-y0  # wicks panel bottom (exclusive) -> rows >= yw are raw world in W  (border ~ 760-772)
la=a.mean(2); lw=w.mean(2)
agree=(np.abs(a-w).max(2)<5); agree[yw-14:]=False
print('agree frac upper', agree[:yw-14].mean())
# below: fit transfer world->panel
ys=slice(yw+2,H)
wa=w[ys]; aa=a[ys]
for s in (0,1,2,3,5):
    wb=cv2.GaussianBlur(wa,(0,0),s) if s else wa
    X=wb.reshape(-1,3); Y=aa.reshape(-1,3)
    keep=np.ones(len(X),bool)
    for it in range(4):
        res=[]
        P=np.zeros_like(Y)
        for c in range(3):
            M=np.c_[X[keep][:,c],np.ones(keep.sum())]
            k,_,_,_=np.linalg.lstsq(M,Y[keep][:,c],rcond=None)
            P[:,c]=X[:,c]*k[0]+k[1]; res.append(k)
        e=np.abs(Y-P).max(1); keep=e<6
    print(s, [np.round(r,3) for r in res], 'rms', np.sqrt(((Y-P)[keep]**2).mean()), 'keep', keep.mean())
