# Handoff: the tutorial environment (the Prologue's world)

## Now (env lead 6, 19 Oct): E3 in progress
- Worktree `.claude/worktrees/env-3`, branch `env-3` (from dc2f991e; its own assets junction, imported, tests 994/0/8). Briefs: `survivorsunchained_inputs\scratch_env6\`. Frames: `survivorsunchained_inputs\env_e3\`. Baseline frames: `godot/.shots/e3r0_{night,dawn,town_dawn,town_day}_NN.png` (round r0, before any E3 change).
- E3 list (7 items):
  1. The W2 ground blend.
  2. At most 4 layers a pixel, anti-tiling and macro.
  3. The road in the terrain: ruts, verges, no grass.
  4. Frost by exposure, and wet hollows.
  5. Scatter along the road.
  6. Town setts (a large varied tile, gutters, puddles).
  7. Our own ground materials: art/ground shipped 7 Poly Haven sets as is.
- Built: solver A (140fa9c0..ca0d83f0: our own materials `tools/assets/env_ground.py`, the 4-layer shader, `GroundPaint.cs` road/ruts/wet mask, the setts tile, provenance), solver B (00791e0d, 79f36205: frost by sky exposure via the `ground_frost` global, the meadow's scales, `Scatter.cs`). Numbers: `env_e3\{a,b}
umbers.md`.
- Judge 1 (xhigh) FAILED, one fix round: `env_e3\judge1erdict.md` (ruts, the dawn frost blotches, the hand-back's white decal frost, the camp-clearing and setts-to-grass edges, setts grime/gutters/puddles, the meadow felt, the egg edge stones, close-up litter). Solver C (`ground_c_brief.md`) is running it. Then judge 2 on the failed frames only; round 3 is the cap.

## Before (env lead 4, 19 Oct): E2 built, judge next (HANDED OFF at ~250k)
- Worktree `.claude/worktrees/env-2`, branch `env-2` (pushed). E1 is merged (8ba3a4e7). Frames: `survivorsunchained_inputs\env_e2\`. Briefs: `survivorsunchained_inputs\scratch_env4\`. The godot import cache is in place. `tools/scratch/env/shots.py <round> <set>` points at env-2. Sets: roofs, ford, pool, campclose (-9.5,92.5: close4 hides the fire).
- **Fog blotches: FIXED (f1f79d05).** They were C01's frost decals (a 44 m patch, left into play), not fog. Proved by A/B (`env_e2\fog_ab\cmp_frost.jpg`). The frost now thaws over 3 s at hand-back. Switch: `--cine-nofrost`. This also fixes the "frost decal on a flat prop" item routed to cinematics.
- **Flame kit: built** (eb3edefe..540309e6). FlameKit.cs, flame_mv.gdshader, and our own Mantaflow flipbook with motion vectors in art/fx/flame (provenance FX-06). Flicker +-11-12%. The loop seam is 7.6/255, one normal step.
- **Lamps round 1** (986f1422, 32a8384a): our own holders (tools/assets/env_lamps.py, Lamps.cs, lamp_glass shader, LampLayer 1<<11): the ford's three lamp-irons, 8 road posts, 3 wall torches, a standing lantern, and the shrine candle. The white disc is gone, BUT no flame shows at the play camera: the ford lamp reads as a dark box, and the road lantern is dark with a bright spot below it. **Round 2 solver a093803a585045fbe is RUNNING** (output `env_e2\lamps2\`). Its report comes to env lead 4, who relays it via main. Check `git log` for its commits.
- **Camp fire: built** (e79ae4c0). Own logs, ember cracks, ash bed, sparks, smoke; 3.7k tris; flicker +-12%. Open: GPU at the camp went 4.4 -> 6.1 ms, unexplained; re-measure on a quiet machine before the MR. The glb carries three 2048 maps (12 MB); 1024 may do. The fire light still bobs 4 mm (ZoneView's formula): drive light 0 with Flame.Drive.
- **Black roof: built** (92a8cfd0). The crypt's slope faced away from the low moon. Now: slate rows along the ridge, wet sheen, lichen and moss, a pale ridge roll and gable coping. Roof luma 20.0 vs 16.2 for the ground beside it. **License rule:** it ships Poly Haven `roof_slates_02` AS IS. Main's ruling is that CC0 photos are raw material only, baked into our own material, so bake it (recolour and combine with our noise or a trim) before the MR.
- **Done:** the look bible's night line (6x) and the dawn sun cheat (bf0a04eb). The Marionette prop format was answered via main: first props wagon, Barrow grave set, crypt, shrine statue, wayside saint. We build the lamps ourselves.
- **NEXT:** (1) when lamps2 lands, run the judge: `scratch_env4\e2_judge1_brief.md` (paste lamps2's numbers in). (2) One fix round from its verdict, with the round cap. (3) The full teach run once (experience.md "Run"), perf (`tools/perf/run.py`, both presets), tests. (4) "MR READY env-2@<commit>". Then E3.
- Seen, not mine: foreground cartoon tree canopies cover her and the HUD on the camp road (E4).

## Now (env lead 3, 19 Oct): E1 DONE, its MR next; then E2
- **E1 light closed at the cap.** Judge 3 (round 3b) passed 14 of 17 frames. Judge 4 (round 3c) passed the camp night and the close-up, found no regressions, and passed the ford night by the numbers after the beacon pool (its call). The wood road at dawn closes for E1 and comes back with E4's canopy gap. Sheets, round 0 against final: `C:\Users\munch\Desktop\survivorsunchained_inputs\env_e1\final\`. Round sheets: `env_e1\r3b\`, `env_e1\r3c\`. Judge briefs and tools: `survivorsunchained_inputs\scratch_env3\` (e1_judge3_brief.md, e1_judge4_brief.md, cheek.py).
- **What rounds 3b-3c changed (dd6ebc40..5b249250):**
  - Night: the moon at 20 deg; sky 2.2; exposure 1.5; contrast 1.13; her ember 2.2, pale gold #ffd0a0, attenuation 1.8; river mist 0.14, river light 0.17.
  - The beacons: glow at a quarter, plus their own short cool light (3, 7 m).
  - Dawn: shade cool (grade tint 0.55, Moon 1.0, sky #6f8fd8); her ember 0.5 by dawn and day.
  - The crowd's ground blobs are on layer 2 now. A blight decal had been painting them into dark squares.
  - The close view by night: her own layer (`PlayerView.HerLayer` 11), so the zone lights keep off her face; `CloseFireFill` keeps 0.3 of the nearest fire as warm fill; key 2.5 at 90 deg; her lamp lights the ground but not her; exposure 1.35.
  - Picture switches: `--ember-att/-range/-color`, `--beacon-glow`, `--beacon-pool`, `--lamp-shadows-off`, `--blob-strength`, `--close-lamp-on-her`, `--close-fire`, `--close-rim-az`. Shot sets `camp`, `camp3`, `nightc`, `close4` in `tools/scratch/env/shots_cfg.py`.
- **Final numbers.** Night p50, p95/p50 and pools by place:
  - camp 16, 4.1, .72
  - road A 14, 3.5, .62
  - road B 26, 2.6, .55
  - ford 26-30, 2.1-2.7, .61-.65
  - wood road 15, 3.2, .57-.71
  Close-up: face 133-150, background 5.2-5.9x under it, the far cheek 1.2-1.6 stops under. Dawn shade 85-96% cool. Dawn and town cover and patch are as in round 3b. Tests 977/0/8.
- **Open, routed or later:**
  - the ford's armoured figure has no rim (rendering);
  - mist rings round the ford's stones (E6);
  - the close-up's chest is as bright as her face (polish: aim the key at her head from 25 deg up);
  - her rim at road B by dawn (rendering).
  - E2 notes from the judges: the camp lamp's art, Tam's lantern a hot blob, lamp pools on dirt muddy brown.
  - The wood road at dawn, after E4's gap: re-measure the patch (>= 1.35); if it's still night-dark, lift that zone's dawn sky fill +0.3 stop, never the shared dawn preset.
- **Owner calls:** the night close-up background at about 6x (judges 2-4 say keep it, and change the bible's night line). The dawn sun is cheated toward the road's far end (judge 2 said yes).
- **M1 perf, E1 MR (`survivorsunchained_inputs\env_perf1\m1\`; both runs reach Exit).** Min / median / max over 20 s windows:
  - 1440p high: GPU 4.9/5.4/7.6 ms, frame 6.7/8.0/9.4 ms, fps 107/125/148 (e1: min 74), shadow draws 248/545/1443.
  - 1080p medium: GPU 3.4/4.9/7.7 ms, frame 5.9/8.0/15.9 ms, shadow draws 232/557/1670. Its worst window had another game on the GPU.
  - Windows over 1,200 shadow draws are cinematic (72-100% cine), and cinemas keep the old shadow rules. Play stays under 1,200.
- **Next: E2** (flames and lamps, board 1j; `docs/art/look_bible/10_props_flames.md` "The trick" and "DONE means"). Start with a solver brief: the shared flame kit (a motion-vector flipbook spatial shader, noise flicker), the lamp and torch holders (1.5k tris, 2 draws, no shadow), the camp fire, the Warden's three blue lamps. Then one judge, then the E2 MR.
- **The coordinator's ruling:** E1 goes to main as its own MR (shadow rules and light, one full run and perf first), then E2, then E3, each with its own MR.
- **The 211 untracked .uid files** that blocked the merge are in the coordinator's scratch, `env3\uid_bak\`. Bin them after the MR; never commit them.

## Start here (env lead 1, agent afa5095757c4beed6, 18 Oct)
- Worktree `.claude/worktrees/env-1`, branch `env-1` (cut from integration 19c4915e). `godot/assets` is a junction to this worktree's own `public/assets`: never stash, reset --hard or checkout . here. Merge `origin/claude/vigilant-galileo-l6jqyx` at the start of each step.
- The bar: `docs/art/look_bible/` (boards 03-08, 10 for the world; page 11 budgets; page 12 inventory, owner "tutorial environment lead*": 233 rows; page 13 beats). Judges: xhigh, whole-frame gate first (`docs/handoff/lead_brief.md`), 1:1 game cameras only, round cap 2-3. Judges and shifts on the API credits are paused: judges run as `su-lead-max` subagents in the foreground.
- **Now:** step 1, the first perf run (helper a9be95f4dde24b572, su-lead-high medium): Release build, autopilot to stage=Exit, flip splits (her, volfog, ground, the road's 70-170 s peak, the post). Output to `survivorsunchained_inputs\env_perf1\`.
- **Next:** E1 below.
- **Main's rulings (18 Oct):** four milestone MRs, M1 first, with cuts following the perf numbers. Impostors, LODs and the foliage shader are ours, inside E4 (there's no rendering lead). Blender Python generators and TRELLIS are ours. CC0 Poly Haven/ambientCG photos are allowed only as raw material: log each one's source, licence and hash in the provenance record the download tools write, and bake it into our own materials (trim sheets, macro textures). Never ship a stock material as is. Each milestone goes to main as "MR READY env-1@<commit>" with its before/after 1:1 frames and the perf table.

## The fixed list (in the order the player sees it; page 13 beats)
| # | Item | Boards | Budget (page 11) | Rough agent time | State |
|---|---|---|---|---|---|
| E1 | Light, grade, mist: zone presets (Low Ford night and dawn, the camp, the town dawn/day), moon 20-30 deg, ambient 2-3 stops under, her ember light, pools from sources, mist planes; shadow rules (one shadowed lamp, no shadows from crowd/fx/scatter/kit pieces, sun distance and 2 splits for the play camera) | 1c | fog+mist <= 0.5 ms; shadow draws <= 1,200 | 4-6 h | DONE (MR) |
| E2 | Flames and lamps: flame kit (motion-vector flipbook shader, noise flicker), modeled lamp frames and posts, torches, the camp fire (logs with ember cracks and end caps, ash bed, sparks, smoke), the Warden's three blue lamps | 1j | lamp 1.5k tris, 2 draws, no shadow | 6-10 h | DONE (MR) |
| E3 | Terrain and road: <= 4 layers a pixel (today 7), height blend, anti-tiling + macro, road into the terrain (ruts, verges, no grass), frost by exposure, wet hollows, base blends, decals and scatter; town cobbles (large varied tile, gutters, puddles) | 1f, 1h | 0.8 ms, 40 draws | 10-14 h | open |
| E4 | Foliage kit: spruce, birch, alder in 3 sizes, ferns, bushes, grass clumps; 3 LODs + impostor, shadow LOD, wind, back light, hue jitter; swapped in by remapping `flora.json` pieces | 1e | trees+bushes+rocks 0.8 ms, 80 draws, 420 shadow; grass 1.0 ms, 10 draws | 16-24 h | open |
| E5 | Rocks and ford stones: shared rock set, triplanar stone, moss upstream, wet band; stepping stones no two alike | 1f, 1g | rock 3k (outcrop 8k) | 6-8 h | open |
| E6 | Water and shore: depth color, a real bed, shore and contact foam, the ford's flow map, a reflection probe (lamps culled), wet banks, mist over water, wading rings | 1d | 0.5 ms, 5 draws | 8-12 h | open |
| E7 | Story props: the camp, the overturned wagon, the watch-post and chest, the Barrow, the heart; the road's 13 `test` rows decided at the first road frames | 1j, 1f | prop 1.5k (carts 4k), the prop atlas | 10-14 h | open |
| E8 | Stone kit and the castle: the far castle (C01 s8a, one mesh, a keep under the gold lamp), the Waystation's gate and walls | 1g | far castle <= 30k, 1 draw, no shadow | 10-14 h | open |
| E9 | The town: timber/plaster/stone kit on two trim sheets, merged buildings, shadow proxies, roof fade at the play camera, smoke and the lit bakery, clutter clusters, a forested skyline | 1h | building <= 25k, 3 draws, 2k shadow proxy | 20-30 h | open |
| E10 | Perf close: a Release whole-Prologue run meets page 11 in every window, 1440p high and 1080p medium | 11 | page 11 | 4-6 h | open |

Milestones, each its own MR: M1 = E1-E3, M2 = E4-E5, M3 = E6-E8, M4 = E9-E10.

## Inputs
- Cinematics' ENV cuts (docs/handoff/cinematics.md top "ENV"): frost prints, flattened grass, log end caps, trunk through frame, flat stepping stones, birches at sa2, cartoon trees, the coal bed, cotton-wool frost, a keep under the gold lamp. Those shots come back when the art lands.
- Last perf run: `survivorsunchained_inputs\look_bible_perf\summary.md`. Tools: `tools/perf/run.py`, `tools/perf/flip.py`, `--perf-flip`/`--perf-off` in `godot/src/Game/Game.cs` ~1640-1775.
- Where the world lives: `godot/data/zones/<zone>/` (zone.json, heights.bin, splat.png, flora.json+bin, props.json, landmarks.glb, water.json+bin; first exported by `tools/godot/export_zone.mjs`); `godot/src/World/` (Ground, Grass, Dressing, Water, Atmosphere, Campfire, Landmarks); shaders `terrain`, `water`, `grass`, `canopy`, `kit`, `sky`, `mist_sheet`.

## Gotchas
- Her cost in env_perf1 is before her play LOD: on integration she draws the full ~1M-tri model at the play camera. Armor 3's MR adds the LOD and the merge by material, and main says when it merges. Re-measure her then, before cutting world parts for her sake.
- No `godot/.godot` in a fresh worktree: copy the main checkout's, then `--headless --import`.
