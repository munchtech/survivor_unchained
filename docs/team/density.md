# Fight density baseline

Measured 2026-11-11, source `ede4bf910` plus the density instrument. ARPG_FUN section 4, P0 item 3. Measurement only; no tuning.

```powershell
dotnet run -c Release --project godot/balance -- density --zones lowford,verge --bots human --seeds 2 --seed0 1 --tier 2 --level 5 --day 1 --date 2026-11-11 --revision ede4bf910
```

Low Ford uses the existing `zone` sim from wake to gate. The first story zone is Thornhollow Verge: the StoryPlay field-pack route, nearest pack then next nearest and back to the entry, with campaign pressing hands. The Verge starts on the stated level/day with starter gear; it is a separate run, not an imported Low Ford save. Quest camps encountered along the walk are measured too.

The clock is elapsed simulation seconds, including travel, loot time, scripted holds, falls and the headless film captions. Low Ford's play-only clock is shown separately. Enemy proximity is sampled every 1/60 s, including the opening and terminal stretches: a living hostile, excluding dying/burrowed foes, whose edge is within `Pilot.EngageRange` (the feet's actual current-build reach, including its ranged-foe rule). This geometric test does not require a clear sight line or a roused foe.

Low Ford groups come from `Encounters.Packs` (waves keep their beat ID) and its separately placed `Champions` keys. Verge groups are retained where its spawner makes them: one `Pack` call including mixed foes and its leader, or a quest crew's existing tag. Pooled identities include their spawn seed. Ungrouped kills still count toward KPM; singleton bosses and unassigned summons are not invented into packs.

Pack gaps use consecutive packs ordered by first positive-damage hit: the previous pack's final death to the next pack's first hit, only if the previous pack cleared. Negative gaps mean the fights overlapped. A positive gap can contain an intervening singleton boss fight; it is not proof of a quiet lull. Elite cadence is first hit to first hit between groups containing a non-boss elite. After-elite gaps are the same pack gaps restricted to elite groups; a final elite with no next encounter is unpaired, not a measured lull. Empty samples are `n/a`; median averages the middle pair; p90 is nearest rank. No missing elite is reported as a zero-second cadence.

| Run | Through / falls / skipped | Elapsed / play s | Kills / KPM | Pack gap s: median / p90 / max (n) | Elite interval s: median / max (n) | After elite gap s: median / max (n) | Longest no enemy s (start-end) | Ungrouped kills |
|---|---|---|---|---|---|---|---|---|
| lowford/warden/human/T2/s1, L1 day 1 | True / 0 / 0 | 352.18 / 307.07 | 157 / 26.75 | 5.75 / 28.87 / 118.15 (16) | 31.21 / 141.65 (8) | 4.43 / 118.15 (8) | 45.60 (182.73-228.33) | 35 |
| lowford/warden/human/T2/s2, L1 day 1 | True / 0 / 0 | 382.07 / 336.95 | 152 / 23.87 | 5.00 / 35.25 / 119.87 (17) | 36.52 / 123.50 (9) | 4.40 / 119.87 (9) | 48.67 (210.53-259.20) | 21 |
| verge/warden/human/T2/s1, L5 day 1 | True / 0 / 0 | 122.13 / 122.13 | 31 / 15.23 | 8.35 / 20.33 / 20.33 (7) | n/a / n/a (0) | n/a / n/a (0) | 19.18 (71.80-90.98) | 0 |
| verge/warden/human/T2/s2, L5 day 1 | True / 0 / 0 | 190.58 / 190.58 | 39 / 12.28 | 8.55 / 31.25 / 31.25 (8) | n/a / n/a (0) | n/a / n/a (0) | 41.43 (149.15-190.58) | 1 |

| Rhythm measure | Target to playtest | Today's observations |
|---|---|---|
| Last pack kill to next first hit | Next pack within 5-8 s | lowford s1: median 5.75 s, p90 28.87 s; lowford s2: median 5.00 s, p90 35.25 s; verge s1: median 8.35 s, p90 20.33 s; verge s2: median 8.55 s, p90 31.25 s |
| Elite first hit to next elite first hit | An elite pack every 60-90 s | lowford s1: median 31.21 s (9 encountered); lowford s2: median 36.52 s (10 encountered); verge s1: median n/a s (0 encountered); verge s2: median n/a s (0 encountered) |
| After each elite | A designed lull; duration to playtest | lowford s1: 6/8 paired exits have a positive gap; lowford s2: 8/9 paired exits have a positive gap; verge s1: n/a (no paired elite exits); verge s2: n/a (no paired elite exits) |
| Kills/min and longest empty stretch | Baseline; no numeric target picked | Per-run figures above and windows below |

| Run | Window s | Kills | Kills/min |
|---|---|---|---|
| lowford s1 human | 0.00-30.00 | 32 | 64.00 |
| lowford s1 human | 30.00-60.00 | 14 | 28.00 |
| lowford s1 human | 60.00-90.00 | 22 | 44.00 |
| lowford s1 human | 90.00-120.00 | 1 | 2.00 |
| lowford s1 human | 120.00-150.00 | 0 | 0.00 |
| lowford s1 human | 150.00-180.00 | 25 | 50.00 |
| lowford s1 human | 180.00-210.00 | 5 | 10.00 |
| lowford s1 human | 210.00-240.00 | 4 | 8.00 |
| lowford s1 human | 240.00-270.00 | 13 | 26.00 |
| lowford s1 human | 270.00-300.00 | 8 | 16.00 |
| lowford s1 human | 300.00-330.00 | 11 | 22.00 |
| lowford s1 human | 330.00-352.18 | 22 | 59.50 |
| lowford s2 human | 0.00-30.00 | 32 | 64.00 |
| lowford s2 human | 30.00-60.00 | 14 | 28.00 |
| lowford s2 human | 60.00-90.00 | 21 | 42.00 |
| lowford s2 human | 90.00-120.00 | 1 | 2.00 |
| lowford s2 human | 120.00-150.00 | 10 | 20.00 |
| lowford s2 human | 150.00-180.00 | 10 | 20.00 |
| lowford s2 human | 180.00-210.00 | 5 | 10.00 |
| lowford s2 human | 210.00-240.00 | 1 | 2.00 |
| lowford s2 human | 240.00-270.00 | 4 | 8.00 |
| lowford s2 human | 270.00-300.00 | 15 | 30.00 |
| lowford s2 human | 300.00-330.00 | 6 | 12.00 |
| lowford s2 human | 330.00-360.00 | 12 | 24.00 |
| lowford s2 human | 360.00-382.07 | 21 | 57.10 |
| verge s1 human | 0.00-30.00 | 9 | 18.00 |
| verge s1 human | 30.00-60.00 | 15 | 30.00 |
| verge s1 human | 60.00-90.00 | 1 | 2.00 |
| verge s1 human | 90.00-120.00 | 6 | 12.00 |
| verge s1 human | 120.00-122.13 | 0 | 0.00 |
| verge s2 human | 0.00-30.00 | 5 | 10.00 |
| verge s2 human | 30.00-60.00 | 15 | 30.00 |
| verge s2 human | 60.00-90.00 | 9 | 18.00 |
| verge s2 human | 90.00-120.00 | 0 | 0.00 |
| verge s2 human | 120.00-150.00 | 9 | 18.00 |
| verge s2 human | 150.00-180.00 | 1 | 2.00 |
| verge s2 human | 180.00-190.58 | 0 | 0.00 |

Windows are [start, end); a kill at the terminal instant belongs to the final window. The final partial window uses its actual duration. Sub-tick floating point drift at a 30 s boundary is snapped within 1e-8 s. JSON retains full precision, kill times, individual groups, gaps and elite intervals for inspection.

JSON output (git-ignored, one file per run):
- `godot/balance/out/density/20261111T0855201044789_lowford_warden_human_t2_s1.json`
- `godot/balance/out/density/20261111T0855201044789_lowford_warden_human_t2_s2.json`
- `godot/balance/out/density/20261111T0855201044789_verge_warden_human_t2_s1.json`
- `godot/balance/out/density/20261111T0855201044789_verge_warden_human_t2_s2.json`
