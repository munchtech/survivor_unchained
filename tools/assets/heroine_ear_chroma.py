"""Her ears' colour brought down to her cheek's, in each head's paint (face 36, 21 October 2026).

Rendered, her ear ran hotter than her cheek beside it (judge J1: "her ear more saturated than her cheek"): Oklab
chroma at matched lightness, ear over cheek, at the Look front and turned 40, own 1.43 / 1.32, Vixen 1.45 / 1.39,
Highborn 1.52 / 1.43, Moonlit 1.44 / 1.47, Fey 1.37 / 1.29; Doe, Hardwon, Wildling 1.14-1.25, Saffron 1.07-1.11,
Sunborn 0.99 (the day close-up: own 1.32-1.37, Vixen 1.25-1.27). Not the light through her ear (backlight 0: 1.28 to
1.27) nor its hollows' warm shade (ear_amount 0: 1.37, hotter): her paint's ear, which heroine_ears.py brought to
the cheek's paint times her face's tone, but the ear takes her body's lamps' tones, not her face's, and sat 13-18%
over her cheek in chroma already in her albedo (dbg_gate 12). This scales the ear's chroma (Oklab a, b; lightness
and hue kept) by FIXES[face], eased in over the ear's root as heroine_ears.py's mask (heroine_ears.from_render).

    python tools/assets/heroine_ear_chroma.py [face ...]      (no faces: every face in FIXES)

Idempotent: heroine_face/ear_chroma_done.json keeps, per paint, the git revision of its original (the paint before
any ear-chroma pass), the factor laid and the written paint's sha1. A paint that still has that sha1 and the same
factor is skipped; with another factor in FIXES, the original is read back from git and the new factor laid on it
(never a factor on a factor). A paint laid again since (another sha1) is taken as a new original.
"""
import hashlib
import json
import os
import subprocess
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_ears as he  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DONE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heroine_face", "ear_chroma_done.json")
# (the ear's chroma factor per face: the rendered ear-over-cheek chroma ratio brought to about 1.07, ears a touch warmer
# than a cheek as in life)
FIXES = {
    "own": 0.6, "vixen": 0.6, "highborn": 0.55, "moonlit": 0.55, "fey": 0.62,
    "doe": 0.8, "hardwon": 0.78, "wildling": 0.8, "saffron": 0.9,
}


def rel(face):
    return "godot/art/people/head_tex/" + ("heroine_head.jpg" if face == "own" else "heroine_head_%s.jpg" % face)


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


def main(faces):
    done = json.load(open(DONE)) if os.path.exists(DONE) else {}
    rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for face in faces or sorted(FIXES):
        c = FIXES[face]
        path = os.path.join(ROOT, rel(face))
        d = done.get(face)
        if d and d["sha1"] == sha1(path):
            if abs(d["c"] - c) < 1e-6:
                print("EAR-C %-9s done (x%.3f)" % (face, c))
                continue
            # (another factor: the original back from git, the new factor on it)
            blob = subprocess.check_output(["git", "show", "%s:%s" % (d["base"], rel(face))], cwd=ROOT)
            with open(path, "wb") as f:
                f.write(blob)
            base = d["base"]
        else:
            # (this paint is the original: it must be committed as is, so it can be read back)
            st = subprocess.check_output(["git", "status", "--porcelain", "--", rel(face)], cwd=ROOT, text=True).strip()
            if st:
                sys.exit("EAR-C %s: %s has uncommitted changes; commit the paint first (its original must be in git)" % (face, rel(face)))
            base = rev
        he.from_render({face: (1.0, c, 0.0)})
        done[face] = {"base": base, "c": c, "sha1": sha1(path)}
        with open(DONE, "w") as f:
            json.dump(done, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    main(sys.argv[1:])
