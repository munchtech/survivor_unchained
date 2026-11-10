"""B3 round 2's sheets (L1 texture authoring): the three bake-off assets today and as A paints them from the calibrated
albedo (tools/look/build.py's maps, --b3-painted), at 1:1, the play frame and the per-item close camera (--b3-cams,
GameLookdev.Items.cs), beside the board crop at the close row's scale. One sheet per asset (day and night rows).

    bash wtlock.sh python tools/look/sheets_r2.py shoot [--round N]    -> b3r<N>/{today,A}/ (frames, logs)
    python tools/look/sheets_r2.py sheet [--round N]                   -> b3r<N>/sheet_<asset>.png

--round: the round's folder (2 by default; round 3 re-shot the same sheets after the joint solve of the albedos and the
day fill, rigs.json as written, so both arms stand under the new fill).
"""
import json, os, shutil, subprocess, sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import bakeoff  # noqa: E402

_a = sys.argv[1:]
OUT = r"C:\Users\munch\Desktop\survivorsunchained_inputs\look_l1\b3r" + (_a[_a.index("--round") + 1] if "--round" in _a else "2")
ITEMS = ["barrel", "boulder", "setts"]
RIGS = ["day", "night"]


def shoot():
    for arm, maps in (("today", bakeoff.manifest("today")), ("A", None)):
        out = os.path.join(OUT, arm)
        extra = f"--b3-cams {','.join(ITEMS)} " + (f"--b3-maps {maps}" if maps else "--b3-painted")
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "style", "lookdev.py"), "shoot", "--out", out, "--rigs", ",".join(RIGS), "--extra", extra, "--stale-ok"], check=False)  # (the items only: her art needn't be current)
        for r in RIGS:
            for it in ITEMS:
                f = os.path.join(ROOT, "godot", ".shots", f"lookdev_{r}_item_{it}_1.png")
                if os.path.exists(f): shutil.copy2(f, os.path.join(out, f"lookdev_{r}_item_{it}.png"))


def play_crop(arm, rig, item):
    d = os.path.join(OUT, arm); items = json.load(open(os.path.join(d, "check_items.json")))
    name = bakeoff.ASSETS[item]["item"]
    box = next((i["rect"] for i in items.get(f"{rig}_play", []) if i["name"] == name), None)
    im = Image.open(os.path.join(d, f"lookdev_{rig}_play.png")).convert("RGB"); W, H = im.size
    x0, y0, x1, y1 = box; p = 0.15
    bx = [max(0, int((x0 - p * (x1 - x0)) * W)), max(0, int((y0 - p * (y1 - y0)) * H)), min(W, int((x1 + p * (x1 - x0)) * W)), min(H, int((y1 + p * (y1 - y0)) * H))]
    if bx[2] - bx[0] > 600: c = (bx[0] + bx[2]) // 2; bx[0], bx[2] = c - 300, c + 300
    if bx[3] - bx[1] > 400: c = (bx[1] + bx[3]) // 2; bx[1], bx[3] = c - 200, c + 200
    return im.crop(bx)


def close_crop(arm, rig, item):
    im = Image.open(os.path.join(OUT, arm, f"lookdev_{rig}_item_{item}.png")).convert("RGB")
    return im.crop((480, 240, 1440, 840))  # (the middle 960 x 600 at 1:1: the item is centred at the close view's distance)


def sheet():
    f = bakeoff.font(); lab = 26
    for item in ITEMS:
        rows = []
        for rig in RIGS:
            rows.append([(f"{a} {rig}/play 1:1", play_crop(a, rig, item)) for a in ("today", "A")])
            rows.append([(f"{a} {rig}/close (item camera) 1:1", close_crop(a, rig, item)) for a in ("today", "A")])
        bfile, bbox = bakeoff.CROPS[item]
        board = Image.open(os.path.join(bakeoff.BOARDS, bfile)).convert("RGB").crop(bbox)
        bh = 600; board = board.resize((int(board.width * bh / board.height), bh), Image.LANCZOS)
        Wt = max(sum(im.width + 12 for _, im in r) for r in rows) + board.width + 12
        Ht = sum(max(im.height for _, im in r) + lab for r in rows)
        S = Image.new("RGB", (Wt, Ht), (14, 14, 16)); D = ImageDraw.Draw(S); y = 0
        for r in rows:
            x = 0
            for t, im in r:
                D.text((x + 4, y + 3), t, fill=(255, 230, 120), font=f); S.paste(im, (x, y + lab)); x += im.width + 12
            y += max(im.height for _, im in r) + lab
        bx = Wt - board.width
        D.text((bx + 4, 3), f"{bfile[:-4]} (height to the close crop's); shot --stale-ok (the items, not her art)", fill=(255, 230, 120), font=f); S.paste(board, (bx, lab))
        p = os.path.join(OUT, f"sheet_{item}.png"); S.save(p); print(p)


if __name__ == "__main__":
    {"shoot": shoot, "sheet": sheet}[sys.argv[1]]()
