# split_size: sizing the split spaulder (10 Nov)

Source: `tools/armor/split_size.py` importing body-p1b@61244c52f `tools/body/ride_travel.py` (her_tracks, extended patch
s -88..+154 mm, theta 21..172, 558 L / 541 R points; 91 frames; sphere t 0..1 step 0.1; extra rides trap + upperarm_twist_01..04).
Outputs here: sweep.json (every box, ref, surface, side, ride family), table.txt, partition.json, tracks.npz (cache), run.log.
Runtime: cache 110 s, sweep 887 s (CPU, numpy/scipy). Floor check: P1's cap_top zone from first reproduces P1 exactly
(NEW L sink 18.53 / travel 23.47, R 12.91 / 21.71: measured).

Numbers: mm, max over 91 frames and points. sink = skin up into the plate, gap = plate lifting off, spread = sink + gap
(no seat height changes it; the line "sink <= 5 and gap <= 8 at some seat height" = spread <= 13). All MEASURED unless marked.
Ride families: bones = share blend of clavicle/upperarm/upperarm_share/delt/scap (LP on shares, the brief's set);
+sph = one sphere turn added; all = + trap + 4 upperarm twists. FLOOR = per-frame Kabsch fit of the piece's own points.

## 1. Headline: no bone blend carries a cap-top piece; the plate must ride a skin-fitted frame
NEW, ref first (Prowl), best realistic ride, both sides max spread (sink L/R):
- P1's cap_top zone (-45..36, th 60..130): 29.2 (sink 14.3/17.9), floor 22.9. Dead either way.
- Best cap boxes with s0 >= -45, any width: (-45,-20,85..135) 13.3 (12 pts); every other s0 15-22. Floor on the same boxes 1.5-4.5.
- Only passing caps on a bone blend: s -60..-35 (the neck end!), th 70..150, 21 pts, spread 12.8, sink 4.9/5.9, gap 6.2/7.0, `all` sph0.
- 20 mm full-wrap lames, realistic spread: s 0..30 ~37-38, s 40..120 17-20, 130..150 8.1, 140..154 4.7. Pass only s >= 130.
- The gap between floor and best blend on small cap pieces is 3-5 vs 13-22: the right rigid motion exists, no blend of
  these bones reproduces it. INFERRED design consequence: articulated pieces should ride a frame fitted to her skin under
  each piece (rivet / Kabsch of a few skinned vertices per piece, runtime-cheap), not bone shares. Below is sized on that (FLOOR).

## 2. Proposed partition (NEW, ref first; FLOOR ride = skin-fitted per piece; s mm, theta deg)
| piece | box s / theta | pts L/R | sink L/R | gap L/R | spread L/R | travel L/R |
|---|---|---|---|---|---|---|
| A neck-cap | -45..-10 / 35..172 | 57/57 | 4.4/7.2 | 5.8/4.9 | 10.2/12.1 | 13.0/13.9 |
| B cap top | -10..+10 / 70..150 | 12/13 | 2.2/2.1 | 1.5/1.8 | 3.8/3.9 | - |
| C cap top | +10..+30 / 70..150 | 18/17 | 4.0/4.6 | 2.6/2.7 | 6.6/7.3 | - |
| D cap top | +30..+50 / 70..150 | 14/14 | 9.8/5.2 | 2.3/2.2 | 12.1/7.4 | - |
| L1..L5 lames | 50-70, 70-90, 90-110, 110-130, 130-154 / 21..172 | 42-69 | 4.7, 5.1, 3.7, 2.3, 3.6 (L) | <=6.1 | 10.6, 9.5, 6.7, 4.5, 5.5 (L); R 10.0, 9.3, 6.5, 4.5, 5.0 | 4.6-10.6 |
A and D, and L1/L2, need a seat (standoff) to get sink <= 5: lift by sink-5 (A R +2.2, D L +4.8) while gap stays <= 8.
Bone-blend fallback measured passing (NEW first): lame s 130..154 `all`, sph0 (spread 8.1; shares in sweep.json) and
140..154 (4.7). Bone shares for A-D/L1-L4 are reported in sweep.json but none passes; I do not propose them.

## 3. Not steel (NEW first, FLOOR, full arming leather/skinned)
- Front and back of the deltoid: s -10..+50 at th 35..70 (spread 17.6 L / 21.6 R) and th 150..172 (19.6 / 15.2): fail even rigid-fitted.
  Small front strip -10..15 th 35..70 passes (4.0/6.1, 9 pts: too few to trust; INFERRED leather).
- Full-wrap bands s -10..+50 (floor 16-21 per 20 mm band): no rigid wrap; the deltoid band is steel on top only (B-D).
- Neck end s < -45: P1 measured travel 35-42; s -60..-35 is the one box where even bones pass (12.8). INFERRED: skinned leather
  below -45 (as the arming), or extend A to -60 (not measured as one box).

## 4. Overlaps (relative motion of neighbours at the shared edge, points within 6 mm, both skin-fitted; total / along normal)
- first L: A|B 16.9/4.9, B|C 15.6/7.9, C|D 16.8/9.8, D|L1 11.6/8.0;  R: 18.2/5.9, 16.9/11.2, 13.8/7.5, 10.7/6.2
- lames (first, coarse chain, the L1 edge was 30 because the middle was one piece then): 70: 6.9 L/10.7 R, 90: 2.8/6.1,
  110: 5.2/8.6, 130: 11.0/18.4, 150: 7.2/10.6.
- INFERRED sizing: overlaps of ~18 mm (cap pieces, A..L1) and ~11-18 mm (lames; 130 edge worst) in the sliding direction,
  normal parts up to 11 mm say the upper piece's edge must sit over the lower with clearance or a flare.
- Edge point counts are 7-11 per cap edge: thin samples.

## 5. Rest vs first
NEW floor numbers barely change (A spread 9.2 rest vs 10.2 first; B-D within 1-2 mm; lames similar or better at rest).
Bone blends DO change: from rest small caps pass on bones (36 boxes, e.g. -60..-25 th 41..151, 12.0) and the realistic
cap-top check is 23.5 vs 29.2. So with a skin-fitted ride the seat pose barely matters (pieces can be built at rest);
with bone shares they must be seated in the stance and still fail. PUB (today's skin) is easier everywhere below the cap
(lame 90..150 bone spread 4.6 from first) and harder at the top (cap_top 40.8): pub vs new disagree most where P1 is changing her.

## Unverified
- No mesh: boxes are skin-point boxes, not plate outlines; 12-20 points per cap piece (mesh resolution).
- The skin-fitted ride is the floor of each piece's own points; a runtime rivet on 3-4 vertices is assumed close (not measured).
- NEW is P1's target, not a skin; no weights exist yet.
