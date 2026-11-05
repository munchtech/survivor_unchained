# B6 WIP: a numpy prototype of fx_cel_bolt's heat field (flow lanes as tongues), for designing the shape against MB5's crop offline before porting to the shader. python tools/style/fx_bolt_proto.py OUT.png [JSON params]
import numpy as np, sys, json
from PIL import Image
S = sys.argv[1] if len(sys.argv) > 1 else 'out.png'
P = dict(R=0.62, span=3.4, N=6.0, warp=0.22, tl=(0.25, 1.0), core=0.72, mid=0.40, t=0.0)
P.update(json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})
W, H = 490, 260
span = P['span']
xs = (np.arange(W) + 0.5) / W * span; ys = ((np.arange(H) + 0.5) / H - 0.5) * 2 * (H / W * span / 2)  # isotropic: y half-extent
X, Y = np.meshgrid(xs, ys)
rng = np.random.default_rng(3)
def h1(i): return np.modf(np.sin(i * 127.1 + 311.7) * 43758.5453)[0] % 1.0
R = P['R']; hx = span - 1.0; x0 = 0.1
along = np.clip((X - x0) / (hx - x0), 0, 1)
t = P['t']
# flow lanes: the body's half-width behind the head, flaring then ragged
w = R * (0.75 + 0.35 * np.sin(np.pi * along ** 0.8))
lane = Y / w
lane = lane + P['warp'] * np.sin(X * 2.3 - t * 5 + lane * 2.0) * (1 - along)
N = P['N']
k = (lane + 1) * N / 2
idx = np.floor(k); u = k - idx
prof = 1 - np.abs(2 * u - 1)           # 1 in a tongue's middle, 0 at its sides
Li = P['tl'][0] + (P['tl'][1] - P['tl'][0]) * h1(idx + 0.37 * np.floor(t * 3))   # each tongue's reach back from the head
reach = (hx - X) / (hx - x0)            # 0 at the head, 1 at the tail
tongue = prof * np.clip(1 - reach / np.maximum(Li, 1e-3), 0, 1) ** 0.6   # tapering to its tip
tongue = np.where(np.abs(lane) <= 1, tongue, 0)
dh = np.hypot(X - hx, Y) / R            # head
head = 1 - dh
heat = np.maximum(head * 1.0 + 0.25, tongue * 0.95 - 0.02)   # the head's rim at heat 0.25
heat = np.where(X > hx, head + 0.25 * np.clip(1 - (X - hx) / R, 0, 1), heat)
heat = np.where(dh < 1, np.maximum(heat, 0.25 + head * 0.9), heat)
# bands
bg = np.array([22, 30, 44]) / 255
col = {'edge': '#cb451e', 'mid': '#fc8923', 'core': '#ffe496', 'glow': '#67281f'}
c = {k: np.array([int(v[i:i + 2], 16) for i in (1, 3, 5)]) / 255 for k, v in col.items()}
img = np.zeros((H, W, 3)) + bg
body = heat > 0.02
img[body] = c['edge']
img[heat > P['mid']] = c['mid']
img[heat > P['core']] = c['core']
# glow off the head
gd = np.clip(dh - 1, 0, None)
g = 0.65 * np.exp(-gd / 0.13) * (gd < 0.35)
m = ~body
img[m] = img[m] * (1 - g[m, None]) + c['glow'] * g[m, None]
Image.fromarray((img * 255).astype(np.uint8)).save(S)
print('shares', round(float((body & (heat <= P['mid'])).mean() / body.mean()), 3), round(float(((heat > P['mid']) & (heat <= P['core'])).mean() / body.mean()), 3), round(float((heat > P['core']).mean() / body.mean()), 3))
