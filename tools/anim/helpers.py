"""Her helper bones: twist bones down each forearm and at each shoulder, and a
share bone at each shoulder, elbow and knee, as AAA rigs have them. This is
the one description of them: tools/assets/heroine_rig.py builds them into her
body (and the hero's) from it, godot/src/Actors/HerJoints.cs drives them in
the game from its copy (godot/art/people/rig_helpers.json, written here), and
the motion tools pose them as the game does.

Why: with only an upper arm, a forearm and a hand, linear skinning can only
blend between them. A forearm turned about its length (the radius rolling
over the ulna) wrings the skin at the elbow or the wrist like a sweet
wrapper, and a bent elbow or knee folds flat at the crease. The helpers
spread the turn and the bend over the flesh as a body does:

- **forearm twist** (`lowerarm_twist_01`, `_02`): the hand's turn about the
  forearm shared along it, two fifths and four fifths, as the radius rolls;
  the forearm bone itself never rolls on the elbow (it is the ulna, on a
  hinge): whatever roll a clip gives it is handed down to the hand;
- **shoulder twist** (`upperarm_twist_01`): the upper arm's turn about its
  length, half undone at the shoulder, where the deltoid is held by the
  shoulder girdle; on her (Body 5 A2) a chain of four (`_01`-`_04`) and five
  weight nodes down the humerus carries the roll evenly (SPEC "twist_chain"),
  gated on `upperarm_twist_02` so a body without it moves as before;
- **shares** (`upperarm_share`, `lowerarm_share`, `calf_share`): half the
  joint's bend, carrying the ring of flesh round the joint, so it bends
  round a corner instead of folding; at the elbow and knee also pushed out
  across the bend as a bent tube is (`bulge`, held on the crease side), and
  kept off the crease itself, which folds in deep as it did (`crease`).

They are children of the bones they help, laid along them, and bound where
those bones' weight was, so a body without the driver moves as before.
"""
from __future__ import annotations

import json
import math

import numpy as np

from rig import REPO, Skeleton, qaxis, qbetween, qinv, qmatrix, qmul, qnorm, qrot, qslerp

SPEC_FILE = REPO / "godot" / "art" / "people" / "rig_helpers.json"

SPEC = {
    "helpers": [
        # The shoulder's twist bone, a quarter of the way down the upper arm.
        {"name": "upperarm_twist_01_{s}", "parent": "upperarm_{s}", "kind": "counter_twist", "bone": "upperarm_{s}",
         "at": 0.25, "amount": 0.5},
        # The forearm's, two fifths and four fifths of the way to the wrist.
        {"name": "lowerarm_twist_01_{s}", "parent": "lowerarm_{s}", "kind": "forearm_twist", "bone": "hand_{s}",
         "at": 0.4, "amount": 0.4},
        {"name": "lowerarm_twist_02_{s}", "parent": "lowerarm_{s}", "kind": "forearm_twist", "bone": "hand_{s}",
         "at": 0.8, "amount": 0.8},
        # Shares: at the joint, half its bend.
        {"name": "upperarm_share_{s}", "parent": "clavicle_{s}", "kind": "share", "bone": "upperarm_{s}", "amount": 0.5,
         "bulge": 0.0, "bulge_max": 1.0, "way": "front"},
        {"name": "lowerarm_share_{s}", "parent": "upperarm_{s}", "kind": "share", "bone": "lowerarm_{s}", "amount": 0.5,
         "bulge": 0.45, "bulge_max": 1.45, "pivot": 0.047, "way": "front",
         # (Body 14: its half-bend about its own hinge, its X (hinge_part), not the swing's shortest arc)
         "hinge": True},
        # The elbow's point: the share's twin, pushed out across the bend
        # (away from the crease, -Z) by `push` metres eased in from `from`
        # to `to` degrees of bend; it takes the share's weight on the
        # patch weights.point gives it.
        {"name": "lowerarm_point_{s}", "parent": "upperarm_{s}", "kind": "point", "bone": "lowerarm_{s}", "amount": 0.5,
         "share": "lowerarm_share_{s}", "push": 0.03, "from": 70, "to": 145, "way": "front", "hinge": True,
         # and drawn in across the bend (its X, the hinge axis) toward
         # `squeeze_x` metres along it, losing `squeeze` of its width there
         # by `to` degrees, eased in from `squeeze_from`: from behind, the
         # tip narrows to a point in line with the forearm's back edge.
         "squeeze": 0.0, "squeeze_x": 0.0, "squeeze_from": 100},
        {"name": "calf_share_{s}", "parent": "thigh_{s}", "kind": "share", "bone": "calf_{s}", "amount": 0.5,
         "bulge": 0.5, "bulge_max": 1.5, "pivot": 0.059, "way": "back"},
        # Her upper arm's twist chain (Body 5 A2, "twist_chain" below): three more counter-twists down the humerus,
        # built into HER body only (extend(chain=True), heroine_rig.add_bones(chain=True)); a body without them (the
        # hero, the NPCs) drives and splits as before. `amount`: how much of the upper arm's roll each undoes.
        {"name": "upperarm_twist_02_{s}", "parent": "upperarm_{s}", "kind": "counter_twist", "bone": "upperarm_{s}",
         "at": 0.25, "amount": 0.525, "chain": True},
        {"name": "upperarm_twist_03_{s}", "parent": "upperarm_{s}", "kind": "counter_twist", "bone": "upperarm_{s}",
         "at": 0.5, "amount": 0.35, "chain": True},
        {"name": "upperarm_twist_04_{s}", "parent": "upperarm_{s}", "kind": "counter_twist", "bone": "upperarm_{s}",
         "at": 0.75, "amount": 0.175, "chain": True},
    ],
    # The forearm bone's own roll on the elbow handed down to the hand.
    "unroll": ["lowerarm_{s}"],
    "weights": {
        # Upper arm: to its twist bone at the shoulder, easing to none this
        # far down the upper arm (smoothly).
        "shoulder_twist_to": 0.55,
        # Forearm: shared between the forearm bone and its twist bones by
        # where a point lies along it (0 elbow, 1 wrist), as hats over these.
        "forearm_nodes": [0.0, 0.4, 0.8],
        # Shares: of a point's blend between the bones above and below, how
        # much the share bone takes (1: a half-and-half point is all its).
        "share": 1.0,
        # The shares cut as a quadratic Bezier (smooth), not a tent: see split.
        "profile": "smooth",
        # (above, below, share)
        "pairs": [["clavicle_{s}", "upperarm_{s}", "upperarm_share_{s}"], ["upperarm_{s}", "lowerarm_{s}", "lowerarm_share_{s}"],
                  ["thigh_{s}", "calf_{s}", "calf_share_{s}"]],
        "cap": 4,
        # The crease (the inside of the bend, the share's `way`): none of the
        # share there, eased out from the joint's line to `reach` metres into
        # the crease. A share there holds the crease's skin out at its rest
        # distance, which leaves it just past the point where a bend folds
        # it: a shallow fold, turned over at the skin itself, which shows at
        # the crease's ends (the tick behind the knee at 120-145). Without
        # it the crease folds in deep, with the bones each side, hidden
        # under them as before the helpers; the share rounds the outside.
        "crease": {"cut": 1.0, "reach": 0.035},
        # The point of a joint (the elbow's olecranon): on the side away
        # from the crease, a patch round the joint's line whose share weight
        # goes to its point bone (a share's twin, pushed out from the joint
        # as it bends: helpers kind "point"), so the tip stands out of the
        # round the share makes. A step in the blend there instead (the
        # bone below carrying the tip) turned the tip's faces over past 120
        # degrees: across a short band the skin is blended between places
        # 145 degrees apart round the joint, and the chord runs into it.
        # half/fade: the patch round the back, degrees (full, then eased
        # out); reach/feather: along the bone either side of `at`, metres.
        "point": {"lowerarm_point_{s}": {"half": 20, "fade": 40, "at": 0.008, "reach": 0.0, "feather": 0.03}},
    },
    # Corrective shapes (pose-space, as Maya's): a move of her skin at rest
    # that a joint's bend eases in, made here (corrective), built into her
    # body and every piece she wears near it as a shape key
    # (heroine_rig.py) and set in the game from the same bend (HerJoints.cs).
    # Bones only blend matrices, so a point standing out of the joint (the
    # olecranon) is beyond them: three helper-bone tries left the elbow,
    # seen from behind, a blunt round cap.
    "correctives": [
        # The elbow's point: bent `full` degrees (bend: drive's measure), the
        # skin at the far side of the bend from the crease pushed out along
        # the bend's outward line (between the upper arm's line and the
        # forearm's, reversed; `lean` -1..1 turns it toward the upper arm or
        # the forearm) by `amount` metres at the tip, falling off smoothly
        # ((1 - r^2)^3: a rounded tip, soft flanks) over `radius` metres:
        # across the hinge, along the bend's plane, and in depth. The tip is
        # her skin's furthest point out along that line within `near` of it.
        # The shape's weight: smoothstep from `from` to `to` degrees of bend
        # (none below `from`). Pieces she wears take the skin's move at the
        # nearest skin point, whole within garment[0] metres of the skin,
        # easing out to none at garment[1].
        {"name": "elbow_point_{s}", "bone": "lowerarm_{s}", "way": "front", "full": 145, "from": 90, "to": 145,
         # (6 mm over 18-26 mm barely showed and read as a nub where it did;
         # broad flanks make the cap a cone with a point: tick.py previews)
         "amount": 0.012, "radius": [0.028, 0.06, 0.045], "lean": 0.0, "near": 0.008, "garment": [0.02, 0.04]},
        # (Body 19) her elbow's pose-space shapes, authored on her body by
        # tools/assets/elbow_psd_post.py (not made here: no "amount"), keyed
        # "on" the forearm's FLEXION (flexion(): its line about its own X; her
        # clips' small "bends" are mostly the forearm swung sideways onto the
        # humerus' line) as in-betweens: `keys` [lo, at, hi], 0 at lo, whole
        # at `at`, 0 again at hi, linear between; hi <= at holds it past `at`.
        {"name": "elbow_psd45_{s}", "bone": "lowerarm_{s}", "on": "flex", "keys": [0, 45, 90]},
        {"name": "elbow_psd90_{s}", "bone": "lowerarm_{s}", "on": "flex", "keys": [45, 90, 135]},
        {"name": "elbow_psd135_{s}", "bone": "lowerarm_{s}", "on": "flex", "keys": [90, 135, 0]},
    ],
    # Panel bones: one centred bone (no {s}) for a hanging front panel (the
    # Reaver's loincloth), a child of the pelvis that swings forward with the
    # leading thigh, so the thigh coming through at a stride's foot strike
    # lifts the panel instead of showing through it (a linear blend of the
    # two thighs averages them: the leading one went through it). panel_turn
    # is the law, HerJoints.cs the game's copy.
    # - rest: at the pelvis's head + `pivot` (metres, her rest axes: +Y up,
    #   +Z her front; 6 cm in front of the pelvis bone at its height, about
    #   6 cm behind the panel's face and 2.5 cm above its top: a pivot inside
    #   her swings the panel's top forward with it, clear of the thigh's
    #   crease, without lifting it into her belly), laid along the panel:
    #   its +Y down, its +Z her front, its +X her right; `length` (Blender).
    # - turn: about her lateral axis (the panel's bottom forward and up) by
    #   amount * softrelu(smooth max of the thighs' forward swing), the swing
    #   read in the pelvis's frame as degrees in her side plane from rest; the
    #   smooth max (polynomial, `soft` degrees wide, less soft/4 so equal
    #   thighs give their own swing) keeps it smooth as the legs cross, and
    #   softrelu (quadratic over the first `soft` degrees) never turns it
    #   back. Damped by up to `spread_damp` as the thighs spread (their mean
    #   abduction from `spread_from` to `spread_to` degrees, smoothstep): on
    #   a seat with the knees apart (sit_log) it lifts 38, not 87.
    # Measured offline on Godot's own poses against the ea6a9417 Reaver build
    # (thigh points inside the panel, run/sprint mean -> frame 14):
    # run_warden 521 -> 0 (f14 2106 -> 0), sprint_warden 478 -> 27 (f14 0),
    # run_reaver 946 -> 33, sprint_reaver 1097 -> 63, walk_tired 1514 -> 0,
    # idle_reaver 0 -> 0; sit_log stretch>1.6x 13% -> 3%, inside 299 -> 161;
    # never into her belly or the trailing thigh.
    # - fall (panel_fall, in time, so only where frames follow each other:
    #   the game, drive's `state`): it rises with the law at once, but falls
    #   as a loose flap does, a first-order lag of `fall_tau` seconds toward
    #   the law and never faster than `fall_rate` degrees a second (15 a
    #   30 fps frame), never below the law (so never into the thigh). On
    #   run_reaver it trails the law's fall by about a frame (90 -> 84, 71,
    #   56, 46 over f6-f9, was 79, 60, 43, 38), the rise and crossovers as
    #   they were.
    #
    # Weighting recipe (heroine_outfits.py, the Reaver's front panel: the
    # loincloth's front piece, the one-piece part FRINGE_ONE moves today):
    # every panel vertex gets W = (1 - k) * W_built + k * panel_front, with
    # W_built its weights as built now (ea6a9417: near the belt pelvis ~0.73,
    # thighs ~0.09 each, spine_01 ~0.09) and k = smoothstep(0, 0.06,
    # top - y), y its rest height and top the panel's top edge (1.047 m on
    # today's body): none at the belt, all of it 6 cm down and below. Keep
    # the thighs' small share in that top band (taking it to the pelvis left
    # the thigh 20-38 mm through the panel's top in a sprint).
    "panels": [
        {"name": "panel_front", "parent": "pelvis", "thighs": ["thigh_l", "thigh_r"], "pivot": [0.0, 0.0, 0.06],
         "length": 0.45, "amount": 1.15, "soft": 12.0, "spread_from": 8.0, "spread_to": 20.0, "spread_damp": 0.6,
         "fall_tau": 0.04, "fall_rate": 450.0,
         # (Body 18, judge at the 1:1 town close-up: "in the run the panel juts forward as a rigid flat board 6-8 cm
         # above the raised thigh". Its pivot sits above and before the hip joint, so turned with the thigh it rode
         # over it; past `drop_from` degrees of lead it turns `drop` a degree less: run peak 84 -> 73 deg on a 77 deg
         # thigh, and its sides lift off the thigh under them ("side" below) so the lowered panel isn't cut by it)
         "drop": 0.4, "drop_from": 45.0,
         # The lower half's fold (Body 17, 27 Oct; panel_fold): not a bone (a bone would change her skeleton,
         # every clip's pack and the body file) but three blend shapes on the panel's own mesh, made by
         # heroine_outfits.py: its points below `hinge` (rest height, glTF metres; eased over +-`band`)
         # turned forward about her lateral axis through the panel's middle there, by `step` (a), a further
         # `step` (b, stacked on a) and back by `neg` (n). The lower half is a damped pendulum (`hz`, `zeta`)
         # hanging toward `rest` degrees from plumb, lying on the leading thigh (never below `contact`[0] x the
         # law's lead - `contact`[1] degrees, measured: the least angle with no thigh through the lower half
         # in walk/run/sprint) and lifted with it, so it drapes over the thigh as it rises and trails it
         # ~0.1 s as it falls. Measured on the shortened panel (S17 solve1 harness.py): walk stand-off
         # 66 -> 53 mm (the full-length panel today: 98), thigh points inside unchanged in run/sprint/idle/sit.
         # (Body 18: hinge 0.86 -> 0.84, 55% down the panel, the judge's bend)
         "fold": {"shapes": ["panel_fold_a", "panel_fold_b", "panel_fold_n"], "hinge": 0.84, "band": 0.03,
                  "step": 25.0, "neg": 25.0, "hz": 1.6, "zeta": 0.45, "rest": 0.0, "contact": [1.12, 9.0], "substeps": 4,
                  # (Body 18) two more shapes: the panel's half over each thigh lifted along its face by up to `lift`
                  # (m, from `x`[0] off her middle to `x`[1], none in its top 3 cm, all from 12 cm down), weighed by
                  # that thigh's forward swing (smoothstep over `swing` degrees): the sheet tilts onto the raised
                  # thigh's crown instead of the thigh cutting through its edge
                  "side": {"shapes": ["panel_side_l", "panel_side_r"], "lift": 0.055, "x": [0.005, 0.06], "swing": [10.0, 45.0]}},
         # (Body 18 r4, judge at the town sprint: "as the near thigh comes down the panel floats as a straight stiff
         # paddle 6-8 cm off it", the fall's hang and the 1.6 Hz fold's slow drop.) In a sprint (panel_sprint: the
         # lead's held peak past `amp`, its held swing past `range`, both held `decay` deg/s, so a seat or a held
         # pose never counts, nor a run, peak 79) the law blends to these: the upper turns `amount` a degree of lead
         # (it lies on the thigh down its whole descent: 1.15 floats 7-10 cm off it there; the walk keeps 1.15, under
         # which its thigh stays out of the panel), falls with no hang (`fall_tau`, `fall_rate`) and the lower half is a
         # critically damped spring (`zeta` 1, `hz` 19: settled in 0.05 s, never overshooting). S18 solve4 h4.py,
         # sprint_reaver(_town): lower half over the descending thigh p10 142 -> 6 mm, skin inside the panel max 76 -> 22
         "sprint": {"amp": [81.0, 86.0], "range": [30.0, 40.0], "decay": 10.0,
                    "amount": 0.5, "fall_tau": 0.012, "fall_rate": 1200.0, "hz": 19.0, "zeta": 1.0}},
    ],
    # Her upper arm's twist chain (Body 5 A2; design: A1 solver, 24 Oct). One twist bone a quarter down the arm
    # undoing half the roll left the turn all in two bands (shear 10.8 deg/cm at reaver_show's +105 roll, girth
    # 0.78 mid-arm); five weight nodes down the humerus carry it evenly. All of it only on a side that has `gate`
    # (a body without the chain: the legacy split and drive, unchanged). Per side:
    "twist_chain": {
        "gate": "upperarm_twist_02_{s}",
        # the upper arm's roll (its twist about its own +Y, from rest) read off this bone
        "roll_bone": "upperarm_{s}",
        # a legacy helper's amount in a chained arm: twist_01 carries 0.30 of the roll (the chain 0.30, 0.475,
        # 0.65, 0.825 of it; the elbow all)
        "amounts": {"upperarm_twist_01_{s}": 0.70},
        # the shoulder's share also takes this much of the roll (the deltoid follows the humerus by 30%): its
        # pose rest x slerp(swing, amount) x twist_y(roll x k) x own
        "roll": {"upperarm_share_{s}": 0.30},
        # the roll unwrapped frame to frame (nearest to the last frame's, within +-this many degrees), so a
        # roll through +-180 doesn't flip the chain's counter-twists; one frame on its own reads it as it is
        "unwrap_max": 270.0,
        # weights: the upper arm's (after the shares) spread as hats over these nodes, t along the humerus
        # (0 shoulder, 1 elbow), each a bone (1.0: the upper arm itself)
        "nodes": [["upperarm_twist_01_{s}", 0.0], ["upperarm_twist_02_{s}", 0.25], ["upperarm_twist_03_{s}", 0.5],
                  ["upperarm_twist_04_{s}", 0.75], ["upperarm_{s}", 1.0]],
        # the shoulder share's and the clavicle's weight handed to the chain from t reach[0], all by reach[1]
        # (smoothstep), so the share no longer reaches down the arm; only near the humerus's line: whole within
        # radius[0] of it, none past radius[1] (smoothstep; in upper-arm lengths), so her torso keeps its own
        "reach": [0.10, 0.60],
        "reach_from": ["upperarm_share_{s}", "clavicle_{s}"],
        "radius": [0.30, 0.40],
    },
    # Her elbow's weights kept off the humerus (Body 14, 26 Oct; elbow_trim, run on a built body by
    # tools/assets/elbow_trim_post.py). The bones that follow the elbow's bend (`lower`: the forearm, its twists, the
    # hand and fingers, the elbow's share and point) reached up the humerus (on B's back 5.5% of the bend at t .75,
    # 16% at .85; mostly the share), so a bend swung the triceps and biceps there: the back edge out 3.9 mm at t .75
    # at 90 deg, the front in 3.1, the outer side caved. Their weight is kept whole from t `full` toward the elbow and
    # eased out (smoothstep) to none at t `gone` (t along the humerus at rest: 0 the shoulder joint, 1 the elbow's),
    # per sector round the arm: `bf` on the back and front (|cos| of the angle round from her front past `c`[1]),
    # `side` on the outer and inner sides (below `c`[0]), smoothstep between; what it loses goes to the upper arm's
    # chain (twist_chain nodes, as hats by t), or the upper arm itself where it has none.
    "elbow_trim": {
        "lower": ["lowerarm_{s}", "lowerarm_twist_01_{s}", "lowerarm_twist_02_{s}", "hand_{s}", "lowerarm_share_{s}",
                  "lowerarm_point_{s}"],
        "fingers": ["index", "middle", "ring", "pinky", "thumb"],
        "bf": [0.82, 0.92], "side": [0.80, 0.92], "c": [0.3, 0.7],
    },
    # Her scapula (Body 6 S1, 24 Oct; the shoulder rig's stage 1). A real shoulder girdle rises with the arm mostly by
    # the SCAPULA's upward rotation (39-50 deg overhead), the clavicle only ~6 deg up; her clavicle alone carried 34
    # deg, the shoulder joint rose ~8 cm and the trapezius came up rigid into a corner (football pads, no neck). Per
    # side, scap_{s} (a child of `parent`, its global rest turn none, at `pivot`: the root of the scapula's spine,
    # medial and behind; her rest space, game axes, her left, the right mirrored) turns about `axis` (the scapular
    # plane's normal, 35 deg off her front; her left, the right mirrored as a turn) by per_deg x (A - from), eased in
    # over `ease` degrees (a quadratic: no kink), A the upper arm's angle from her torso's down axis read after the
    # clavicle lift. With it her clavicle lift is shrug_max x the smoothstep (13 overhead), its outer end turned
    # shrug_roll of it (back). Only on a body with the bones (`gate`): the hero, the NPCs and her older bodies drive
    # as before. Built by tools/assets/scap_rig_post.py, which also writes her weights onto it ("weights").
    "scap": {
        "gate": "scap_{s}",
        "bone": "scap_{s}",
        "parent": "spine_03",
        "pivot": [0.075, 1.45, -0.085],
        "axis": [-0.5736, 0.0, 0.8192],
        "per_deg": 0.43, "from": 50.0, "ease": 25.0,
        "shrug_max": 13.0, "shrug_roll": -0.6,
        "weights": {
            # along her trapezius' top: the clavicle's share of the non-arm weight a smoothstep in x (m from her
            # midline) from x0 to x1; the arm's a smoothstep over arm_ramp; full within band[0] m below the top, none
            # past band[1]; eased back to her own weights over `out` (x)
            "x0": 0.06, "x1": 0.23, "arm_ramp": [0.19, 0.25], "band": [0.015, 0.05], "out": [0.24, 0.27],
            # the blade: up to blade_max of the non-arm weight to scap_{s}, full over the x and y spans, eased out
            # over blade_fade; only behind blade_z (eased over blade_fade)
            "blade_max": 0.55, "blade_x": [0.07, 0.13], "blade_y": [1.335, 1.435], "blade_fade": 0.04,
            "blade_z": -0.03,
        },
    },
    # Her shoulder's muscle helpers (Body 6 S2, 24 Oct; the shoulder rig's stage 2): with both arms up the judge saw
    # "arms as tubes plugged into the corners of a box". Per side, each a child of the one bone (`parent`) whose weight
    # it takes (tools/assets/shoulder_rig_post.py), so below `A`[0] (the arm's angle from her torso's down axis, as
    # HerScap reads it) it moves exactly as that bone did: her idles and the Look are unchanged to the bit. Past it, g
    # (a smoothstep over `A`) of: a turn of `follow` of the way from the bone's line to the aim (a point on her humerus
    # `aim`[0] m below the joint plus `aim`[1], carried by `on`), a stretch along its line of (L/L0)^ka and across of
    # (L/L0)^-kp (L the pivot-to-aim length), times 1+`sa` along and 1+`sp` across, and a move of `off` (m, her rest
    # axes, turned with the parent). `pivot`: her rest space (her left; the right mirrored), or ["hum", m] on the humerus.
    # delt: the deltoid bunching (wider across, shorter along) on the upper arm's outer side; trap: the outer trapezius
    # top lifted 15 mm (none near her neck); pec: the pec's lower-lateral band turned and stretched toward the arm (the
    # front axillary fold); lat: the lat band below the armpit turned in toward the arm's line (the torso narrows from
    # the armpit down, behind the breast). Weights ("weights"): smoothstep bands in her rest space, x out from her midline.
    "shoulder": {
        "gate": "delt_{s}",
        "A": [60.0, 120.0],
        "bones": {
            "delt": {"parent": "upperarm_twist_02_{s}", "pivot": ["hum", 0.05], "aim": [0.30, [0, 0, 0]], "on": "upperarm_{s}",
                     "follow": 0.0, "ka": 0.0, "kp": 0.0, "sa": -0.10, "sp": 0.45, "off": [0, 0, 0]},
            "trap": {"parent": "clavicle_{s}", "pivot": [0.10, 1.535, -0.04], "aim": None, "on": "upperarm_{s}",
                     "follow": 0.0, "ka": 0.0, "kp": 0.0, "sa": 0.0, "sp": 0.0, "off": [0.0, 0.015, 0.0]},
            "pec": {"parent": "spine_03", "pivot": [0.05, 1.42, 0.05], "aim": [0.08, [0, 0, 0.025]], "on": "upperarm_{s}",
                    "follow": 0.2, "ka": 0.5, "kp": 0.0, "sa": 0.0, "sp": 0.0, "off": [0, 0, 0]},
            "lat": {"parent": "spine_03", "pivot": [0.09, 1.20, -0.05], "aim": [0.07, [-0.01, 0, 0.01]], "on": "upperarm_{s}",
                    "follow": 0.15, "ka": 0.0, "kp": 0.0, "sa": 0.0, "sp": 0.0, "off": [0, 0, 0]},
        },
        # (S2b, 8 weights: the masks eased over her surface; pec and lat follow cut from 0.6 / 0.4, which folded the
        # breast's top and the pit's lat edge at A 150-160; the delt's bulge 0.30 -> 0.45: its offset 45 -> 55 mm)
        "smooth": 10,
        "weights": {
            # delt: t (m along the humerus from the joint) in, full, full, out; c the cosine to its top-outer side
            # (in from, full at); none past r m from the humerus
            "delt": {"t": [0.0, 0.03, 0.10, 0.14], "c": [-0.3, 0.3], "r": 0.10},
            # trap: x in, full, full, out; d below the top of her silhouette (full within, none past)
            "trap": {"x": [0.10, 0.15, 0.17, 0.20], "d": [0.02, 0.045]},
            # pec: x in; y in, full, full, out; z in (the front of her armpit); less over the breast (1 - bre x its weight)
            "pec": {"x": [0.07, 0.13], "y": [1.39, 1.43, 1.50, 1.54], "z": [0.02, 0.05], "bre": 1.0},
            # lat: x in; y in, full, full, out (the armpit's dome stays on spine_03 and the share); z: out at the front
            # (from, to), in at the back (from, to)
            "lat": {"x": [0.08, 0.12], "y": [1.22, 1.30, 1.38, 1.43], "z": [0.02, 0.06, -0.07, -0.03]},
        },
    },
}


def _smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)

# Where along a parent's line a twist bone lies: toward its main child.
MAIN_CHILD = {"upperarm": "lowerarm", "lowerarm": "hand"}


def each(text):
    return [text.replace("{s}", s) for s in "lr"]


def write_spec():
    SPEC_FILE.write_text(json.dumps(SPEC, indent=1) + "\n")


def names():
    return [n for h in SPEC["helpers"] for n in each(h["name"])] + [p["name"] for p in SPEC.get("panels", [])]


def has_helpers(sk: Skeleton):
    return "lowerarm_twist_01_l" in sk.index


def has_chain(index, s):
    """The upper arm's twist chain on side `s` (SPEC "twist_chain"): `index` any name lookup (a dict, a set)."""
    return SPEC["twist_chain"]["gate"].replace("{s}", s) in index


def unwrap_roll(last, deg, lim=None):
    """The roll `deg` (-180..180) as the turn nearest `last` (the last frame's, None: the first), deg or deg +-360
    within +-lim (SPEC twist_chain unwrap_max), so a roll through +-180 carries on instead of flipping."""
    if last is None:
        return deg
    lim = SPEC["twist_chain"]["unwrap_max"] if lim is None else lim
    best = deg
    for c in (deg - 360.0, deg + 360.0):
        if abs(c) <= lim and abs(c - last) < abs(best - last):
            best = c
    return best


# --------------------------------------------------------------- geometry --
def _twist_y(d):
    """d split as swing * twist, the twist about the bone's own +Y:
    (swing, twist, twist angle in degrees)."""
    t = np.array([0.0, d[1], 0.0, d[3]])
    n = np.linalg.norm(t)
    t = t / n if n > 1e-9 else np.array([0, 0, 0, 1.0])
    if t[3] < 0:
        t = -t
    ang = math.degrees(2 * math.atan2(t[1], t[3]))
    return qmul(d, qinv(t)), t, ang


def hinge_turn(child_global_rot, joint_from, joint_at, way, front=(0, 0, 1.0)):
    """Degrees about the bone below a joint, along its own line, that bring
    its X onto the axis the joint bends about (as keyed.Rig keeps it: across
    the bone above and her front for an elbow, her back for a knee), read
    from a right-angle bend. `front` is her front in the space given (+Z in
    the game's; -Y in Blender's)."""
    u = np.asarray(joint_at, float) - np.asarray(joint_from, float)
    u = u / np.linalg.norm(u)
    w = np.asarray(front, float) * (1.0 if way == "front" else -1.0)
    h = np.cross(u, w)
    h = h / np.linalg.norm(h)
    g = np.asarray(child_global_rot, float)
    d = qmul(qinv(g), qmul(qaxis(h, 90), g))
    sw, _, _ = _twist_y(d)
    a = sw[:3] / max(np.linalg.norm(sw[:3]), 1e-9)
    return math.degrees(math.atan2(-a[2], a[0]))


# ------------------------------------------------------------- skeleton --
def extend(sk: Skeleton, chain=False) -> Skeleton:
    """The skeleton with her helper bones added after its own (if missing),
    rests as heroine_rig.py builds them. The upper arm's twist chain
    (SPEC "twist_chain") only with `chain` (hers, explicitly)."""
    names_, parent = list(sk.names), list(sk.parent)
    rot, pos = list(sk.rest_rot), list(sk.rest_pos)
    I = dict(sk.index)
    grot, gpos = sk.rest_globals()
    for h in SPEC["helpers"]:
        if h.get("chain") and not chain:
            continue
        for s in "lr":
            n = h["name"].replace("{s}", s)
            if n in I:
                continue
            p = I[h["parent"].replace("{s}", s)]
            if h["kind"] in ("share", "point"):
                b = I[h["bone"].replace("{s}", s)]
                above = sk.parent[b]
                turn = hinge_turn(grot[0, b], gpos[0, above], gpos[0, b], h["way"])
                r, t = qmul(sk.rest_rot[b], qaxis([0, 1.0, 0], turn)), sk.rest_pos[b]
            else:
                main = MAIN_CHILD[sk.names[p].split("_")[0]] + "_" + s
                t = sk.rest_pos[I[main]] * h["at"]
                r = np.array([0, 0, 0, 1.0])
            I[n] = len(names_)
            names_.append(n)
            parent.append(p)
            rot.append(np.array(r, float))
            pos.append(np.array(t, float))
    for pn in SPEC.get("panels", []):
        if pn["name"] in I or pn["parent"] not in I:
            continue
        p = I[pn["parent"]]
        gp = grot[0, p]
        # laid along the panel: +Y down, +Z her front (so +X her right)
        r = qmul(qinv(gp), PANEL_REST)
        t = qrot(qinv(gp), np.asarray(pn["pivot"], float))
        I[pn["name"]] = len(names_)
        names_.append(pn["name"])
        parent.append(p)
        rot.append(np.array(r, float))
        pos.append(np.array(t, float))
    out = Skeleton(names=names_, parent=parent, rest_rot=np.array(rot), rest_pos=np.array(pos), path=sk.path)
    out.index = I
    return out


# --------------------------------------------------------------- driving --
def forearm_turn(sk, h, hand_local):
    """The hand's turn about the forearm (degrees), on the forearm's own
    frame: its thumb side's way across the forearm against where it lies at
    rest (neither a bend toward the palm nor to the side changes it)."""
    a = sk.rest_pos[h] / np.linalg.norm(sk.rest_pos[h])
    t0 = qrot(sk.rest_rot[h], [0, 0, 1.0])
    t = qrot(hand_local, [0, 0, 1.0])
    t0 = t0 - a * np.dot(t0, a)
    t = t - a * np.dot(t, a)
    if np.linalg.norm(t0) < 1e-9 or np.linalg.norm(t) < 1e-9:
        return 0.0
    return math.degrees(math.atan2(float(np.dot(np.cross(t0, t), a)), float(np.dot(t0, t))))


def hinge_part(swing, own, amount):
    """`amount` of a joint's bend about the share's own hinge (its X, the share's rest turn `own` about the bone's
    line carries it into the bone below's rest frame), as a rotation in that frame: the angle about the hinge that
    takes the bone's line (+Y) to its posed line, both seen along the hinge. The swing's shortest arc runs about
    Y x Y', off the hinge wherever the joint carries an angle (her elbow's ~16 deg: 23 deg off at 90, 64 at 145), and
    half of it swung the flesh above the elbow sideways; the hinge's own turn bends it in the bend's plane."""
    a = qrot(own, [1.0, 0, 0])
    y1 = qrot(swing, [0, 1.0, 0])
    p0 = np.array([0, 1.0, 0]) - a * a[1]
    p1 = y1 - a * float(a @ y1)
    ang = math.degrees(math.atan2(float(np.cross(p0, p1) @ a), float(p0 @ p1)))
    return qaxis(a, ang * amount)


def _swing_deg(swing):
    """Degrees a swing (no turn about the bone's own line) turns."""
    return 2 * math.degrees(math.acos(min(1.0, abs(float(swing[3])))))


def bend(sk: Skeleton, rot, bone):
    """Degrees the joint above `bone` is bent in the pose (local rotations):
    the bone's swing from its rest, its turn about its own line left out.
    The shares are driven by it and the correctives keyed on it."""
    j = sk.index[bone]
    swing, _, _ = _twist_y(qmul(qinv(sk.rest_rot[j]), rot[j]))
    return _swing_deg(swing)


def flexion(sk: Skeleton, rot, bone):
    """Degrees the joint above `bone` is flexed: its line (+Y) in its rest
    frame, seen along its own X (the hinge her clips bend about), from rest
    toward +Z (her front); negative past rest. The swing's sideways part (the
    forearm swung onto the humerus' line) and its turn about its line left
    out. Play/ElbowPsd.Flexion is the game's twin."""
    j = sk.index[bone]
    d = qrot(qmul(qinv(sk.rest_rot[j]), rot[j]), [0, 1.0, 0])
    return math.degrees(math.atan2(float(d[2]), float(d[1])))


def corrective_weight(c, deg):
    """A corrective shape's weight at `deg` degrees of its joint's bend (or
    flexion, c["on"] "flex"): eased in (smoothstep) from c["from"] to
    c["to"], none below; or (c["keys"] [lo, at, hi]) an in-between: 0 at lo
    and below, linear to 1 at `at`, linear to 0 at hi (hi <= at: held at 1
    past `at`). Play/ElbowPsd.Weight is the game's twin."""
    if "keys" in c:
        lo, at, hi = (float(x) for x in c["keys"])
        if deg <= lo:
            return 0.0
        if deg < at:
            return (deg - lo) / (at - lo)
        if hi <= at:
            return 1.0
        return max(0.0, 1.0 - (deg - at) / (hi - at))
    t = min(max((deg - c["from"]) / (c["to"] - c["from"]), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def corrective_weights(sk: Skeleton, rot):
    """{shape name: weight} for the pose (local rotations, as drive takes them)."""
    out = {}
    for c in SPEC.get("correctives", []):
        for s in "lr":
            b = c["bone"].replace("{s}", s)
            if b in sk.index:
                deg = flexion(sk, rot, b) if c.get("on") == "flex" else bend(sk, rot, b)
                out[c["name"].replace("{s}", s)] = corrective_weight(c, deg)
    return out


def bulge(bend, h):
    """How far the flesh round a joint bent `bend` degrees is pushed out
    across the bend, as a stretch along the share bone's Z. With the skin's
    weights a quadratic Bezier over the joint (split, "smooth"), a point
    halfway round lies at (cos(bend/2) + stretch) / 2 of its rest distance
    from the joint, so a stretch of 2 - cos(bend/2) keeps it there: the
    joint bends round as a rounded corner, neither cut across nor pushed to
    a point. `bulge` of that stretch, at most `bulge_max`.

    With a `pivot` (metres along the share's Z: the flexor side, the inside
    of the bend, which is +Z at the elbow and the knee) the stretch is about
    that point, not the bone's line: the crease side is held where it is (a
    stretch there pushed the crease's skin over itself: a fold-over tick
    behind the knee), and the extensor side, twice as far from the pivot,
    takes the whole push from half the bulge."""
    k = 2.0 - math.cos(math.radians(min(bend, 180.0) / 2))
    return float(min(1.0 + h.get("bulge", 0.0) * (k - 1.0), h.get("bulge_max", 1.0)))


def point_push(bend, h):
    """How far a point bone is pushed out across the bend (metres, along
    its -Z: away from the crease), eased in from h["from"] to h["to"]
    degrees of bend. Nothing for a share."""
    if h["kind"] != "point":
        return 0.0
    t = min(max((bend - h["from"]) / (h["to"] - h["from"]), 0.0), 1.0)
    return float(h["push"] * t * t * (3 - 2 * t))


def point_squeeze(bend, h):
    """How much of a point bone's width along its X (the hinge axis) is drawn
    in toward h["squeeze_x"], eased in from h["squeeze_from"] to h["to"]
    degrees of bend. Nothing for a share."""
    if h["kind"] != "point" or not h.get("squeeze"):
        return 0.0
    t = min(max((bend - h["squeeze_from"]) / (h["to"] - h["squeeze_from"]), 0.0), 1.0)
    return float(h["squeeze"] * t * t * (3 - 2 * t))


# A panel's rest in her rest axes: half a turn about +Z (+Y down, +X her right).
PANEL_REST = np.array([0.0, 0.0, 1.0, 0.0])


def _smax(a, b, k):
    """Polynomial smooth max, `k` wide (max + k/4 where a == b)."""
    h = max(k - abs(a - b), 0.0) / k
    return max(a, b) + h * h * k / 4


def _softrelu(x, k):
    """0 below 0, x - k/2 above k, a quadratic between (smooth, never < 0)."""
    return 0.0 if x <= 0 else (x * x / (2 * k) if x < k else x - k / 2)


def panel_turn(pn, fl, fr, al, ar, drop=True):
    """Degrees a panel turns forward (SPEC "panels"): from each thigh's
    forward swing (fl, fr) and spread (al, ar), degrees from rest. Past
    `drop_from` degrees of lead it turns `drop` a degree less (softly, and
    not with the thighs spread), so at a run's raised knee it lies on the
    thigh rather than riding over it (Body 18); drop=False: without that
    (the fold's contact reads the thigh's own lead)."""
    k = pn["soft"]
    lead = _smax(fl, fr, k) - k / 4
    spread = (al + ar) / 2
    sp = float(_smooth((spread - pn["spread_from"]) / (pn["spread_to"] - pn["spread_from"])))
    damp = 1.0 - pn["spread_damp"] * sp
    t = pn["amount"] * _softrelu(lead, k) * damp
    if drop and pn.get("drop"):
        t -= pn["drop"] * _softrelu(lead - pn["drop_from"], k) * (1.0 - sp)
    return t


def side_weights(sd, fl, fr):
    """The panel's side shapes' weights (left, right) from each thigh's forward swing (SPEC "panels" "fold"
    "side"): smoothstep over `swing`. PanelSwing.SideWeights' twin."""
    a, b = sd["swing"]
    return float(_smooth((fl - a) / (b - a))), float(_smooth((fr - a) / (b - a)))


def panel_sprint(sd, st, lead, dt):
    """How much of a sprint the panel's law is in (0..1, SPEC "panels" "sprint") from the lead's swing this frame
    and `st` (a dict kept frame to frame, {} at the first): its peak and trough held, each easing back toward the lead
    `decay` deg/s; the held peak past `amp` (smoothstep) times the held swing (peak - trough) past `range`.
    PanelSwing.Sprint's twin."""
    if "hi" not in st:
        st.update(hi=lead, lo=lead)
    else:
        st["hi"] = max(lead, st["hi"] - sd["decay"] * dt)
        st["lo"] = min(lead, st["lo"] + sd["decay"] * dt)
    a0, a1 = sd["amp"]
    r0, r1 = sd["range"]
    return float(_smooth((st["hi"] - a0) / (a1 - a0))) * float(_smooth((st["hi"] - st["lo"] - r0) / (r1 - r0)))


def sprint_blend(pn, g):
    """The panel's law `pn` blended `g` of the way to its "sprint" numbers (the fold's hz and zeta with it)."""
    sd = pn.get("sprint")
    if not sd or g <= 0:
        return pn
    out = dict(pn)
    for k in ("amount", "fall_tau", "fall_rate"):
        out[k] = pn[k] + (sd[k] - pn[k]) * g
    if "fold" in pn:
        out["fold"] = dict(pn["fold"], **{k: pn["fold"][k] + (sd[k] - pn["fold"][k]) * g for k in ("hz", "zeta")})
    return out


def panel_fall(pn, prev, target, dt):
    """The panel's turn this frame (degrees) from last frame's (`prev`, None
    at the first) and the law's (`target`), `dt` seconds on: up at once,
    down as a first-order lag (`fall_tau`), at most `fall_rate` deg/s, never
    below the law. PanelSwing.Fall's twin."""
    if prev is None or target >= prev:
        return target
    if dt <= 0:
        return prev
    y = target + (prev - target) * math.exp(-dt / pn["fall_tau"])
    return max(target, y, prev - pn["fall_rate"] * dt)


def panel_fold(fd, st, turn, amount, th, dt):
    """The lower half's fold this frame (degrees past the upper's turn `th`, + forward) from the law's turn
    `turn` (before its fall; `amount` the law's amount) and `st` (a dict kept from frame to frame, {} at the
    first: the half's own angle from plumb, its speed, last frame's contact), `dt` seconds on (SPEC "panels"
    "fold"). PanelSwing.Fold's twin."""
    c1, c0 = fd["contact"]
    push = c1 * (turn / amount if amount else 0.0) - c0
    if "lam" not in st:
        st.update(lam=max(push, fd["rest"]), v=0.0, push=push)
    if dt > 0:
        w = 2 * math.pi * fd["hz"]
        z = fd["zeta"]
        # (substeps: at least `substeps`, and enough that w h <= 1, so a stiff spring holds at a long frame)
        n = max(int(fd["substeps"]), math.ceil(w * dt))
        h = dt / n
        p0 = st["push"]
        rate = (push - p0) / dt
        lam, v = st["lam"], st["v"]
        for s in range(n):
            ps = p0 + (push - p0) * (s + 1) / n
            v += (w * w * (fd["rest"] - lam) - 2 * z * w * v) * h
            lam += v * h
            if lam < ps:
                lam = ps
                v = max(v, rate)
        st.update(lam=lam, v=v, push=push)
    beta = st["lam"] - th
    if beta > 2 * fd["step"]:
        beta = 2 * fd["step"]
        st["lam"] = th + beta
    return max(beta, -fd["neg"])


def fold_weights(fd, beta):
    """The fold's three shapes' weights (a, b, n) for `beta` degrees (panel_fold)."""
    s = fd["step"]
    if beta >= 0:
        return min(beta / s, 1.0), min(max((beta - s) / s, 0.0), 1.0), 0.0
    return 0.0, 0.0, min(-beta / fd["neg"], 1.0)


def _swing_spread(v, v0, side):
    """A thigh's line v (its +Y, in her rest axes carried with the pelvis)
    against its rest v0: (forward swing in her side plane, spread out to
    `side` (+1 her left, -1 her right)), degrees."""
    fwd = lambda u: math.degrees(math.atan2(u[2], -u[1]))
    out = lambda u: math.degrees(math.asin(min(1.0, max(-1.0, u[0] * side))))
    return fwd(v) - fwd(v0), out(v) - out(v0)


def _below(sk: Skeleton, rot, top, bone):
    """`bone`'s rotation in `top`'s frame (local rotations down the chain)."""
    q = np.array([0, 0, 0, 1.0])
    j = bone
    while j != top and j >= 0:
        q = qmul(rot[j], q)
        j = sk.parent[j]
    return q


def panel_angles(sk: Skeleton, rot, pn):
    """(fl, fr, al, ar): each thigh's forward swing and spread in the
    pelvis's frame, degrees from rest (local rotations as drive takes them)."""
    I = sk.index
    p = I[pn["parent"]]
    gp = sk.rest_globals()[0][0, p]
    res = []
    for name, side in zip(pn["thighs"], (1, -1)):
        t = I[name]
        v = qrot(gp, qrot(_below(sk, rot, p, t), [0, 1.0, 0]))
        v0 = qrot(gp, qrot(_below(sk, sk.rest_rot, p, t), [0, 1.0, 0]))
        res.append(_swing_spread(v, v0, side))
    (fl, al), (fr, ar) = res
    return fl, fr, al, ar


def drive_panels(sk: Skeleton, rot, state=None, dt=None):
    """The panel bones turned (local rotations, changed in place). With
    `state` (a dict kept from frame to frame, {} at the first) and `dt`
    (seconds since the last frame), each falls as panel_fall has it, as the
    game does; without, the law alone (one frame on its own)."""
    I = sk.index
    for pn in SPEC.get("panels", []):
        j = I.get(pn["name"])
        if j is None:
            continue
        p = I[pn["parent"]]
        ang = panel_angles(sk, rot, pn)
        if state is not None and "sprint" in pn:
            k = pn["soft"]
            g = panel_sprint(pn["sprint"], state.setdefault(pn["name"] + ":sprint", {}),
                             _smax(ang[0], ang[1], k) - k / 4, dt if dt is not None else 0.0)
            state[pn["name"] + ":sprint_g"] = g
            pn = sprint_blend(pn, g)
        law = deg = panel_turn(pn, *ang)
        if state is not None:
            deg = state[pn["name"]] = panel_fall(pn, state.get(pn["name"]), deg, dt if dt is not None else 0.0)
            if "fold" in pn:
                # (the lower half's fold: its shapes' weights left in state[name + ":fold"])
                st_ = state.setdefault(pn["name"] + ":fold_st", {})
                beta = panel_fold(pn["fold"], st_, law, pn["amount"], deg, dt if dt is not None else 0.0)
                state[pn["name"] + ":fold"] = (beta, fold_weights(pn["fold"], beta))
                if "side" in pn["fold"]:
                    state[pn["name"] + ":side"] = side_weights(pn["fold"]["side"], ang[0], ang[1])
        # about her lateral axis (+X her right), in the pelvis's frame: the
        # panel's bottom forward and up
        gp = sk.rest_globals()[0][0, p]
        ax = qrot(qinv(gp), [-1.0, 0, 0])
        rot[j] = qnorm(qmul(qaxis(ax, deg), sk.rest_rot[j]))
    return rot


# ------------------------------------------------------------ clavicle lift --
# Her shoulder girdle as an arm rises (armor 17 C2; body5 lift, 24 Oct): a real clavicle and scapula carry the raise
# with the arm (scapulohumeral rhythm, about 2:1 glenohumeral to scapular), and many clips leave her clavicle where it
# rests, so the raised shoulder sat low and the arm plugged into a flat shelf at a V (judge 12: "a doll's ball joint").
# Per side: A = the upper arm's angle from her torso's down axis (pelvis to neck_01; 90 level, 180 overhead); the
# clavicle's wanted rise above its rest is SHRUG_MAX x smoothstep((A - SHRUG_FROM) / (SHRUG_TO - SHRUG_FROM)): nothing
# at and below SHRUG_FROM (60: her idles, the Look and the town untouched), eased in (no kink), 5 at level, 15 at 115,
# 25 at 140, easing out to SHRUG_MAX at SHRUG_TO (180). The clip's own rise counts (the larger wins, never a sum); the
# outer end rolls forward SHRUG_ROLL of the added rise. The hand stays where the clip puts it (two-bone re-aim of the
# upper and lower arm, the elbow kept in the clip's bend plane; its world turn kept); where the lifted shoulder can't
# reach the hand the lift is cut back until it can. The game's twin: Play/ClavicleLift.cs, run by HerShrug before
# HerRaise. SHRUG_OFF=1 (env) turns it off (the game: --shrug-off).
SHRUG_MAX, SHRUG_FROM, SHRUG_TO, SHRUG_ROLL, SHRUG_REACH = 34.0, 60.0, 180.0, 0.25, 0.999


def shrug_target(A, scap=False):
    """The clavicle's wanted rise (degrees above rest) for an upper arm at A degrees (`scap`: a body with her scapula
    helpers, SPEC "scap": its shrug_max instead of SHRUG_MAX)."""
    x = (A - SHRUG_FROM) / (SHRUG_TO - SHRUG_FROM)
    if x <= 0:
        return 0.0
    x = min(x, 1.0)
    return (SPEC["scap"]["shrug_max"] if scap else SHRUG_MAX) * x * x * (3 - 2 * x)


def has_scap(index, s):
    """Her scapula helper on side `s` (SPEC "scap"): `index` any name lookup."""
    return SPEC["scap"]["gate"].replace("{s}", s) in index


def scap_angle(A):
    """The scapula's upward rotation (degrees) for an upper arm at A degrees (SPEC "scap"): none at and below
    `from`, a quadratic over `ease` degrees, then per_deg a degree."""
    c = SPEC["scap"]
    x = A - c["from"]
    if x <= 0:
        return 0.0
    e = c["ease"]
    return c["per_deg"] * (x * x / (2 * e) if x < e else x - e / 2)


def scap_axis(s):
    """The scapula's turning axis for side `s` in her rest space (game axes); the right a mirror (as a turn)."""
    a = np.asarray(SPEC["scap"]["axis"], float)
    return a if s == "l" else a * np.array([1.0, -1.0, -1.0])


def scap_pivot(s):
    p = np.asarray(SPEC["scap"]["pivot"], float)
    return p if s == "l" else p * np.array([-1.0, 1.0, 1.0])


def add_scap(sk: Skeleton) -> Skeleton:
    """The skeleton with her scapula helpers added (if missing), rests as scap_rig_post.py builds them: a child of
    SPEC scap parent, no global rest turn (the skeleton's axes), at the pivot."""
    c = SPEC["scap"]
    names_, parent = list(sk.names), list(sk.parent)
    rot, pos = list(sk.rest_rot), list(sk.rest_pos)
    I = dict(sk.index)
    grot, gpos = sk.rest_globals()
    for s in "lr":
        n = c["bone"].replace("{s}", s)
        if n in I:
            continue
        p = I[c["parent"]]
        I[n] = len(names_)
        names_.append(n)
        parent.append(p)
        rot.append(np.array(qinv(grot[0, p]), float))
        pos.append(np.array(qrot(qinv(grot[0, p]), scap_pivot(s) - gpos[0, p]), float))
    out = Skeleton(names=names_, parent=parent, rest_rot=np.array(rot), rest_pos=np.array(pos), path=sk.path)
    out.index = I
    return out


def scap(sk: Skeleton, rot, report=None):
    """Her scapulae (SPEC "scap") on local rotations rot [J, 4], changed in place, from the pose as it stands (after
    her clavicle lift): each scap_{s} its rest x a turn about its axis (in its rest frame) by scap_angle(A). `report`
    (a dict), if given, gets per side (A, degrees)."""
    I = sk.index
    if not any(has_scap(I, s) for s in "lr") or "pelvis" not in I:
        return rot
    grot, gpos = sk.fk(rot[None])
    grot, gpos = grot[0], gpos[0]
    down = _torso(grot, gpos, I)[0]
    g0 = getattr(sk, "_scap_rest", None)
    if g0 is None:
        g0 = sk._scap_rest = sk.rest_globals()[0][0]
    for s in "lr":
        if not has_scap(I, s):
            continue
        j = I[SPEC["scap"]["bone"].replace("{s}", s)]
        S, E = gpos[I["upperarm_" + s]], gpos[I["lowerarm_" + s]]
        A = math.degrees(math.acos(float(np.clip((E - S) / np.linalg.norm(E - S) @ down, -1, 1))))
        deg = scap_angle(A)
        rot[j] = qnorm(qmul(sk.rest_rot[j], qaxis(qrot(qinv(g0[j]), scap_axis(s)), deg)))
        if report is not None:
            report[s] = (A, deg)
    return rot


# ---- her shoulder's muscle helpers (SPEC "shoulder"; Play/ShoulderHelpers.cs is the twin) ----
def _rotm(ax, ang):
    ax = np.asarray(ax, float)
    ax = ax / np.linalg.norm(ax)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


def has_shoulder(index, s):
    """Her shoulder helpers on side `s` (SPEC "shoulder"): `index` any name lookup."""
    return SPEC["shoulder"]["gate"].replace("{s}", s) in index


def shoulder_g(A):
    """How far the shoulder helpers act (0-1) for an upper arm at A degrees: a smoothstep over SPEC shoulder A."""
    a0, a1 = SPEC["shoulder"]["A"]
    return float(_smooth((A - a0) / (a1 - a0)))


def shoulder_rest(Grest):
    """{helper name: dict(G0 rest global 4x4, parent, on, T0, L0, c, s, off)} from {bone: rest global 4x4} (her
    skeleton space): each at its pivot, its Y toward its aim (up if none), X square to Y and her front."""
    out = {}
    for s, sg in (("l", 1.0), ("r", -1.0)):
        J, E = Grest["upperarm_" + s][:3, 3], Grest["lowerarm_" + s][:3, 3]
        h = (E - J) / np.linalg.norm(E - J)
        m = np.array([sg, 1.0, 1.0])
        for k, c in SPEC["shoulder"]["bones"].items():
            pv = J + c["pivot"][1] * h if c["pivot"][0] == "hum" else np.asarray(c["pivot"], float) * m
            T0 = None if c["aim"] is None else J + c["aim"][0] * h + np.asarray(c["aim"][1], float) * m
            Y = np.array([0, 1.0, 0]) if T0 is None else T0 - pv
            L0 = float(np.linalg.norm(Y))
            Y = Y / L0
            X = np.cross(Y, [0, 0, 1.0])
            X /= np.linalg.norm(X)
            G0 = np.eye(4)
            G0[:3, :3] = np.c_[X, Y, np.cross(X, Y)]
            G0[:3, 3] = pv
            out[f"{k}_{s}"] = dict(G0=G0, parent=c["parent"].replace("{s}", s), on=c["on"].replace("{s}", s),
                                   T0=T0, L0=L0, c=c, s=s, off=np.asarray(c["off"], float) * m)
    return out


def _blend_move(P1, P2, w):
    """Rigid moves P1 -> P2 (4x4, rotation and origin) blended by w: the rotation turned along its arc, the origin lerped."""
    if w <= 0:
        return P1
    D = P2[:3, :3] @ P1[:3, :3].T
    ang = math.acos(float(np.clip((np.trace(D) - 1) / 2, -1, 1)))
    out = P1.copy()
    if ang > 1e-9:
        ax = np.array([D[2, 1] - D[1, 2], D[0, 2] - D[2, 0], D[1, 0] - D[0, 1]])
        out[:3, :3] = _rotm(ax, ang * w) @ P1[:3, :3]
    out[:3, 3] = P1[:3, 3] + w * (P2[:3, 3] - P1[:3, 3])
    return out


def shoulder_helper(f, A, Mp, Gp0, Mon=None, Gon0=None, Mc=None, Gc0=None):
    """One helper's posed global 4x4 (rotation x scale, origin) from its parent's posed and rest globals (Mp, Gp0),
    its aim's carrier's (Mon, Gon0) and A (degrees). g 0: exactly its parent's move. A helper with a "carry" [bone,
    w] is carried part way (w x g) from its parent's move to that bone's (Mc, Gc0) before it acts (the cap's
    clavicle-weighted skin taken along with the raised humerus)."""
    c = f["c"]
    g = shoulder_g(A)
    P = Mp @ np.linalg.inv(Gp0) @ f["G0"]
    if c.get("carry") and g > 0:
        P = _blend_move(P, Mc @ np.linalg.inv(Gc0) @ f["G0"], c["carry"][1] * g)
    Rrel = P[:3, :3] @ np.linalg.inv(f["G0"][:3, :3])
    R, O = P[:3, :3].copy(), P[:3, 3].copy()
    sa = sp = 1.0
    if f["T0"] is not None and g > 0:
        T = (Mon @ np.linalg.inv(Gon0) @ np.r_[f["T0"], 1.0])[:3]
        d = T - O
        L = float(np.linalg.norm(d))
        r = L / f["L0"]
        ax = np.cross(R[:, 1], d)
        sn = float(np.linalg.norm(ax))
        if c["follow"] > 0 and sn > 1e-9:
            R = _rotm(ax / sn, math.atan2(sn, float(R[:, 1] @ d)) * c["follow"] * g) @ R
        sa *= 1 + g * (r ** c["ka"] - 1)
        sp *= 1 + g * (r ** -c["kp"] - 1)
    sa *= 1 + g * c["sa"]
    sp *= 1 + g * c["sp"]
    O = O + g * (Rrel @ f["off"])
    G = np.eye(4)
    G[:3, :3] = R @ np.diag([sp, sa, sp])
    G[:3, 3] = O
    return G


def shoulder_pose(M, Grest, frames, report=None):
    """{helper: posed global 4x4} from posed globals M {bone: 4x4} (Godot's skeleton space, after HerScap), her rest
    globals and shoulder_rest's frames. A per side as HerScap reads it (ScapRotation.ArmAngle)."""
    out = {}
    down = M["pelvis"][:3, 3] - M["neck_01"][:3, 3]
    down = down / np.linalg.norm(down)
    for n, f in frames.items():
        s = f["s"]
        u = M["lowerarm_" + s][:3, 3] - M["upperarm_" + s][:3, 3]
        A = math.degrees(math.acos(float(np.clip(u @ down / np.linalg.norm(u), -1, 1))))
        cb = f["c"]["carry"][0].replace("{s}", s) if f["c"].get("carry") else f["on"]
        out[n] = shoulder_helper(f, A, M[f["parent"]], Grest[f["parent"]], M[f["on"]], Grest[f["on"]], M[cb], Grest[cb])
        if report is not None:
            report[n] = (A, shoulder_g(A))
    return out


def _torso(grot, gpos, I):
    down = gpos[I["pelvis"]] - gpos[I["neck_01"]]
    down = down / np.linalg.norm(down)
    left = qrot(grot[I["spine_03"]], [1.0, 0, 0])
    left = left - (left @ down) * down
    left = left / np.linalg.norm(left)
    return down, left, np.cross(down, left)


def _elev(v, down):
    return math.degrees(math.asin(float(np.clip(-(v @ down) / np.linalg.norm(v), -1, 1))))


def shrug(sk: Skeleton, rot, report=None):
    """Her clavicle lift (the block above) on local rotations rot [J, 4], changed in place. `report` (a dict), if
    given, gets per side (A, rise before, added lift, hand move m, elbow move m)."""
    import os
    I = sk.index
    if os.environ.get("SHRUG_OFF") or "clavicle_l" not in I or "pelvis" not in I:
        return rot
    rest = getattr(sk, "_shrug_rest", None)
    if rest is None:
        g0, p0 = sk.fk(sk.rest_rot[None])
        d0 = _torso(g0[0], p0[0], I)[0]
        rest = {s: _elev(p0[0][I["upperarm_" + s]] - p0[0][I["clavicle_" + s]], d0) for s in "lr"}
        sk._shrug_rest = rest
    grot, gpos = sk.fk(rot[None])
    grot, gpos = grot[0], gpos[0]
    down, left, fwd = _torso(grot, gpos, I)
    for s in "lr":
        c, u, lo, h = (I[n + "_" + s] for n in ("clavicle", "upperarm", "lowerarm", "hand"))
        lat = left if s == "l" else -left
        Pc, S, E, H = gpos[c], gpos[u], gpos[lo], gpos[h]
        A = math.degrees(math.acos(float(np.clip((E - S) / np.linalg.norm(E - S) @ down, -1, 1))))
        rise = _elev(S - Pc, down) - rest[s]
        sc = has_scap(I, s)
        t = shrug_target(A, sc)
        d = min(t, max(0.0, t - rise))   # (none at and below SHRUG_FROM, even with the clip's clavicle dropped)
        if d < 1e-4:
            if report is not None:
                report[s] = (A, rise, 0.0, 0.0, 0.0)
            continue
        up_ax, roll_ax = np.cross(down, lat), np.cross(lat, fwd)   # outer end up; outer end forward
        L1, L2 = np.linalg.norm(E - S), np.linalg.norm(H - E)

        roll_k = SPEC["scap"]["shrug_roll"] if sc else SHRUG_ROLL

        def lifted(k):
            q = qmul(qaxis(roll_ax, roll_k * k), qaxis(up_ax, k))
            return q, Pc + qrot(q, S - Pc)
        q, S2 = lifted(d)
        if np.linalg.norm(H - S2) > SHRUG_REACH * (L1 + L2):        # cut back until the hand is in reach
            lo_k, hi_k = 0.0, d
            for _ in range(20):
                m = 0.5 * (lo_k + hi_k)
                if np.linalg.norm(H - lifted(m)[1]) > SHRUG_REACH * (L1 + L2):
                    hi_k = m
                else:
                    lo_k = m
            d = lo_k
            q, S2 = lifted(d)
        Dv = H - S2
        D = np.linalg.norm(Dv)
        ax = Dv / D
        pole = (E - S) - ((E - S) @ ax) * ax                      # the clip's bend plane
        if np.linalg.norm(pole) < 1e-6:
            pole = qrot(q, E - S) - (qrot(q, E - S) @ ax) * ax
        pole = pole / max(np.linalg.norm(pole), 1e-12)
        ca = float(np.clip((L1 * L1 + D * D - L2 * L2) / (2 * L1 * D), -1, 1))
        E2 = S2 + L1 * (ca * ax + math.sqrt(1 - ca * ca) * pole)
        Cg = qmul(q, grot[c])
        Ug = qnorm(qmul(qbetween(E - S, E2 - S2), grot[u]))
        Lg = qnorm(qmul(qbetween(H - E, H - E2), grot[lo]))
        rot[c] = qnorm(qmul(qinv(grot[sk.parent[c]]), Cg))
        rot[u] = qnorm(qmul(qinv(Cg), Ug))
        rot[lo] = qnorm(qmul(qinv(Ug), Lg))
        rot[h] = qnorm(qmul(qinv(Lg), grot[h]))
        if report is not None:
            g2, p2 = sk.fk(rot[None])
            report[s] = (A, rise, d, float(np.linalg.norm(p2[0][h] - H)), float(np.linalg.norm(p2[0][lo] - E)))
    return rot


def drive(sk: Skeleton, rot, scale=None, shift=None, state=None, dt=None, panels=True):
    """Her helpers posed from the pose (local rotations [J, 4], changed in
    place): the forearm's roll handed to the hand, the twists shared out, the
    shares half bent and swollen across the bend (`scale` [J, 3], if given,
    takes their stretch, and `shift` [J, 3] the move in the bone's own frame
    that holds its pivot still). As HerJoints.cs does it, after every other layer;
    her clavicle lift first (shrug, as HerShrug does before HerRaise).
    `state` and `dt`: the twist roll's unwrap and (with `panels`) the panels' fall from frame to frame (drive_panels)."""
    I = sk.index
    ident = np.array([0, 0, 0, 1.0])
    shrug(sk, rot)   # her clavicle lift first (HerShrug runs before every other layer of hers)
    scap(sk, rot)    # her scapulae from the lifted arm (as HerScap, after HerShrug and HerRaise)
    for s in "lr":
        la, h = I.get(f"lowerarm_{s}"), I.get(f"hand_{s}")
        if f"lowerarm_twist_01_{s}" not in I:
            continue
        # The forearm bone kept on its hinge: its roll goes to the hand.
        d = qmul(qinv(sk.rest_rot[la]), rot[la])
        sw, tw, _ = _twist_y(d)
        rot[la] = qnorm(qmul(sk.rest_rot[la], sw))
        rot[h] = qnorm(qmul(tw, rot[h]))
        turn = forearm_turn(sk, h, rot[h])
        # The upper arm's twist chain (SPEC "twist_chain"): its roll read once, unwrapped from the last frame's.
        tc = SPEC["twist_chain"]
        chain = has_chain(I, s)
        if chain:
            ub = I[tc["roll_bone"].replace("{s}", s)]
            _, _, roll = _twist_y(qmul(qinv(sk.rest_rot[ub]), rot[ub]))
            if state is not None:
                key = "roll:" + sk.names[ub]
                roll = state[key] = unwrap_roll(state.get(key), roll)
            amounts = {k.replace("{s}", s): v for k, v in tc["amounts"].items()}
            rolls = {k.replace("{s}", s): v for k, v in tc["roll"].items()}
        for hh in SPEC["helpers"]:
            j = I.get(hh["name"].replace("{s}", s))
            if j is None:
                continue
            if hh["kind"] == "forearm_twist":
                rot[j] = qaxis([0, 1.0, 0], turn * hh["amount"])
            elif hh["kind"] == "counter_twist":
                b = I[hh["bone"].replace("{s}", s)]
                if chain and b == ub:
                    rot[j] = qaxis([0, 1.0, 0], -roll * amounts.get(sk.names[j], hh["amount"]))
                    continue
                _, _, ang = _twist_y(qmul(qinv(sk.rest_rot[b]), rot[b]))
                rot[j] = qaxis([0, 1.0, 0], -ang * hh["amount"])
            elif hh["kind"] in ("share", "point"):
                b = I[hh["bone"].replace("{s}", s)]
                swing, _, _ = _twist_y(qmul(qinv(sk.rest_rot[b]), rot[b]))
                own = qmul(qinv(sk.rest_rot[b]), sk.rest_rot[j])        # its turn about the line
                if chain and sk.names[j] in rolls:
                    # (and its share of the upper arm's roll, about its own line)
                    own = qmul(qaxis([0, 1.0, 0], roll * rolls[sk.names[j]]), own)
                if hh.get("hinge"):
                    # (about its own hinge only: the swing's off-hinge rest stays with the bone below)
                    rot[j] = qnorm(qmul(sk.rest_rot[b], qmul(hinge_part(swing, own, hh["amount"]), own)))
                else:
                    rot[j] = qnorm(qmul(sk.rest_rot[b], qmul(qslerp(ident, swing, hh["amount"]), own)))
                if scale is not None:
                    deg = _swing_deg(swing)
                    hs = hh if hh["kind"] == "share" else next(x for x in SPEC["helpers"] if x["name"] == hh["share"])
                    k = bulge(deg, hs)
                    q = point_squeeze(deg, hh)
                    scale[j] = (1.0 - q, 1.0, k)
                    if shift is not None:
                        shift[j] = (q * hh.get("squeeze_x", 0.0), 0.0, (1.0 - k) * hs.get("pivot", 0.0) - point_push(deg, hh))
    drive_panels(sk, rot, state if panels else None, dt)
    return rot


# ---- HerRaise.cs's pull on her breasts as an arm rises (its defaults; RaiseRamp the twin) ----
RAISE = dict(start=-10.0, full=70.0, pitch=20.0, yaw=12.0, up=0.034, out=0.010, back=0.006, sup=0.22, sside=0.03, rigid=0.0)


def raise_breasts(sk: Skeleton, rot, pos, scale, squash=1.0):
    """Her breast bones (local rotations rot and positions pos [J, ...], and `scale` [J, 3], changed in place) as
    HerRaise sets them, after HerShrug: per side, w a smoothstep of the upper arm's elevation in spine_03's frame
    (RAISE start..full); the bone moved out/up/back, turned (yaw out, pitch up) and stretched up (the volume kept);
    `squash` HerJiggle.Squash (the worn top's; 0 under plate: no lift)."""
    I = sk.index
    if "spine_03" not in I:
        return rot
    c = RAISE
    grot, gpos = sk.fk(rot[None], pos[None])
    grot, gpos = grot[0], gpos[0]
    ci = qinv(grot[I["spine_03"]])
    for i, s in enumerate("lr"):
        b, u, lo = (I.get(n + "_" + s) for n in ("breast", "upperarm", "lowerarm"))
        if b is None or u is None or lo is None:
            continue
        d = qrot(ci, gpos[lo] - gpos[u])
        d = d / np.linalg.norm(d)
        el = math.degrees(math.asin(float(np.clip(d[1], -1, 1))))
        t = float(np.clip((el - c["start"]) / (c["full"] - c["start"]), 0, 1)) if c["full"] > c["start"] else float(el >= c["full"])
        w = t * t * (3 - 2 * t)
        if w <= 0:
            continue
        side = 1.0 if i == 0 else -1.0
        held, splay = c["rigid"] + (1 - c["rigid"]) * squash, squash
        turn = qmul(qaxis([0, 1.0, 0], c["yaw"] * side * w * splay), qaxis([1.0, 0, 0], -c["pitch"] * w * held))
        pos[b] = pos[b] + np.array([c["out"] * side * splay, c["up"] * held, -c["back"] * held]) * w
        rot[b] = qnorm(qmul(turn, rot[b]))
        if scale is not None:
            uu, ss = 1 + w * squash * c["sup"], 1 + w * squash * c["sside"]
            scale[b] = scale[b] * np.array([ss, 1 / (uu * ss), uu])
    return rot


def drive_shoulder(sk: Skeleton, G):
    """Her shoulder helpers (SPEC "shoulder") in bone globals G [J, 4, 4] (changed in place) as HerShoulder.cs poses
    them, last of her layers: each from its own rest global (the skeleton's, as Godot's GetBoneGlobalRest), its
    parent's and its aim carrier's posed and rest globals and A (the upper arm from neck_01 -> pelvis)."""
    I = sk.index
    if "pelvis" not in I or "neck_01" not in I:
        return G
    fr = getattr(sk, "_shoulder_rest", None)
    if fr is None:
        grot, gpos = sk.rest_globals()
        R = np.tile(np.eye(4), (len(sk.names), 1, 1))
        for j in range(len(sk.names)):
            R[j, :3, :3] = qmatrix(grot[0, j])
            R[j, :3, 3] = gpos[0, j]
        fr = {}
        for s, sg in (("l", 1.0), ("r", -1.0)):
            if not has_shoulder(I, s):
                continue
            J0, E0 = R[I["upperarm_" + s]][:3, 3], R[I["lowerarm_" + s]][:3, 3]
            h = (E0 - J0) / np.linalg.norm(E0 - J0)
            m = np.array([sg, 1.0, 1.0])
            for k, c in SPEC["shoulder"]["bones"].items():
                j = I.get(f"{k}_{s}")
                pj, oj = I.get(c["parent"].replace("{s}", s)), I.get(c["on"].replace("{s}", s))
                if j is None or pj is None or oj is None:
                    continue
                G0 = R[j]
                T0 = None if c["aim"] is None else J0 + c["aim"][0] * h + np.asarray(c["aim"][1], float) * m
                L0 = 1.0 if T0 is None else float(np.linalg.norm(T0 - G0[:3, 3]))
                fr[j] = (dict(G0=G0, T0=T0, L0=L0, c=c, s=s, off=np.asarray(c["off"], float) * m), pj, oj, R[pj], R[oj])
        sk._shoulder_rest = fr
    if not fr:
        return G
    down = G[I["pelvis"], :3, 3] - G[I["neck_01"], :3, 3]
    down = down / np.linalg.norm(down)
    A = {}
    for s in "lr":
        if "upperarm_" + s in I:
            u = G[I["lowerarm_" + s], :3, 3] - G[I["upperarm_" + s], :3, 3]
            A[s] = math.degrees(math.acos(float(np.clip(u @ down / np.linalg.norm(u), -1, 1))))
    for j, (f, pj, oj, Rp0, Ron0) in fr.items():
        # (the parent's and carrier's rotations orthonormal, as HerShoulder reads them: Basis.Orthonormalized)
        Mp, Mon = G[pj].copy(), G[oj].copy()
        for M in (Mp, Mon):
            M[:3, :3] = M[:3, :3] / np.linalg.norm(M[:3, :3], axis=0)
        G[j] = shoulder_helper(f, A[f["s"]], Mp, Rp0, Mon, Ron0)
    return G


# --------------------------------------------------------------- weights --
def split(W, P, index, heads, front=None):
    """Weights [V, J] (columns by `index`, name to column, the helpers'
    included) shared onto the helpers by where each point lies (P [V, 3]),
    with `heads` each bone's head at rest (name to point), then cut back to
    `cap` bones a point (each weight less the point's (cap+1)-th, so
    neighbours cut alike) and made whole. The space is any: only lengths
    along her bones are read, and with `front` (her front in that space:
    +Z in the game's, -Y in Blender's) which side of a joint is its crease."""
    W = np.array(W, float)
    I = index
    cfg = SPEC["weights"]
    for s in "lr":
        if f"lowerarm_twist_01_{s}" not in I:
            continue
        # The shares first: the blend between the bones above and below
        # each joint, carried by its share bone.
        for top, low, share in cfg["pairs"]:
            a, b, c = I.get(top.replace("{s}", s)), I.get(low.replace("{s}", s)), I.get(share.replace("{s}", s))
            if a is None or b is None or c is None:
                continue
            if cfg.get("profile") == "smooth":
                # As a quadratic Bezier's weights over the point's blend x
                # toward the bone below: (1-x)^2, 2x(1-x), x^2. Each point
                # turns on average as it did (x of the bend), and the skin
                # round the joint is a smooth curve through the share's ring.
                # (Weights cut as a tent, the most a share can take, leave
                # it two straight runs meeting in a ridge: at a deep bend the
                # knee came to a point.)
                tot = W[:, a] + W[:, b]
                x = np.where(tot > 1e-9, W[:, b] / np.maximum(tot, 1e-9), 0.0)
                k = cfg["share"]
                hs = next(h for h in SPEC["helpers"] if h["name"] == share)
                mid = tot * x * (1 - x)
                cr = cfg.get("crease")
                if cr and front is not None and "pivot" in hs:
                    # How far into the crease a point lies: along her front
                    # (elbow) or back (knee), square to the bone above.
                    j = np.asarray(heads[low.replace("{s}", s)], float)
                    ax = j - np.asarray(heads[top.replace("{s}", s)], float)
                    ax = ax / np.linalg.norm(ax)
                    w = np.asarray(front, float) * (1.0 if hs["way"] == "front" else -1.0)
                    w = w - ax * (w @ ax)
                    w = w / np.linalg.norm(w)
                    depth = np.clip(((P - j) @ w) / cr["reach"], 0.0, 1.0)
                    k = k * (1.0 - cr["cut"] * depth * depth * (3 - 2 * depth))
                W[:, c] += 2 * k * mid
                W[:, a] = tot * (1 - x) ** 2 + (1 - k) * mid
                W[:, b] = tot * x ** 2 + (1 - k) * mid
                for pn, po in (cfg.get("point") or {}).items():
                    hp_ = next(h for h in SPEC["helpers"] if h["name"] == pn)
                    d = I.get(pn.replace("{s}", s))
                    if hp_["share"] != share or d is None or front is None:
                        continue
                    # The patch round the joint's far side from the crease.
                    j = np.asarray(heads[low.replace("{s}", s)], float)
                    ax = j - np.asarray(heads[top.replace("{s}", s)], float)
                    ax = ax / np.linalg.norm(ax)
                    w = np.asarray(front, float) * (1.0 if hs["way"] == "front" else -1.0)
                    w = w - ax * (w @ ax)
                    w = w / np.linalg.norm(w)
                    rel = P - j
                    along = rel @ ax
                    perp = rel - along[:, None] * ax
                    cosang = (perp @ -w) / np.maximum(np.linalg.norm(perp, axis=1), 1e-9)
                    c0, c1 = math.cos(math.radians(po["half"] + po["fade"])), math.cos(math.radians(po["half"]))
                    f = _smooth((cosang - c0) / (c1 - c0))
                    f = f * _smooth((po["reach"] + po["feather"] - np.abs(along - po["at"])) / po["feather"])
                    W[:, d] += W[:, c] * f
                    W[:, c] *= 1 - f
            else:
                m = np.minimum(W[:, a], W[:, b]) * 2 * cfg["share"]
                W[:, c] += m
                W[:, a] -= m / 2
                W[:, b] -= m / 2
        # The shoulder's twist bone.
        ua, el = I[f"upperarm_{s}"], I[f"lowerarm_{s}"]
        sh, ax = np.asarray(heads[f"upperarm_{s}"], float), np.asarray(heads[f"lowerarm_{s}"], float) - np.asarray(heads[f"upperarm_{s}"], float)
        u = ((P - sh) @ ax) / (ax @ ax)
        if has_chain(I, s):
            _chain_split(W, P, I, s, sh, ax, u)
        else:
            frac = np.clip(1 - u / cfg["shoulder_twist_to"], 0, 1)
            frac = frac * frac * (3 - 2 * frac)
            tw = I[f"upperarm_twist_01_{s}"]
            W[:, tw] += W[:, ua] * frac
            W[:, ua] *= 1 - frac
        # The forearm's twist bones: hats over the nodes along it.
        la = I[f"lowerarm_{s}"]
        el_p = np.asarray(heads[f"lowerarm_{s}"], float)
        ax = np.asarray(heads[f"hand_{s}"], float) - el_p
        t = ((P - el_p) @ ax) / (ax @ ax)
        nodes = cfg["forearm_nodes"]
        bones = [la, I[f"lowerarm_twist_01_{s}"], I[f"lowerarm_twist_02_{s}"]]
        w = W[:, la].copy()
        W[:, la] = 0
        x = np.clip(t, nodes[0], nodes[-1])
        for k, (n0, b0) in enumerate(zip(nodes, bones)):
            hat = np.ones_like(x)
            if k > 0:
                hat = np.where(x < n0, (x - nodes[k - 1]) / (n0 - nodes[k - 1]), hat)
            if k + 1 < len(nodes):
                hat = np.where(x > n0, (nodes[k + 1] - x) / (nodes[k + 1] - n0), hat)
            W[:, b0] += w * np.clip(hat, 0, 1)
    W = np.maximum(W, 0)
    cap = cfg["cap"]
    if cap and W.shape[1] > cap:
        nth = -np.partition(-W, cap, axis=1)[:, cap]
        W = np.maximum(W - nth[:, None], 0)
    return W / np.maximum(W.sum(1, keepdims=True), 1e-12)


def _chain_split(W, P, I, s, sh, ax, u):
    """The upper arm's twist chain's weights (SPEC "twist_chain"), W changed in place: the upper arm's weight (with
    whatever its chain already had) spread as hats over the nodes by u (along the humerus, 0 shoulder, 1 elbow), the
    shoulder share's and clavicle's handed to the chain as they reach down the arm, near its line only."""
    tc = SPEC["twist_chain"]
    nodes = [(I[n.replace("{s}", s)], t) for n, t in tc["nodes"]]
    w = np.zeros(len(W))
    for j, _ in nodes:
        w += W[:, j]
        W[:, j] = 0
    r = np.linalg.norm((P - sh) - u[:, None] * ax, axis=1) / math.sqrt(ax @ ax)
    r0, r1 = tc["reach"]
    q0, q1 = tc["radius"]
    f = _smooth((u - r0) / (r1 - r0)) * (1 - _smooth((r - q0) / (q1 - q0)))
    for n in tc["reach_from"]:
        j = I.get(n.replace("{s}", s))
        if j is None:
            continue
        w += W[:, j] * f
        W[:, j] *= 1 - f
    ts = [t for _, t in nodes]
    x = np.clip(u, ts[0], ts[-1])
    for k, (j, t) in enumerate(nodes):
        hat = np.ones_like(x)
        if k > 0:
            hat = np.where(x < t, (x - ts[k - 1]) / (t - ts[k - 1]), hat)
        if k + 1 < len(nodes):
            hat = np.where(x > t, (ts[k + 1] - x) / (ts[k + 1] - t), hat)
        W[:, j] += w * np.clip(hat, 0, 1)


def elbow_trim(W, P, names, heads, s, front=(0, 0, 1.0), cfg=None):
    """Weights W [V, J] (columns `names`) on rest points P [V, 3] with side `s`'s elbow bones' weight kept off the
    humerus (SPEC "elbow_trim"), as a new array; `heads` each bone's rest head (name to point), `front` her front in
    that space. Points with none of those bones' weight are returned as they were."""
    cfg = cfg or SPEC["elbow_trim"]
    W = np.array(W, float)
    I = {n: i for i, n in enumerate(names)}
    low = [I[n.replace("{s}", s)] for n in cfg["lower"] if n.replace("{s}", s) in I]
    low += [i for n, i in I.items() if n.endswith("_" + s) and n.split("_")[0] in cfg["fingers"]]
    sh, el = np.asarray(heads[f"upperarm_{s}"], float), np.asarray(heads[f"lowerarm_{s}"], float)
    ax = el - sh
    L2 = float(ax @ ax)
    u = ax / math.sqrt(L2)
    rel = P - sh
    t = rel @ ax / L2
    f = np.asarray(front, float) - u * (u @ np.asarray(front, float))
    f = f / np.linalg.norm(f)
    perp = rel - np.outer(rel @ u, u)
    c = np.abs(perp @ f) / np.maximum(np.linalg.norm(perp, axis=1), 1e-9)
    k = _smooth((c - cfg["c"][0]) / (cfg["c"][1] - cfg["c"][0]))
    gone = cfg["side"][0] + k * (cfg["bf"][0] - cfg["side"][0])
    full = cfg["side"][1] + k * (cfg["bf"][1] - cfg["side"][1])
    keep = _smooth((t - gone) / (full - gone))
    lw = W[:, low].sum(1)
    rows = np.nonzero((lw > 0) & (keep < 1))[0]
    if not len(rows):
        return W
    moved = W[rows][:, low].sum(1) * (1 - keep[rows])
    W[np.ix_(rows, low)] *= keep[rows, None]
    tc = SPEC["twist_chain"]
    nodes = [(I.get(n.replace("{s}", s)), tt) for n, tt in tc["nodes"]]
    if not has_chain(I, s) or any(j is None for j, _ in nodes):
        nodes = [(I[f"upperarm_{s}"], 1.0)]
    ts = [tt for _, tt in nodes]
    x = np.clip(t[rows], ts[0], ts[-1])
    for n_, (j, tt) in enumerate(nodes):
        hat = np.ones_like(x)
        if n_ > 0:
            hat = np.where(x < tt, (x - ts[n_ - 1]) / (tt - ts[n_ - 1]), hat)
        if n_ + 1 < len(nodes):
            hat = np.where(x > tt, (ts[n_ + 1] - x) / (ts[n_ + 1] - tt), hat)
        W[rows, j] += moved * np.clip(hat, 0, 1)
    return W


# ----------------------------------------------------------- correctives --
def mats(grot, gpos, scale=None, shift=None):
    """Bone globals [J, 4, 4] from global rotations and positions, a
    helper's stretch (`scale` [J, 3]) and move (`shift` [J, 3]) in its own
    frame, as the game and skin.Body build them."""
    M = np.tile(np.eye(4), (len(grot), 1, 1))
    for j in range(len(grot)):
        R = qmatrix(grot[j])
        M[j, :3, :3] = R if scale is None else R @ np.diag(scale[j])
        M[j, :3, 3] = gpos[j] if shift is None else gpos[j] + R @ shift[j]
    return M


def bent(sk: Skeleton, bone, deg, front=(0, 0, 1.0), way="front"):
    """Her rest pose with the joint above `bone` bent `deg` degrees as bend
    reads it, about its hinge (across the bone above and her front, or her
    back for a knee: `way`), as the review's test poses bend it."""
    j = sk.index[bone]
    p = sk.parent[j]
    grot, gpos = sk.rest_globals()
    u = gpos[0, j] - gpos[0, p]
    u = u / np.linalg.norm(u)
    h = np.cross(u, np.asarray(front, float) * (1.0 if way == "front" else -1.0))
    h = h / np.linalg.norm(h)

    def at(a):
        rot = sk.rest_rot.copy()
        rot[j] = qmul(qinv(grot[0, p]), qmul(qaxis(h, a), grot[0, j]))
        return rot
    a = float(deg)
    for _ in range(4):          # (a hinge a little off the bone's own frame reads a little less)
        a += deg - bend(sk, at(a), bone)
    return at(a)


def corrective(P, W, sk: Skeleton, front=(0, 0, 1.0)):
    """Her corrective shapes as moves of her points at rest: {name: [V, 3]}.
    P [V, 3] her rest points, W [V, J] their weights (the helpers' split in,
    columns by sk's bones), both in sk's space; `front` her front there (+Z
    in the game's, -Y in Blender's). Each shape is made where it is whole:
    the joint bent c["full"] degrees and her helpers driven as the game
    drives them; the move wanted there, posed, is carried back to rest
    through the inverse of each point's blended skin matrix, so skinned at
    that bend the shape is exactly that move, and at other bends it turns
    with the limb."""
    P = np.asarray(P, float)
    W = np.asarray(W, float)
    front = np.asarray(front, float)
    grot0, gpos0 = sk.rest_globals()
    rest_inv = np.linalg.inv(mats(grot0[0], gpos0[0]))
    out = {}
    for c in SPEC.get("correctives", []):
        if "amount" not in c:
            continue    # (authored by a post step on her body: elbow_psd_post)
        for s in "lr":
            name, bone = c["name"].replace("{s}", s), c["bone"].replace("{s}", s)
            if bone not in sk.index:
                continue
            j = sk.index[bone]
            p = sk.parent[j]
            kid = sk.index[MAIN_CHILD[bone.split("_")[0]] + "_" + s]
            rot = bent(sk, bone, c["full"], front, c.get("way", "front"))
            scale, shift = np.ones((len(sk.names), 3)), np.zeros((len(sk.names), 3))
            rot = drive(sk, rot, scale, shift)
            grot, gpos = sk.fk(rot[None])
            S = mats(grot[0], gpos[0], scale, shift) @ rest_inv
            # This limb's points round the joint (the bones each side of it,
            # their helpers, the one below): only they move.
            heads = (sk.names[p].split("_")[0], bone.split("_")[0], sk.names[kid].split("_")[0])
            cols = [k for k, n in enumerate(sk.names) if n.endswith("_" + s) and n.split("_")[0] in heads]
            limb = W[:, cols].sum(1)
            cand = np.nonzero((limb > 0.02) & (np.linalg.norm(P - gpos0[0, j], axis=1) < 0.15))[0]
            A = np.einsum("vk,kab->vab", W[cand], S)
            q = np.einsum("vab,vb->va", A[:, :3, :3], P[cand]) + A[:, :3, 3]
            cj = gpos[0, j]
            u = cj - gpos[0, p]
            u = u / np.linalg.norm(u)
            f = gpos[0, kid] - cj
            f = f / np.linalg.norm(f)
            lean = c.get("lean", 0.0)
            n = (1 - lean) * u - (1 + lean) * f
            n = n / np.linalg.norm(n)
            h = np.cross(u, f)
            h = h / np.linalg.norm(h)
            t = np.cross(n, h)
            rel = q - cj
            along = rel @ n
            off = np.linalg.norm(rel - along[:, None] * n, axis=1)
            ray = off < c["near"]
            tip = cj + n * (along[ray].max() if ray.any() else along.max())
            d = q - tip
            rh, rt, rn = c["radius"]
            r2 = (d @ h / rh) ** 2 + (d @ t / rt) ** 2 + (d @ n / rn) ** 2
            fall = np.clip(1.0 - r2, 0.0, 1.0) ** 3 * np.clip(limb[cand], 0.0, 1.0)
            mv = fall > 0
            delta = np.zeros_like(P)
            want = c["amount"] * fall[mv, None] * n[None, :]
            delta[cand[mv]] = np.linalg.solve(A[mv, :3, :3], want[..., None])[..., 0]
            out[name] = delta
    return out


def corrective_names():
    return [n for c in SPEC.get("correctives", []) for n in each(c["name"])]


if __name__ == "__main__":
    write_spec()
    print("wrote", SPEC_FILE)
