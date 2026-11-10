# Why the carried target's edges stretch (9 Nov, helper for P1 lead 16)

`python tools/body/region_shape.py edges --provider carried [--poses a,b] [--over 2.5]` -> `tools/body/out/shoulder/edges_carried.json`
(per over-stretched edge: side, zone, class, worst pose, the four ratios, bridge measure, rows needed; table; five worst poses a zone
with the bones' local turns). 141 poses, target_a.npz equals the live blend (0.000 mm). 730 edges are over 2.5x in some pose.
Each edge is classed once, at its worst pose; the rule is `classify_edges`' docstring (pocket, published, A's own, border blend,
bridge, carrier, first that holds). Zone = the named band, else border rows by what bounds them + the rest normal's facing.

| zone | class | edges l / r | worst | poses over |
|---|---|---|---|---|
| border midline back | published / border blend / carrier | 3/3, 9/8, 2/2 | 4.61, 3.88, 4.05 | 13, 9, 9 |
| border midline top (throat pit) | published / border blend / bridge / carrier | 14/13, 1/1, 1/1, 1/1 | 9.10, 3.44, 6.09, 7.31 | 49, 7, 20, 23 |
| border open seam back (neck top) | border blend | 18/15 | 4.62 | 18 |
| border open seam front | published / border blend | 0/1, 6/8 | 3.22, 4.32 | 1, 9 |
| border rigid trunk / arm back | A's own / border blend / bridge / carrier | 2/2, 80/103, 0/1, 10/2 | 2.86, 4.98, 2.66, 3.05 | 5, 32, 1, 2 |
| border rigid trunk / arm front | border blend | 13/37 | 5.39 | 30 |
| border rigid trunk / arm top | border blend / carrier | 1/2, 1/1 | 3.53, 4.31 | 7, 11 |
| breast_edge | published / border blend / carrier | 29/28, 20/25, 6/6 | 3.92, 5.28, 3.57 | 30, 51, 17 |
| trap_line (neck side, trap top) | published / border blend / carrier | 2/11, 49/64, 5/6 | 3.57, 6.35, 6.21 | 9, 57, 38 |
| deltoid_cap | A's own | 7/40 | 3.63 | 8 |
| fold_back | pocket / A's own | 1/2, 4/12 | 3.60, 3.43 | 6, 32 |
| fold_front | A's own | 0/3 | 2.62 | 2 |
| inner back | pocket / A's own | 8/6, 4/6 | 2.76, 2.93 | 5, 12 |
| inner front | pocket / A's own | 8/11, 0/4 | 3.33, 2.91 | 11, 11 |

Totals: border blend 460, published 104, A's own 84, carrier 43, pocket 36, bridge 3.

1. **A's own stretch (the floor): 84 edges, median 2.68x, max 3.63x (A itself 3.64x).** Deltoid cap 47 edges, worst 3.63 at
   p4:heroic_leap@7 / @9 / @12:r (arm 150-180 deg); back fold 16, worst 3.43 at x:flex120:l (over in 32 poses); inner back 10 (2.93),
   inner front 4 (2.91), front fold 3 (2.62), trunk-back border 4 (2.86). Nothing outside the border rows is anything but A's own
   or the pocket: the interior of the target is clean.
2. **The border blend makes 460 of the 730 (63%).** By border: trunk back (rest y 1.31-1.34 m, the lower / medial back) 183 edges,
   worst 4.98 at Jog_Fwd@11:r and 4.86 at @14:l (clavicle keyed 35-40 deg), carried against published up to 62.8 mm (p50 49.5),
   rows needed p50 13 (4 today); neck side / trap top 113, worst 6.35 at p4:idle_warden_town@122:l, 6.03 at @126:r, 6.21 at
   p4:iron_vow@75:r (neck_01 28-29 deg), disagreement up to 69.4 mm, rows p50 7.5; trunk front (front armpit / lateral breast side)
   50, worst 5.39 at idle_warden_town@126:r, rows p50 7.2, max 12.4; breast edge 45, worst 5.28 at Jog_Fwd@11:r, 5.23 at
   iron_vow@9:l, up to 67.8 mm, rows p50 8.6, max 16.8; neck top back 33 (4.62, rows 8.2 / 11.8); neck top front 14 (4.32, rows
   7.7 / 8.6); midline back 17 (3.88, rows 5.0 / 7.1). The arm side has none (the "rigid trunk / arm" name merges the two; these
   edges all sit on the trunk). Worst pose by clip: Jog_Fwd 212 edges, idle_warden_town 163, iron_vow 63, heroic_leap 16. Rows
   needed = disagreement / ((2.5 - the larger of the carried and published ratios) x rest edge): 124 of 460 fit in 7 rows, 286 in
   10; for 14 one of the two surfaces is already at 2.5x, so no row count cures them. Wider rows alone do not fix the back
   (13 rows): there the two surfaces must agree better (the keyed-clavicle Jog poses, the neck turn) or the share must follow the pose.
3. **Bridges the 60 deg rule misses: none real.** 3 edges trip the measure, at 2.3-2.6x the edge length along A (the vertex-graph
   path overestimates; A's edges are 4.8 mm against B's 6.3) with a straight gap of 1.0x: two at the throat pit are the published
   surface's stretch on a blend row (published 7.1 / 5.0, carried 0.99 / 1.04), one on the trunk back at 2.66 (A's own 2.06).
4. **The throat pit is the published surface alone.** 27 edges at share 0 (14 l / 13 r), worst 9.10 at p4:iron_vow@75:r, 8.47 at
   @72:l, 7.61 at @76:r; the carried ratio there never passes 1.07. Worst pose is iron_vow for 17 edges, idle_warden_town for 10;
   single edges stay over 2.5x in up to 27 poses (49 poses touch the zone). Turns from rest in those poses: neck_01 24-29 deg,
   neck_02 8-17, spine_05 0-4, clavicle 1-10: it follows neck_01's turn, not the clavicle or the arm (106 to 180 deg, no
   relation). The two rows above it (share 0.16) carry the same stretch into the target (7.31, 6.09). Other published-only
   stretch: breast edge ring rows 57 edges up to 3.92 (30 poses), midline back 6 up to 4.61, trap ring rows 13 up to 3.57.
5. **`carrier`: 43 edges, all "published-led blend row"**: the published ratio explains the target on a row with share < 1 while
   the carried ratio does not (breast edge 12, trunk back 12, trap line 11, midline back 4, throat 2, trunk top 2; worst 7.31).
   None is "carry over A" and none is unexplained: the carry itself is wrong nowhere.

Caveats: one class per edge at its worst pose only (an edge can be A's own in one pose and blend in another); zones by the
lower-share end; the bridge path is a vertex-graph bound, not an exact geodesic; B has no `head` bone by that name, so no head turn.
