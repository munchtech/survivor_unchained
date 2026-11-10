# B6 round 2: the cel bolt's heat field in numpy, mirrored line for line by shaders/fx_cel_bolt.gdshader (the shape designed here beside MB5's FIRE crop, then ported). python tools/style/fx_bolt_proto.py OUT.png [JSON params]
import numpy as np, sys, json
from PIL import Image
OUT = sys.argv[1]
P = dict(sh=0.0, bo=0.25, bx=1.6, br=0.85, bb=0.6, wv=0.0, bp=2.0, wt=0.3, hs=1.0, hp=1.0, ip=1.0, gf=(0.5, 3.0), gk=1.5, gp=0.7, g0=0.1, span=5.2, R=0.66, W=0.80, x0=0.15, t=0.0, seed=7.0,
         base_tail=0.55, base_head=1.15, lf=(1.0, 1.9), la=(0.55, 0.12), bf=(1.5, 2.6), bthr=(0.05, 0.55), bk=2.5,
         te=0.0, tm=0.34, tc=0.75, wpow=0.5)
P.update(json.loads('{"R":0.36,"wt":2.4,"bx":2.2,"wpow":0.8,"lf":[0.8,2.6],"la":[0.6,0.12],"gf":[0.45,3.2],"gk":2.0,"g0":0.0,"bf":[1.0,3.2],"bthr":[-0.05,1.0],"bp":2.0,"bk":3,"base_tail":0.7,"base_head":1.05,"hp":2.0,"ip":2.0,"bb":0.7,"br":1.0,"wv":0.5,"sh":0.9}'))  # the shader's defaults (fx_cel_bolt.gdshader's uniforms)
P.update(json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})
span = P['span']; H = 260; W = int(round(H * span / 2))
x = (np.arange(W) + 0.5) / W * span; y = ((np.arange(H) + 0.5) / H - 0.5) * 2
X, Y = np.meshgrid(x, y)
def fract(v): return v - np.floor(v)
def hsh(px, py): return fract(np.sin(px * 127.1 + py * 311.7) * 43758.5453)
def gn(px, py):
    ix, iy = np.floor(px), np.floor(py); fx, fy = px - ix, py - iy
    ux = fx**3 * (fx * (fx * 6 - 15) + 10); uy = fy**3 * (fy * (fy * 6 - 15) + 10)
    def g(ox, oy):
        a = hsh(ix + ox, iy + oy) * 6.2831853
        return np.cos(a) * (fx - ox) + np.sin(a) * (fy - oy)
    return ((g(0, 0) * (1 - ux) + g(1, 0) * ux) * (1 - uy) + (g(0, 1) * (1 - ux) + g(1, 1) * ux) * uy) * 1.6
R = P['R']; hx = span - 1.0; x0 = P['x0']; t = P['t']; sd = P['seed']
a = np.clip((X - x0) / (hx - x0), 0, 1)
w = R * (P['wt'] + (1 - P['wt']) * a ** P['wpow'])
v = Y / w
v = v + P['wv'] * (1 - a) * gn(X * 0.35 + 2.0, 0.5 + sd)
dh = np.hypot(np.maximum(X - hx, 0) * P['hs'], Y) / R
inside = np.where(X < hx, np.abs(v), dh)
hot = P['base_tail'] + (P['base_head'] - P['base_tail']) * a ** P['hp']
base = np.where(inside < 1, 1 - inside ** P['ip'], (1 - inside) * P['ip']) * hot
ball = np.hypot((X - (hx - P['bo'])) / P['bx'], Y) / (R * P['br'])
base += P['bb'] * np.clip(1 - ball, 0, 1) ** 0.5
lf = P['lf']; la = P['la']
Xs = X + P['sh'] * np.abs(v)
X_ = X; X = Xs
amp = la[0] + (la[1] - la[0]) * a
n = gn((X + t) * lf[0], v * lf[1] + sd) * 0.65 + gn((X + t) * lf[0] * 2.3 + 5.1, v * lf[1] * 2.1 - sd) * 0.35
heat = base + n * amp
gf = P['gf']
gs = gn((X + t * 0.8) * gf[0] + 3.7, v * gf[1] + sd * 0.7)
heat -= P['gk'] * (1 - a) ** P['gp'] * np.maximum(gs - P['g0'], 0)
bf = P['bf']
b = gn((X + t * 0.6) * bf[0] + 11.0, v * bf[1] + sd * 1.3)
thr = P['bthr'][0] + (P['bthr'][1] - P['bthr'][0]) * a ** P['bp']
heat = np.minimum(heat, (thr - b) * P['bk'])
X = X_
heat -= (1 - np.clip(X / 0.9, 0, 1)) * 1.2
col = {'edge': '#cb451e', 'mid': '#fc8923', 'core': '#ffe496', 'glow': '#67281f'}
c = {k: np.array([int(vv[i:i + 2], 16) for i in (1, 3, 5)]) / 255 for k, vv in col.items()}
img = np.zeros((H, W, 3)) + np.array([22, 30, 44]) / 255
body = heat > P['te']
img[body] = c['edge']; img[heat > P['tm']] = c['mid']; img[heat > P['tc']] = c['core']
gd = np.clip(-heat, 0, None)
g = (0.3 + 0.35 * a) * np.exp(-gd / 0.13) * (gd < 0.35)
m = ~body
img[m] = img[m] * (1 - g[m, None]) + c['glow'] * g[m, None]
Image.fromarray((img * 255).astype(np.uint8)).save(OUT)
bs = body.sum()
print('W', W, 'shares e/m/c', round(float((body & (heat <= P['tm'])).sum() / bs), 3), round(float(((heat > P['tm']) & (heat <= P['tc'])).sum() / bs), 3), round(float((heat > P['tc']).sum() / bs), 3))
