"""Which body the kit armor route builds on (lane D, 16 Nov 2026): `--body a|p1`, default a.

    a   the shipped heroine.glb: every path below is what the tools used before this module existed (sha1-same outputs).
    p1  body B (godot/art/people/body_p1, the published P1 body, as gear_fit.BIND_BODY): its body.glb, and where its
        inputs and outputs are. Nothing ships on p1 yet: outputs go to a body-keyed place, never over A's installs.

A tool parses `--body` with `take(argv)` (which also sets SU_ARMOR_BODY, so a subprocess or a module that reads
`cur()` sees the same choice); everything else asks `cur()`. A name that is not a body is left to the tool (piece_ship's
--body also takes a path). A p1 input that does not exist yet fails through `need()` naming the input: never a silent
fall back to A.

Body-keyed outputs for p1 (A's are unchanged):
    kit_* build   godot/art/armor/body_p1/src/<piece>/   (A: godot/art/armor/src/<piece>/; build.json is still read from A's)
    piece_ship    installs into godot/art/armor/body_p1/ (A: godot/art/armor); stages under .shots/armor2/ship/body_p1/
    wearcheck, cover  the --out dir the caller names.
"""
import os

ENV = "SU_ARMOR_BODY"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PEOPLE = os.path.join(ROOT, "godot", "art", "people")
ARMOR = os.path.join(ROOT, "godot", "art", "armor")
DATA = os.path.join(ROOT, "tools", "anim", "data")


class Missing(SystemExit):
    """A body input that is not there: the message names it and who owes it."""


class Body:
    def __init__(self, name, glb, skeleton, clips, src, art, ship_sub, owes):
        self.name, self.glb, self.skeleton, self.clips = name, glb, skeleton, clips
        self.src, self.art, self.ship_sub, self.owes = src, art, ship_sub, owes

    def __repr__(self):
        return f"Body({self.name})"

    def need(self, path, what):
        """`path` if it exists, else stop with a message naming the input (not a fall back to body A)."""
        if not os.path.exists(path):
            raise Missing(f"BODY {self.name}: missing input: {what}: {path} ({self.owes})")
        return path


BODIES = {
    "a": Body("a", os.path.join(PEOPLE, "heroine.glb"), os.path.join(DATA, "heroine_skeleton.json"), None,
              os.path.join(ARMOR, "src"), ARMOR, "", "body A"),
    "p1": Body("p1", os.path.join(PEOPLE, "body_p1", "body.glb"), os.path.join(DATA, "body_p1_skeleton.json"),
               os.path.join(DATA, "body_p1", "clips"), os.path.join(ARMOR, "body_p1", "src"),
               os.path.join(ARMOR, "body_p1"), "body_p1", "lane G ports it"),
}


def cur(name=None):
    n = name or os.environ.get(ENV) or "a"
    if n not in BODIES:
        raise SystemExit(f"BODY: unknown body {n!r} (a or p1)")
    return BODIES[n]


def take(argv):
    """Read `--body <a|p1>` from argv (removed from the list, in place), set the env var, return the Body.
    A value that is not a body name is left in argv (a tool's own --body <path>)."""
    if "--body" in argv:
        i = argv.index("--body")
        if i + 1 < len(argv) and argv[i + 1] in BODIES:
            os.environ[ENV] = argv[i + 1]
            del argv[i:i + 2]
    return cur()


def skeleton_for(skin):
    """Skeleton.load's file: body A's is skin.SKELETONS/heroine_skeleton.json (ANIM_SKELETONS honoured, as before)."""
    return skin.SKELETONS / "heroine_skeleton.json" if cur().name == "a" else skeleton_path()


def glb_for(skin):
    """The body glb for skin.Body: body A's is skin.PEOPLE/heroine.glb (ANIM_PEOPLE honoured, as before)."""
    b = cur()
    return skin.PEOPLE / "heroine.glb" if b.name == "a" else skin.Path(b.need(b.glb, "body.glb"))


def use_for_check(wc, clips):
    """wearcheck / cover for p1: stop unless its skeleton dump, clips and installed index exist (naming the first
    missing); then catalogue reads only body_p1's index (A's outfits and installs are body A's). A: nothing."""
    b = cur()
    if b.name == "a":
        return
    skeleton_path()
    b.need(b.glb, "body.glb")
    b.need(b.clips, "clip library dir (<clip>.json per clip)")
    for c in clips:
        b.need(os.path.join(b.clips, f"{c}.json"), f"clip {c}")
    wc.INDEXES = (b.need(os.path.join(b.art, "armor_index.json"), "installed armor_index.json (nothing is shipped on p1 yet)"),)


def skeleton_path():
    """The Skeleton.load file for the body (tools/anim/data/<name>_skeleton.json form)."""
    b = cur()
    return b.skeleton if b.name == "a" else b.need(b.skeleton, "skeleton dump in tools/anim/skeleton form (bones, model, skeleton_path, skeleton_xform)")
