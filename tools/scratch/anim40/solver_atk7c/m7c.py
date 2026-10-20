"""solver 7c measures, play-true-ish on the built clip (her own legs). python m7c.py CLIP [-v]
wand runs: the left fist (hand_l..middle_01_l midpoint) in her rest torso frame (taken through spine_02):
  y cm (navel 115, underbust 130, bust front z 17), z cm forward, x cm out; elbow deg; at the fwd extreme + back extreme.
axes runs: the left axe head (verts of viking_axe@hand_l more than 0.45 m up the haft) skin distance (cm) to her
  knee (calf_l-weighted verts within 8 cm of the knee joint), shin (calf_l verts below that), feet (foot/ball either side);
  haft angle back from vertical (+ back), head fwd of knee (cm), edge dir, elbow, upper arm out, fist fwd of hip crease."""
import sys, json
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
from skin import Body
from scipy.spatial import cKDTree

name = sys.argv[1]; verb = '-v' in sys.argv
b = Body.heroine(jiggle=False)
c = b.clip(name, ANIM / 'out/clips'); Gs = b.frames(c)
I = b.sk.index if hasattr(b, 'sk') else None
if I is None:
    import audit as A
    I = A.Skeleton.load(A.DATA / 'heroine_skeleton.json').index
R = b.rest
def P_(G, j): return G[I[j]][:3, 3] * 100
def to_rest(G, j, x):  # world cm point -> her rest body frame through bone j
    M = R[I[j]] @ np.linalg.inv(G[I[j]]); return (M[:3, :3] @ (x / 100) + M[:3, 3]) * 100
def ang(a, b_, c_):
    u, v = a - b_, c_ - b_; return np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
rows = []
if 'wand' in name:
    for f, G in enumerate(Gs):
        fist = (P_(G, 'hand_l') + P_(G, 'middle_01_l')) / 2
        r = to_rest(G, 'spine_02', fist)
        el = ang(P_(G, 'upperarm_l'), P_(G, 'lowerarm_l'), P_(G, 'hand_l'))
        hip = to_rest(G, 'pelvis', fist)
        rows.append((f, r, el, hip))
    zs = np.array([r[1][2] for r in rows]); fwd, bk = int(zs.argmax()), int(zs.argmin())
    for tag, i in (('fwd', fwd), ('back', bk)):
        f, r, el, hip = rows[i]
        print(f"{name:22s} {tag:4s} f{f:2d} fist x {r[0]:5.1f} y {r[1]:6.1f} (navel+{r[1]-115:5.1f}, underbust {r[1]-130:+5.1f}) z {r[2]:5.1f} (bust front +{r[2]-17:5.1f}) elbow {el:4.0f}  pelvis-frame z {hip[2]:5.1f}")
    if verb:
        for f, r, el, hip in rows: print(f"  f{f:2d} x {r[0]:5.1f} y {r[1]:6.1f} z {r[2]:5.1f} el {el:4.0f}")
else:
    arms = json.load(open(ANIM / 'data/arms_local.json')); d = arms['viking_axe@hand_l']
    v = np.array(d['v']); hdir = np.array([0.0, 0.63, 0.78]); hd = v[(v @ hdir) > 0.45]; tip = v[np.argmax(v @ hdir)]
    edge_l = np.array([0.0, 0.78, -0.63])
    W, J = b.W, b.J
    dom = J[np.arange(len(J)), W.argmax(1)]
    names = {j: n for n, j in I.items()}
    dn = np.array([names.get(int(j), '') for j in dom])
    calf = np.isin(dn, ['calf_l', 'calf_twist_01_l', 'calf_twist_02_l'])
    feet = np.isin(dn, ['foot_l', 'ball_l', 'foot_r', 'ball_r'])
    thigh = np.isin(dn, ['thigh_l', 'thigh_twist_01_l', 'thigh_twist_02_l'])
    out = []
    for f, G in enumerate(Gs):
        P = b.pose(G) * 100
        M = G[I['hand_l']]
        H = (M[:3, :3] @ hd.T).T * 100 + M[:3, 3] * 100
        T = (M[:3, :3] @ tip) * 100 + M[:3, 3] * 100
        hand = M[:3, 3] * 100
        kn = P_(G, 'calf_l')
        dk = np.linalg.norm(P - kn, axis=1)
        knee = (calf | thigh) & (dk < 9); shin = calf & ~knee
        dist = lambda m: float(cKDTree(P[m]).query(H)[0].min())
        pel = P_(G, 'pelvis'); lat = P_(G, 'thigh_l') - P_(G, 'thigh_r'); lat[1] = 0; lat /= np.linalg.norm(lat)
        fw = np.cross(lat, [0, 1, 0]); fw *= -1 if fw[2] < 0 else 1
        haft = T - hand; haft /= np.linalg.norm(haft)
        back = np.degrees(np.arctan2(-(haft @ fw), -haft[1]))
        outa = np.degrees(np.arctan2(haft @ lat, -haft[1]))
        e = M[:3, :3] @ edge_l; e /= np.linalg.norm(e)
        crease = (P_(G, 'thigh_l'))
        el = ang(P_(G, 'upperarm_l'), P_(G, 'lowerarm_l'), P_(G, 'hand_l'))
        ua = P_(G, 'lowerarm_l') - P_(G, 'upperarm_l'); uo = np.degrees(np.arctan2(ua @ lat, -ua[1]))
        head_c = H.mean(0)
        out.append((f, dist(knee), dist(shin), dist(feet), back, outa, (head_c - kn) @ fw, (hand - crease) @ fw,
                    e @ fw, e @ lat, e[1], el, uo, (head_c - kn) @ lat))
    a = np.array(out)
    print(f"{name:22s} head-to-skin min cm: knee {a[:,1].min():5.1f} (f{int(a[a[:,1].argmin(),0])}) shin {a[:,2].min():5.1f} (f{int(a[a[:,2].argmin(),0])}) feet {a[:,3].min():5.1f} (f{int(a[a[:,3].argmin(),0])})"
          f" | haft back {a[:,4].min():.0f}..{a[:,4].max():.0f} out {a[:,5].min():.0f}..{a[:,5].max():.0f} | head fwd of knee max {a[:,6].max():.1f}"
          f" | fist fwd of crease max {a[:,7].max():.1f} | edge fwd {a[:,8].min():.2f}..{a[:,8].max():.2f} | elbow {a[:,11].min():.0f}..{a[:,11].max():.0f} | uarm out {a[:,12].min():.0f}..{a[:,12].max():.0f} | head out of knee min {a[:,13].min():.1f}")
    if verb:
        for r in a: print("  f%2d knee %5.1f shin %5.1f feet %5.1f back %4.0f out %4.0f hfk %5.1f fist %5.1f edge f%.2f l%.2f u%.2f el %4.0f uo %4.0f hout %5.1f" % tuple(r))
