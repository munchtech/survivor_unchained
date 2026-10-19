# Handoff: the tutorial environment (the Prologue's world)

## Now (env lead 2, 19 Oct): E1 round 2 running
- **Perf baseline done** (`survivorsunchained_inputs\env_perf1\`: lf_hi, lf_med reach Exit; flips st_*/road_*; windows tables). Release, 1440p high, her pre-LOD: GPU 4.3-6.7 ms (the 6-10 ms was the Debug build); shadow draws 2,050-4,400 and render CPU 3.5-8.3 ms were the failures. Her cost 0.56 ms / 1.39M prims pre-LOD: budget on the post-LOD ~0.3 ms (main approved).
- **E1 shadow rules DONE and measured** (aa758a64; `godot/src/World/ShadowLamp.cs`, one shadowed omni at a time with a cross-fade; no crowd/fx shadows; sun 2 splits at 50 m on High/Medium; cinemas keep the old rules). After (`env_perf1\e1\`): play shadow draws 374-627, GPU 4.3-5.8, render CPU 2.4-3.8 (Boss over 3), draws 438-518 (over 450 at Ambush/Post/Boss). Frames 8-13 ms against 4.5 ms GPU: an unexplained CPU-side gap, for E10.
- **E1 light presets:** round 1 built (4e41dfe0..db54f11e: play-only presets LowFordNight/Dawn, WaystationDawn/Day; hand-backs blend to "play"; MistLayers; `--spots`, `--air-tune`, `tools/scratch/env/shots.py`). Judge 1 (xhigh) FAILED, 1/14 gate. Its fixes are in the round-2 brief (scratchpad `env/e1_r2_brief.md`; copied into `survivorsunchained_inputs\env_e1\e1_r2_brief.md`). Judge rulings: night close-up background 4-7x under her face (not 1.6-1.9x); dawn sun cheated toward the road's far end. Both are taste calls for the owner via main. The ford's water and lamp go to E6/E2.
- Next: round-2 judge, then (round cap 3) E2.

## Start here (env lead 1, agent afa5095757c4beed6, 18 Oct)
- Worktree `.claude/worktrees/env-1`, branch `env-1` (cut from integration 19c4915e). `godot/assets` is a junction to this worktree's own `public/assets`: never stash, reset --hard or checkout . here. Merge `origin/claude/vigilant-galileo-l6jqyx` at the start of each step.
- The bar: `docs/art/look_bible/` (boards 03-08, 10 for the world; page 11 budgets; page 12 inventory, owner "tutorial environment lead*": 233 rows; page 13 beats). Judges: xhigh, whole-frame gate first (`docs/handoff/lead_brief.md`), 1:1 game cameras only, round cap 2-3. Judges and shifts on the API credits are paused: judges run as `su-lead-max` subagents in the foreground.
- **Now:** step 1, the first perf run (helper a9be95f4dde24b572, su-lead-high medium): Release build, autopilot to stage=Exit, flip splits (her, volfog, ground, the road's 70-170 s peak, the post). Output to `survivorsunchained_inputs\env_perf1\`.
- **Next:** E1 below.
- **Main's rulings (18 Oct):** four milestone MRs, M1 first, with cuts following the perf numbers. Impostors, LODs and the foliage shader are ours, inside E4 (there's no rendering lead). Blender Python generators and TRELLIS are ours. CC0 Poly Haven/ambientCG photos are allowed only as raw material: log each one's source, licence and hash in the provenance record the download tools write, and bake it into our own materials (trim sheets, macro textures). Never ship a stock material as is. Each milestone goes to main as "MR READY env-1@<commit>" with its before/after 1:1 frames and the perf table.

## The fixed list (in the order the player sees it; page 13 beats)
| # | Item | Boards | Budget (page 11) | Rough agent time | State |
|---|---|---|---|---|---|
| E1 | Light, grade, mist: zone presets (Low Ford night and dawn, the camp, the town dawn/day), moon 20-30 deg, ambient 2-3 stops under, her ember light, pools from sources, mist planes; shadow rules (one shadowed lamp, no shadows from crowd/fx/scatter/kit pieces, sun distance and 2 splits for the play camera) | 1c | fog+mist <= 0.5 ms; shadow draws <= 1,200 | 4-6 h | open |
| E2 | Flames and lamps: flame kit (motion-vector flipbook shader, noise flicker), modeled lamp frames and posts, torches, the camp fire (logs with ember cracks and end caps, ash bed, sparks, smoke), the Warden's three blue lamps | 1j | lamp 1.5k tris, 2 draws, no shadow | 6-10 h | open |
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
