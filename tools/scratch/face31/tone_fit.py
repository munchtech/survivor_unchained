"""fit.py DIR: per face at its default bead, the HerFaceTone factor that takes the cheek to the target
(L chest+LT, hue mean(neck,chest)+HT, C max(cheek, 1.12 chest)). Prints new = old * k."""
import sys, math, numpy as np
from PIL import Image
sys.argv=[sys.argv[0], sys.argv[1], '/dev/null']
exec(open(__file__.replace('tone_fit.py','tone_meas.py')).read().split("d, out = sys.argv")[0])
D = sys.argv[1]
import json, os
old = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tone_tones.json")))  # the table the DIR was shot with
LT, HT = 0.015, 1.0  # r1 used 0.02, 2.0: hue overshot by ~2 deg on the fair faces
for a in sys.argv[3:] if False else []: pass
dflt={'own':'fair','highborn':'fair','vixen':'fair','doe':'rose','sunborn':'brown','moonlit':'fair','saffron':'warm','wildling':'rose','hardwon':'rose','fey':'fair'}
M1=np.array([[0.4122214708,0.5363325363,0.0514459929],[0.2119034982,0.6806995451,0.1073969566],[0.0883024619,0.2817188376,0.6299787005]])
M2=np.array([[0.2104542553,0.7936177850,-0.0040720468],[1.9779984951,-2.4285922050,0.4505937099],[0.0259040371,0.7827717662,-0.8086757660]])
def tolin(L,C,h):
    lab=np.array([L,C*math.cos(math.radians(h)),C*math.sin(math.radians(h))])
    return np.linalg.solve(M1, (np.linalg.solve(M2,lab))**3)
def mean_lin(im,box):
    x0,y0,x1,y1=box; px=lin(im[y0:y1,x0:x1].reshape(-1,3)); Y=px@np.array([.2126,.7152,.0722])
    lo,hi=np.percentile(Y,[30,85]); return px[(Y>=lo)&(Y<=hi)].mean(0)
for f,b in dflt.items():
    if f not in old: continue
    im=np.asarray(Image.open(f'{D}/{f}_{b}.png').convert('RGB')).astype(float)/255
    ck,nk,cs=(region(im,BOXES[k]) for k in ('cheek','neck','chest'))
    hn=nk[2]+((cs[2]-nk[2]+180)%360-180)/2
    t=tolin(cs[0]+LT, max(ck[1],1.12*cs[1]), hn+HT)
    k=t/mean_lin(im,BOXES['cheek'])
    n=np.array(old[f])*k
    print(f"{f:9s} dL {100*(ck[0]-cs[0]):+.1f} dh {ck[2]-hn:+.1f}  k {k.round(3)}  new ({n[0]:.3f}f, {n[1]:.3f}f, {n[2]:.3f}f)")
