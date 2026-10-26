"""Her raised-arm shoulder join SCULPTED at the key poses, replacing the skinned surface there (Body 9, 24 Oct 2026).

Five rounds of small correctives on the skinned join (bumps, hollows, folds, the 8-weight helper rig, the reweight) left
every judge saying the raised arm looks PLUGGED IN: the deltoid a ball on the torso's corner with a notch under it,
the pec not tenting into the arm, the arm's underside one sausage into a pinched pit crease. The fault is big form, so
this pass doesn't nudge the skinned surface: at each key pose Godot dumped (tools/assets/shoulder_sculpt_poses.json)
her body is skinned with all 8 weights (NO shoulder shapes) and the arm-chest-shoulder region is RE-SOLVED as a new
surface in her chest's frame, then carried back to the bind shape through the inverse of each point's blended skin
matrix (pit_hollow_post's machinery), so at the key it lands exactly and between keys it rides with the skin.

The construction (per side, at each key; m in her rest unless said):
  region  within 0.10-0.135 of the shoulder joint (eased), the breast's core, the sternum side (x < 0.07-0.11) and
          the neck kept; plus (round 2) the BREAST PANEL: her front chest on that side from the sternum (and the other
          breast's inner edge) out to x 0.19-0.23, y 1.18-1.53; those and everything outside are the boundary, three
          rings of it held (tangent continuity)
  solve   least squares on the uniform Laplacian: each point's Laplacian made her REST one turned into the pose
          (min |L X - R dU|^2), so the skin keeps its own curvature and spacing but not the skinning's ball, notch,
          slot and crumples; the turn R is the skin's own (polar of the blended matrix) blended toward the humerus'
          turn on the cap and arm (arm-ness 0 at 0.08 medial of the joint plane, 1 at 0.04 down the arm), so the
          deltoid's mass moves with the arm instead of sitting on the torso's corner; on the breast none (her rest)
  flat    in the pit and the front crease (the under side about the humerus, and its front-under side out from
          0.035 medial of the joint plane, inside 0.115 of the joint) her rest curvature is dropped (the A-pose's
          closed pit valley isn't carried up): a thin-plate fill there; at the pit's core the spacing too
  lift    (round 2) the breast rises with the arm: its core (smoothed breast weight > 0.45) is her REST breast moved
          LIFT x (A - 70) / 80 up (along the chest wall: a quarter back, a fifth out toward the arm; 27 mm at A 150,
          ~13 at A 114), its upper pole drawn in FLAT (the pole flattens as the pec pulls it), held hard; the panel
          solved round it, so the breast keeps its round rest shape (never a disc) and the skin above and below it
          (and HerRaise's crumpled upper pole at A 150) is her rest skin stretched, never crumpled
  pull    the breast's upper-outer edge drawn along her skin toward the front fold's arm end (PULL), so the fold
          runs into the breast
  folds   anchors on the filled surface: the back fold (BACK, from the lat's edge to the arm's back-inner side), the
          pit pushed in as one elliptic dome along its own axis (DOME, 50 x 38 mm, long along the arm), the deltoid's
          front and middle heads one teardrop on the arm's top-outer side (DELT, peak ~0.04 down the humerus), the
          old soft front ridge (RIDGE, off by default since round 2: the lip replaces it); re-solved once
  relax   the pit's core relaxed (RELAX, 15 Laplacian passes): the fold's leftover nick under the arm's root
  detail  (round 2) offsets along the normal, eased: the PEC'S LOWER BORDER one rounded lip from the breast's
          upper-outer edge into the arm's front (LIP mm proud on the spine, falling 22 mm wide over the chest and
          9 mm into the pit: a ~15-20 mm edge radius), the BICEPS/TRICEPS GROOVE up the arm's inner face into the
          pit (GROOVE deep, 9 mm wide, 0.04-0.21 down the humerus), the DELTOID'S INSERTION a soft V on the arm's
          outer side closing ~45% down the humerus (INS proud inside the V)
  scale   the anatomy (folds, dome, delt, pull, details) eased in with A: 0 at A 60, whole from A 114
Round 3 (25 Oct): NORMALS: each slot's normal is now solved so Godot's blend (base x (1 - sum w) + sum w x the slots'
          unit normals, skinned by the blended matrix) gives the sculpt's own geometric normal at every key (eased to
          her stored normal over the region's edge); rounds 1-2 turned the SKINNED normal by the sculpt's turn, which
          carried the helper rig's skinning errors (60-90 degrees at the join's front-top, 160 where the skinned skin
          folds) into the light: the dark puckers Godot showed and Blender never did. SHRINK: the rest Laplacian's
          target scaled by the skinned pose's local shrink where the raise packs the skin. FAIR (last): every point
          that sits in from its 2 x 12 mm patch's quadric (her rest's residual left out) moved onto it, alternated
          with the untangle, fold-safe; what's left smoothed on the spot. The shoulder's top valley's floor lifted
          (VLIFT). The breast lift's curve 0/24.5/37.5 mm at A 70/115/150, graded to 0.38 of it at the core's foot
          (the fold under it rises ~9 mm, the nipple ~23 at A 114-117, ~35 at A 150), its side toward the pit drawn 6 mm
          toward the pit, the upper pole 5 mm in; the pec's lower border a round roll (9 mm, 16 mm over the chest,
          12 into the pit, whole from 20 mm off its chest end, fading to nothing at its arm end ~80 mm up the inner
          arm); the groove and the insertion V off (muscle tone is a detail normal map's job now).
Round 4 (25 Oct, the owner on round 3: "the indent arch from underarm to elbow far too exaggerated"; "the breast
          work wasn't great"): NO CUT: the solve's turned rest Laplacian (its turn only part of the humerus' within ~40 mm
          of the joint) thinned the arm's back-underside 9-15 mm there, so the underside line rose into the pit as an
          arch; every point on the arm side of the joint (not its deltoid top) is put back out to its skinned radius from
          the humerus wherever the sculpt took it inside (NOCUT); the flat sector and the pit core stop at the joint plane
          (ARMKEEP). The BREAST lift gentle and near-rigid: its core her rest breast translated whole along the lift
          (IMFR 1: the fold under it rises with it; no teardrop EDGE pull, no upper-pole FLAT), 0/14.5/24.5 mm at A
          70/115/150 (nipple ~13 at A 114-117, ~23 at A 150).
Round 5 (25 Oct, the judge on round 4: breast facets, the pinch where the arm lands on the breast, row 1's V):
          NORMALS: the target in the region is her STORED normal carried by the sculpt's own local turn (per-triangle
          polar rotations rest -> sculpt, area-weighted per point: _turned_stored), not the raw area-weighted geometric
          normal, whose facet noise lit the breasts in straight-edged facets; on the rigid breast core it is her stored
          normal, in the join the sculpt's normal without the noise (SCULPT_NGEO=1 gives round 4's). CLOSE: no fold in
          the join tighter than 12 mm at the overhead keys (a rolling ball's closing, _close; from A 80, whole at 105: at
          the lowered key it bent the underside's line), the shoulder's top with an 18 mm ball (the
          deltoid and the torso's cap met in a deep narrow fold: the V); DELT 15 mm (was 5: the deltoid's top fuller by
          the joint); NOCUT's ramp at the overhead keys -0.03..+0.07 down the humerus (ncT2; the lowered key keeps
          round 4's), so the underside tapers into the back fold. Row 1's V 16 -> 4 px (offline silhouette).
          NB round 4's "left cast cut" was prof4's frame flipping hand (its 'z > 0' rule at a near-horizontal e1): with
          a mirror-consistent frame the left cast's back-underside matches the right's.
Round 6 (25 Oct, the contact V where the arm's underside lands on the breast's upper-outer edge, rows 1, 3, 5): at the
          game cameras the V's apex is the pit's apex (her armpit pole, a 42-triangle fan with spokes to 35 mm, folded
          even at rest), and the breast's outline meets it because her lateral breast stands 15-20 mm out past the chest
          wall under the pit (an occlusion, ~13 cm in front of the arm's underside; no 3D fold to round). BIN: the
          breast's upper-outer side drawn in and down-medial (12 mm at its far edge, a smooth field from its centre,
          ~10 mm on its outline at the overhead keys, 3 at the lowered key; nipple rise -0.5 mm); DOMEX: the pit 9 mm
          deeper at the overhead keys (from A 80, whole at 105), its apex up into the arm. RSM (off): the turn field
          smoothed (it didn't take the side wall's streaks: those are the stretched rest shape's). Softens the V; a
          smaller dark notch remains.
Round 8 (25 Oct, on round 7's armpit topology; the owner: "do not narrow bust", a volume-kept draw-in and a slight
          push-together allowed): CLOSE's search solved exactly per ball (it stepped 0.5 mm: ~470 points a key took a
          random 0 / 0.5 mm) and a point no ball reaches takes its met neighbours' fill (it was pushed the whole 20 mm
          into the facing mass: the cleavage and the fold under the breast "closed" into fold-overs, ~280 folded faces
          for the untangle to smear; the sculpt moved up to 19 mm for a 1e-9 m change of its input, now 0); the join's
          zone off the breast's inner and lower sides. JOINT: the two-arm keys sculpted once for both sides and shared
          out across the sternum (MID), so Godot's sum of the two sides' slots is that one sculpt (rounds 2-7 moved the
          cleavage twice: the cast's fold-over). VKEEP: both breasts' closed volume never under the skinned key's (her
          Body 8's), this side's 1% over it: the draw-in's loss goes back on the breast's front and inner-lower side.
          IMFS: the move smoothed over the breast's lower rim. NTS: the normal's turn field smoothed 8 passes (the fold
          under the breast lit in a sawtooth of specks). CLEAR: the last faces folded past 90 degrees smoothed out (the
          shoulder's front-top, the nick in row 1's outline), bounded (CLEARMAX)
Round 9 (25 Oct): JCLOSE, a 24 mm ball's closing on the arm-breast junction pocket at the overhead keys.
Round 10 (25 Oct, the owner on round 9: "the breasts aren't doin great. if they didn't move at all would there be
          issues?"; at the raised keys they read squared and boxy: the draw-in took the outer edge in, the top-up went
          to the front and inner-lower side, heavy-bottomed under flat upper poles). Two breasts, SCULPT_BREAST:
          NATURAL (default): her rest breast carried up whole by the lift (round 8's nipple rise), NO draw-in (BIN 0),
          the volume top-up spread round the whole breast (VKEEP_ROUND), the pec's roll carried whole to its chest end
          and LIPEND onto the breast's upper-outer surface (roll and breast one convex form), the pit's extra depth
          (DOMEX) eased off its front quarter (DOME_FRONT), the move's smoothing under the breast carried out to its
          lateral border at the overhead keys (IMF_OUT, 4 passes more). STILL: the sculpt never touches the breasts
          (no lift, no draw-in, no top-up): both (smoothed breast weight >= STILL_T) ride the chest as the skin and the
          helpers (HerRaise) carry them, the join's move eased to nothing over STILL_R outside their border, her
          skinned normal on them. "r9" rebuilds round 9's breasts.
Round 11 (25 Oct, the owner on round 10's NATURAL cast: "what are those lumps", one each side where the arm's underside
          comes down onto the breast): the lumps were the PEC'S ROLL (LIP): its chest end stood 9 mm proud between the
          arm's underside and the breast's upper-outer side, a separate form in the front view (offline: LIP 0 alone
          takes both away; a roll tapered in from 20-40 mm off its chest end still bumps). NATURAL: LIPHI 0, the roll
          eased out over A 80-105 (the lowered key keeps round 10's, so row 3 is unchanged); the arm's underside runs
          into the breast's side in one curve. The serrated dark edge under the lifted breast (the cast, her left) was
          the crease's down-turned normals interpolated across her chest wall's long triangles under it, once the lift
          showed the crease (it is in the skinned crease too, smaller): IMFHS 8, the slots' normal target smoothed 8
          passes over the fold's band (S.fb: from the breast's rim under the nipple out to IMFHR past its border),
          one soft gradient. IMFH (the move made harmonic over that band) and IMFHN (her turned skinned normal there)
          are off: neither took the edge.
Round 12 (25 Oct, the owner: "fix the small step at the shoulder top in the overhead front"): the step was a crumple of
          10-26 flipped faces where the raised deltoid meets the trapezius' end, at every overhead key: the solve packs
          that skin into a crease and the 18 mm closing pushed the crease's floor out along each point's own normal, the
          moves crossed. From A 100 (the lowered key unchanged): that closing's ball CLOSERT_HI 24 mm along a direction
          field smoothed CLOSET_NSM 60 passes (parallel moves); STOP last: the faces still flipped on the shoulder top
          and 2 rings round them smoothed till none is left (moves <= STOP_MAX). Show 16 -> 6 flipped, cast 11/15 -> 6/8.
          STOP_KEEP: everything off the shoulder top kept exactly round 11's (round 11's sculpt made too, this one kept
          over the top's closing zone, eased): the cleanup loops stop on the whole region's fold count, so the top's
          fewer folds had changed the passes the arm-breast junction got (slots off the top now within 0.03 mm).
Keys and slots: the reaver_show key (right A 113.5, az 23) and the cast key (l A 117 az 70, r A 114 az 61) give the
A 117 slots: per point the abd117 and flex117 shapes solved so Play/ShoulderPsd's weights at each key give back that
key's sculpt exactly (the left's show key is the right's mirrored); the old overhead cast (l A 148, r A 155) gives
the 140 and 175 slots and their shrug twins (shared accessors); (round 2) the lowered swing (right A 75 az 40) gives
the LEVEL slot shoulder_lvl80 (ShoulderPsd: eased in from A 60, whole at 80, handed to the 117 slots by 117; its
share subtracted at the other keys first; whole at 80, not 90, so the key (0.85 there) isn't doubled at A 85-95,
where a level slot whole at 90 buckled the fold). So nothing up to A 60 (the Look and the idles move 0.00 mm).
pit_hollow_post's shapes in those slots are REPLACED (they were authored on the pre-reweight weights and are the old
nudges): run on its output, this pass takes them off first. The hero and NPCs carry no such shapes: untouched.

    SHOULDER_SCULPT=1 python tools/assets/shoulder_sculpt_post.py <src.glb> <dst.glb>
Run after shoulder_reweight_post.py (weights read and kept). Without SHOULDER_SCULPT=1 it copies unchanged.
"""
import json
import os
import shutil
import struct
import sys

import numpy as np
import scipy.sparse as sps
from scipy.sparse.csgraph import dijkstra
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "anim"))
from heroine_neck import _Gl  # noqa: E402
from worn_reaver_post import _sparse  # noqa: E402
import pit_hollow_post as ph  # noqa: E402
import shoulder_psd_post as sp  # noqa: E402

POSES = os.path.join(HERE, "shoulder_sculpt_poses.json")
_E = os.environ.get
# (round 10) the breasts' mode, SCULPT_BREAST: "natural" (her rest breast carried up whole by the pec, no draw-in, a
# volume top-up spread round the breast, the arm-breast pocket closed by the pec's roll), "still" (the sculpt never
# touches the breasts: they ride the chest as the skin and the helpers carry them, the join's move eased to nothing
# at their border) or "r9" (round 9's breasts: the draw-in and the front/inner-lower top-up)
BREAST = _E("SCULPT_BREAST", "natural")
assert BREAST in ("natural", "still", "r9"), BREAST


def _bm(env, r9, still, nat):
    """a knob whose default follows the breasts' mode (its own env var still wins)"""
    return float(_E(env, {"r9": r9, "still": still, "natural": nat}[BREAST]))


P = dict(ridge=float(_E("SCULPT_RIDGE", 0.0)), back=float(_E("SCULPT_BACK", 0.003)), dome=float(_E("SCULPT_DOME", 0.011)),
         dRu=0.05, dRv=0.038, pull=float(_E("SCULPT_PULL", 0.008)), delt=float(_E("SCULPT_DELT", 0.015)),
         cr=0.2, cd=0.02, cl=0.05, aw=(0.08, 0.12), sf=(0.15, 0.035),
         relax=float(_E("SCULPT_RELAX", 1.0)), relaxIt=int(_E("SCULPT_RELAX_IT", 15)),
         liftA3=(70.0, 115.0, 150.0), liftV3=(0.0, float(_E("SCULPT_LIFT115", 0.0145)), float(_E("SCULPT_LIFT150", 0.0245))),
         lback=0.25, llat=0.2, imfR=float(_E("SCULPT_IMFR", 1.0)), edge=float(_E("SCULPT_EDGE", 0.0)),
         flat=float(_E("SCULPT_FLAT", 0.0)), cb=30.0,
         lip=float(_E("SCULPT_LIP", 0.009)), lipF=0.016, lipP=0.012,
         groove=float(_E("SCULPT_GROOVE", 0.0)), grooveW=0.009, ins=float(_E("SCULPT_INS", 0.0)), insT=0.45,
         fair=float(_E("SCULPT_FAIR", 1.0)), fairIt=int(_E("SCULPT_FAIR_IT", 12)), kA=(60.0, 114.0),
         nRing=int(_E("SCULPT_NRING", 4)), shrink=float(_E("SCULPT_SHRINK", 1.0)), shrinkP=0.5,
         rmin=float(_E("SCULPT_RMIN", 0.015)), rminLow=float(_E("SCULPT_RMIN_LOW", 0.025)), dip=0.0003,
         vr=0.012, vNew=1 / 0.04, vIt=int(_E("SCULPT_VIT", 16)), vK=0, vFold=0, vDil=3, vProj=1,
         vLift=float(_E("SCULPT_VLIFT", 0.003)), vLr=0.02, uR=20, cyc=2, spot=int(_E("SCULPT_SPOT", 8)),
         armKeep=(float(_E("SCULPT_ARMKEEP0", -0.01)), float(_E("SCULPT_ARMKEEP_W", 0.04))),
         noCut=float(_E("SCULPT_NOCUT", 1.0)), ncT=(-0.01, 0.035), ncOut=0.6,
         nGeo=int(_E("SCULPT_NGEO", 0)),
         ncT2=(-0.03, 0.10), ncA=(80.0, 110.0),
         vfX=0.14, vfY=1.40, vfZ=-0.01, vfW=0.06,
         close=float(_E("SCULPT_CLOSE", 1.0)), closeR=float(_E("SCULPT_CLOSER", 0.012)),
         closeRt=float(_E("SCULPT_CLOSERT", 0.018)), closeMax=0.02, closeA=(80.0, 105.0),
         closeSm=int(_E("SCULPT_CLOSE_SM", 0)), closeNever=_E("SCULPT_CLOSE_NEVER", "rim"),
         closeX=(float(_E("SCULPT_CLOSE_X0", 0.09)), 0.03), closeY=(float(_E("SCULPT_CLOSE_Y0", 1.26)), 0.04),
         bin=_bm("SCULPT_BIN", 0.012, 0.0, 0.0), binS=(0.0, 0.08, 0.13), binSm=int(_E("SCULPT_BIN_SM", 15)), binA=(float(_E("SCULPT_BIN_A0", 100.0)), 105.0),
         domeX=float(_E("SCULPT_DOMEX", 0.009)), domeA=(80.0, 105.0), rsm=int(_E("SCULPT_RSM", 0)),
         joint=int(_E("SCULPT_JOINT", 1)), mid=float(_E("SCULPT_MID", 0.035)),
         vkeep=_bm("SCULPT_VKEEP", 1.0, 0.0, 1.0), vkeepM=float(_E("SCULPT_VKEEP_M", 0.01)),
         vkeepRound=_bm("SCULPT_VKEEP_ROUND", 0.0, 0.0, 1.0),
         clear=int(_E("SCULPT_CLEAR", 12)), clearMax=float(_E("SCULPT_CLEAR_MAX", 0.002)), imfS=int(_E("SCULPT_IMF_S", 12)), nTs=int(_E("SCULPT_NTS", 8)),
         jclose=float(_E("SCULPT_JCLOSE", 1.0)), jcloseR=float(_E("SCULPT_JCLOSER", 0.024)),
         jcloseMax=float(_E("SCULPT_JCLOSE_MAX", 0.012)), jcloseRad=float(_E("SCULPT_JCLOSE_RAD", 0.07)), jcloseA=(95.0, 105.0),
         still=_bm("SCULPT_STILL", 0.0, 1.0, 0.0), stillT=float(_E("SCULPT_STILL_T", 0.1)), stillR=float(_E("SCULPT_STILL_R", 0.02)),
         domeF=_bm("SCULPT_DOME_FRONT", 0.0, 0.0, 1.0), imfOut=_bm("SCULPT_IMF_OUT", 0.0, 0.0, 1.0),
         lipEnd=_bm("SCULPT_LIP_END", 0.0, 0.0, 0.035),
         lipC0=_bm("SCULPT_LIP_C0", 0.0, 0.0, 0.0), lipC=_bm("SCULPT_LIP_C", 0.02, 0.02, 0.02),
         lipFo=_bm("SCULPT_LIP_FO", 0.4, 0.4, 0.4), lipHi=_bm("SCULPT_LIP_HI", 1.0, 1.0, 0.0), lipHiA=(80.0, 105.0),
         imfH=_bm("SCULPT_IMF_H", 0.0, 0.0, 0.0), imfHR=float(_E("SCULPT_IMF_HR", 0.025)),
         imfHIn=float(_E("SCULPT_IMF_HIN", 0.3)), imfHY=float(_E("SCULPT_IMF_HY", 0.01)), imfHA=(75.0, 95.0),
         imfHN=_bm("SCULPT_IMF_HN", 0.0, 0.0, 0.0), imfHS=_bm("SCULPT_IMF_HS", 0.0, 0.0, 8.0),
         stop=_bm("SCULPT_STOP", 0.0, 0.0, 1.0), stopF=float(_E("SCULPT_STOP_F", 0.0005)),
         stopKeep=int(_E("SCULPT_STOP_KEEP", 1)), stopD=int(_E("SCULPT_STOP_D", 2)), stopIt=int(_E("SCULPT_STOP_IT", 40)),
         stopMax=float(_E("SCULPT_STOP_MAX", 0.010)), stopA=(95.0, 105.0),
         closeRtHi=float(_E("SCULPT_CLOSERT_HI", 0.024)), closeTNsm=int(_E("SCULPT_CLOSET_NSM", 60)))
SLOTS117 = ("shoulder_abd117", "shoulder_flex117")
SLOTS150 = ("shoulder_abd140", "shoulder_flex140", "shoulder_up175", "shoulder_abd140s", "shoulder_flex140s", "shoulder_up175s")
LVL = "shoulder_lvl80"
KEYS = (("show", "r"), ("cast", "l"), ("cast", "r"), ("cast150", "l"), ("cast150", "r"), ("low", "r"))


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _ramp(x, a, c):
    return float(np.clip((x - a) / (c - a), 0, 1))


def _unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _polar(Bm):
    U_, _, Vt = np.linalg.svd(Bm)
    R = U_ @ Vt
    neg = np.linalg.det(R) < 0
    if neg.any():
        U_[neg, :, 2] *= -1
        R[neg] = U_[neg] @ Vt[neg]
    return R


class Her:
    """the welded body (pit_hollow_post.Body), its uniform Laplacian, rest Laplacian coordinates, edge graph"""

    def __init__(s, G):
        b = s.b = ph.Body(G)
        n = len(b.U)
        s.L = (sps.diags(1.0 / b.deg) @ b.A - sps.identity(n)).tocsr()
        s.dU = s.L @ b.U
        s.M0 = np.linalg.inv(b.ibm)
        s.NU = ph.vn(b.U, b.F)
        E = np.unique(np.sort(np.r_[b.F[:, [0, 1]], b.F[:, [1, 2]], b.F[:, [2, 0]]], axis=1), axis=0)
        el = np.linalg.norm(b.U[E[:, 0]] - b.U[E[:, 1]], axis=1)
        s.GR = sps.coo_matrix((np.r_[el, el], (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()
        # (round 3) her stored normals (the primitives', welded: what Godot skins), for the normal targets
        g = G.g
        mesh = g["meshes"][[nd for nd in g["nodes"] if nd.get("name") == "Heroine"][0]["mesh"]]
        Ns, o = np.zeros((n, 3)), 0
        for p in mesh["primitives"]:
            c = g["accessors"][p["attributes"]["POSITION"]]["count"]
            Ns[b.wid[o:o + c]] = G.get(p["attributes"]["NORMAL"])
            o += c
        s.Ns = _unit(Ns)
        _NB["U"] = b.U

    def rings(s, m, k):
        out = m.copy()
        for _ in range(k):
            out = out | (s.b.A @ out.astype(float) > 0)
        return out

    def smooth(s, f, k):
        for _ in range(k):
            f = 0.5 * f + 0.5 * (s.b.A @ f) / (s.b.deg if f.ndim == 1 else s.b.deg[:, None])
        return f

    def path(s, a, c):
        _, pred = dijkstra(s.GR, indices=a, return_predecessors=True)
        p = [c]
        while p[-1] != a:
            p.append(pred[p[-1]])
        return np.array(p[::-1])


class Side:
    """one side's rest fields: the region, the flat sector, arm-ness, the fold anchors and spines, the pit's apex,
    the breast panel and core, the arm's rest frame"""

    def __init__(s, H, side, p=P):
        b, U = H.b, H.b.U
        sg = 1 if side == "l" else -1
        J0 = H.M0[b.I["upperarm_" + side]][:3, 3]
        h0 = _unit(H.M0[b.I["lowerarm_" + side]][:3, 3] - J0)
        v = U - J0
        t0 = v @ h0
        rj = np.linalg.norm(v, axis=1)
        s.aw = b.arm_w(side)
        s.bw = b.Wd[:, b.I["breast_" + side]]
        x = U[:, 0] * sg
        up = _unit(np.array([0, 1.0, 0]) - h0[1] * h0)
        fr = _unit(np.array([0, 0, 1.0]) - h0[2] * h0 - (np.array([0, 0, 1.0]) @ up) * up)
        c = np.cross(h0, fr)
        med = c if c[0] * sg < 0 else -c
        rr = v - t0[:, None] * h0
        rn = np.maximum(np.linalg.norm(rr, axis=1), 1e-9)
        cosu, cosf = (rr @ up) / rn, (rr @ fr) / rn
        phi = _ss((0.135 - rj) / 0.035) * (1 - _ss((s.bw - 0.35) / 0.3)) * _ss((x - 0.07) / 0.04)
        phi *= 1 - _ss((U[:, 1] - 1.53) / 0.03) * _ss((0.13 - x) / 0.04)
        s.phi = phi * (x > 0.02)
        sect = np.maximum(_ss((-0.1 - cosu) / 0.5),
                          _ss((p["sf"][0] - cosu) / 0.35) * _ss((cosf - 0.15) / 0.4) * _ss((t0 + p["sf"][1]) / 0.03))
        # (round 4) the arm's own underside keeps its curvature: the flat sector and the pit core stop at the joint
        # plane (fading out over armKeep), so the triceps' round cross-section isn't thin-plated flat (rounds 1-3 cut
        # the arm's back-underside 9-15 mm in within 40 mm of the joint: the owner's "indent arch" from pit to elbow)
        keep = 1 - _ss((t0 - p["armKeep"][0]) / p["armKeep"][1]) if p["armKeep"][1] > 0 else 1.0
        s.kap = 1 - sect * _ss((0.115 - rj) / 0.035) * (1 - _ss((t0 - 0.06) / 0.05)) * keep
        s.arm = _ss((t0 + p["aw"][0]) / p["aw"][1])
        s.core = _ss((-0.3 - cosu) / 0.4) * _ss((0.09 - rj) / 0.03) * keep

        def arm_pt(t, d):
            i = np.nonzero((s.aw > 0.8) & (np.abs(t0 - t) < 0.006))[0]
            return int(i[np.argmax(H.NU[i] @ d)])
        s.a_fa = arm_pt(0.095, _unit(0.75 * fr + 0.66 * med))
        s.a_ba = arm_pt(0.090, _unit(-0.75 * fr + 0.66 * med))
        Bm = s.bw > 0.3
        Bc = (U[Bm] * s.bw[Bm, None]).sum(0) / s.bw[Bm].sum()
        # (round 2: the fold's chest end where the breast's upper-outer edge meets her chest wall, ~45 mm over the
        # nipple; round 1's was on the breast's upper pole, so its fold crossed the breast)
        i = np.nonzero((s.bw > 0.06) & (s.bw < 0.2) & (U[:, 2] > 0.05) & (U[:, 1] > 1.36))[0]
        s.a_fc = int(i[np.argmax(U[i] @ np.array([0.9 * sg, 0.44, 0.0]))])
        d = np.linalg.norm(U - np.array([0.125 * sg, 1.31, -0.085]), axis=1)
        s.a_bc = int(np.argmin(np.where(s.aw < 0.2, d, 9)))
        s.faf, s.baf = H.path(s.a_fc, s.a_fa), H.path(s.a_bc, s.a_ba)
        s.apex = ph.apex(b, U, side)
        # the breast panel (her front chest this side; the sternum and the other breast's inner edge free too, its
        # core held), the breast's core and its nipple
        bo = b.Wd[:, b.I["breast_" + ("r" if side == "l" else "l")]]
        y, z = U[:, 1], U[:, 2]
        s.phib = (_ss((x + 0.03) / 0.04) * (1 - _ss((bo - 0.15) / 0.2)) * _ss((y - 1.18) / 0.06)
                  * (1 - _ss((y - 1.50) / 0.03)) * _ss(z / 0.04) * (1 - _ss((x - 0.19) / 0.04)))
        # and her side under the pit (the lat's front edge, the serratus: the skinning's streaks there)
        side_ = (_ss((x - 0.11) / 0.03) * (1 - _ss((x - 0.24) / 0.03)) * _ss((y - 1.20) / 0.05)
                 * (1 - _ss((y - 1.42) / 0.04)) * _ss((z + 0.10) / 0.03) * (s.aw < 0.3))
        s.phib = np.maximum(s.phib, side_)
        s.bsm = H.smooth(s.bw, 6)
        s.kb = _ss((s.bsm - 0.2) / 0.3)
        s.bcore = np.nonzero(s.bsm > 0.45)[0]
        s.bcw = _ss((s.bsm[s.bcore] - 0.45) / 0.15)
        i = np.nonzero(s.bw > 0.5)[0]
        s.nip = int(i[np.argmax(U[i, 2])])
        # (round 10) STILL: both breasts (smoothed breast weight >= STILLT) kept as the skin carries them; the join's
        # move eased to nothing at their border (over STILLR along her skin outside it)
        s.keepB = np.zeros(len(U))
        if p.get("still", 0) > 0:
            bb = np.maximum(s.bsm, H.smooth(bo, 6))
            dg = dijkstra(H.GR, indices=np.nonzero(bb >= p["stillT"])[0], min_only=True, limit=3 * p["stillR"])
            s.keepB = 1 - _ss(np.where(np.isfinite(dg), dg, 1.0) / p["stillR"])
        # (round 11) IMFH: the fold under the breast, the band the move is made harmonic over: her skin under the
        # nipple's height (less IMFHY) from the breast's rim (smoothed breast weight under IMFHIN, not its core) out to
        # IMFHR past its border (smoothed weight 0.03) along her skin, this side
        s.fb = np.zeros(len(U), bool)
        s.fbE = np.zeros(len(U))
        if p.get("imfH", 0) > 0 or p.get("imfHN", 0) > 0 or p.get("imfHS", 0) > 0:
            dg = dijkstra(H.GR, indices=np.nonzero(s.bsm >= 0.03)[0], min_only=True, limit=2 * p["imfHR"])
            dg = np.where(np.isfinite(dg), dg, 1.0)
            s.fb = (s.bsm < p["imfHIn"]) & (dg <= p["imfHR"]) & (U[:, 1] < U[s.nip, 1] - p["imfHY"]) & (x > 0.005)
            s.fbE = np.clip(H.smooth(s.fb.astype(float), 3) * 1.5, 0, 1)
        # the arm's rest frame square to the humerus: out (the deltoid's side) and front
        lat0 = np.array([sg * 1.0, 0, 0])
        s.lat0 = _unit(lat0 - (lat0 @ h0) * h0)
        f0 = np.array([0, 0, 1.0])
        s.fr0 = _unit(f0 - (f0 @ h0) * h0 - (f0 @ s.lat0) * s.lat0)
        # (round 8) her breast's region for its volume (smoothed breast weight > 0.02 on this side; closed by the fan
        # from its border's centre, so a slide along her chest keeps it) and where a volume top-up goes: the breast's
        # front and inner-lower side (not the upper-outer side the draw-in takes in): a fuller, slightly pushed-together
        # breast, the owner's allowance
        # (and the same for her other breast, whose inner edge this side's breast panel reaches: 0.15% over it)
        s.vb = []
        for sgv, bwv in ((sg, s.bw), (-sg, bo)):
            bsv = H.smooth(bwv, 6)
            m = (bsv > 0.02) & (U[:, 0] * sgv > 0.005)
            Fr = b.F[m[b.F].all(1)]
            E = np.sort(np.r_[Fr[:, [0, 1]], Fr[:, [1, 2]], Fr[:, [2, 0]]], 1)
            Eu, cnt = np.unique(E, axis=0, return_counts=True)
            eo = _unit(np.array([sgv * 1.0, 0.8, -0.3]))
            Bmv = bwv > 0.3
            so = (U - (U[Bmv] * bwv[Bmv, None]).sum(0) / bwv[Bmv].sum()) @ eo
            vw = H.smooth(_ss((bsv - 0.25) / 0.35) * _ss((H.NU[:, 2] + 0.2) / 0.6) * (1 - 0.8 * _ss((so - 0.01) / 0.06)), 4)
            if p.get("vkeepRound", 0) > 0:
                # (round 10) the top-up spread round the whole breast (its core most, nothing at its border): fuller
                # and still round (round 8's front and inner-lower top-up made them heavy-bottomed and boxy)
                vw = H.smooth(_ss((bsv - 0.1) / 0.5), 4)
            s.vb.append(((Fr, np.unique(Eu[cnt == 1].ravel())), vw))


def _solve(H, Pin, phi, delta, anchors=None, c_core=1e-7, c_fix=1e2):
    """min sum |(L X)_i - delta_i|^2 + c_i |X_i - Pin_i|^2 (+ anchors' |X_i - target_i|^2 w) over phi's points and
    three rings beyond; c from phi (held where phi is 0)"""
    act = H.rings(phi > 1e-4, 3)
    ia, io = np.nonzero(act)[0], np.nonzero(~act)[0]
    ir = np.nonzero(H.rings(act, 1))[0]
    Lr = H.L[ir]
    LA, LO = Lr[:, ia], Lr[:, io]
    c = c_core + c_fix * (1 - phi[ia]) ** 2
    cw, tgt = np.zeros(len(Pin)), Pin.copy()
    for idx, T, w in anchors or []:
        cw[idx] += w
        tgt[idx] = T
    lu = splu((LA.T @ LA + sps.diags(c + cw[ia])).tocsc())
    rhs = LA.T @ (delta[ir] - LO @ Pin[io]) + c[:, None] * Pin[ia] + cw[ia, None] * tgt[ia]
    X = Pin.copy()
    X[ia] = np.stack([lu.solve(rhs[:, k]) for k in range(3)], 1)
    return X


def _angles(H, d, side):
    """bone globals [J, 4, 4] from a dump entry and the side's (A, azimuth)"""
    b = H.b
    Mg = np.stack([np.eye(4)] * len(b.names))
    for i, n in enumerate(b.names):
        v = d[n]
        Mg[i, :3, 0], Mg[i, :3, 1], Mg[i, :3, 2], Mg[i, :3, 3] = v[0:3], v[3:6], v[6:9], v[9:12]
    A, az = sp.arm_angles(Mg, b.I, side)
    return Mg, A, az


def _folds(H, X, live):
    """faces more than ~78 degrees off the surface smoothed (15 passes): folded over or about to"""
    F = H.b.F
    Xs = H.smooth(X, 15)
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-15)
    return np.nonzero(((q * ph.vn(Xs, F)[F].mean(1)).sum(1) < 0.2) & live[F].all(1))[0]


_NB = {}


def _ring_nb(A, idx, k=4, K=48):
    """[len(idx), K] neighbour ids within k rings along the mesh (padded with the point itself), cached"""
    key = (id(A), k, K, len(idx), int(idx[:50].sum()))
    if key not in _NB:
        R = sps.identity(A.shape[0], format="csr") + A
        Rk = R[idx]
        for _ in range(k - 1):
            Rk = Rk @ R
        Rk = Rk.tocsr()
        out = np.repeat(idx[:, None], K, 1)
        U = _NB.get("U")
        for j in range(len(idx)):
            c = Rk.indices[Rk.indptr[j]:Rk.indptr[j + 1]]
            c = c[c != idx[j]]
            if U is not None and len(c) > K:
                c = c[np.argsort(np.linalg.norm(U[c] - U[idx[j]], axis=1))]
            out[j, :min(len(c), K)] = c[:K]
        _NB[key] = out
    return _NB[key]


def quad(X, N, idx, r=0.010, A=None):
    """per point of idx: a quadric height field (in the frame of the normal N) fitted to its neighbours within r (a
    2r patch, itself left out; along the mesh when A is given, so a deep valley's far side never counts): (c0 the
    fit's height over the point, + = the point sits IN: a dip; the fit's largest concave curvature 1/m, + = a valley)"""
    if A is None:
        dist, nb = cKDTree(X).query(X[idx], k=24)
    else:
        nb = _ring_nb(A, idx)
        dist = np.linalg.norm(X[nb] - X[idx][:, None], axis=2)
    ok = (dist > 1e-9) & (dist < 1.6 * r)
    n = N[idx]
    e1 = _unit(np.cross(n, np.where(np.abs(n[:, :1]) < 0.9, np.array([[1.0, 0, 0]]), np.array([[0, 1.0, 0]]))))
    e2 = np.cross(n, e1)
    d = X[nb] - X[idx][:, None]
    a, c, h = (d * e1[:, None]).sum(2), (d * e2[:, None]).sum(2), (d * n[:, None]).sum(2)
    w = np.where(ok, np.exp(-(dist / (0.7 * r)) ** 2), 0)
    Am = np.stack([np.ones_like(a), a, c, a * a, a * c, c * c], 2)
    M = np.einsum("nk,nki,nkj->nij", w, Am, Am) + np.diag([1, r ** 2, r ** 2, r ** 4, r ** 4, r ** 4]) * (1e-4 * (w.sum(1) + 1e-3))[:, None, None]
    co = np.linalg.solve(M, np.einsum("nk,nki,nk->ni", w, Am, h)[:, :, None])[:, :, 0]
    Hs = np.stack([np.stack([2 * co[:, 3], co[:, 4]], 1), np.stack([co[:, 4], 2 * co[:, 5]], 1)], 1)
    return co[:, 0], np.linalg.eigvalsh(Hs)[:, 1]


def _fair_patches(H, X, phi, S, rmin, p):
    """(X, 'rounds: points flagged per round') every flagged point's patch (dilated 2 rings: >= 20 mm across) re-solved
    to the curvature round it: its Laplacian made the harmonic fill of the Laplacian round the patch, the rest held
    (so a dip, a fold-over or a V takes the bend of the skin about it and joins it smoothly)"""
    b = H.b
    live = (phi > 0.05) & (S.bsm < 0.45)
    idx = np.nonzero(live)[0]
    c0u, ku = quad(b.U, H.NU, idx, p["vr"], b.A)
    log = []
    for _ in range(p["vIt"]):
        N = ph.vn(X, b.F)
        c0, k = quad(X, N, idx, p["vr"], b.A)
        bad = np.zeros(len(X), bool)
        val = np.zeros(len(X), bool)
        val[idx[(k > 1 / rmin) & (k - np.maximum(ku, 0) > p["vNew"])]] = p["vK"] > 0
        bad[idx[c0 - np.maximum(c0u, 0) > p["dip"]]] = True
        if p["vFold"]:
            bad[b.F[_folds(H, X, live)].ravel()] = True
        log.append("%d/%d" % (int(val.sum()), int(bad.sum())))
        if not (bad.any() or val.any()):
            break
        if val.any():
            # a valley tighter than rmin opened: its strip (a ring round it, eased) relaxed toward its neighbours'
            # mean (the floor rises, the sides barely move)
            wv = np.clip(H.smooth(H.rings(val, 1).astype(float), 2) * 1.5, 0, 1) * live
            for _ in range(5):
                X = X + 0.5 * wv[:, None] * b.lap(X)
            N = ph.vn(X, b.F)
            c0, _ = quad(X, N, idx, p["vr"], b.A)
            bad[:] = False
            bad[idx[c0 - np.maximum(c0u, 0) > p["dip"]]] = True
        if p["vProj"] and bad.any():
            # each flagged point (and a ring round it) moved along its normal onto its patch's quadric, by its excess
            # over her rest's own residual
            ex = np.zeros(len(X))
            ex[idx] = c0 - c0u
            m = H.rings(bad, 1) & live
            fv = np.zeros(len(X), bool)
            fv[b.F[_folds(H, X, live)].ravel()] = True
            m &= ~H.rings(fv, 1)                              # (a tipped face's normals are no guide)
            Xn = X + (0.8 * ex * m)[:, None] * N
            # a move that tips a face is taken back
            tip = np.zeros(len(X), bool)
            tip[b.F[_folds(H, Xn, live)].ravel()] = True
            tip &= ~fv
            X = np.where(H.rings(tip, 1)[:, None], X, Xn)
            continue
        m = H.rings(bad, p["vDil"]) & live
        mi, oi = np.nonzero(m)[0], np.nonzero(~m)[0]
        dc = H.L @ X
        # the Laplacian round the patch carried in harmonically
        Lmm = H.L[mi][:, mi].tocsc()
        di = dc.copy()
        lu = splu(Lmm)
        rhs = -(H.L[mi][:, oi] @ dc[oi])
        di[mi] = np.stack([lu.solve(rhs[:, j]) for j in range(3)], 1)
        # X in the patch to it (rows: the patch and a ring round it), the rest held
        ri = np.nonzero(H.rings(m, 1))[0]
        Lr = H.L[ri]
        A_ = Lr[:, mi]
        lu = splu((A_.T @ A_ + sps.identity(len(mi)) * 1e-9).tocsc())
        rhs = A_.T @ (di[ri] - Lr[:, oi] @ X[oi])
        X = X.copy()
        X[mi] = np.stack([lu.solve(rhs[:, j]) for j in range(3)], 1)
    return X, "->".join(map(str, log))


def _close(H, X, zw, R, smax=0.02, step=0.0005, sm=0, never="rim", nsm=4):
    """(X, fill) (round 5) every fold of the zone tighter than R ROUNDED by a rolling ball of radius R (a morphological
    closing): the balls that touch the surface from outside without cutting it (centres X + R N from the zone and six
    rings round it, kept where no body point is nearer than 0.9 R) make an envelope; each zone point is moved out along
    its smoothed-surface normal till it meets it (a convex or open point meets its own ball at once: 0), at most smax,
    eased by zw (0-1). So a pinch or a V between two masses becomes a fold of radius R, and nothing wider moves"""
    F = H.b.F
    Nn = ph.vn(X, F)
    Ns = ph.vn(H.smooth(X, nsm), F)
    cand = np.nonzero(H.rings(zw > 0.01, 6))[0]
    O = X[cand] + R * Nn[cand]
    dmin, _ = cKDTree(X).query(O)
    O = O[dmin > 0.9 * R]
    if not len(O):
        return X, np.zeros(len(X))
    to = cKDTree(O)
    idx = np.nonzero(zw > 0.01)[0]
    s = np.full(len(idx), np.nan)
    if never == "cap":
        for sv in np.arange(0, smax + 1e-9, step):
            d, _ = to.query(X[idx] + sv * Ns[idx])
            s[np.isnan(s) & (d <= R)] = sv
    else:
        # (round 8) the move to the envelope solved exactly (the ray's first entry into each of the 24 nearest balls,
        # the least of them), not stepped 0.5 mm at a time: a convex point sat on its own ball's sphere (d == R) and
        # rounding put it at 0 or at the next step, so ~470 points per key took a random 0 / 0.5 mm, and the joins'
        # closing amplified it to mm (surface noise)
        Xi, ni = X[idx], Ns[idx]
        kk = min(24, len(O))
        _, jj = to.query(Xi, k=kk, distance_upper_bound=R + smax + 1e-6)
        jj = jj.reshape(len(idx), kk)
        okj = jj < len(O)
        Oj = O[np.where(okj, jj, 0)]
        q = Xi[:, None] - Oj
        bq = (q * ni[:, None]).sum(2)
        cq = (q * q).sum(2) - R * R
        disc = bq * bq - cq
        sv = np.where(cq <= R * R * 1e-9, 0.0, -bq - np.sqrt(np.maximum(disc, 0)))
        hit = okj & ((cq <= R * R * 1e-9) | ((disc >= 0) & (sv >= 0))) & (sv <= smax)
        sv = np.where(hit, np.maximum(sv, 0), np.inf).min(1)
        s = np.where(np.isfinite(sv), sv, np.nan)
    if never == "cap":
        s = np.where(np.isnan(s), smax, s)
    fill = np.zeros(len(X))
    fill[idx] = s
    if never != "cap":
        # (round 8) a point that never meets the envelope within smax has had every ball near it rejected: two masses
        # facing closer than 0.9 R (the breasts at the cleavage, the arm's underside on her side). Rounds 5-7 pushed it
        # the whole smax along its normal INTO the facing mass (~30 points per overhead key, ~280 faces folded for the
        # untangle to smear: the cast's cleavage fold-over, and a result that moved up to 19 mm for a 1e-9 m change of
        # its input). Now it takes the most its met neighbours (3 rings) were filled (a deep V's floor filled like its
        # rim), else nothing
        miss = np.zeros(len(X), bool)
        miss[idx] = np.isnan(fill[idx])
        fill[miss] = -1.0
        Am = H.b.A.tocsr()
        for _ in range(3):
            g = np.asarray(Am.multiply(np.maximum(fill, 0)[None, :]).max(axis=1).todense()).ravel()
            got = miss & (fill < 0) & (g > 0)
            fill[got] = g[got]
        fill[fill < 0] = 0.0
        fill = np.minimum(fill, smax)
    fill = H.smooth(np.minimum(fill, H.smooth(fill, 1) * 1.5), sm) * zw if sm else np.minimum(fill, H.smooth(fill, 1) * 1.5) * zw
    return X + fill[:, None] * Ns, fill


def _flips(F, X):
    """faces whose normal turns past 90 degrees from a neighbour's across an edge (folded over)"""
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-15)
    E = np.c_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]].reshape(-1, 2)
    fid = np.repeat(np.arange(len(F)), 3)
    k = np.sort(E, 1)
    k = k[:, 0].astype(np.int64) * (F.max() + 1) + k[:, 1]
    o = np.argsort(k, kind="stable")
    ks = k[o]
    i = np.nonzero(ks[1:] == ks[:-1])[0]
    f1, f2 = fid[o[i]], fid[o[i + 1]]
    bad = (q[f1] * q[f2]).sum(1) < 0
    m = np.zeros(len(F), bool)
    m[f1[bad]] = m[f2[bad]] = True
    return m


def _untangle(H, X, live, rounds=8, its=6):
    b = H.b
    n0 = None
    for _ in range(rounds):
        fl = _folds(H, X, live)
        n0 = len(fl) if n0 is None else n0
        if not len(fl):
            break
        m = np.zeros(len(X), bool)
        m[b.F[fl].ravel()] = True
        m = H.rings(m, 2) & live
        for _ in range(its):
            X = X + 0.5 * m[:, None] * b.lap(X)
            X = X - 0.53 * m[:, None] * b.lap(X)
    return X, (n0, len(_folds(H, X, live)))


def author(H, S, d, side, p=P, info=None, X0in=None, **_):
    """(D the posed move in her chest frame, B blended chest-frame matrices) for one side at one key; (round 8) X0in:
    the surface it starts from (the other side's sculpt at a two-arm key) instead of the skinned pose"""
    b = H.b
    F, U = b.F, b.U
    M, T, X0, B = b.pose(d)
    if X0in is not None:
        X0 = X0in
    _, A, _ = _angles(H, d, side)
    kA = _ramp(A, *p["kA"])
    # (round 3) the lift's curve: 0 at A 70, LIFT3[1] at 115, LIFT3[2] at 150 (the nipple rises ~23 mm at the A 114-117
    # keys, ~35 at the old cast's A 148-155)
    Lc = float(np.interp(A, p["liftA3"], p["liftV3"]))
    kL = Lc / p["liftV3"][-1]
    sg = 1 if side == "l" else -1
    J = (T @ M["upperarm_" + side])[:3, 3]
    Eb = (T @ M["lowerarm_" + side])[:3, 3]
    h = _unit(Eb - J)
    Lh = np.linalg.norm(Eb - J)
    Sa = T @ M["upperarm_" + side] @ b.ibm[b.I["upperarm_" + side]]
    Ra = _polar(Sa[None, :3, :3])[0]
    ra = _polar((1 - S.arm)[:, None, None] * np.eye(3)[None] + S.arm[:, None, None] * Ra[None])
    w = S.phi[:, None, None]
    R = _polar((1 - w) * _polar(B[:, :3, :3]) + w * ra)
    kb = S.kb[:, None, None]
    R = _polar((1 - kb) * R + kb * np.eye(3)[None])
    if p.get("rsm", 0) > 0:
        # (round 6) the turn field smoothed over her skin (RSM passes, re-made a turn): the skinned blend's turn varies
        # point to point on her side under the pit (the arm's and helpers' weights), and the turned rest Laplacian
        # carried that noise into the solve as vertical streaks on the side wall and lumps in the pit
        R = _polar(H.smooth(R.reshape(-1, 9), int(p["rsm"])).reshape(-1, 3, 3))
    dR = np.einsum("nab,nb->na", R, H.dU)
    phi = np.maximum(S.phi, S.phib)
    still = p.get("still", 0) > 0
    if still:
        phi = phi * (1 - S.keepB)                             # (round 10) the breasts held as skinned
    if p["shrink"] > 0:
        # (round 3) where the raise packs the skin (the shoulder's top between the neck and the raised deltoid, the
        # join's front-top under the acromion) the rest Laplacian asked for more skin than there is room for, and the
        # solve buckled it (3-7 mm dips there in Godot and the "V with a tick"): its target scaled by the local
        # shrink of the skinned pose (one-ring area, posed over rest, square-rooted), never grown
        def va(Y):
            q = 0.5 * np.linalg.norm(np.cross(Y[F[:, 1]] - Y[F[:, 0]], Y[F[:, 2]] - Y[F[:, 0]]), axis=1)
            a = np.zeros(len(Y))
            for k in range(3):
                np.add.at(a, F[:, k], q)
            return a
        sh = np.clip(H.smooth(va(X0) / np.maximum(va(U), 1e-12), 4) ** p["shrinkP"], 0.3, 1.0)
        dR = dR * (1 - p["shrink"] * phi * (1 - sh))[:, None]
    out = phi < 1e-4
    # the breast lifted: its core her rest breast moved up the chest wall (a little out toward the arm), the upper
    # pole drawn in; held hard
    ldir = _unit(np.array([sg * p["llat"], 1.0, -p["lback"]]))
    # (round 3) graded: whole from the nipple up, IMFR of it at the core's foot, so the fold under the breast rises
    # ~9 mm while the nipple rises ~23 and the lower pole lengthens round; the side toward the pit drawn EDGE along
    # the chest toward the pit (the teardrop toward the arm); the upper pole drawn FLAT into the pec
    # (both gradings smooth fields over her skin, eased: a clipped ramp creased the breast along its kink lines)
    yb, yn = U[S.bcore, 1], U[S.nip, 1]
    y0 = yb.min()
    dpit = _unit((U[S.apex] - U[S.nip]) * np.array([1.0, 1.0, 0.3]))
    wl = H.smooth(p["imfR"] + (1 - p["imfR"]) * _ss((U[:, 1] - y0) / max(yn + 0.03 - y0, 1e-6)), 8)[S.bcore]
    uo = H.smooth(_ss(((U - U[S.nip]) @ dpit + 0.03) / 0.09), 8)[S.bcore]
    tc = (U[S.bcore] + (Lc * wl)[:, None] * ldir + (p["edge"] * kL * uo)[:, None] * dpit
          - (p["flat"] * kL * _ss((yb - yn) / 0.05))[:, None] * H.NU[S.bcore])
    abr = [] if still else [(S.bcore, tc, p["cb"] * S.bcw)]

    def fill(Pin, anchors, its=2):
        X = Pin.copy()
        for _ in range(its):
            N = ph.vn(X, F)
            dn = (dR * N).sum(1, keepdims=True) * N
            delta = (dR - (1 - S.kap[:, None]) * dn) * (1 - S.core[:, None])
            delta[out] = (H.L @ Pin)[out]
            X = _solve(H, Pin, phi, delta, anchors)
        return X
    Xf = fill(X0, abr)
    Nf = ph.vn(Xf, F)
    anc = list(abr)
    # the breast's upper-outer edge drawn along her skin toward the front fold's arm end
    m = S.bw > 0.3
    Bc = (Xf[m] * S.bw[m, None]).sum(0) / S.bw[m].sum()
    du = _unit(Xf[S.a_fa] - Bc)
    rb = np.linalg.norm(Xf - Bc, axis=1)
    k = H.smooth(H.smooth(S.bw, 20) * _ss(((Xf - Bc) @ du) / 0.08) * _ss((rb - 0.03) / 0.04), 10)
    k = k / max(k.max(), 1e-9)
    ip = np.nonzero((k > 0.02) & (phi > 0.5))[0]
    ip = ip[~np.isin(ip, S.bcore)]
    if p["pull"] > 0:
        anc.append((ip, Xf[ip] + (p["pull"] * kA * k[ip])[:, None] * (du[None, :] - (Nf[ip] @ du)[:, None] * Nf[ip]), p["cr"]))
    for pth, amp in ((S.faf, p["ridge"]), (S.baf, p["back"])):
        if amp > 0:
            sl = np.linspace(0, 1, len(pth))
            a = kA * amp * np.sin(np.pi * np.clip(sl * 1.15 - 0.05, 0, 1)) ** 0.7
            anc.append((pth, Xf[pth] + a[:, None] * Nf[pth], p["cr"]))
    C = Xf[S.apex]
    ax = _unit(Nf[np.linalg.norm(Xf - C, axis=1) < 0.02].mean(0))
    hu = _unit(h - (h @ ax) * ax)
    q = Xf - C
    rho = np.sqrt(((q @ hu) / p["dRu"]) ** 2 + ((q - (q @ hu)[:, None] * hu - (q @ ax)[:, None] * ax) ** 2).sum(1) / p["dRv"] ** 2)
    core = np.nonzero((rho < 1.0) & (S.phi > 0.5))[0]
    # (round 6) the pit deeper at the overhead keys (DOMEX more, from A 80, whole at 105): its apex rises into the arm
    # and away from the breast's upper-outer edge, so the contact V opens (the lowered key keeps round 5's dome)
    dmx = p.get("domeX", 0.0) * _ramp(A, *p.get("domeA", (80.0, 105.0)))
    dm = kA * p["dome"] + dmx * np.ones(len(core))
    if p.get("domeF", 0) > 0:
        # (round 10) that extra depth eased off the pit's FRONT quarter (toward the pec's fold and the breast): there it
        # deepened the pocket between the pec's roll and the breast's upper-outer side that the front cameras see
        vf = np.cross(ax, hu)
        vf = vf if vf[2] > 0 else -vf
        dm = dm - p["domeF"] * dmx * _ss(((q[core] @ vf) / p["dRv"] - 0.25) / 0.5)
    anc.append((core, Xf[core] - (dm * (1 - rho[core] ** 2) ** 2)[:, None] * ax, p["cd"]))
    up = _unit(np.array([0, 1.0, 0]) - h[1] * h)
    c = np.cross(up, h)
    dt = _unit(np.cos(np.radians(25)) * up + np.sin(np.radians(25)) * (c if c[2] > 0 else -c))
    v = Xf - J
    ta = v @ h
    rr = v - ta[:, None] * h
    ca = (rr @ dt) / np.maximum(np.linalg.norm(rr, axis=1), 1e-9)
    wdl = _ss((ta + 0.015) / 0.04) * (1 - _ss((ta - 0.06) / 0.065)) * _ss(ca / 0.6) * (S.aw > 0.3) * (S.phi > 0.05)
    dl = np.nonzero(wdl > 0.02)[0]
    if p["delt"] > 0:
        anc.append((dl, Xf[dl] + (kA * p["delt"] * wdl[dl])[:, None] * Nf[dl], p["cl"]))
    X = fill(Xf, anc, its=1)
    # the pit's core relaxed (plain passes: Taubin left it): the A-pose fold's leftover nick where the arm's underside
    # meets the torso wall eased out
    wr = p["relax"] * H.smooth(np.minimum(S.core * 1.5, 1) * S.phi, 6)
    for _ in range(p["relaxIt"]):
        X = X + 0.5 * wr[:, None] * b.lap(X)
    # faired: each point moved along its normal till its ring's curvature is her rest's (none in the flat sector);
    # the solve's rotated rest Laplacian leaves 1-1.5 mm single-point dips where its turn and the surface's disagree
    # (odd valence points on the chest's front by the fold: a dark nick in Godot)
    Xr = X.copy()
    wf = p["fair"] * H.smooth(phi, 4) * (phi > 1e-4)
    k0 = S.kap * (H.dU * H.NU).sum(1)
    for _ in range(p["fairIt"]):
        N = ph.vn(X, F)
        X = X + (0.5 * wf * ((b.lap(X) * N).sum(1) - k0))[:, None] * N
    Xa = X.copy()
    # detail along the normal: the pec's lower border a rounded lip, the biceps/triceps groove, the deltoid's insertion
    N = ph.vn(X, F)
    off = np.zeros(len(X))
    if p["lip"] > 0:
        # its spine: the fold's edge path (zigzag along edges) smoothed and resampled
        Xs = X[S.faf].copy()
        for _ in range(30):
            Xs[1:-1] = 0.5 * Xs[1:-1] + 0.25 * (Xs[:-2] + Xs[2:])
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Xs, axis=0), axis=1))]
        ns = 240
        Xs = np.stack([np.interp(np.linspace(0, cum[-1], ns), cum, Xs[:, k]) for k in range(3)], 1)
        tg = _unit(np.gradient(Xs, axis=0))
        bn = _unit(np.cross(tg, N[cKDTree(X).query(Xs)[1]]))
        mid = slice(ns // 3, 2 * ns // 3)
        if ((X[S.apex] - Xs[mid]) * bn[mid]).sum() > 0:
            bn = -bn                                          # + over the chest, - into the pit
        dist, qq = cKDTree(Xs).query(X)
        nr = np.nonzero((dist < 0.06) & (phi > 0.05))[0]
        qq = qq[nr]
        vv = X[nr] - Xs[qq]
        sx, al = (vv * bn[qq]).sum(1), (vv * tg[qq]).sum(1)
        sl = qq / (ns - 1.0)
        # (round 3) a round roll: whole from 20 mm off its chest end, fading from 40% of the way to nothing at the
        # arm end (~80 mm up the inner arm)
        sm = sl * cum[-1]
        if p.get("lipEnd", 0) > 0:
            # (round 10) the roll's CHEST END carried onto the breast's upper-outer surface: whole to its end, fading
            # over LIPEND past it on the breast, so roll and breast read as one convex form (round 3's roll rose from
            # nothing over its first 20 mm: the notch between them was the pocket rows 1 and 5 look into)
            env = (1 - _ss((sl - 0.4) / 0.6)) * np.where(qq == 0, _ss(1 - np.maximum(-al, 0) / p["lipEnd"]), 1.0)
            env *= np.where(qq == ns - 1, _ss(1 - np.abs(al) / 0.02), 1.0)
        else:
            # (round 11) rising from nothing at LIPC0 off its chest end, whole LIPC later (round 3: 0 and 20 mm),
            # fading from LIPFO of the way to nothing at its arm end
            c0, c1, fo = p.get("lipC0", 0.0), p.get("lipC", 0.02), p.get("lipFo", 0.4)
            env = _ss((sm - c0) / c1) * (1 - _ss((sl - fo) / (1 - fo)))
            env *= np.where((qq == 0) | (qq == ns - 1), _ss(1 - np.abs(al) / 0.02), 1.0)
        prof = np.where(sx >= 0, np.exp(-(sx / p["lipF"]) ** 2), np.exp(-(sx / p["lipP"]) ** 2))
        # (round 11) LIPHI: the roll's share at the overhead keys (eased over LIPHIA): NATURAL none. With the arms up
        # the roll stood as its own form between the arm's underside and the breast's upper-outer side (the owner's
        # "lumps" at the cast, both sides); without it the arm's underside runs into the breast's side in one curve
        kHi = 1 - (1 - p.get("lipHi", 1.0)) * _ramp(A, *p.get("lipHiA", (80.0, 105.0)))
        off[nr] += p["lip"] * kA * kHi * env * prof
    lat, fr = Ra @ S.lat0, Ra @ S.fr0
    v = X - J
    ta = v @ h
    rr = v - ta[:, None] * h
    rn = np.maximum(np.linalg.norm(rr, axis=1), 1e-9)
    ang = np.arctan2(rr @ fr, rr @ lat)                       # 0 out (the deltoid), +90 front, 180 in
    armm = _ss((S.aw - 0.5) / 0.3)
    if p["groove"] > 0:
        arc = np.angle(np.exp(1j * (ang - np.radians(160)))) * rn
        envg = _ss((ta - 0.04) / 0.03) * (1 - _ss((ta - 0.19) / 0.04))
        off -= p["groove"] * kA * envg * np.exp(-(arc / p["grooveW"]) ** 2) * armm
    if p["ins"] > 0:
        ti = p["insT"] * Lh
        hw = np.radians(80) * np.clip((ti - ta) / (ti - 0.03), 0, 1)
        dv = np.abs(np.angle(np.exp(1j * (ang - np.radians(10)))))
        off += p["ins"] * kA * _ss((hw - dv) / np.radians(14)) * _ss((ta - 0.035) / 0.03) * armm
    off = H.smooth(off, 3)
    if p["vLift"] > 0:
        # (round 3) the shoulder's top between the neck and the raised deltoid opened from a V to a U: its floor (a
        # new valley tighter than 30 mm on a 40 mm patch, her rest's own left out) lifted out by a broad eased field
        sg = 1 if side == "l" else -1
        zt = np.nonzero((phi > 0.3) & (S.bsm < 0.2) & (U[:, 0] * sg > 0.14) & (U[:, 1] > 1.43) & (np.abs(U[:, 2] + 0.005) < 0.06))[0]
        _, kz = quad(X, N, zt, p["vLr"], b.A)
        _, kzu = quad(U, H.NU, zt, p["vLr"], b.A)
        wv = np.zeros(len(X))
        wv[zt] = np.clip((kz - np.maximum(kzu, 0) - 1 / 0.04) / (1 / 0.012 - 1 / 0.04), 0, 1)
        wv = H.smooth(wv, 6)
        off += p["vLift"] * kA * wv / max(wv.max(), 1e-9)
    X = X + off[:, None] * N
    if p["noCut"] > 0:
        # (round 4) NO CUT on the arm's underside: the solve's turned Laplacian thinned the arm's back-underside 9-15 mm
        # within 40 mm of the joint (its turn half the humerus' there), so the underside line rose into the pit as an
        # arch (the owner, 25 Oct). Every point on the arm side of the joint (eased in over ncT down the humerus) and
        # not on its top-outer side (the deltoid's: eased out over the upper half) is put back out to its skinned
        # radius from the humerus wherever the sculpt took it inside it; the push smoothed (no step at the mask's edge)
        v0, v1 = X0 - J, X - J
        t0_, t1_ = v0 @ h, v1 @ h
        q0, q1 = v0 - t0_[:, None] * h, v1 - t1_[:, None] * h
        r0, r1 = np.linalg.norm(q0, axis=1), np.maximum(np.linalg.norm(q1, axis=1), 1e-9)
        up_ = _unit(np.array([0, 1.0, 0]) - h[1] * h)
        cu = (q1 @ up_) / r1
        # (round 5) at the overhead keys the restore ramps in over a longer reach (ncT2: the arm whole only from ~70 mm
        # down the humerus), so the underside tapers into the back fold by the joint instead of a full round tube
        # pressed into the torso (row 2's crease down the deltoid's back edge); the lowered key keeps round 4's (its
        # straight underside, the owner's note)
        kN = _ramp(A, *p["ncA"])
        nc0, nc1 = (1 - kN) * p["ncT"][0] + kN * p["ncT2"][0], (1 - kN) * p["ncT"][1] + kN * p["ncT2"][1]
        mk = (_ss((t1_ - nc0) / nc1) * (1 - _ss((cu - 0.1) / p["ncOut"])) * (r0 < 0.075)
              * (S.aw > 0.3) * (phi > 1e-4))
        raw = p["noCut"] * mk * np.maximum(r0 - r1, 0)
        push = H.smooth(np.maximum(raw, H.smooth(raw, 3)), 2)
        X = X + push[:, None] * (q1 / r1[:, None])
        if info is not None:
            info["nocut"] = 1000 * push.max()
    if p.get("bin", 0) > 0:
        # (round 6) the arm's underside landed on the breast's upper-outer edge in a dark pinched V (rows 1, 3, 5): the
        # breast's lateral side stood 15-20 mm out past her chest wall under the pit, so its outline met the pit's apex
        # in the camera's view. The breast's upper-outer side drawn in and down-medial (BIN at its far edge, a smooth
        # field from its centre (BINS along the outer-up axis: 0 at the centre, whole at 80 mm, gone past 130), its
        # weight smoothed BINSM passes so no ridge crosses it), eased in from A 60, whole at 105: a strip of chest wall
        # opens between the pit and the breast (the targets), the breast's core and its lift barely move
        sg = 1 if side == "l" else -1
        mb = S.bw > 0.3
        Bc2 = (X[mb] * S.bw[mb, None]).sum(0) / S.bw[mb].sum()
        eo = _unit(np.array([sg * 1.0, 0.8, -0.3]))
        so = (X - Bc2) @ eo
        s0_, s1_, s2_ = p["binS"]
        wb = _ss((so - s0_) / (s1_ - s0_)) * (1 - _ss((so - s2_) / 0.03)) * _ss((S.bsm - 0.02) / 0.2)
        wb = H.smooth(wb, p["binSm"]) * np.clip(H.smooth(phi, 2) * 1.5, 0, 1)
        md = _unit(np.array([-sg * 0.8, -0.6, 0.0]))
        X = X + (p["bin"] * _ramp(A, *p["binA"]) * wb)[:, None] * md
        if info is not None:
            info["bin"] = 1000 * p["bin"] * _ramp(A, *p["binA"]) * wb.max()
    wtop = None
    if p["close"] > 0:
        # (round 5) no fold in the join tighter than CLOSER (a rolling ball's closing, _close): the arm's underside
        # landing on the breast's upper-outer edge in a pinched V (rows 1, 3, 5), the crease down the deltoid's back
        # edge into the pit (row 2) become folds of that radius; the shoulder's top between the trapezius and the raised
        # deltoid (row 1's V: two masses meeting in a deep narrow fold) closed with the larger CLOSERT, so the deltoid
        # flows into the trapezius; the breast core not touched; whole from A 75 (nothing below A 60)
        sg = 1 if side == "l" else -1
        xs_, ys_, zs_ = U[:, 0] * sg, U[:, 1], U[:, 2]
        kC = p["close"] * _ramp(A, 60.0, 75.0)
        # (the join's closing only from the overhead keys: at the lowered key it bent the underside's line, sag 3.3
        # -> 4.2 mm at the A 75 front camera, and that line is the owner's note)
        # (round 8) the join's zone off her breast's inner and lower sides (lateral of x closeX, over y closeY): its
        # rest valleys (the cleavage, the fold under the breast) were in it and got "closed" into fold-overs
        wj = H.smooth(_ss((phi - 0.1) / 0.3) * (1 - _ss((S.bsm - 0.3) / 0.15))
                      * _ss((xs_ - p["closeX"][0]) / p["closeX"][1]) * _ss((ys_ - p["closeY"][0]) / p["closeY"][1]), 2)
        wj = wj * p["close"] * _ramp(A, *p["closeA"])
        wt = (_ss((xs_ - p["vfX"]) / 0.03) * _ss((ys_ - p["vfY"]) / 0.04) * (1 - _ss((np.abs(zs_ - p["vfZ"]) - p["vfW"]) / 0.03))
              * (1 - _ss((S.bsm - 0.1) / 0.15)) * _ss((phi - 0.15) / 0.3))
        wt = H.smooth(wt, 3) * kC
        wtop = wt
        cf = []
        if p["closeRt"] > 0:
            # (round 12) at the overhead keys (from A 100) the shoulder's top closed with a larger ball (CLOSERT_HI) along
            # a direction field smoothed over its size (CLOSET_NSM passes, was 4): the moves along the crease's own
            # normals crossed and folded its faces (the crumple STOP clears last); the lowered key keeps round 11's
            hiT = _ramp(A, *p.get("stopA", (95.0, 105.0))) >= 0.5 and p.get("stop", 0) > 0
            X, f = _close(H, X, wt, p["closeRtHi"] if hiT else p["closeRt"], p["closeMax"], sm=p["closeSm"],
                          never=p["closeNever"], nsm=int(p["closeTNsm"]) if hiT else 4)
            cf.append(f)
        X, f = _close(H, X, wj, p["closeR"], p["closeMax"], sm=p["closeSm"], never=p["closeNever"])
        cf.append(f)
        if p.get("jclose", 0) > 0:
            # (round 9) the arm-breast JUNCTION at the overhead keys (rows 1 and 5's V/wedge where the arm's underside
            # lands on the breast's upper-outer corner): it is NOT below the join's zone (wj is whole there) and not
            # tighter than CLOSER (the 12 mm ball rolls in freely: fill 0): it is a pocket 25-40 mm across between
            # the pec's lower-border roll (LIP), the pit's front wall and the breast's upper-outer side, which the
            # front cameras look into. A larger ball (JCLOSER) closes that pocket only: the zone round the fold's
            # chest end (S.a_fc, within JCLOSE_RAD at rest, eased), lateral of the cleavage, off the breast's core,
            # whole from A 105 (nothing at the lowered key); the fill capped (JCLOSE_MAX)
            dj = np.linalg.norm(U - U[S.a_fc], axis=1)
            wk = H.smooth(_ss((p["jcloseRad"] - dj) / 0.03) * (1 - _ss((S.bsm - 0.35) / 0.15))
                          * _ss((xs_ - 0.10) / 0.03) * (phi > 1e-4), 3)
            wk = wk * p["jclose"] * _ramp(A, *p["jcloseA"])
            if wk.max() > 0.01:
                X, f = _close(H, X, wk, p["jcloseR"], p["jcloseMax"], never=p["closeNever"])
                cf.append(f)
        if info is not None:
            info["close"] = [1000 * c.max() for c in cf]
    # untangled: where the bend packs the skin past what her rest shape fits (the join's front-top, the fold's chest
    # end) the solve buckles a few triangles over (dark nicks in Godot): those and two rings round them smoothed
    # (Taubin, no shrink) till none is left
    X, nfold = _untangle(H, X, H.rings(phi > 1e-4, 1))
    Xu = X.copy()
    # (round 3) the LAST stage: every valley the raise made rounded to at least RMIN (a 2 x 12 mm patch's quadric:
    # its concave curvature) and every point that sits in from its patch lifted onto it (no single-point dip), by
    # filling only: the points that break either (and a ring round them) moved out along the normal to their
    # neighbours' mean, never in, till none is left. Her rest valleys (the fold under the breast, the cleavage)
    # are hers: only curvature the pose added counts. Rows 1-3's puckers (the join's front-top under the acromion,
    # where the raise packs the skin), the trapezius-deltoid V, the pit floor's V, the lowered fold's line
    # (the fairing moves along normals, and where the raise packs the skin a few faces tip: untangled again, the
    # fairing again, twice; the fairing last)
    rm = p["rmin"] if A > p["kA"][0] + 25 else p["rminLow"]
    for _ in range(p["cyc"]):
        X, nval = _fair_patches(H, X, phi, S, rm, p)
        X, nfold2 = _untangle(H, X, H.rings(phi > 1e-4, 1), rounds=p["uR"], its=6)
    X, nval = _fair_patches(H, X, phi, S, rm, p)
    # what's left (a few tipped faces with a dip by them, where the raise packs the skin) smoothed on the spot: those
    # points and two rings round them, eased, toward their neighbours' mean
    live = (phi > 0.05) & (S.bsm < 0.45)
    idx = np.nonzero(live)[0]
    c0u, _ = quad(U, H.NU, idx, p["vr"], b.A)
    for _ in range(p["spot"]):
        spot = np.zeros(len(X), bool)
        spot[F[_folds(H, X, live)].ravel()] = True
        c0, _ = quad(X, ph.vn(X, F), idx, p["vr"], b.A)
        spot[idx[c0 - np.maximum(c0u, 0) > p["dip"]]] = True
        if not spot.any():
            break
        ws = np.clip(H.smooth(H.rings(spot, 1).astype(float), 2) * 1.5, 0, 1) * live
        for _ in range(4):
            X = X + 0.5 * ws[:, None] * b.lap(X)
    X, nval = _fair_patches(H, X, phi, S, rm, p)               # (fold-safe: a move that tips a face is taken back)
    if p.get("imfS", 0) > 0:
        # (round 8) the fold under her breast: the lift holds the breast's core (smoothed breast weight > 0.45) hard on
        # its lifted place and solves the skin round it, so the move steps along the core's ragged edge (a vertex
        # set) and the fold under the breast came out as a jagged dark line (from the first fill on; rounds 2-7, the
        # "ragged line under the breasts"). The MOVE (not the shape: her skinned fold is smooth) smoothed over the
        # breast's lower rim, IMFS passes, eased in: the fold rises as one smooth line
        yn = U[S.nip, 1]
        # (round 10) IMFOUT: at the overhead keys carried out to the breast's lateral border, 4 passes more (the outer
        # end of the fold under her left breast stayed ragged at the cast)
        ko = p.get("imfOut", 0) * _ramp(A, 95.0, 105.0)
        b0 = 0.08 - 0.07 * ko
        wi = (_ss((yn + 0.01 - U[:, 1]) / 0.03) * _ss((S.bsm - b0) / (0.15 - 0.05 * ko)) * (1 - _ss((S.bsm - 0.8) / 0.15))
              * (phi > 1e-4))
        wi = np.clip(H.smooth(wi, 3) * 1.5, 0, 1)
        Dm = H.smooth(X - X0, p["imfS"] + int(round(4 * ko)))
        X = X + wi[:, None] * (X0 + Dm - X)
    kH = p.get("imfH", 0) * _ramp(A, *p.get("imfHA", (75.0, 95.0)))
    if kH > 0 and not still:
        # (round 11) IMFH: the fold under the breast kept as her skin folds it (the skinned crease is clean: Body 8,
        # STILL): over the fold's band (S.fb) the move is the HARMONIC fill of the move round it (the lifted breast's
        # rim above, her chest wall IMFHR below), so it varies smoothly across the crease and the crease is carried,
        # not sheared: the lift's step at the core's ragged edge (the held core over the solved panel) tipped the
        # crease's thin triangles into a serrated dark edge (the cast's "ragged line under her left breast")
        band = S.fb & (phi > 1e-4)
        if band.any():
            bi, bo_ = np.nonzero(band)[0], np.nonzero(~band)[0]
            D = X - X0
            lu = splu(H.L[bi][:, bi].tocsc())
            rhs = -(H.L[bi][:, bo_] @ D[bo_])
            Dh = D.copy()
            Dh[bi] = np.stack([lu.solve(rhs[:, k]) for k in range(3)], 1)
            X = X + kH * (Dh - D)
            if info is not None:
                info["imfH"] = (int(band.sum()), 1000 * np.linalg.norm(Dh - D, axis=1).max())
    if p.get("vkeep", 0) > 0:
        # (round 8) her breast NEVER smaller (the owner: "do not narrow bust"; a draw-in only if "it dosn't get
        # smaller"): the draw-in (BIN) and the lift's stretch took 5-9% off her breast's volume at the A 114-117 keys.
        # If the region's closed volume is under the skinned key's (her Body 8 volume there) by VKEEPM, her breast's
        # front and inner-lower side are filled out along the (smoothed) normal (a smooth field, one scalar solved: two Newton
        # steps) till it is VKEEPM over it
        def vol(Y, reg):
            Fr, bd = reg
            c = Y[bd].mean(0)
            return abs((((Y[Fr[:, 0]] - c) * np.cross(Y[Fr[:, 1]] - c, Y[Fr[:, 2]] - c)).sum()) / 6.0)
        for (reg, vw), mg in zip(S.vb, (p["vkeepM"], 0.15 * p["vkeepM"])):
            Vt = vol(X0, reg) * (1 + mg)
            V1 = vol(X, reg)
            if V1 >= Vt:
                continue
            Nv = ph.vn(H.smooth(X, 4), F)                     # (the smoothed surface's: no crumple's noise)
            q = 0.5 * np.linalg.norm(np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]]), axis=1)
            Av = np.zeros(len(X))
            for k in range(3):
                np.add.at(Av, F[:, k], q / 3)
            a = 0.0
            for _ in range(2):
                a += (Vt * 1.0005 - vol(X + (a * p["vkeep"] * vw)[:, None] * Nv, reg)) / max((vw * Av).sum() * p["vkeep"], 1e-12)
            X = X + (a * p["vkeep"] * vw)[:, None] * Nv
            if info is not None:
                info.setdefault("vkeep", []).append((1e6 * V1, 1e6 * Vt, 1000 * a))
    if p.get("clear", 0) > 0:
        # (round 8) the last folded faces (a face turned past 90 degrees from its neighbour: the join's front-top
        # under the acromion, where the raise packs the skin; 7-15 per overhead key, the jagged nick in the shoulder's
        # outline in row 1) smoothed out: their points and two rings round them (not her breast's core), plain
        # Laplacian passes eased over a ring, till none is left (at most CLEAR rounds of 3)
        # (a crumple of sub-millimetre faces it can't open stops it: no more than CLEARMAX moved anywhere, and it ends
        # when two rounds bring no fewer folds, so it never grinds a patch down)
        lc = H.rings(phi > 1e-4, 1) & (S.bsm < 0.45)
        Xc = X.copy()
        best, stall = int((_flips(F, X) & lc[F].all(1)).sum()), 0
        for _ in range(p["clear"]):
            fl = _flips(F, X) & lc[F].all(1)
            if not fl.any():
                break
            m = np.zeros(len(X), bool)
            m[F[fl].ravel()] = True
            wc = np.clip(H.smooth(H.rings(m, 2).astype(float), 1) * 1.5, 0, 1) * lc
            for _ in range(3):
                X = X + 0.5 * wc[:, None] * b.lap(X)
            n = int((_flips(F, X) & lc[F].all(1)).sum())
            stall = 0 if n < best else stall + 1
            best = min(best, n)
            if stall >= 2:
                break
        mv = X - Xc
        X = Xc + mv * np.minimum(1, p["clearMax"] / np.maximum(np.linalg.norm(mv, axis=1), 1e-12))[:, None]
        if info is not None:
            info["clear"] = int((_flips(F, X) & lc[F].all(1)).sum())
    kS = p.get("stop", 0) * _ramp(A, *p.get("stopA", (95.0, 105.0)))
    if kS > 0 and wtop is not None:
        # (round 12) STOP: the shoulder's top where the raised deltoid meets the trapezius (the owner: "the small step
        # at the shoulder top", row 1). The solve packs the skin there into a crease (40-90 faces folded, Xa); the
        # 18 mm closing pushes the crease's floor out along its normals, so the folded faces come up onto the surface
        # and the untangle, fairing and CLEAR leave a crumple of 10-26 flipped faces at every overhead key (show,
        # cast both sides, cast150): at the front camera it sits on the outline as a notch between the trapezius'
        # end and the deltoid. Last: the faces still flipped on the shoulder's top (the closing's zone), STOPD rings
        # round them, re-solved as a thin plate (Laplacian zero, eased in over the band's edge; the rest held): one
        # smooth fillet from the trapezius into the deltoid. Eased in from A 95, whole at 105 (the lowered key: none)
        top = H.rings(wtop > 0.05, 1) & (S.bsm < 0.1)
        X1, n0 = X.copy(), int((_flips(F, X) & top[F].all(1)).sum())
        for _ in range(p["stopIt"]):
            fl = _flips(F, X1) & top[F].all(1)
            if not fl.any():
                break
            m = np.zeros(len(X), bool)
            m[F[fl].ravel()] = True
            ws = np.clip(H.smooth(H.rings(m, int(p["stopD"])).astype(float), 1) * 1.5, 0, 1) * top
            for _ in range(3):
                X1 = X1 + 0.5 * ws[:, None] * b.lap(X1)
        mv = X1 - X
        X1 = X + mv * np.minimum(1, p["stopMax"] / np.maximum(np.linalg.norm(mv, axis=1), 1e-12))[:, None]
        if info is not None:
            info["stop"] = (n0, int((_flips(F, X1) & top[F].all(1)).sum()), round(1000 * np.linalg.norm(X1 - X, axis=1).max(), 1))
        X = X + kS * (X1 - X)
        if p.get("stopKeep", 1) > 0:
            # everything off the shoulder's top kept EXACTLY round 11's: the cleanup loops above (untangle, fairing,
            # spot, CLEAR) stop on the fold count over the whole region, so fewer folds on the shoulder's top changed
            # the passes the arm-breast junction got (the cast's pocket 4.9/5.8 -> 0.5/1.4 mm). Round 11's sculpt
            # (STOP off) is made too and this one kept only over the shoulder top's closing zone (3 rings round it,
            # eased over 3 more)
            D11, _ = author(H, S, d, side, dict(p, stop=0.0), X0in=X0in)
            wm = np.clip(H.smooth(H.rings(wtop > 0.01, 3).astype(float), 3) * 1.5, 0, 1)
            dX = X - (X0 + D11)
            if info is not None:
                info["stopKeep"] = (int((wm > 0).sum()), round(1000 * np.linalg.norm((1 - wm)[:, None] * dX, axis=1).max(), 2))
            X = (X0 + D11) + wm[:, None] * dX
    if still:
        # (round 10) STILL: nothing on the breasts, the join's move eased to nothing at their border
        X = X0 + (1 - S.keepB)[:, None] * (X - X0)
    nfold = (nfold[0], nfold[1], len(_folds(H, X, H.rings(phi > 1e-4, 1))))
    if info is not None:
        info.update(X0=X0, Xf=Xf, Xr=Xr, Xa=Xa, Xu=Xu, X=X)
        info["num"] = "A %.1f kA %.2f kL %.2f: nipple rise %.1f mm (skinned %.1f), detail offset %.1f/%.1f mm, folds %d -> %d -> %d, valley fill %s" % (
            A, kA, kL, 1000 * (X[S.nip, 1] - U[S.nip, 1]), 1000 * (X0[S.nip, 1] - U[S.nip, 1]), 1000 * off.min(), 1000 * off.max(), *nfold, nval)
    return X - X0, B


def _rest(B, D):
    return np.einsum("nab,nb->na", np.linalg.inv(B[:, :3, :3]), D)


def _turned_stored(H, X1, sm=0):
    """(round 5) her STORED normal carried by the surface's own local turn from her rest to X1: per triangle the
    turn of its deformation (edges and normal, rest -> X1: the polar of [e1' e2' n'] [e1 e2 n]^-1, which takes the
    rest face normal exactly to the posed one), area-weighted per point and made a turn again, applied to her stored
    normal. Where the sculpt keeps her rest shape (the near-rigid breast core) it IS her stored normal; where it bends
    the skin (the join) it is the sculpt's own normal but without the area-weighted normal's facet noise (her stored
    normals are her smooth surface's; the welded mesh's geometric ones scatter 0.5-0.9 deg median, 3 at p90, up to 8)"""
    U, F = H.b.U, H.b.F

    def frame(Y):
        e1, e2 = Y[F[:, 1]] - Y[F[:, 0]], Y[F[:, 2]] - Y[F[:, 0]]
        n = np.cross(e1, e2)
        a = np.linalg.norm(n, axis=1)
        return np.stack([e1, e2, n / np.maximum(a, 1e-15)[:, None]], 2), a
    E0, a0 = frame(U)
    E1, _ = frame(X1)
    ok = a0 > 1e-12
    Ft = np.tile(np.eye(3), (len(F), 1, 1))
    Ft[ok] = E1[ok] @ np.linalg.inv(E0[ok])
    Rt = _polar(Ft)
    Rv = np.zeros((len(U), 3, 3))
    for k in range(3):
        np.add.at(Rv, F[:, k], Rt * a0[:, None, None])
    if sm > 0:
        # (round 8) the turn field smoothed over her skin first (SM passes, then made a turn): where the skin is
        # stretched hard across a crease (the fold under the breast as the lift opens it) the triangles' own turns
        # scatter, and the per-point turn lit the fold in a sawtooth of bright and dark specks (the "ragged line under
        # the breasts"); her stored normal's own bend across the fold is kept (only its turn is smoothed)
        Rv = H.smooth((Rv / np.maximum(np.linalg.norm(Rv.reshape(-1, 9), axis=1), 1e-18)[:, None, None]).reshape(-1, 9), sm).reshape(-1, 3, 3)
    Rv = _polar(Rv + 1e-18 * np.eye(3)[None])
    return _unit(np.einsum("nab,nb->na", Rv, H.Ns))


def _unit_toward(c, wsum, t):
    """unit u with c + wsum u along +t (per row): Godot blends a slot's unit normal as base (1 - sum w) + sum w u"""
    tc = (t * c).sum(1)
    lam = tc + np.sqrt(np.maximum(tc * tc - (c * c).sum(1) + wsum * wsum, 0))
    return _unit(lam[:, None] * t - c)


def _pair_toward(cs, cc, Wm, ts, tc, its=30):
    """unit (ua, uf) with cs + Wm[0] . (ua, uf) along +ts and cc + Wm[1] . (ua, uf) along +tc (Newton on the two
    keys' free lengths); rows where it fails keep the normalised linear answer"""
    Wi = np.linalg.inv(Wm)
    p1, q1, r1 = Wi[0, 0] * ts, Wi[0, 1] * tc, Wi[0, 0] * cs + Wi[0, 1] * cc
    p2, q2, r2 = Wi[1, 0] * ts, Wi[1, 1] * tc, Wi[1, 0] * cs + Wi[1, 1] * cc
    lam = np.ones((len(ts), 2))
    for _ in range(its):
        ua = lam[:, :1] * p1 + lam[:, 1:] * q1 - r1
        uf = lam[:, :1] * p2 + lam[:, 1:] * q2 - r2
        f = np.stack([(ua * ua).sum(1) - 1, (uf * uf).sum(1) - 1], 1)
        Jm = 2 * np.stack([np.stack([(ua * p1).sum(1), (ua * q1).sum(1)], 1),
                           np.stack([(uf * p2).sum(1), (uf * q2).sum(1)], 1)], 1)
        ok = np.abs(np.linalg.det(Jm)) > 1e-9
        step = np.zeros_like(lam)
        step[ok] = np.linalg.solve(Jm[ok], f[ok][:, :, None])[:, :, 0]
        lam = lam - np.clip(step, -0.5, 0.5)
    ua = lam[:, :1] * p1 + lam[:, 1:] * q1 - r1
    uf = lam[:, :1] * p2 + lam[:, 1:] * q2 - r2
    good = (np.abs(np.linalg.norm(ua, axis=1) - 1) < 1e-3) & (np.abs(np.linalg.norm(uf, axis=1) - 1) < 1e-3) & (lam > 0).all(1)
    return _unit(ua), _unit(uf), good


def build(G, log=print):
    """{group_side: rest delta}, the keys' rest normal targets and their slot weights (the slots' unit normals are
    solved per primitive in run, against each primitive's own normals)"""
    H = Her(G)
    b = H.b
    poses = json.load(open(POSES))
    S = {s: Side(H, s) for s in "lr"}
    samp = {}
    U = b.U
    # (round 8) at the two-arm keys (the cast, the old cast) the two sides' regions overlap across her sternum (each
    # side's breast panel runs to the other breast's inner edge) and Godot ADDS the two sides' slots there: rounds 2-7
    # moved the cleavage twice (a fold-over, a jagged line between the breasts). Now the key is sculpted ONCE for both
    # sides (each side re-solved on the other's result, both orders averaged: they differ < 1 mm) and that move is
    # shared out between the sides' slots by a smooth split across the sternum (MID: all the left's at x > MID, all
    # the right's at x < -MID, half each on the midline), so the sum at the key is the one sculpt
    joint = {}
    for key in ("cast", "cast150"):
        if not P["joint"] or not all((key, s_) in KEYS for s_ in "lr"):
            continue
        d = poses[key]
        _, _, X0j, Bj = b.pose(d)
        Dl, _ = author(H, S["l"], d, "l")
        Dr, _ = author(H, S["r"], d, "r")
        Drl, _ = author(H, S["r"], d, "r", X0in=X0j + Dl)
        Dlr, _ = author(H, S["l"], d, "l", X0in=X0j + Dr)
        Tj = 0.5 * (Dl + Drl + Dr + Dlr)
        shl = _ss((U[:, 0] + P["mid"]) / (2 * P["mid"]))
        joint[key] = (Tj, Bj, {"l": shl, "r": 1 - shl})
        both = (np.linalg.norm(Dl, axis=1) > 1e-4) & (np.linalg.norm(Dr, axis=1) > 1e-4)
        log("SCULPT %s joint: %d points in both sides' moves (added they reached %.1f mm), orders differ %.2f mm max" % (
            key, int(both.sum()), 1000 * np.linalg.norm(Dl + Dr, axis=1)[both].max() if both.any() else 0.0,
            1000 * np.linalg.norm((Dl + Drl) - (Dr + Dlr), axis=1).max()))
    for key, side in KEYS:
        if key in joint:
            Tj, B, sh = joint[key]
            D = sh[side][:, None] * Tj
        else:
            D, B = author(H, S[side], poses[key], side)
        _, _, X0, _ = b.pose(poses[key])
        Mg, A, az = _angles(H, poses[key], side)
        wts = sp.psd_weights(A, az, sp.clavicle_rise(Mg, H.M0, b.I, side))
        # (round 3) the normal Godot is to shade with at the key: the SCULPT'S OWN (the posed surface's geometric
        # normal) carried back through the blended matrix (Godot skins normals by it), so Godot lights the shape the
        # solve made; round 1-2 wrote the skinned normal turned by the sculpt's turn, which carried the skinning's
        # own normal errors (60-90 degrees at the join's front-top under the helper bones, 160 where the skinned
        # skin folds) into the light: the dark puckers Godot showed and Blender (geometric normals) never did.
        # Eased to that old normal over the region's edge (rings beyond it), where it is her stored normal.
        # (round 5) inside the region that normal is no longer the raw area-weighted geometric one (its facet noise
        # lit her breasts in straight-edged light/dark facets at 1:1, rows 1 and 5) but her STORED normal carried by
        # the sculpt's own local turn (_turned_stored): her stored normal on the near-rigid breast core, the sculpt's
        # normal without the noise in the join (still no skinned normal in it: the puckers stay fixed)
        L = B[:, :3, :3]
        Li = np.linalg.inv(L)
        # (round 8) at a joint key the normal target is the one sculpt's (both sides' regions), each side's slots
        # turning her normal by its share of the way (slot_normals)
        Dt = joint[key][0] if key in joint else D
        N0, N1 = ph.vn(X0, b.F), ph.vn(X0 + Dt, b.F)
        g0 = _unit(np.einsum("nab,nb->na", L, H.Ns))
        nt = _unit(np.einsum("nab,nb->na", Li, ph._rot(N0, N1, g0)))
        ng = _unit(np.einsum("nab,nb->na", Li, N1 if P["nGeo"] else _turned_stored(H, X0 + Dt, P["nTs"])))
        sides = "lr" if key in joint else side
        reg = H.rings(np.max([np.maximum(S[s_].phi, S[s_].phib) for s_ in sides], 0) > 1e-4, P["nRing"])
        wn = np.clip(H.smooth(reg.astype(float), P["nRing"]) * 2, 0, 1)
        wn = wn * wn * (3 - 2 * wn)
        if P["still"] > 0:
            wn = wn * (1 - S[side].keepB)                     # (round 10) STILL: her skinned normal on the breasts
        if P["imfHN"] > 0:
            # (round 11) on the fold under the breast, her skinned normal turned by the surface's own turn there
            wn = wn * (1 - P["imfHN"] * np.max([S[s_].fbE for s_ in sides], 0))
        t = _unit(wn[:, None] * ng + (1 - wn[:, None]) * nt)
        if P["imfHS"] > 0:
            # (round 11) the fold under the breast lit as one soft gradient: the target smoothed IMFHS passes over the
            # fold's band (eased): the crease's down-turned normals were interpolated across the chest wall's long
            # triangles under it into dark wedges (the serrated edge Godot showed under the lifted breast)
            fbE = np.max([S[s_].fbE for s_ in sides], 0)
            t = _unit(t + fbE[:, None] * (_unit(H.smooth(t, int(P["imfHS"]))) - t))
            wn = np.maximum(wn, fbE)
        live = (np.linalg.norm(D, axis=1) > 1e-6) | (wn > 1e-4)
        shs = joint[key][2][side] if key in joint else None
        if shs is not None:
            live &= shs > 1e-4
        samp[key + "_" + side] = (_rest(B, D), wts, t, live, shs)
        log("SCULPT %s %s: A %.1f az %.1f, posed move max %.1f mm, %d points" % (
            key, side, A, az, 1000 * np.linalg.norm(D, axis=1).max(), int((np.linalg.norm(D, axis=1) > 1e-4).sum())))
    for key in ("show", "low"):
        Dr, wr, tr, lr, _ = samp[key + "_r"]
        lm = ph.mirror(b, np.repeat(lr[:, None], 3, 1).astype(float))[:, 1] > 1e-3
        samp[key + "_l"] = (ph.mirror(b, Dr), wr, np.where(lm[:, None], _unit(ph.mirror(b, tr)), H.Ns), lm, None)
    rest = {}
    for side in "lr":
        # the level slot alone at the lowered key; its share taken off the other keys
        Dl, wl, _, _, _ = samp["low_" + side]
        rest["lvl80_" + side] = Dl / max(wl[LVL], 1e-6)
        log("SCULPT lvl80 %s: key weight %.2f" % (side, wl[LVL]))

        def less(key):
            D, wk, _, _, _ = samp[key + "_" + side]
            return D - wk[LVL] * rest["lvl80_" + side], wk
        # the A 117 pair: per point abd/flex so each key's weights give back its sculpt (2 x 2, the same for all points)
        (Ds, ws), (Dc, wc) = less("show"), less("cast")
        Wm = np.array([[ws["shoulder_abd117"], ws["shoulder_flex117"]], [wc["shoulder_abd117"], wc["shoulder_flex117"]]])
        Wi = np.linalg.inv(Wm)
        rest["abd117_" + side] = Wi[0, 0] * Ds + Wi[0, 1] * Dc
        rest["flex117_" + side] = Wi[1, 0] * Ds + Wi[1, 1] * Dc
        log("SCULPT 117 %s: key weights abd/flex show %.2f/%.2f cast %.2f/%.2f (level %.2f/%.2f)" % (
            side, *Wm.ravel(), ws[LVL], wc[LVL]))
        D150, w150 = less("cast150")
        tot = sum(w150[k] for k in SLOTS150)
        rest["150_" + side] = D150 / max(tot, 1e-6)
    keys = {k: (v[1], v[2], v[3], v[4]) for k, v in samp.items()}
    return b, rest, keys


def slot_normals(Ns, w, keys, side):
    """{group: unit normal per point} for one primitive's normals Ns (its welded ids w): each slot's normal solved so
    Godot's blend (base x (1 - sum w) + sum w x slot normal, then skinned) points along the key's target at every key
    (the level slot from the lowered key, the 117 pair from the show and cast keys together, the 150 group from the
    old cast), so the light at each key is the sculpt's exactly; untouched points keep their own"""
    def kw(key):
        wk, t, live, sh = keys[key + "_" + side]
        tw = t[w]
        if sh is not None:
            # (round 8) a joint key: this side's slots turn her normal its share of the way to the one sculpt's (the
            # two sides' blends add up to it)
            tw = _unit(Ns + sh[w][:, None] * (tw - Ns))
        return wk, tw, live[w]
    out = {}
    wl, tl, ll = kw("low")
    out["lvl80"] = np.where(ll[:, None], _unit_toward((1 - sum(wl.values())) * Ns, wl[LVL], tl), Ns)
    (ws, ts, ls), (wc, tc, lc) = kw("show"), kw("cast")
    cs = (1 - sum(ws.values())) * Ns + ws[LVL] * out["lvl80"]
    cc = (1 - sum(wc.values())) * Ns + wc[LVL] * out["lvl80"]
    Wm = np.array([[ws["shoulder_abd117"], ws["shoulder_flex117"]], [wc["shoulder_abd117"], wc["shoulder_flex117"]]])
    ua, uf, good = _pair_toward(cs, cc, Wm, ts, tc)
    lv = (ls | lc)[:, None]
    out["abd117"], out["flex117"] = np.where(lv, ua, Ns), np.where(lv, uf, Ns)
    w5, t5, l5 = kw("cast150")
    c5 = (1 - sum(w5.values())) * Ns + w5[LVL] * out["lvl80"] + w5["shoulder_abd117"] * out["abd117"] + w5["shoulder_flex117"] * out["flex117"]
    out["150"] = np.where(l5[:, None], _unit_toward(c5, sum(w5[k] for k in SLOTS150), t5), Ns)
    return out, int((~good & lv[:, 0]).sum())


def run(src, dst):
    G = _Gl(src)
    g = G.g
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    names0 = list((mesh.get("extras") or {}).get("targetNames", []))
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    assert len(prims) == len(mesh["primitives"])
    # pit_hollow_post's shapes in these slots off first (the sculpt replaces them; accessors left unreferenced)
    keep = [i for i, n in enumerate(names0) if not n.startswith("shoulder_")]
    if len(keep) < len(names0):
        print("SCULPT: replacing", len(names0) - len(keep), "shoulder shapes")
    for p in prims:
        p["targets"] = [p["targets"][i] for i in keep] if p.get("targets") else []
    w0 = list(mesh.get("weights", [0] * len(names0)))
    names = [names0[i] for i in keep]
    weights = [w0[i] for i in keep]
    b, rest, keys = build(G)
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    acc = {key: [] for key in rest}
    o = 0
    for p in prims:
        n = g["accessors"][p["attributes"]["POSITION"]]["count"]
        w = b.wid[o:o + n]
        o += n
        Ns = _unit(G.get(p["attributes"]["NORMAL"]).astype(float))
        for side in "lr":
            un, bad = slot_normals(Ns, w, keys, side)
            if bad:
                print("SCULPT normals %s: %d points kept the normalised linear pair" % (side, bad))
            for grp, u in un.items():
                key = grp + "_" + side
                Dp = rest[key][w]
                dNp = u - Ns
                ip = np.nonzero(np.abs(Dp).max(1) > 1e-7)[0]
                inn = np.nonzero(np.abs(dNp).max(1) > 1e-6)[0]
                acc[key].append((_sparse(g, binb, n, ip, Dp[ip]), _sparse(g, binb, n, inn, dNp[inn])))
    added = []
    for nm, grp in [(n, n.replace("shoulder_", "")) for n in SLOTS117] + [(n, "150") for n in SLOTS150] + [(LVL, "lvl80")]:
        for side in "lr":
            for pi, p in enumerate(prims):
                pa, na = acc[grp + "_" + side][pi]
                p.setdefault("targets", []).append({"POSITION": pa, "NORMAL": na})
            added.append(nm + "_" + side)
    for p in prims:
        assert len(p["targets"]) == len(names) + len(added)
    mesh.setdefault("extras", {})["targetNames"] = names + added
    mesh["weights"] = weights + [0] * len(added)
    g["asset"].setdefault("extras", {}).pop("pit_hollow", None)
    g["asset"]["extras"]["shoulder_sculpt"] = {"keys": [k + " " + s for k, s in KEYS],
                                               "params": {k: v for k, v in P.items()}}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("SCULPT shapes", len(added), "->", dst)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if os.environ.get("SHOULDER_SCULPT", "0") != "1":
        shutil.copyfile(a[0], a[1])
        print("SCULPT off (SHOULDER_SCULPT=1 builds it): copied")
    else:
        run(a[0], a[1])
