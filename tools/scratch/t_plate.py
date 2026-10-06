import sys, math, time
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import numpy as np
from PIL import Image
import forge as F, frames as FR, ornament as O, preview as PV

SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\.shots"
V = sys.argv[1] if len(sys.argv) > 1 else "v2"


def plate_post(s, m, st, k, tx):
    holes = np.zeros((s.h, s.w), np.float32)
    top = st.rim_height * k
    for i, (cx, cy, sx, sy) in enumerate(FR._corner_centres(s, m, st, k)):
        # A drawn bar along each edge from the coin, ending in a tight scroll.
        for axis in (0, 1):
            if axis == 0:
                start = (cx + sx * 8 * k, cy)
                end = (cx + sx * 21 * k, cy + sy * 0 * k)
                curl = O.spiral(cx + sx * 24 * k, cy + sy * 4.2 * k, 4.2 * k, 1.0 * k, math.pi / 2 * (-sy), 0.85 * (1 if sx * sy > 0 else -1), 26)
            else:
                start = (cx, cy + sy * 8 * k)
                end = (cx, cy + sy * 21 * k)
                curl = O.spiral(cx + sx * 4.2 * k, cy + sy * 24 * k, 4.2 * k, 1.0 * k, (0 if sx < 0 else math.pi), -0.85 * (1 if sx * sy > 0 else -1), 26)
            path = [start, end] + curl
            O.forged_bar(s, path, 6.0 * k, 1.8 * k, 3.6 * k, mat="iron", base=top + 0.3 * k)
        cov, hole = O.coin(s, cx, cy, 34 * k, mat="iron", base=top + 0.8 * k)
        holes = np.maximum(holes, hole)
    band = np.clip((FR_d(s) - st.lip * k) / (2 * k), 0, 1) * np.clip((st.rim * k - 3 * k - FR_d(s)) / (2 * k), 0, 1)
    starts = [(60 * k, 10 * k), (s.w - 52 * k, s.h - 12 * k), (11 * k, s.h - 64 * k)]
    veins = O.cracks(s, band, seed=3, length=40 * k, step=1.5 * k, width=0.9 * k, depth=0.9 * k, start_pts=starts)
    light = O.vein_light(veins, awake=0.0, sleeping=1.0) + holes[..., None] * (O.EMBER_DEEP * 0.45 + O.EMBER * 0.10)
    return light


def FR_d(s):
    return F.sd_box(s.xx, s.yy, s.w / 2, s.h / 2, s.w / 2 - 1, s.h / 2 - 1, 6 * 2)


def build_plate(ss=2):
    st = FR.Style(rim=28, lip=5, rim_height=7, inner_bevel=4, centre_drop=2.5, inlay=33, inlay_w=3.0,
                  corner=None, seed=11, dents=0.7, dent_cell=34, centre_dents=0.35, grain=0.10)
    st.extra["corner_off"] = 27
    return FR.frame(512, 512, (28, 28, 28, 28), st, ss=ss, post=plate_post)


t = time.time()
img = build_plate()
print("built", time.time() - t)
img.save(SCR + rf"\plate_{V}.png")
shown = PV.halve(img)
big = PV.nine(shown, (1500, 790), (28, 28, 28, 28), tile=True)
bg = Image.open(SHOTS + r"\base_char.png").convert("RGBA")
comp = PV.over(bg, big, (210, 145))
comp.save(SCR + rf"\plate_{V}_ctx.png")
comp.crop((190, 125, 190 + 480, 125 + 270)).resize((960, 540), Image.NEAREST).save(SCR + rf"\plate_{V}_zoom.png")
img.crop((0, 0, 128, 128)).resize((512, 512), Image.NEAREST).save(SCR + rf"\plate_{V}_corner.png")
