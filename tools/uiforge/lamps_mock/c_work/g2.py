import numpy as np, cv2
from PIL import Image
O='../shoot/out/'
A=np.asarray(Image.open(O+'u25_today_lamps.png').convert('RGB')).astype(np.float32)
W=np.asarray(Image.open(O+'u25_today_wicks.png').convert('RGB')).astype(np.float32)
N=np.asarray(Image.open(O+'u25_today_lamps_night.png').convert('RGB')).astype(np.float32)
x0,y0,x1,y1=1016,145,1891,1010
a=A[y0:y1,x0:x1]; w=W[y0:y1,x0:x1]; n=N[y0:y1,x0:x1]
H,Wd=a.shape[:2]; yw=772-y0
K=np.array([0.163,0.161,0.156]); C=np.array([21.83,18.28,19.51])
def nconv(img,m,s):
    m=m.astype(np.float32)
    num=cv2.GaussianBlur(img*m[...,None],(0,0),s); den=cv2.GaussianBlur(m,(0,0),s)[...,None]
    return num/np.maximum(den,1e-4), den[...,0]
up=np.zeros((H,Wd),bool); up[:yw-16]=True
lo=np.zeros((H,Wd),bool); lo[yw+1:]=True
agree=(np.abs(a-w).max(2)<5)&up
P=w*K+C
B,_=nconv(a,agree,4)
da=np.abs(a-B).max(2); dw=np.abs(w-B).max(2)
TA=np.zeros((H,Wd),bool)
TA|= up & ~agree & (da>=dw)
TA|= up & ~agree & (da>7)
TA|= lo & (np.abs(a-P).max(2)>6)
band=~up&~lo
Bb,_=nconv(a,~TA&(up|lo),5)
TA|= band & (np.abs(a-Bb).max(2)>5)
TA=cv2.dilate(TA.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
Wclean= up & (np.abs(w-B).max(2)<6)
print('TA frac',TA.mean())
day=a.copy(); hole=TA.copy()
m=TA&Wclean; day[m]=w[m]; hole&=~m
m=TA&lo; day[m]=P[m]; hole&=~m
print('day hole frac',hole.mean())
np.save('TA.npy',TA); np.save('dayhole.npy',hole)
def fill(img,hole,seed=1):
    out=img.copy(); known=~hole
    tone=np.zeros_like(img); got=np.zeros(hole.shape,bool)
    for s in (2,4,8,16,32):
        t,den=nconv(img,known,s); ok=(den>0.15)&~got&hole
        tone[ok]=t[ok]; got|=ok
    # grain: local hi-pass std from known pixels
    hp=img-cv2.GaussianBlur(img,(0,0),2)
    sd=np.sqrt(nconv(hp**2,known&~cv2.dilate(hole.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool),12)[0].mean(2,keepdims=True))
    rng=np.random.default_rng(seed); g=rng.normal(0,1,img.shape[:2]).astype(np.float32)
    g=cv2.GaussianBlur(g,(0,0),0.7); g/=g.std()
    tone=tone+g[...,None]*sd
    out[hole]=tone[hole]; return out
day=fill(day,hole)
night=fill(n,TA,2)
Aout=A.copy(); Aout[y0:y1,x0:x1]=day; Nout=N.copy(); Nout[y0:y1,x0:x1]=night
Image.fromarray(np.clip(Aout,0,255).astype(np.uint8)).save('ground_day.png')
Image.fromarray(np.clip(Nout,0,255).astype(np.uint8)).save('ground_night.png')
Image.fromarray(np.clip(Aout,0,255).astype(np.uint8)).crop((1000,120,1910,640)).save('gd_crop1.png')
Image.fromarray(np.clip(Aout,0,255).astype(np.uint8)).crop((1000,600,1910,1030)).save('gd_crop2.png')
Image.fromarray(np.clip(Nout,0,255).astype(np.uint8)).crop((1000,120,1910,640)).save('gn_crop1.png')
