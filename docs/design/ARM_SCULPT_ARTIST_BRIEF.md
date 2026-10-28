# Artist brief: the heroine's arms and shoulders (DRAFT, 27 Oct 2026)

Status: a DRAFT for the owner. Nothing is packaged or sent until the owner says yes to commissioning (main, 27 Oct). Owner: Body lead (armor-7). The work is for hire, and the result is ours outright with no credit line (memory: no-credit-assets).

## Why
The owner, on her bent arm at the town close-up: "that bend still just dosn't look feminine OR athletic - it just looks clunky like quaternus model or whatever". On her arm hanging, seen front 3/4: "armpit problems there too, and elbow". Three procedural rounds of mm-level edits (outline carves and pose correctives) were each invisible to blind judges at the game's camera (1 mm is about 0.9 px there). The arm needs a sculptor's eye on the forms as a whole, not more numbers.

## The target
A slim, toned, feminine athletic arm, in the class of an AAA heroine (TLOU2's Ellie, Horizon's Aloy, at a slimmer build). The read is the OUTLINE alternating wide and narrow:
- **Deltoid:** a teardrop cap narrowing to a V about 45% down the upper arm, a visible change of slope (not a ring, not a ball). Its volume goes down and forward, not outward: her shoulder width at the Look must not grow (about 2.7 head widths).
- **Front armpit:** a soft anterior axillary fold, a wedge 25-35 mm wide from the pec's lower border into the arm, visible above the breast's outer upper edge. Today the arm looks plugged in behind the breast.
- **Upper arm:** a gentle biceps belly, the triceps' back line, then a NARROW point above the elbow (the lower third at about 75-80% of mid-arm depth, a flat triceps tendon).
- **Elbow:** bony. The olecranon a point 15-20 mm wide, the epicondyles as small side bumps. End-on it reads as a triangle, not a dome.
- **Forearm:** the brachioradialis/extensor swell on the thumb side, high (peaking 30-50 mm below the joint), tapering to a flat narrow wrist (depth about 0.65 of width; the widest point at least 1.4x the wrist).
- **Never:** thin dark lengthwise grooves (the owner earlier failed "weird vein looking things on each arm"), a twisted-skin look, bulk.

## What we hand over (once the owner says yes)
- Her body mesh: `godot/art/people/heroine.glb`, two body primitives (40,816 + 3,697 vertices), a 100-bone skeleton, with UVs, vertex colors and two weight sets. A .blend with the rig, her textures packed, and nothing else in the scene.
- **The 9 game poses** as a pose library in that .blend: the town idles (warden hand on hip, stalker, reaver, reaver town) and the Look's stance. Each comes with the game camera matched, so the artist sculpts looking through the player's own camera: w_p45, w_m45, w_p80, w_m80, s_p45, r132_p45, r132_m45, rL90_m45, look_f.
- The owner's crops (`survivorsunchained_inputs\owner_frames_27oct\elbow_bend.png`, plus the front 3/4 described above), and the before frames from those cameras.
- Our existing correctives, for reference only: the shoulder raise shapes (`shoulder_*`), `elbow_point_l/_r`, and the reaver garment shape `worn_reaver`.

## Deliverables
1. **A rest-pose sculpt** of both arms, the shoulder join and the armpit, as a shape key on her mesh. Hard rules: the SAME vertices in the same order, UVs untouched, no retopology. Left and right are mirrored, apart from the asymmetry her pose library needs. The neck, breasts and torso are not moved beyond a 30 mm feather into the shoulder and armpit.
2. **Elbow correctives** at flexion 45, 90 and 135 (shape keys per side; we drive them from her elbow's flexion as in-betweens, our `ElbowPsd` drive). They give the biceps bunching a little, the inner crease a short soft slanted fold (no V, no ring), the forearm mass rising over the crease on the thumb side, the outer corner an angle with a bony point (radius 8 mm or less at 90), and no volume loss.
3. **A check of the arm-down armpit** in the warden and stalker town idles. If the rest sculpt can't hold it there, add one corrective at arm-down/forward (`shoulder_lvl0`).
4. Optional: a tangent-space detail normal for the arm (soft forms only, 20 mm or wider). We can bake it ourselves.
Our side afterwards: re-run the shoulder raise shapes on the new rest, re-fit the outfits (body follow), re-key the garment tuck records, LODs, the dressed judge and the owner's A|B.

## Acceptance
- At the game's own cameras at 1:1 (the town close-up, the Look), a fresh viewer picks the new arm at a glance in every frame where the arm shows (our blind judge: 9 of 9).
- Outline moves of roughly 12-20 px at the town close-up where the forms change. The Look's shoulder width stays the same (within ±3 px).
- No folded or kinked faces at any of the 9 poses, or across the elbow's range from 0 to 145.
- Then the owner sees the bare A|B at their two crops, before any outfit work.

## Rough scope (an experienced character artist)
| Piece | Hours |
|---|---|
| Rest sculpt (deltoid, armpit, arm, forearm, wrist) | 8-12 |
| Elbow correctives 45/90/135 (both sides) | 5-8 |
| The arm-down armpit check or corrective | 2-4 |
| Two revision rounds against our judge and the owner | 4-6 |
| **Total** | **about 20-30** |

Our own token cost: about 100k to package, then about 300-400k to wire it in (correctives drive, chain, tuck re-key, judge, MR).
