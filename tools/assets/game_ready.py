"""Photoscans brought down to a game's weight (gltfpack, from meshoptimizer:
npm i -g gltfpack): each simplified to a triangle budget by what it is,
textures as fetched (1k), written as one .glb Godot loads (no quantisation,
which Godot's importer does not read).

    python tools/assets/game_ready.py <scans dir> <out dir> [id ...]

The budgets: scatter (stones, grass, moss, ferns, weeds) 3k, pieces (rocks,
stumps, roots, branches, shrubs) 8k, set pieces (boulders, dead trunks, a
statue, barrels) 15k. The normal maps keep the scanned detail the
triangles give up.
"""
import json
import os
import subprocess
import sys

SCATTER = {"stone_01", "namaqualand_stones_01", "grass_medium_01", "grass_medium_02", "moss_01", "fern_02",
           "nettle_plant", "weed_plant_02", "shrub_03", "bark_debris_01"}
SET_PIECES = {"boulder_01", "dead_tree_trunk", "dead_tree_trunk_02", "gothic_statue", "wooden_barrels_01",
              "stone_fire_pit", "rock_moss_set_01", "rock_moss_set_02"}


def budget(model):
    if model in SCATTER:
        return 3000
    if model in SET_PIECES:
        return 15000
    return 8000


def tris(gltf):
    g = json.load(open(gltf, encoding="utf-8"))
    return sum(g["accessors"][p["indices"]]["count"] // 3 for m in g["meshes"] for p in m["primitives"] if "indices" in p)


def main():
    src, out = sys.argv[1], sys.argv[2]
    ids = sys.argv[3:] or sorted(os.listdir(src))
    os.makedirs(out, exist_ok=True)
    gltfpack = "gltfpack.cmd" if os.name == "nt" else "gltfpack"
    for m in ids:
        gltf = os.path.join(src, m, f"{m}.gltf")
        have = tris(gltf)
        ratio = min(1.0, budget(m) / max(1, have))
        dst = os.path.join(out, f"{m}.glb")
        subprocess.run([gltfpack, "-i", gltf, "-o", dst, "-noq", "-si", f"{ratio:.5f}", "-se", "0.08",
                        "-kn"], check=True, capture_output=True)
        print(f"{m:26s} {have:>7} -> {budget(m):>6} tris  {os.path.getsize(dst) / 1e6:5.1f} MB", flush=True)


if __name__ == "__main__":
    main()
