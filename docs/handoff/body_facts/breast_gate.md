# Breast-top gate on Jog_Fwd (judge fix 3), solver for lead 21, 10 Nov: NOT MET, the rule built and left inert

## Measure chosen: B's published stretch on the gate's own rows (not the clavicle)
- `Her.gate_open(G, side)`: smoothstep over `stretch` [lo, hi] of the worst edge ratio (posed / rest) of B's PUBLISHED surface of the whole pose on the first gate's own rows (closed share 0, opened > 0; 535 edges a side). `Model.blend` takes max(elevation's g, this g). Where this is at or under the elevation's g, the share is bit for bit.
- Why not the clavicle: Jog's clavicle turn (spine_05 frame) is 35-40 deg on every frame and its lift is only 5-7 deg, but the published stretch swings 3.1x-8.6x with the arm's swing in the same clip (frames 4-5 and 17-18 are the lows). The clavicle doesn't key the tear. The stretch is continuous in the pose (a max of edge lengths), so it never pops. On Jog every frame (29, both sides) it sits over 2.5, so the share is 1.0 flat.
- Config: support `"open": {"stretch": [1.8, 2.5]}`. ABSENT (inert, like depinch): without the key the target is unchanged, bit for bit. Code: `Her.gate_open`, `Her.gate_shut` (shut = under lo and opening 0, used by cmd_target's shut report and T16), `Her.open_off` (T18 runs inside it with map_off), T25 (runs only with the key), `region_target.Model.blend` (the `open` hook).

## Why it doesn't fix Jog (measured with the key on, clip Jog_Fwd, every frame)
- With the first gate fully open (share 1.0 on all 29 frames), the composed breast-top max is still the published one: frame 14 l 7.91 = 7.91, frame 0 r 8.61 = 8.61. Only the frames near the 3.1x lows drop (frame 4 l 3.13 -> 2.16).
- The torn edges are on the gate's RAMP rows, not its open rows. Jog_Fwd@14:l: 5931-6017 pub 7.91 (opened share 0.074 / 0.020), 2605-5930 6.13, 5932-6018 5.35 (0.156 / 0.074), 5930-5931 4.20, 5933-6019 3.92. Jog_Fwd@11:r: 21481-21547 9.23 (share 0.26 / 0.16, not gated), 24889-24975 7.68. These are gate2's own two edges (6017-6018, 5932-5933; the twins on r). Only gate2 (0.79-0.89 there, opened over 90-130 deg) carries them, and its relax rule fills them.
- A's own (carried) on the gated part: 1.95-2.08 on every frame. That is the floor the shape can reach.
- Jog_Fwd@14:l side l: 40 region edges composed over 2.5, 7 on the gated part. @11:r: 26 and 4.

## What would fix it (the next attempt)
1. The opening must drive the share on the ramp rows, not the first gate's value. Either (a) the stretch g also opens gate2 (its share 0.8 there plus its relax rule, which took the same two edges 3.63 -> 1.44 at abd150), or (b) a stretch-keyed stage whose rows come out to the torn edges with share 1 and its border moved outward, past the rows where published tears.
2. Blending alone can't pass: at share 0.8, 0.2 x 7.9 + 0.8 x 2.0 is still about 3.2x. It needs share 1, or a relax fill on the torn rows in step with the opening (gate2's `relax`, ratio 2.5, rows 2).
3. Then measure: a 141-pose before/after count, region_shape edges and shift on a dev target, and T25 with the key on.

## Other poses the published stretch would open (published worst on the gate's own rows, share today, off side mostly)
crossbow_shoot@0:r l 4.59 (0.21), sword_back@8:r l 4.91 (0.17), axe_heavy@7:r l 4.30 (0), axe_back@10:r l 4.39 (0), axe_heavy@1:r l 3.85 (0), crossbow_shoot@10 l 3.97 (0), daggers_back@8:r l 3.23 (0), axe_back@12:l l 3.42 (0), sword_heavy@0:r l 3.71 (0), sword_back@4:l l 4.30 (0.04), daggers_fore@7:r r 3.54 (0), daggers_fore@3:l r 3.41 (0), run_reaver@0/@8/@11 2.7-2.9 (0), idle_arcanist_town@68:l r 2.21 (0). About 60 (pose, side) pairs are over 1.8 with share under 1. The region_shape "published" count (36 = Jog) reads each pose's own side only, so the off sides are not counted there.

## Numbers (a)-(e): not measured with the key on. Nothing changed, so the target is round 1's
Commands: `python tools/body/carried_target.py test` (key absent). The probes are in the session scratchpad: probe1.py (jog / all), probe3.py (torn edges).
