# Handoff: the tutorial environment (the Prologue's world)

## Paused here; next: (env lead 2, at the coordinator's wind-down, 19 Oct)
- **Next: E1 round 3's judge** (the round cap; xhigh, whole-frame gate, `su-lead-max` in the foreground). Sheets (round 0 left, round 3 right): `C:\Users\munch\Desktop\survivorsunchained_inputs\env_e1\r3\` r3_night_play, r3_dawn_day_play, r3_closeup_night, r3_town_dawn, r3_town_day. Reuse the round-2 judge brief (`C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_env1_8f465914\env\e1_judge2_brief.md`) with its "Round 2" and "Numbers" sections replaced by round 3's (below). Then close E1: frames whose light passes but whose gate needs later art (road A's canopy E4, the ford's water E6 and beacon E2, the town kit, the dawn wood road's trees E4) close for E1 and return with those items. Then E2.
- **Verdicts:** judge 1 `C:\Users\munch\Desktop\survivorsunchained_inputs\env_e1\judge1_verdict.md` (FAIL 1/14); judge 2 `C:\Users\munch\Desktop\survivorsunchained_inputs\env_e1\r2\judge2_verdict.md` (0/17 but "a clear improvement, the structure is right": two faults, warm brown shade and khaki moonlight). Briefs for every helper: `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_env1_8f465914\env\` (with the solver's offline grade copy `grade.py`, plus cover.py and chroma.py).
- **Round 3 (3c4ade60, the solver's diagnosis):**
  - Night shade: the ambient was blue already, but 5 stops under the moon. Ambient raised to 2.5 stops under (hemi 2.4, env 1.2).
  - Khaki: AgX on olive grass. Fixed by a new grade step `GradeSettings.Moon` (weak colours take the moon's silver-blue; it's off in non-play presets and on her skin). Moon 4.9.
  - Dawn and town brown: C04 A's orange sky horizon. Cooled, with a neutral gain; sun #ffdbad at az -60.
  - Close-up: key 55 deg off her face, color (1, 0.6, 0.35), exposure 1.57.
  - Smaller: the camp lamp at 22 (zone.json); beacon emission 0.12; night ember stones x1.6. The town spots moved to its streets (`3,3;24,0;0,-24`); town day sun ENE.
- **Round 3 numbers** (round 0 -> 2 -> 3):
  - Night p50, camp / road A / road B / ford / wood: 38/36/32/35/33 -> 26/19/49/39/21 -> 28/21/31-37/37/23.
  - p95/p50: 2.75/2.86/2.0/1.84/2.52.
  - Pools: .60/.52/.51/.46/.53, under the 0.55 target except the camp. The shade lift flattened them; an untried sweep is `--air-tune ember=2.2,hemi=2.0`.
  - Shade median RGB about [10,16,21].
  - Close-up: face 169, 6.0x over the background.
  - Dawn cover / patch: 48/44/75/17/78 (1.7/1.8/1.9/1.1/1.0). The wood road stays shaded at any azimuth; spot `-5,-66` has a lit patch (1.87).
  - Town dawn 60/62/63 (1.68/1.64/1.39); town day 31/56/37 (1.46/1.43/1.42).
  - Clipping <= 0.04%. Fog+mist 0.07-0.10 ms (round 2). Shadow draws not re-run since round 2 (about 351 in play).
- **Tools:** `--spots`, `tools/scratch/env/shots.py` + `sweep.py` + `shots_cfg.py` (several jobs, one build, one turn), `--air-tune` (colours and grade keys), `--air-old`, `--grade-off`, `--spots-unshadowed`, `--close-key-az`, `--close-moon-off`, the perf flip "mist". Run `dotnet build` before any shoot (shoots don't rebuild the DLL). `dotnet test` 942/0/8 at 3c4ade60.
- **E1 shadow rules: DONE and measured** (aa758a64, `godot/src/World/ShadowLamp.cs`; `C:\Users\munch\Desktop\survivorsunchained_inputs\env_perf1\e1\`): in play at 1440p high, shadow draws 374-627 (were 2,050-4,400), GPU 4.3-5.8 ms, render CPU 2.4-3.8 (Boss over 3), draws 438-518 (over 450 at Ambush/Post/Boss). Frames are 8-13 ms against 4.5 ms GPU: a CPU-side gap, for E10. Baseline runs `C:\Users\munch\Desktop\survivorsunchained_inputs\env_perf1\` (lf_hi, lf_med reach Exit; her pre-LOD 0.56 ms / 1.39M prims: budget the post-LOD ~0.3 ms, main approved).
- **Changed beyond the zones (tell cinematics):** c01, c02 and c04a hand-backs blend to the new preset name "play". The key direction switches on the hand-back cut. Cinemas keep the old shadow rules and sun.
- **Owner taste calls (both judges recommend yes):** the night close-up background 3.5-6x under her face, not the board's 1.6-1.9x; the dawn sun cheated toward the road's far end instead of true east.

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
