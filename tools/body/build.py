"""Her new body's base, v1: MakeHuman's woman (CC0 quads, loops at every joint), our skeleton, weights as build steps,
exported in A's contract (godot/art/people/heroine.glb) with her shipped head copied verbatim. docs/team/body.md P1.

    python tools/body/build.py tools/body/specs/base_woman.json <out_dir>            # takes a blender turn, runs:
    (her: tools/body/specs/her.json, base_woman.json with her sliders, stance and residual: wrap.py made them)
    blender -b --python tools/body/build.py -- tools/body/specs/base_woman.json <out_dir>

Writes <out>/body.glb, <out>/rig.json (the check's poser: hinge axes, helpers, correctives), <out>/build.json
(counts, timings, checks) and <out>/stage/ (each stage's arrays: base.npz is the unsubdivided base mesh).
Check it: python tools/body/check.py <out>/body.glb --ref godot/art/people/heroine.glb --rig <out>/rig.json
          --poser lbs --same-head --out <dir>
Stages (each a function, no hand steps):
  1 base      MakeHuman's woman from the spec (mh_base.py, in Blender), and with "sliders" the slider body
              (sliders.py, catalogue.json);
  2 place     the similarity laying our subdivided head on A's HeroineHead and the 1:1 head correspondence
              (headmatch.py); then her forms (forms.py: the slider body joined under the head, her stance and
              residual from "stance" and "forms");
  3 tiers     close = every skin face subdivided once (subdiv.py, her head's scheme), the head's faces dropped (the
              body ends at SPLIT; its ring is the head's, snapped exactly, the fit's move eased into the body below);
  4 skeleton  tools/body/skeleton.json placed from MakeHuman's landmarks (skeleton.py);
  5 weights   MakeHuman's CC0 weights mapped onto ours, split along chains, helpers, capped (weights.py);
  6 export    body.glb (glbwrite.py) + rig.json.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BLENDER = r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe"
TURN = os.path.join(r"C:\Users\munch\Desktop\survivorsunchained", "tools", "turn.py")
sys.path.insert(0, HERE)

try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

import numpy as np  # noqa: E402


def stage_base(spec, out):
    """1: the MakeHuman woman (in Blender), saved as stage/base.npz; outside Blender, read from there."""
    path = os.path.join(out, "stage", "base.npz")
    if IN_BLENDER:
        import mh_base
        b = mh_base.make_base(spec)
        g = b.pop("groups")
        np.savez(path, **b, **{"g:" + k: v for k, v in g.items()})
    z = np.load(path)
    b = {k: z[k] for k in z.files if not k.startswith("g:")}
    b["groups"] = {k[2:]: z[k] for k in z.files if k.startswith("g:")}
    return b


def run(spec_path, out):
    import pipeline
    os.makedirs(os.path.join(out, "stage"), exist_ok=True)
    from sliders import load_spec
    spec = load_spec(spec_path)
    t0 = time.time()
    rep = {"spec": os.path.relpath(os.path.abspath(spec_path), REPO).replace("\\", "/"), "timings_s": {}}
    base = stage_base(spec, out)
    rep["timings_s"]["base"] = round(time.time() - t0, 2)
    pipeline.run(spec, base, out, rep)
    rep["timings_s"]["total"] = round(time.time() - t0, 2)
    with open(os.path.join(out, "body.glb"), "rb") as f:
        rep["glb_sha256"] = hashlib.sha256(f.read()).hexdigest()
    with open(os.path.join(out, "build.json"), "w") as f:
        json.dump(rep, f, indent=1)
    print("BUILD", out, rep["glb_sha256"][:16], rep["timings_s"])


def main():
    if IN_BLENDER:
        a = sys.argv[sys.argv.index("--") + 1:]
        run(a[0], os.path.abspath(a[1]))
        return
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    spec, out = a[0], os.path.abspath(a[1])
    if "--no-blender" in sys.argv:          # (stages 2-6 only, from <out>/stage/base.npz: for working on them)
        run(spec, out)
        return
    os.makedirs(os.path.join(out, "stage"), exist_ok=True)
    subprocess.run([sys.executable, TURN, "take", "blender", "body-p1: base build", "--wait", "10"], check=True)
    try:
        r = subprocess.run([BLENDER, "-b", "--python-exit-code", "1", "--python", os.path.abspath(__file__), "--", os.path.abspath(spec), out])
    finally:
        subprocess.run([sys.executable, TURN, "give", "blender"])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
