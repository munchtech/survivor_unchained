"""B3 round 1's bake-off (L1 texture authoring): each painter arm's maps on the Waystation setts, the barrel and the
boulder on the lookdev stage (tools/style/lookdev.py; the maps go on through godot/src/World/B3Maps.cs, --b3-maps, and
the material library's loader), then one sheet per asset at 1:1 (today | A | B | C) beside board crops at the same scale.

    python tools/look/bakeoff.py manifest ARM          -> B3/bakeoff/ARM/maps.json (ARM's maps for the three)
    bash wtlock.sh python tools/look/bakeoff.py shoot [today,A,B,C]
    python tools/look/bakeoff.py sheet                 -> B3/bakeoff/sheet_<asset>_<rig>.png, numbers.json
"""
import json, os, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
B3 = r"C:\Users\munch\Desktop\survivorsunchained_inputs\look_l1\b3"
BOARDS = r"C:\Users\munch\Desktop\survivorsunchained_inputs\look_l1\a2\r2"
ARMS = ["today", "A", "B", "C"]  # (and "Alit": A from the boards' lit color, for the albedo question)
# at: the lookdev stage's own placement (GameLookdev: At(x, y, yaw)); near: where the bake-off moves it, beside her,
# so the close view sees it too (the barrel at her right, the boulder behind her left)
ASSETS = {"barrel": dict(node="own_barrel", item="barrel", at=[0.1, 5.3, 20], near=[0.95, 1.4, 20]),
          "boulder": dict(node="own_boulder_b", item="boulder", at=[6.8, 4.1, 30], near=[-2.9, 3.6, 30]),
          "setts": dict(node="LookSetts", item="setts", tile=4.0, name="setts_b3")}
# board crops for each asset (board, box in board px, the board's size of the thing in cm across the box)
CROPS = {"barrel": ("MB3_town.png", (1450, 120, 1640, 440)), "boulder": ("MB4_wild_r3.png", (700, 150, 1000, 440)),
         "setts": ("MB3_town.png", (85, 90, 400, 440))}


def manifest(arm):
    items = []
    for a, it in ASSETS.items():
        d = os.path.join(B3, arm if arm != "today" else "A", a); f = json.load(open(os.path.join(B3, "forms", a, "forms.json")))
        maps = {c: {k: os.path.join(d, f"{k}.png") for k in ("albedo", "normal", "rough")} for c in f["classes"]}
        e = dict(node=it["node"], maps=maps if arm != "today" else {})
        if "near" in it: e.update(at=it["at"], near=it["near"])
        if f["kind"] == "prop": e["mesh"] = os.path.join(B3, "forms", a, "mesh.glb")
        else: e.update(tile=it["tile"], name=it["name"])
        items.append(e)
    out = os.path.join(B3, "bakeoff", arm); os.makedirs(out, exist_ok=True)
    p = os.path.join(out, "maps.json"); json.dump({"items": items}, open(p, "w"), indent=1)
    return p


def shoot(arms):
    for arm in arms:
        out = os.path.join(B3, "bakeoff", arm)
        extra = ["--extra", f"--b3-maps {manifest(arm)}"]
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "style", "lookdev.py"), "shoot", "--out", out, "--rigs", "day,night"] + extra, check=False)


def font(n=18):
    try: return ImageFont.truetype("arial.ttf", n)
    except Exception: return ImageFont.load_default()


def sheet():
    nums = {}
    for a, it in ASSETS.items():
        for rig in ("day", "night"):
            cols = []
            for cam in ("play", "close"):
                row = []
                for arm in ARMS:
                    d = os.path.join(B3, "bakeoff", arm)
                    fr = os.path.join(d, f"lookdev_{rig}_{cam}.png")
                    items = json.load(open(os.path.join(d, "check_items.json"))) if os.path.exists(os.path.join(d, "check_items.json")) else {}
                    box = next((i["rect"] for i in items.get(f"{rig}_{cam}", []) if i["name"] == it["item"]), None)
                    if not os.path.exists(fr) or box is None: row.append(None); continue
                    im = Image.open(fr).convert("RGB"); W, H = im.size
                    x0, y0, x1, y1 = box; pad = 0.15
                    bx = [max(0, int((x0 - pad * (x1 - x0)) * W)), max(0, int((y0 - pad * (y1 - y0)) * H)),
                          min(W, int((x1 + pad * (x1 - x0)) * W)), min(H, int((y1 + pad * (y1 - y0)) * H))]
                    if bx[2] - bx[0] > 900:  # (a ground patch wider than the frame: its middle 900 px)
                        cx = (bx[0] + bx[2]) // 2; bx[0], bx[2] = max(0, cx - 450), min(W, cx + 450)
                    if bx[3] - bx[1] > 600: bx[1] = bx[3] - 600
                    if bx[2] - bx[0] < 8 or bx[3] - bx[1] < 8: row.append(None); continue  # (off this frame)
                    row.append((arm, im.crop(bx), (bx[2] - bx[0])))
                cols.append((cam, row))
            # the sheet: per camera one row, at 1:1 (no scaling), arms left to right, the board crop scaled to the
            # close row's asset width (the same scale: the asset across its crop)
            f = font(); lab = 26
            rows_h = [max((c[1].height for c in r if c), default=0) for _, r in cols]
            widths = [sum((c[1].width for c in r if c)) + 12 * len(r) for _, r in cols]
            bfile, bbox = CROPS[a]
            board = Image.open(os.path.join(BOARDS, bfile)).convert("RGB").crop(bbox)
            closew = max((c[2] for c in cols[1][1] if c), default=board.width)
            bscaled = board.resize((closew, int(board.height * closew / board.width)), Image.LANCZOS)
            Wt = max(widths) + bscaled.width + 24; Ht = sum(rows_h) + lab * len(cols) + 8
            Ht = max(Ht, bscaled.height + lab + 8)
            S = Image.new("RGB", (Wt, Ht), (14, 14, 16)); D = ImageDraw.Draw(S)
            y = 0
            for (cam, r), h in zip(cols, rows_h):
                x = 0
                for c in r:
                    if not c: continue
                    arm, im, _ = c
                    D.text((x + 4, y + 3), f"{arm}  {rig}/{cam}  1:1", fill=(255, 230, 120), font=f)
                    S.paste(im, (x, y + lab)); x += im.width + 12
                y += h + lab
            bx0 = max(widths) + 12
            D.text((bx0 + 4, 3), f"{bfile[:-4]} (to the close row's scale)", fill=(255, 230, 120), font=f)
            S.paste(bscaled, (bx0, lab))
            p = os.path.join(B3, "bakeoff", f"sheet_{a}_{rig}.png"); S.save(p); print(p)
    sys.path.insert(0, os.path.join(ROOT, "tools", "style")); import palette
    for arm in ARMS:
        d = os.path.join(B3, "bakeoff", arm)
        items = json.load(open(os.path.join(d, "check_items.json"))) if os.path.exists(os.path.join(d, "check_items.json")) else {}
        nums[arm] = {}
        # the play camera's scale: the setts patch is 6 m across (GameLookdev.LookSetts)
        sr = next((i["rect"] for i in items.get("day_play", []) if i["name"] == "setts"), None)
        ppm_play = (sr[2] - sr[0]) * 1920 / 6.0 if sr else None
        for a, it in ASSETS.items():
            pj = os.path.join(B3, arm, a, "paint.json")
            n = json.load(open(pj)) if os.path.exists(pj) else {}
            fj = os.path.join(B3, "forms", a, "forms.json")
            if n and os.path.exists(fj): n["build_s"] = round(json.load(open(fj))["seconds"] + n["seconds"] + (40 if arm in ("B", "C") else 0), 1)
            if ppm_play and n: n["brush_px_play"] = {c: round(v / 100 * ppm_play, 1) for c, v in n["brush_cm"].items()}
            for rig in ("day", "night"):
                for cam in ("play", "close"):
                    box = next((i["rect"] for i in items.get(f"{rig}_{cam}", []) if i["name"] == it["item"]), None)
                    fr = os.path.join(d, f"lookdev_{rig}_{cam}.png")
                    if not box or not os.path.exists(fr): continue
                    im = Image.open(fr).convert("RGB"); W, H = im.size
                    c = im.crop((int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)))
                    t = os.path.join(B3, "bakeoff", "_crop.png"); c.save(t)
                    n[f"midC_{rig}_{cam}"] = round(float(palette.stats(t, False)[0]["midC"]), 4)
            nums[arm][a] = n
        nums[arm]["play_px_per_m"] = round(ppm_play, 1) if ppm_play else None
    json.dump(nums, open(os.path.join(B3, "bakeoff", "numbers.json"), "w"), indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "manifest": print(manifest(sys.argv[2]))
    elif cmd == "shoot": shoot(sys.argv[2].split(",") if len(sys.argv) > 2 else ARMS)
    elif cmd == "sheet" and len(sys.argv) > 2: ARMS[:] = sys.argv[2].split(","); sheet()
    elif cmd == "sheet": sheet()
