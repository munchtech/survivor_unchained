"""Fetch ambientCG materials (CC0, scanned and made by Lennart Demes and
contributors) for the heroine's outfits.

    python tools/assets/ambientcg.py <out dir> <AssetId> [AssetId ...] [--res 1K]

Each lands as <id>_diff/_nor/_rough/_metal/_ao.jpg in <out dir>, in the
names the outfit builder reads; the normal map is the OpenGL one (Godot's
and Blender's convention). An asset already there is not fetched again. Its
licence is CC0; a line in public/assets/CREDITS.md is courtesy.
"""
import io
import os
import sys
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CREDITS = os.path.join(HERE, "..", "..", "public", "assets", "CREDITS.md")
UA = {"User-Agent": "SurvivorUnchained-asset-fetch/1.0"}
MAP = {"_Color": "diff", "_NormalGL": "nor", "_Roughness": "rough", "_Metalness": "metal", "_AmbientOcclusion": "ao"}


def fetch(asset, out, res):
    if os.path.exists(os.path.join(out, f"{asset}_diff.jpg")):
        return False
    url = f"https://ambientcg.com/get?file={asset}_{res}-JPG.zip"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    for name in z.namelist():
        for key, suffix in MAP.items():
            if key in name and name.endswith(".jpg"):
                with open(os.path.join(out, f"{asset}_{suffix}.jpg"), "wb") as f:
                    f.write(z.read(name))
    return True


def credit(asset):
    line = f"- {asset}: ambientCG (https://ambientcg.com/view?id={asset}), CC0\n"
    text = open(CREDITS, encoding="utf-8").read() if os.path.exists(CREDITS) else ""
    if line not in text:
        with open(CREDITS, "a", encoding="utf-8") as f:
            f.write(line)


if __name__ == "__main__":
    args = sys.argv[1:]
    res = "1K"
    if "--res" in args:
        res = args[args.index("--res") + 1]
        args = [a for i, a in enumerate(args) if a != "--res" and (i == 0 or args[i - 1] != "--res")]
    out, ids = args[0], args[1:]
    os.makedirs(out, exist_ok=True)
    for a in ids:
        print(a, "fetched" if fetch(a, out, res) else "already there")
        credit(a)
