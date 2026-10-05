"""What a release pack carries, listed and checked before an upload (the legal
lead's checklist: docs/legal/STEAM_CHECKLIST.md asks for it each time).

    python tools/godot/pack_listing.py [PRESET] [--out FILE]

PRESET is an export preset's name (default Windows). It exports the preset's
pack as a zip (so it can be read), then checks that:
  - nothing the preset's exclude_filter names is in it;
  - every JSON, licence text and zone file the game reads with FileAccess is in it
    (any .json under art/ and data/, data's .bin and .png, licences/);
  - every dependency of every resource in it is in it too (tools/godot/pack_deps.gd).
It writes every path with its size (imported data counted) to FILE (default
release/godot/pack_listing_PRESET.txt), deletes the zip, and exits 1 if a check
failed. Needs the export templates (tools/godot/setup.sh --templates).
"""
import fnmatch
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME = os.path.join(ROOT, "godot")
GODOT = os.environ.get("GODOT", r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe")


def preset_filters(name):
    text = open(os.path.join(GAME, "export_presets.cfg"), encoding="utf-8").read()
    for block in re.split(r"(?m)^\[preset\.\d+\]\s*$", text)[1:]:
        if re.search(rf'(?m)^name="{re.escape(name)}"', block):
            ex = re.search(r'(?m)^exclude_filter="([^"]*)"', block).group(1)
            return [f.strip() for f in ex.split(",") if f.strip()]
    sys.exit(f"no preset named {name}")


def sources(z):
    """Each source path in the pack and its size: imported files by their
    .import/.remap, with the imported data they point to."""
    names = {i.filename: i.file_size for i in z.infolist()}
    out = {}
    for n in names:
        if n.endswith((".import", ".remap")):
            txt = z.read(n).decode("utf-8", "replace")
            data = re.findall(r'"?(res://\.godot/[^"\]\s]+)', txt)
            out[n[: n.rfind(".")]] = sum(names.get(p.replace("res://", ""), 0) for p in set(data))
    for n, s in names.items():
        if not n.endswith((".import", ".remap")) and not n.startswith(".godot/"):
            out.setdefault(n, s)
    return out


def main():
    args = sys.argv[1:]
    out_file = None
    if "--out" in args:
        i = args.index("--out")
        out_file = args[i + 1]
        del args[i:i + 2]
    preset = args[0] if args else "Windows"
    out_file = out_file or os.path.join(ROOT, "release", "godot", f"pack_listing_{preset}.txt")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    excludes = preset_filters(preset)

    tmp = tempfile.mkdtemp()
    pack = os.path.join(tmp, "pack.zip")
    print(f"exporting the {preset} pack...")
    r = subprocess.run([GODOT, "--headless", "--path", GAME, "--export-pack", preset, pack], capture_output=True, text=True, errors="replace")
    if not os.path.exists(pack):
        print(r.stdout[-3000:], r.stderr[-3000:])
        sys.exit("the export made no pack")
    with zipfile.ZipFile(pack) as z:
        ship = sources(z)
    os.remove(pack)
    failed = False

    bad = {e: [p for p in ship if fnmatch.fnmatch(p, e)] for e in excludes}
    for e, hits in bad.items():
        if hits:
            failed = True
            print(f"SHIPS DESPITE THE EXCLUDE {e}: {hits[:5]}")
    print(f"excludes: {sum(1 for h in bad.values() if not h)} of {len(bad)} hold")

    read = []
    for top in ("art", "data", "licences"):
        for d, _, files in os.walk(os.path.join(GAME, top)):
            for f in files:
                rel = os.path.relpath(os.path.join(d, f), GAME).replace("\\", "/")
                # JSON anywhere; the zones' data (heights, flora, paint); the licence texts.
                wanted = rel.endswith(".json") or top == "licences" or top == "data" and rel.endswith((".bin", ".png"))
                if wanted and not any(fnmatch.fnmatch(rel, e) for e in excludes):
                    read.append(rel)
    missing = [p for p in read if p not in ship]
    for p in missing:
        failed = True
        print(f"READ BY THE GAME BUT NOT SHIPPED: {p}")
    print(f"files read with FileAccess: {len(read) - len(missing)} of {len(read)} ship")

    listing = os.path.join(tmp, "paths.txt")
    with open(listing, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(ship)))
    r = subprocess.run([GODOT, "--headless", "--path", GAME, "-s", os.path.join(ROOT, "tools", "godot", "pack_deps.gd"), "--", listing],
                       capture_output=True, text=True, errors="replace")
    deps = [l for l in r.stdout.splitlines() if l.startswith("deps ") or l.startswith("  ")]
    print("\n".join(deps) or r.stdout[-2000:])
    if not any(l.startswith("deps ") and l.endswith(" 0") for l in deps):
        failed = True
    os.remove(listing)
    os.rmdir(tmp)

    by = defaultdict(lambda: [0, 0])
    for p, s in ship.items():
        parts = p.split("/")
        k = "C# script stubs" if p.endswith(".cs") else "/".join(parts[:2]) if len(parts) > 2 else parts[0]
        by[k][0] += 1
        by[k][1] += s
    with open(out_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"The {preset} release pack: {len(ship)} paths, {sum(ship.values()) / 1e6:.1f} MB uncompressed\n\nBy folder (MB, files)\n")
        for k in sorted(by, key=lambda k: -by[k][1]):
            f.write(f"  {by[k][1] / 1e6:8.1f} {by[k][0]:5d}  {k}\n")
        f.write("\nEvery path (bytes, path)\n")
        for p in sorted(ship):
            f.write(f"{ship[p]:>12}  {p}\n")
    print(f"{len(ship)} paths listed in {out_file}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
