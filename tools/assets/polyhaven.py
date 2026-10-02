"""Fetch Poly Haven models (CC0, photoscanned) as glTF for the game's world.

    python tools/assets/polyhaven.py <out dir> <id> [id ...] [--res 1k]
    python tools/assets/polyhaven.py --list <category>

Each model lands in <out dir>/<id>/ as the .gltf with its .bin and
textures beside it, at the texture size asked for (1k unless told). A model
already there is not fetched again. Poly Haven needs no key; its licence is
CC0, so a line per model in public/assets/CREDITS.md is courtesy, not a
condition, and is added the first time a model is fetched.
"""
import json
import os
import sys
import urllib.request

API = "https://api.polyhaven.com"
HERE = os.path.dirname(os.path.abspath(__file__))
CREDITS = os.path.join(HERE, "..", "..", "public", "assets", "CREDITS.md")
UA = {"User-Agent": "SurvivorUnchained-asset-fetch/1.0"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r:
        return r.read()


def fetch(model, out, res):
    dst = os.path.join(out, model)
    gltf_path = os.path.join(dst, f"{model}.gltf")
    if os.path.exists(gltf_path):
        return False
    files = json.loads(get(f"{API}/files/{model}"))
    g = files["gltf"].get(res) or files["gltf"][sorted(files["gltf"])[0]]
    g = g["gltf"]
    os.makedirs(dst, exist_ok=True)
    with open(gltf_path, "wb") as f:
        f.write(get(g["url"]))
    for rel, inc in g.get("include", {}).items():
        p = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(get(inc["url"]))
    info = json.loads(get(f"{API}/info/{model}"))
    authors = ", ".join(info.get("authors", {}).keys())
    line = f"- \"{info.get('name', model)}\" by {authors}, Poly Haven (https://polyhaven.com/a/{model}), CC0 -> public/assets/env/polyhaven/{model}\n"
    text = open(CREDITS, encoding="utf-8").read() if os.path.exists(CREDITS) else ""
    if f"polyhaven.com/a/{model})" not in text:
        if "## Poly Haven models (CC0)" not in text:
            text += "\n## Poly Haven models (CC0)\n\n"
        text += line
        open(CREDITS, "w", encoding="utf-8").write(text)
    return True


def main():
    args = sys.argv[1:]
    if args and args[0] == "--list":
        d = json.loads(get(f"{API}/assets?t=models"))
        print(" ".join(sorted(k for k, v in d.items() if args[1] in v.get("categories", []))))
        return
    res = "1k"
    if "--res" in args:
        i = args.index("--res")
        res = args[i + 1]
        del args[i:i + 2]
    out, ids = args[0], args[1:]
    for m in ids:
        print(("fetched " if fetch(m, out, res) else "have ") + m, flush=True)


if __name__ == "__main__":
    main()
