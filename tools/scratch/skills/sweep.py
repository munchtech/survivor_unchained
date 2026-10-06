"""Every skill in play, one run each, for grading: python sweep.py TAG [ids...] [--rank R] [--people P] [--time T]

Each run: the skill alone (--lab) at rank R, a crowd round the survivor in an
arena, a frame every 0.08 s from 2.5 s for about two seconds. Frames go to
godot/.shots/TAG_<id>_NN.png; a sheet per skill to scratchpad/skills/TAG/."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8bafe3cd8a229639\godot"

SKILLS = {
    "oathblade": "warden", "cleaver": "reaver", "axe_gyre": "reaver", "iron_palms": "reaver", "reaving_arc": "reaver",
    "volley": "stalker", "knifestorm": "stalker", "gale_chakram": "stalker", "judgement_disc": "warden", "firepot": "stalker",
    "seeking_motes": "arcanist", "moonbrand": "arcanist", "cinderfall": "arcanist", "rimeshard": "arcanist", "hoarfrost": "arcanist",
    "arcweb": "arcanist", "thunderhead": "arcanist", "umbral_bolt": "arcanist", "grave_tether": "reaver", "gravecall": "reaver",
    "dawnpulse": "warden", "hallowed_ring": "warden", "blightfield": "stalker", "thornbloom": "stalker", "verdant_lance": "stalker",
    "spirit_herd": "stalker",
    "frostfire_comet": "arcanist", "the_tempest": "arcanist", "rotwood": "stalker", "butchers_wheel": "reaver",
    "hail_of_steel": "stalker", "dawns_judgement": "warden", "barrow_host": "reaver", "soul_lantern": "reaver", "starfall": "arcanist",
}


def main():
    argv = sys.argv[1:]
    tag = argv[0]
    rank, people, time_, count, every, start, extra = "4", "dead", "night", "24", "0.08", "2.5", []
    horde, dist, spread = "70,8:risen!", "3", "9"
    ids = []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--rank": rank = argv[i + 1]; i += 2; continue
        if a == "--people": people = argv[i + 1]; i += 2; continue
        if a == "--time": time_ = argv[i + 1]; i += 2; continue
        if a == "--count": count = argv[i + 1]; i += 2; continue
        if a == "--every": every = argv[i + 1]; i += 2; continue
        if a == "--start": start = argv[i + 1]; i += 2; continue
        if a == "--horde": horde = argv[i + 1]; i += 2; continue
        if a == "--dist": dist = argv[i + 1]; i += 2; continue
        if a == "--spread": spread = argv[i + 1]; i += 2; continue
        if a == "--extra": extra = argv[i + 1].split(" "); i += 2; continue
        ids.append(a)
        i += 1
    ids = ids or list(SKILLS)
    outdir = os.path.join(HERE, tag)
    os.makedirs(outdir, exist_ok=True)
    for sid in ids:
        give = sid if ":" in sid else f"{sid}:{rank}"
        base = sid.split(":")[0].split("@")[0]
        calling = SKILLS.get(base, "arcanist")
        name = f"{tag}_{sid.replace(':', '_').replace('@', '_')}"
        args = [sys.executable, os.path.join(HERE, "shot.py"), name, "--quick", calling, "--zone", "arena", "--people", people,
                "--time", time_, "--tier", "2", "--lab", "--give", give, "--horde", horde, "--dist", dist, "--spread", spread,
                "--seconds", start, "--every", every, "--count", count] + extra
        r = subprocess.run(args, capture_output=True, text=True)
        print(sid, r.stdout.strip().splitlines()[0] if r.stdout.strip() else r.stderr[-300:], flush=True)
        subprocess.run([sys.executable, os.path.join(HERE, "sheet.py"), os.path.join(outdir, f"{name}.png"), "4", "560",
                        "--crop", "1200,700", os.path.join(WT, ".shots", f"{name}_*.png")], capture_output=True)


if __name__ == "__main__":
    main()
