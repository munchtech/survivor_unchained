"""UI 23, HUD A: check the baked art (dg_keeper_hud.py) against the mockup with the judge's fixes (mock8.py).

    python tools/uiforge/dg_keeper_check.py [MOCK_DIR]

MOCK_DIR holds mock8.py (the R6 mockup + fixes K1-K4, P1, P2, G1, the snapped inlay) and its sources; its backdrops
are MOCK_DIR/../out/bd21vx_hud1.png (day) and bd21nx_hud0.png (night). For day, night and READY the script runs mock8
(env DXG=0 GAP_R=-17 KEEPER=ks60_2304_0 KLOCK=1), takes its live layers (her figure's light, shine and globe, the seats'
icons, flask, dash, the XP fill, the text, the ember glass) and composites ONLY the baked files at 0.5 by
hud_a_geo.json in their place: keeper.png, the glass, keeper_lip.png, her, panel.png. Prints the mean abs diff per
region against mock8's own frame, then GAPS, the figure-under-panel depths, the corner backdrop px above each end cap,
the keeper vs girl luma, the heights and the READY core. Writes MOCK_DIR/../bake/baked_{day,night,ready}.png and
baked_strips_1x.png (the bottom 320 rows, day over night).
"""
import json, os, runpy, sys
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt as edt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dg_keeper_hud as HB

ROOT = HB.ROOT
UI = HB.UI
MOCK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get('TEMP', ''), 'claude',
                                                            'C--Users-munch-Desktop-survivorsunchained',
                                                            '61174ebb-acb9-4478-bb4b-9e034656f17e', 'scratchpad', 'ui23', 'R6')
BAKE = os.path.join(MOCK, '..', 'bake')
LUMW = HB.LUMW


def run_mock(tod, charge):
    os.environ.update(DXG='0', GAP_R='-17', KEEPER='ks60_2304_0', KLOCK='1', DUMP_GRADE='0')
    sys.argv = ['mock8.py', tod, str(charge), 'CHK', 'A']
    cwd = os.getcwd()
    os.chdir(MOCK)
    if MOCK not in sys.path:
        sys.path.insert(0, MOCK)
    try:
        return runpy.run_path(os.path.join(MOCK, 'mock8.py'), run_name='mock8')
    finally:
        os.chdir(cwd)


def placed(path, rect):
    return HB.place(HB.load_rgba(path), rect[0], rect[1], rect[2], rect[3], (1920, 1080))


def top_of(a, x0, x1, thr=0.2):
    rows = np.nonzero((a[:, x0:x1] > thr).any(1))[0]
    return 1080 - rows.min() if len(rows) else 0


def main():
    geo = json.load(open(os.path.join(UI, 'dg_keeper', 'hud_a_geo.json')))
    krect, prect = geo['keeper']['rect'], geo['panel']['rect']
    Kb = placed(os.path.join(UI, 'dg_keeper', 'keeper.png'), krect)
    Lb = placed(os.path.join(UI, 'dg_keeper', 'keeper_lip.png'), krect)
    Pb = placed(os.path.join(UI, 'dg_panel', 'panel.png'), prect)
    over = HB.over
    girl_same = np.array_equal(np.asarray(Image.open(os.path.join(UI, 'lamp_life', 'drowned', 'lamp_cold.png'))),
                               np.asarray(Image.open(os.path.join(MOCK, 'girl_R6g.png'))))
    print('her art: lamp_cold.png == mock8 girl_R6g.png:', girl_same)
    frames = {}
    for tag, tod, ch in (('day', 'day', 0.5), ('night', 'night', 0.5), ('ready', 'day', 1.0)):
        g = run_mock(tod, ch)
        G, EG, EGA = g['G'], g['EG'], g['EGA']
        out = g['canvas'].copy()
        out = over(out, Kb)
        out = over(out, EG)
        out = over(out, Lb)
        out[..., :3] += EGA * (1 - 0.75 * Lb[..., 3])[..., None]
        out = over(out, G)
        out = over(out, Pb)
        for L in (g['SE_W'], g['FD'], g['ME_LV']):
            out = over(out, L)
        out = over(out, g['T'])
        S, DXG = g['S'], g['DXG']
        out = over(out, g['place'](g['_badge'], DXG + 295.33 + (590 - 295.33) * S, 1080 - (1080 - 864) * S, 40 * S, 28 * S))
        ref = g['out']
        frames[tag] = out
        res = Image.fromarray((np.clip(out[..., :3], 0, 1) * 255 + 0.5).astype(np.uint8))
        os.makedirs(BAKE, exist_ok=True)
        res.save(os.path.join(BAKE, f'baked_{tag}.png'))
        yy, xx = np.mgrid[0:1080, 0:1920]
        egx, egy = g['egx'], g['egy']
        glass = np.hypot(xx - egx, yy - egy) < 37 + 8
        regs = {'girl': (xx < 576) & (yy > 800), 'panel': (xx >= 576) & (xx < 1344) & (yy >= 988),
                'keeper': (xx >= 1344) & (yy > 860) & ~glass, 'glass': glass}
        print('nan out/ref', int(np.isnan(out).sum()), int(np.isnan(ref).sum()))
        dif = np.abs(np.clip(out[..., :3], 0, 1) - np.clip(ref[..., :3], 0, 1)).max(-1) * 255
        print(f'[{tag}] mean abs diff /255 vs mock8: ' + '  '.join(f'{k} {dif[m].mean():.2f} (p99 {np.percentile(dif[m], 99):.1f})' for k, m in regs.items()))
        Yc = np.clip(out[..., :3], 0, 1) @ LUMW
        if tag == 'ready':
            core = np.hypot(xx - egx, yy - egy) < 0.35 * 37
            print(f'[ready] READY core luma {Yc[core].mean():.3f} (mock8 {(np.clip(ref[..., :3], 0, 1) @ LUMW)[core].mean():.3f})')
            continue
        # gaps, depths, corners, tones, heights
        pl = Pb[..., 3] > 0.85
        dpl = edt(~pl)
        rm = (Kb[..., 3] > 0.25) | (EG[..., 3] > 0.5)
        rm[:, :1100] = False
        print(f'[{tag}] GAPS girl->panel {dpl[G[..., 3] > 0.25].min():.1f}  panel->right {dpl[rm].min():.1f}')
        if tag == 'day':
            dl, dr = [], []
            for y in range(int(HB.PL_TOP + HB.VOL_R), 1080):
                row = Pb[y, :, 3] > 0.5
                xl = np.nonzero(row[:960])[0].min()
                xr = np.nonzero(row[960:])[0].max() + 961
                ge = np.nonzero(G[y, :960, 3] > 0.5)[0]
                ke = np.nonzero(Kb[y, 960:, 3] > 0.5)[0]
                dl.append(ge.max() + 1 - xl if len(ge) else np.nan)
                dr.append(xr - (ke.min() + 960) if len(ke) else np.nan)
            dl, dr = np.array(dl, float), np.array(dr, float)
            ys = np.arange(int(HB.PL_TOP + HB.VOL_R), 1080)
            bad = [int(y) for y, a, b in zip(ys, dl, dr) if not (3.5 <= a <= 10.5 and 3.5 <= b <= 10.5)]
            print(f'[day] figure under panel, rows {ys[0]}..1079: girl {np.nanmin(dl):.0f}..{np.nanmax(dl):.0f} px  keeper '
                  f'{np.nanmin(dr):.0f}..{np.nanmax(dr):.0f} px  rows outside 4-10: {bad[:12]}{" ..." if len(bad) > 12 else ""} ({len(bad)})')
        cov = 1 - (1 - G[..., 3]) * (1 - Kb[..., 3]) * (1 - Pb[..., 3]) * (1 - EG[..., 3])
        x0, x1 = int(HB.PL_X0) - 14, int(HB.PL_X0 + 2 * HB.VOL_R)
        y0, y1 = int(HB.PL_TOP) - 14, int(HB.PL_TOP + HB.VOL_R)
        cl_ = int((cov[y0:y1, x0:x1] < 0.5).sum())
        cr_ = int((cov[y0:y1, 1920 - x1:1920 - x0] < 0.5).sum())
        print(f'[{tag}] corner backdrop px above the end caps (box {x1 - x0}x{y1 - y0}): left {cl_}  right {cr_}')
        g_sel = g['g_sel']
        km = (Kb[..., 3] > 0.98) & (g['KFIRE'] < 0.05) & ((EGA @ LUMW) < 0.03) & (EG[..., 3] < 0.05)
        gp = np.percentile(Yc[g_sel], [50, 90]); kp = np.percentile(Yc[km], [50, 90])
        print(f'[{tag}] luma p50/p90 girl {gp[0]:.3f}/{gp[1]:.3f}  keeper {kp[0]:.3f}/{kp[1]:.3f}  '
              f'(keeper/girl {kp[0] / gp[0]:.3f}/{kp[1] / gp[1]:.3f})')
        if tag == 'day':
            egm = (EG[..., 3] > 0.2) | ((EGA @ LUMW) > 0.08)
            right = max(top_of(Kb[..., 3], 1240, 1920), 1080 - np.nonzero(egm[:, 1240:].any(1))[0].min())
            print(f'[day] HEIGHTS left {top_of(G[..., 3], 0, 700)}  middle {top_of(Pb[..., 3], 600, 1320, 0.6)}  right {right}')
    strip = np.concatenate([frames['day'][760:], frames['night'][760:]], 0)
    Image.fromarray((np.clip(strip[..., :3], 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(BAKE, 'baked_strips_1x.png'))
    print('wrote', os.path.abspath(BAKE))


if __name__ == '__main__':
    main()
