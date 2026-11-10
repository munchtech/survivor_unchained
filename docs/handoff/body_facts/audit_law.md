# deform_audit: B's clavicle by the girdle law (10 Nov)

**Changed** (`tools/body/deform_audit.py`, db6e6f668): `Body.pose_rig(d)` + `Body.clavicle` ("frozen" default for importers; the
audit's runs set "law"). Under law, every B pose the audit measures (ROM, clip frames, all layers, Bplay) is driven with
`law_rig` where the clip leaves the clavicle unkeyed (`unkeyed`, bone names from rig.json `girdle.clavicle`); ROM always.
New flags: `--clavicle law|frozen`, `--cols`, `--p4`, `--rom <prefix>` (merges), `--compare old.json --compare-out f`.
Test `test_clavicle_law_and_frozen` (13 green). A's side untouched; `out/audit/audit.json` and brief_full.txt untouched.

**Commands** (1 worker; new json in `tools/body/out/audit_law/`, seeded with a copy of the old audit.json):
- `python tools/body/deform_audit.py --only rom --rom sh_ --cols B.full,B.nocorr,B.nolaws,Bplay.full --procs 1 --out tools/body/out/audit_law` (1 min)
- `... --only p4 --cols B.full --procs 1 --p4 bladestorm_loop,heroic_leap,iron_vow,run_warden,run_warden_town,shield_charge,walk_warden,walk_warden_town --out tools/body/out/audit_law` (5 min)
- `... --only none --out tools/body/out/audit_law --compare tools/body/out/audit/audit.json --compare-out tools/body/out/audit/overhead_old_new.txt`
- `python tools/body/deform_brief.py tools/body/out/audit_law/audit.json > tools/body/out/audit/brief_law.txt`

**NOT re-measured** (rows in the tables are copies of the old numbers): (the four idles on B.full WERE re-measured after this was written, about 12 min, and both tables refreshed: their rows
are in overhead_old_new.txt, not summarized here; idle_fight_a / _b have no old row) p4 on B.nocorr / B.nolaws / Bplay
(`--only p4 --cols B.nocorr,B.nolaws,Bplay.full`, about 50 min), the 33 library dumps (their clavicle: not checked here).

**B.full, old (frozen) | new (law) | A.full** (full table, Bplay too: `out/audit/overhead_old_new.txt`)

| row | ball st99 % | ball kink99 | ball flip % | ball bad % | axilla st99 % | axilla bad % | at_mm |
|---|---|---|---|---|---|---|---|
| sh_abd135 | 166 / 154 / 114 | 81 / 80 / 41 | 1.22 / 1.06 / 4.15 | 5.5 / 7.1 / 10.7 | 188 / 218 / 146 | 8.1 / 15.1 / 14.7 | 0 / 0 / 0 |
| sh_abd170 | 219 / 222 / 113 | 108 / 93 / 37 | 2.56 / 2.40 / 6.81 | 9.3 / 12.4 / 10.7 | 223 / 277 / 151 | 11.1 / 20.2 / 14.9 | 0 / 0 / 0 |
| sh_flex135 | 232 / 251 / 96 | 128 / 140 / 40 | 4.71 / 4.45 / 6.10 | 8.1 / 9.8 / 11.3 | 183 / 240 / 113 | 11.0 / 16.3 / 11.9 | 0 / 0 / 0 |
| sh_flex170 | 284 / 298 / 144 | 131 / 127 / 49 | 5.54 / 4.38 / 6.57 | 10.3 / 12.4 / 12.1 | 217 / 283 / 171 | 14.4 / 18.5 / 12.9 | 0 / 0 / 0 |
| sh_abd90 | 70 / 75 / 86 | 64 / 48 / 32 | 0.64 / 0.29 / 0.15 | 2.1 / 2.2 / 5.5 | 96 / 128 / 86 | 3.6 / 3.2 / 9.3 | 0 / 0 / 0 |
| sh_flex90 | 102 / 103 / 83 | 111 / 112 / 61 | 2.11 / 2.37 / 1.79 | 11.2 / 11.6 / 16.0 | 139 / 160 / 89 | 14.7 / 13.1 / 14.2 | 0 / 0 / 0 |
| sh_hadd40 | 162 / 166 / 87 | 119 / 129 / 60 | 5.47 / 5.67 / 5.71 | 14.4 / 15.2 / 19.8 | 155 / 176 / 90 | 14.5 / 15.6 / 18.8 | 10.9 / 5.8 / 2.4 |
| p4:iron_vow @72 | 313 / 337 / - | 153 / 149 / - | 12.6 / 14.1 / - | 21.8 / 23.5 / - | 229 / 268 / - | 28.0 / 29.1 / - | 29.4 / 29.8 / - |
| p4:heroic_leap @12 > @13 | 254 / 314 / - | 132 / 149 / - | 5.41 / 6.82 / - | 14.4 / 18.9 / - | 237 / 288 / - | 15.3 / 34.6 / - | 29.8 / 10.2 / - |
| p4:shield_charge @15 > @3 | 205 / 182 / - | 144 / 135 / - | 4.58 / 3.49 / - | 16.6 / 14.5 / - | 154 / 170 / - | 15.6 / 18.2 / - | 29.8 / 6.1 / - |
| p4:bladestorm_loop @25 > @28 | 120 / 119 / - | 116 / 110 / - | 1.67 / 1.25 / - | 5.6 / 4.9 / - | 117 / 114 / - | 8.5 / 7.2 / - | 12.3 / 14.7 / - |

Walk and run clips: within 5 points of st99 and 1 point of bad either way. sh_abd45, sh_ext40, twists: within 4 points.

**Verdict.** The frozen clavicle did NOT overstate B's overhead stretch: on equal kinematics the overhead rows read the
same or WORSE. Overstated by the frozen pose (old > new): the arm-under-torso depth at_mm (shield_charge 29.8 > 6.1,
heroic_leap 29.8 > 10.2, sh_hadd40 10.9 > 5.8; A 2.4), kink99 at sh_abd90 (64 > 48) and sh_abd170 (108 > 93), kinkmax at
sh_abd45 / sh_ext40 (30 > 21, 68 > 47), flips at sh_flex170 (5.54 > 4.38) and sh_abd90, shield_charge's ball st99 (205 > 182).
Understated (new is worse): axilla st99 at every raised pose (+30 at abd135, +54 at abd170, +57 at flex135, +66 at
flex170, +32 at abd90) and axilla bad % overhead (abd170 11 > 20, abd135 8 > 15, flex135 11 > 16); ball st99 on
heroic_leap (254 > 314) and iron_vow (313 > 337), heroic_leap's axilla bad 15 > 35; ball bad % up 1.6 to 3 points overhead.
Rows that stand, still worse than A: every overhead row on st99 (ball about 2x A, axilla 1.5 to 2x) and kink99 (2 to 3x);
B's flips stay below A's at abd135/170 and flex135/170. New against A: axilla bad % at abd170 and flex135/170 now reads
worse than A (20 vs 15, 16 vs 12, 19 vs 13) where the old audit read better; ball bad % at abd170 and flex170 now a little
over A's. Likely cause to check: the correctives and weights were fitted with the clavicle frozen.

**clav / neck.** clav slope (B old > new, A): sh_abd170 st99 84 > 93 (A 29), sh_flex170 70 > 68 (A 29), kinkmax 45 > 53 and
86 > 128. The neck region moved a little, not zero: iron_vow st99 298.6 > 297.2, heroic_leap 146.4 > 156.1 (flip 2.08 > 2.90).
All non-shoulder ROM rows are identical old to new (checked).
