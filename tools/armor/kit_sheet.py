"""A kit piece's look sheet: the design's turnaround views (top) over the lookdev renders (bottom), one column a view.

    python tools/armor/kit_sheet.py <lookdev prefix> <out.png> [--design <turnaround png>] [--crop y0,y1]

Views: front, 3/4, side, back (lookdev.py's <prefix>_{front,34,side,back}.png; the turnaround's four figures).
"""
import os
import sys

from PIL import Image

DESIGN = r"C:\Users\munch\Desktop\survivorsunchained_inputs\gpt_sol\kit\01_turnaround.png"
VIEWS = ("front", "34", "side", "back")


def main(argv):
    prefix, out = argv[0], argv[1]
    design = argv[argv.index("--design") + 1] if "--design" in argv else DESIGN
    y0, y1 = (int(v) for v in (argv[argv.index("--crop") + 1].split(",") if "--crop" in argv else (110, 560)))
    D = Image.open(design).convert("RGB")
    cw = D.width // 4
    H = 520
    cells = []
    for k, v in enumerate(VIEWS):
        d = D.crop((k * cw, y0, (k + 1) * cw, y1))
        d = d.resize((int(d.width * H / d.height), H))
        r = Image.open(f"{prefix}_{v}.png").convert("RGB")
        r = r.crop((r.width // 2 - 330, 0, r.width // 2 + 330, r.height))
        r = r.resize((int(r.width * H / r.height), H))
        cells.append((d, r))
    W = sum(max(d.width, r.width) for d, r in cells)
    S = Image.new("RGB", (W, 2 * H), (40, 40, 40))
    x = 0
    for d, r in cells:
        w = max(d.width, r.width)
        S.paste(d, (x + (w - d.width) // 2, 0))
        S.paste(r, (x + (w - r.width) // 2, H))
        x += w
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    S.save(out)
    print("SHEET", out, S.size)


if __name__ == "__main__":
    main(sys.argv[1:])
