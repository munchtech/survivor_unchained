# Fight density baseline

Measured 2026-11-11, source `2dc76580b` plus the density instrument. ARPG_FUN section 4, P0 item 3. Measurement only; no tuning.

```powershell
dotnet run -c Release --project godot/balance -- density --zones lowford,verge --bots human --seeds 2 --seed0 1 --tier 2 --level 5 --day 1 --date 2026-11-11 --revision 2dc76580b
```

Low Ford uses the existing `zone` sim from wake to gate. The first story zone is Thornhollow Verge: the StoryPlay field-pack route, nearest pack then next nearest and back to the entry, with campaign pressing hands. The Verge starts on the stated level/day with starter gear; it is a separate run, not an imported Low Ford save. Quest camps encountered along the walk are measured too.

The Verge walk retains its player-radius path through combat pauses and uses it when a foe is separated by a wall. Its default wall-clock budget is 60 s; the regression test uses 20 s and 300 simulation seconds, with the stop reason, position and route progress included on failure.

The clock is elapsed simulation seconds, including travel, loot time, scripted holds, falls and the headless film captions. Low Ford's play-only clock is shown separately. Enemy proximity is sampled every 1/60 s, including the opening and terminal stretches: a living hostile, excluding dying/burrowed foes, whose edge is within `Pilot.EngageRange` (the feet's actual current-build reach, including its ranged-foe rule). This geometric test does not require a clear sight line or a roused foe.

Low Ford groups come from `Encounters.Packs` (waves keep their beat ID) and its separately placed `Champions` keys. Verge groups are retained where its spawner makes them: one `Pack` call including mixed foes and its leader, or a quest crew's existing tag. Pooled identities include their spawn seed. Ungrouped kills still count toward KPM; singleton bosses and unassigned summons are not invented into packs.

Pack gaps use consecutive packs ordered by first positive-damage hit: the previous pack's final death to the next pack's first hit, only if the previous pack cleared. Negative gaps mean the fights overlapped. A positive gap can contain an intervening singleton boss fight; it is not proof of a quiet lull. Elite cadence is first hit to first hit between groups containing a non-boss elite. After-elite gaps are the same pack gaps restricted to elite groups; a final elite with no next encounter is unpaired, not a measured lull. Empty samples are `n/a`; median averages the middle pair; p90 is nearest rank. No missing elite is reported as a zero-second cadence.

| Run | Through / falls / skipped | Elapsed / play s | Kills / KPM | Pack gap s: median / p90 / max (n) | Elite interval s: median / max (n) | After elite gap s: median / max (n) | Longest no enemy s (start-end) | Ungrouped kills |
|---|---|---|---|---|---|---|---|---|
| lowford/warden/human/T2/s1, L1 day 1 | True / 0 / 0 | 348.87 / 303.75 | 138 / 23.73 | 5.75 / 28.00 / 94.45 (17) | 38.23 / 96.33 (9) | 5.10 / 94.45 (9) | 45.38 (176.57-221.95) | 8 |
| lowford/warden/human/T2/s2, L1 day 1 | True / 0 / 0 | 372.57 / 327.45 | 161 / 25.93 | 5.67 / 46.43 / 121.45 (17) | 32.18 / 123.53 (9) | 5.52 / 121.45 (9) | 48.52 (215.15-263.67) | 32 |
| verge/warden/human/T2/s1, L5 day 1 | True / 0 / 0 | 122.45 / 122.45 | 31 / 15.19 | 8.10 / 19.58 / 19.58 (7) | n/a / n/a (0) | n/a / n/a (0) | 18.70 (72.37-91.07) | 0 |
| verge/warden/human/T2/s2, L5 day 1 | True / 0 / 0 | 169.52 / 169.52 | 39 / 13.80 | 8.77 / 30.40 / 30.40 (8) | n/a / n/a (0) | n/a / n/a (0) | 37.45 (132.07-169.52) | 1 |

| Rhythm measure | Target to playtest | Today's observations |
|---|---|---|
| Last pack kill to next first hit | Next pack within 5-8 s | lowford s1: median 5.75 s, p90 28.00 s; lowford s2: median 5.67 s, p90 46.43 s; verge s1: median 8.10 s, p90 19.58 s; verge s2: median 8.77 s, p90 30.40 s |
| Elite first hit to next elite first hit | An elite pack every 60-90 s | lowford s1: median 38.23 s (10 encountered); lowford s2: median 32.18 s (10 encountered); verge s1: median n/a s (0 encountered); verge s2: median n/a s (0 encountered) |
| After each elite | A designed lull; duration to playtest | lowford s1: 7/9 paired exits have a positive gap; lowford s2: 8/9 paired exits have a positive gap; verge s1: n/a (no paired elite exits); verge s2: n/a (no paired elite exits) |
| Kills/min and longest empty stretch | Baseline; no numeric target picked | Per-run figures above and windows below |

| Run | Window s | Kills | Kills/min |
|---|---|---|---|
| lowford s1 human | 0.00-30.00 | 32 | 64.00 |
| lowford s1 human | 30.00-60.00 | 14 | 28.00 |
| lowford s1 human | 60.00-90.00 | 22 | 44.00 |
| lowford s1 human | 90.00-120.00 | 1 | 2.00 |
| lowford s1 human | 120.00-150.00 | 9 | 18.00 |
| lowford s1 human | 150.00-180.00 | 3 | 6.00 |
| lowford s1 human | 180.00-210.00 | 0 | 0.00 |
| lowford s1 human | 210.00-240.00 | 6 | 12.00 |
| lowford s1 human | 240.00-270.00 | 15 | 30.00 |
| lowford s1 human | 270.00-300.00 | 5 | 10.00 |
| lowford s1 human | 300.00-330.00 | 11 | 22.00 |
| lowford s1 human | 330.00-348.87 | 20 | 63.60 |
| lowford s2 human | 0.00-30.00 | 32 | 64.00 |
| lowford s2 human | 30.00-60.00 | 14 | 28.00 |
| lowford s2 human | 60.00-90.00 | 2 | 4.00 |
| lowford s2 human | 90.00-120.00 | 20 | 40.00 |
| lowford s2 human | 120.00-150.00 | 10 | 20.00 |
| lowford s2 human | 150.00-180.00 | 1 | 2.00 |
| lowford s2 human | 180.00-210.00 | 21 | 42.00 |
| lowford s2 human | 210.00-240.00 | 5 | 10.00 |
| lowford s2 human | 240.00-270.00 | 4 | 8.00 |
| lowford s2 human | 270.00-300.00 | 14 | 28.00 |
| lowford s2 human | 300.00-330.00 | 8 | 16.00 |
| lowford s2 human | 330.00-360.00 | 13 | 26.00 |
| lowford s2 human | 360.00-372.57 | 17 | 81.17 |
| verge s1 human | 0.00-30.00 | 9 | 18.00 |
| verge s1 human | 30.00-60.00 | 15 | 30.00 |
| verge s1 human | 60.00-90.00 | 1 | 2.00 |
| verge s1 human | 90.00-120.00 | 6 | 12.00 |
| verge s1 human | 120.00-122.45 | 0 | 0.00 |
| verge s2 human | 0.00-30.00 | 5 | 10.00 |
| verge s2 human | 30.00-60.00 | 15 | 30.00 |
| verge s2 human | 60.00-90.00 | 9 | 18.00 |
| verge s2 human | 90.00-120.00 | 6 | 12.00 |
| verge s2 human | 120.00-150.00 | 4 | 8.00 |
| verge s2 human | 150.00-169.52 | 0 | 0.00 |

Windows are [start, end); a kill at the terminal instant belongs to the final window. The final partial window uses its actual duration. Sub-tick floating point drift at a 30 s boundary is snapped within 1e-8 s. JSON retains full precision, kill times, individual groups, gaps and elite intervals for inspection.

JSON output (git-ignored, one file per run):
- `godot/balance/out/density/20261111T1924043768968_lowford_warden_human_t2_s1.json`
- `godot/balance/out/density/20261111T1924043768968_lowford_warden_human_t2_s2.json`
- `godot/balance/out/density/20261111T1924043768968_verge_warden_human_t2_s1.json`
- `godot/balance/out/density/20261111T1924043768968_verge_warden_human_t2_s2.json`
