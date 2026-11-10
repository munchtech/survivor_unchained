# Neck fit: neck + head stump skin weights fitted to Her's target (10 Nov, helper for the P1 lead; nothing published)

Script `tools/body/neck_fit.py` (CPU numpy/scipy). Output `tools/body/out/neck_fit/fit.npz` (ids = free vertices, J/W top 8,
lam, key = sha of carried_target.py + poses.npz); targets cached in `target.npz`; logs `fit_check.log`, `neck20.log`.
Numbers below are on carried_target at 1c23d317a (neck relax in), 141 poses of out/shoulder/poses.npz, lam 100.

## Method
- Free set: welded points of the `neck` region + head vertices with Head < 0.999 (5156 points, 5553 vertices, 701 on the head).
  A point is free only if every copy is; the head ring copies share the body ring's point, so the seam steps 0. Held: Head >= 0.999.
- Bones per point: every bone it already has over 0.01, then neck_01, spine_05, neck_02, Head, spine_04 while under 8 (the GLB's 8).
  spine_04 is barred above the ring (y > 1495 mm, |x| < 90 mm, section 7's proxy line).
- Data: with sum w = 1, posed - target = sum_b w_b (S_b p - y): one quadratic per point over the 141 poses (copies and correctives
  in), mean squared mm per pose. Smoothness lam * |w_i - w_j|^2 / l_mm over welded edges (held neighbours as constants).
  Sum = 1 by a stiff row, w >= 0 by an exact block active-set on the sparse normal equations (SuperLU; 35 rounds, KKT 0).
- Target = `compose(G, ["neck"])` (published + the neck's delta). The full compose adds the girdle deltas, up to 80 mm on the
  shoulder tops the neck region reaches (x +-205 mm; neck_01 > 0.02 there); fitting those into neck weights tore the border
  (first try, 65 mm). They stay the girdle's: check rows "fitted+deltas" = fitted skin + (full - neck target).

## The six numbers (fitted | published | target)
1. skin vs neck target, mm mean / p95 / max: 0.55 / 2.36 / 12.95 | 2.59 / 11.79 / 60.43. Worst: heroic_leap@7:r 13.0, @9:r 12.4,
   @12:r 11.9, @6:r 11.9, iron_vow@72:l 9.1. Fitted+deltas vs full target the same; published vs full 5.48 / 20.81 / 83.90.
2. edge-poses over 2.5x, neck set + head piece (64707 edges): fitted+deltas 425, max 4.48 | published 8054, max 11.68 | target
   417, max 4.47 (worst fitted+deltas = the target's own: x:abd150:l y1423, heroic_leap@7:r y1487-1495, Jog_Fwd y1452).
   Fitted skin ALONE 4370, max 8.93: all on the shoulder tops (e4144-4145 x 153 y 1521 iron_vow@72:l, published 9.21 there),
   the girdle's rows, not the neck.
3. seam gap, body ring (96) vs head copies, max over 141 poses: 0.0 mm (fitted and published).
4. weights array_equal where Head >= 0.999 and off the free set: yes; head rest / order unchanged: yes (no GLB write).
5. VERDICT 2: spine_04 above ring 0.000 (pub 0.934); worst F drop up an edge |x|<70 0.028 (pub 0.925, proxy 0.12);
   max dw/mm neck_01 0.006 / neck_02 0.008 / Head 0.019 (pub 0.190 / 0.034 / 0.044; target < 0.03). All met.
6. neck20 under the fit (`neck_fit.py neck20`, pit/trap/nape, bar max(2.5, A + 0.15)):
   neck_01 alone, largest passing: flex >= 60, extend 40, side 50, twist >= 60 (proxy n=4: 60 / 40 / 50 / 40). Extension binds at
   the PIT now (2.43 at 40, 2.76 at 50; trap 2.17 / 2.46), side at the pit too (2.52 at 60).
   Seven clips, worst pit/trap/nape, frames over: keyed | 20/30/50
   idle_warden_town 1.99/2.03/1.66 (0) | 1.28/1.29/1.14 (0); iron_vow 1.78/1.78/1.34 (0) | 1.84/1.79/1.14 (0);
   bladestorm_loop 1.93/1.94/1.32 (0) | 1.55/1.53/1.23 (0); heroic_leap 1.63/1.67/1.54 (0) | 1.63/1.57/1.46 (0);
   shield_charge 1.71/1.73/1.34 (0) | 1.46/1.46/1.17 (0); run_warden 1.38/1.39/1.17 (0) | 1.18/1.15/1.09 (0);
   run_warden_town 1.43/1.40/1.12 (0) | 1.21/1.21/1.10 (0). Published keyed: 20-163 frames over on every clip.
   Section 7's rule (neck_01 <= 40 deg, flexion to 60) holds on the fit.

## Commands (from the worktree root)
`python tools/body/neck_fit.py fit [--lam 100] [--reuse]` (fit + check; ~4 min when carried_target changed, else ~1 min;
--reuse keeps cached targets whatever the key), `... check`, `... neck20` (~6 min).
Hook: `neck_fit.skin(V0, (J, W) or dense W, G, bd)`; `neck_fit.load_fit(bd)` -> full dense W with the fit written in.
lam 30 / 100 / 300 moved item 1 by < 0.1 mm mean, 0.5 mm max (measured on an earlier bone set); the residual is LBS's.
