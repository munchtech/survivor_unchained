# Handoff: the tutorial environment (the Prologue's world)

## Now (env lead 11, 20 Oct night): E5 DONE (judge r3: rocks PASS-WITH-NOTES, pebbles PASS, stepping stones PASS-WITH-NOTES), MR; next E6 water
- Scratch: this session's scratchpad `489a0bd2-...\scratchpad\env\` (briefs `e5b_brief.md`, `e5c_brief.md`, judges `e5b_judge.md`, `e5c_judge.md`, `final_e5.sh`); backed up to `survivorsunchained_inputs\scratch_env11\` at stretch end.
- **E5 round 2-3 landed:** stepping stones are 5-7 sided slabs (dome ~2 cm), a braided zigzag causeway (data keys incl. `dry`), tops 12-20 cm proud, wet band 2/3 of the side, algae line, per-stone value/cool tint; boulders have 2-3 fracture faces; pebble clusters 3-6 stones in 3 sizes, slate/ochre/umber, the terrain's AO (no extra fill); night: stone value -24%, floor halved, `night_tint`; dressing keeps trunks 0.3 m+ off boulder rims (cliffs exempt) and rocks 0.3 m off props; frames.py sets `stonesnight`, `fordpost`, `roadrock`, switch `--flora-hide`. Grass sunlit body hue 104 -> 94 (forddawn), 112 -> 100 (roaddawn): FIXED.
- **Closed as known (r3, cap):** the big road boulder's top still a soft dome from the play camera (for the painted remake: flat broken top, finer blotches); a dark dome rock under a crown at roadrock_o_00 (560-780, 0-160); a pale rock at stones_o_01 (1215,630); the dark-litter pebble ratio. Cliff chunks stand only in the forest walls (68 m+ from the road): unjudged, not seen from the road.
- **Routed:** the cyan upright slivers at stonesnight_o_00 (685,255), (750,435) are not ours (a landmark or item); the stretched steep west bank is terrain. **To E6:** the stepping stones' contact rings and foam, 2-3 angular/long stones, the milky flat water, figures standing on water. **To E7:** a stepping stone blown white under the ford lantern at fordpost_o_00 (1010,690) (stone tops are rough 0.88; the lamp's energy), the lantern top a glowing white box, the grey cart, the bedroll and salmon chest.

## Paused here (env lead 10, 20 Oct night); next: E5 fix round 2 (the judge's six fixes), reshoot, judge, MR
- Branch `env-4` (pushed). **E4 is MERGED** (87c640e6). Scratch and texts are backed up in `survivorsunchained_inputs\scratch_env10\`: `e5a_brief.md` (the E5 build brief), `e5a_judge.md` (the judge brief: reuse it for round 2 with the changes), **`e5a_verdict.md` (round 1's verdict, the fix list)**, `g1_judge_common.md` (the judge rules), `final_e4.sh` (tests, Release perf and the teach run; copy it for the MR).
- **E5 so far (47ae68f5, unjudged-to-pass):**
  - The generator `tools/assets/env_rocks.py` has presets: boulder, fieldrock, cliff, pebbles, stepping (4-6 variants each, LODs, baked edge-wear vertex colour).
  - One stone material: `OWN_ROCK` in `godot/shaders/kit.gdshader` (triplanar paint, moss, grime, wet band, global `water_level`; the uniform is `stone_rough`). The palette is data in `flora_species.json` `"stone"`.
  - Swapped through `flora_species.json` (`"kind/piece"` keys).
  - The ford causeway is data in `godot/data/zones/lowford/flora_species.json`. The old one was 18 kit rocks from `src/world/zones/lowford.ts:322`. Dressing drops kit rocks within 2.7 m of the line.
  - `--flora-kit` brings back the kit rocks too. There is a perf flip `rocks`.
  - The `stones` shot set (frames.py) has three day spots.
  - Perf at road_night: rocks 6 draws, 12 shadow, ~0.03 ms.
- **Round 1 judge (xhigh): rocks FAIL, stepping stones FAIL (close).** Fix list in `e5a_verdict.md`:
  1. Turtle-shell tops: open fractures, flatter crowns, 5-7 sided slabs.
  2. One braided path, not two rows; drop the stones on the dry ramp.
  3. Night value -25%, a warmer brown-grey, moss on boulder tops.
  4. Stones 12-22 cm proud with the wet band visible.
  5. Visible pebble clusters.
  6. A reshoot showing boulders, field rocks and cliffs by day and by night; `stones_o_02` showed no rock and needs a new spot.
- **Carried notes:**
  - Grass, from the E4 judge and still open: sunlit blades read teal/mint. Move the blade body's hue toward green in sun, not just the tips (`sun_tip` in `grass_own.gdshader` didn't do it). The ±35% size variance is FIXED.
  - **E7: the camp lantern's cyan pool** (`LampColor` #ffc890 in `ZoneView.cs` is every road lamp; the camp lantern needs its own amber), and the few olive-yellow grass tips in it.
  - E6 owns, at the stones: contact foam rings and a short downstream wake, a bed seen through 10-30 cm, shore darkening meeting the wet band, wading ripples, her standing on the surface in a gap, debris on the surface, a lens-flare ring on the bank at ford_o_05.
- **Order after E5:** E6 water, E7 camp, E9 town (the dawn mud decal gate), then **E8 castle/gate/walls and E10 perf close, both confirmed as env's** (the coordinator, 20 Oct). Build every remake as a generator or kit with data presets. Each MR says in one line what a new zone gets free and what it still needs. The town comes first; don't let it add rounds.

## Done (env lead 10, 20 Oct): E4 foliage (MERGED 87c640e6)
- Branch `env-4`. Scratch and briefs: `survivorsunchained_inputs\scratch_env10\` (backed up at each stretch's end): judges `e4e_judge.md` (r3), `e4g_judge.md` (r4 + step C), `e4i_judge.md` (step D); solver briefs `e4f_brief.md`, `e4h_brief.md`; `final_e4.sh` (tests, Release perf, teach run).
- **E4 is ours and the DEFAULT:** spruce, alder, snags (dead spruce), hazel and elder bushes, bracken, and grass, all from `tools/assets/env_trees.py` (presets `SPRUCE`, `ALDER`, `SNAG`, `BUSH`, `BRACKEN`, `PAL`, grass; `tex [--species X]`, then `blender -b -P tools/assets/env_trees.py -- mesh [--species X]`, then `Godot_console --headless --path godot --import`; frames.py does not reimport). `--flora-kit` brings the kit back (frames.py `g`).
  - **Data:** `godot/data/flora_species.json` (kit-to-own map with per-copy picks, LODs, cells, shadows, wind, shader values, `night_hue`/`night_value`, the `grass` section; an empty `own` list drops a kit piece), read by `FloraSpecies.cs`. A zone overrides with `godot/data/zones/<zone>/flora_species.json`. **A new zone gets the six species and the grass for free by data; it needs only new species presets if its biome differs.**
  - Grass: `Grass.Own` + `godot/shaders/grass_own.gdshader` (one camera-facing clump card a cell, drift noise, olive to blue-green, ground-blended base). Kit clover, flowers and mushrooms are dropped (1.5% of clumps flower).
  - Light: **LowFordNight moon 20 -> 28 degrees, strength x0.55** (`Atmospheres.cs`), so the spruce shadows read as conifers, not bars; the lit ground holds G1's value; her close-up hair stays copper (hue 39).
- **Judges (xhigh):** r3 spruce PASS, alder PASS-WITH-NOTES, shadows FAIL -> moon raised; r4 every frame GATE YES, shadows PASS, snags/bracken PASS, bushes PASS-WITH-NOTES; step D every frame (8) GATE YES, grass PASS-WITH-NOTES, elder closed as plain elder (no flowers at 1:1).
- **Riding to E5's round** (the judge: none blocks E4's merge): warm the sunlit grass tips toward olive (hue 85-95) so drifts don't look pasted on at forddawn; vary grass card size ±35% and mix 2-3 clump shapes (stamped look in dense drifts). **Riding to E7:** the camp lantern's cyan pool (and the few olive-yellow tips in it) once the lantern is amber.
- **Perf at road_night:** flora 63 draws (was 99), 106 shadow draws (192), 0.30 ms GPU (0.46); grass 2 draws, 0.20 ms (kit 1.07 ms). LOD2 impostors were dropped: unneeded at these numbers. Release (`env_perf1\e4\`): Low Ford 1440p high fps 106/172/242 (G1 108/136/172), median shadow draws 265 (503); hub 92 fps (CPU-bound). Tests 1018/0/8; teach 11/11.

## Paused here (env lead 9, 20 Oct); next: judge E4 step B round 2, then step C
- Branch `env-4` (pushed). G1 is MERGED. Scratch, briefs and measuring scripts are backed up in `survivorsunchained_inputs\scratch_env9\` (`e4\` holds the tree work; briefs `e4a_brief.md` to `e4d_brief.md`, judges `e4a_judge.md`, `e4b_judge.md`, `e4c_judge.md`). Shots are in the worktree's `godot\.shots\` (`e4a_` to `e4d_`; `_g_` is the kit, `_o_` is ours).
- **E4 so far: our own spruce and alder,** behind `--flora-own` (default OFF until E4 closes).
  - Generator `tools/assets/env_trees.py`: `python tools/assets/env_trees.py tex` (the atlases, through `paint_tex.py`'s new `bark` and `foliage` presets), then `blender -b -P tools/assets/env_trees.py -- mesh`, then `Godot --headless --import`. **`frames.py` does not reimport**, so run the import after every mesh build.
  - Output in `godot/art/world/flora/`. Shader: the `OWN_FOLIAGE` block in `godot/shaders/kit.gdshader`, plus the global `flora_light` (Atmosphere.cs, project.godot).
  - Swap in `Dressing.cs`, `ZoneData.cs` and `KitLook.cs`: Pine_1-5 become spruce_a/b/c, CommonTree_1-5 become alder_a/b/c, in both zones. Our trees merge across placement groups, with shadow-only proxies in 48 m cells. LOD0 to 44 m, LOD1 to 100 m.
  - Perf flips `pines` and `broadleaf`; the `road_night` view is in `tools/perf/run.py`. Whole flora at road_night: 0.46 ms GPU (kit 1.44), 99 draws (budget 80; about 57 of them are kit bushes, ferns, rocks and dead trees, so step C closes it), 192 shadow draws (budget 420).
- **Judges:**
  - Spruce: the foliage passes (fern read, dawn yellow and per-tree variation fixed).
  - Alder: PASS-WITH-NOTES at dawn.
  - Round 3 (e4c) failed camp_00/_01, road_00 and town_03. Solver e4d (cf29db6b) then fixed the marks below; **its shots `e4d_*` are NOT judged yet.**
    - The night shadow blades: the proxy rebuilt with concave notched tiers, gaps cut between tiers, lean and ±30% height. This is the shadows' last round: if they fail, raise the LowFordNight moon from 20 to about 26-28 degrees, or close them as known.
    - The alder crown no longer reads as a hole in town: its median 21.6 against the cobble shadow's 20.0, but only 43% of it is olive against the 50% asked.
    - The night shade is no longer black: shaded crowns at the road's L, blue-green.
    - The alder has lobed leaf rims, and a dawn hue floor of 98.
    - Near trees are dimmed 20% by day, but the nearest roaddawn spruce is still the brightest patch.
  - The Low Ford moon's angular size is 0 (the 1.2 degrees is arenas only), so the light was untouched.
- **Next:**
  1. A xhigh judge on `e4d_*_o_*`, using `e4c_judge.md` with e4d's changes.
  2. Step C: snags (DeadTree_1-5, from the spruce generator with no needles), bushes (Bush_Common and its flowering version, hazel or elder), bracken (Fern_1, Plant_1_Big), all merged the same way to bring draws under 80. What they must match: the same 40-60 px clumps with dark cores and lit rims, a hue between the alder's olive and the spruce's blue-green (never the kit's lime), the night ambient floor, a dark base at the ground, an outline per species. Then the LOD2 impostors.
  3. Grass and tufts (the Poly Haven scans and Grass.cs).
  4. Make `--flora-own` the default, run the full test and teach run, then the MR.
  Then E5 rocks, E6 water (fixes the ford), E7 bedroll, chest and the amber camp lantern (`LampColor` is shared by every road lamp, so the camp lantern needs its own), E9 buildings, roofs, well, stalls and the setts. **E9 gate item: the dawn town's mud decals go black in shade.** That's the decal asset, not the light (the same with the old light). E9's setts remake must pass that frame.
- **Gotchas:**
  - Merge with the junction removed (README); a failed merge's hard reset wiped this worktree's assets once (restored).
  - The camp lamp pool's cyan left half belongs to lighting, not the trees.

## Done (env lead 9, 20 Oct): G1, the painted light and grade as the default (MERGED)
- Branch `env-4`. Scratch, briefs and measuring scripts: `survivorsunchained_inputs\scratch_env9\` (backed up at the end of each stretch); judges' briefs `g1_judge_*.md`, `g2_*`, `g4_*`.
- **What G1 built:** the paint grade is data. `GradeSettings.Paint*` (vib, vib-dark, hi, shadow hex, shadowk, lift) in `godot/logic/World/Zone.cs`, applied in `GradeLut` (`Paint` in `godot/src/World/Atmosphere.cs`). Vibrance fades in the darks (`VibDeep`) and spares skin and copper. Hi spares skin. `--grade-try` still overrides any key, for pictures.
  - Presets (`godot/logic/World/Atmospheres.cs`): WaystationDay, LowFordNight, LowFordDawn (WaystationDawn inherits it), and `CloseNightPaint`, the close view's grade. The Look and the title (`Atmospheres.Front`) take CloseNightPaint's paint by default; `--front-unpainted` gives the old grade.
  - The close view (`godot/src/Game/GameCloseUp.cs`): key-night 1.7 at 18 degrees, fire 0.9, rim 3.0 at 10 degrees, exposure-night 1.2. The rim is kept off her hair: `PlayerView.HerHairLayer`, bit 12; `--close-rim-hair` restores the old behaviour.
  - Untouched: the base presets (Night, Day, Dawn, Dusk, NightTown) and the brush post-filter (`--brush`). The brush is dropped: its code stays behind its flag, off by default (+2.3 ms at 1440p, invisible at the play camera). Don't build on it.
- **Her: the grade is on her, with no mask** (main's call, from the owner's question). The r4 max judge passed all four close-ups and the Look with the paint grade. Her neck shade stays warm rose-brown (hue 21, C 9; it would read as bruised below hue 20), and the copper is deep. At the play camera her shaded side takes the moon's blue, which reads as moonlight. Mask: not needed.
- **World judges (xhigh), round 2:** 7 of 8 frames pass the gate. The dawn town's mud decals go black in shade. They measure the same with the old dawn light and no paint (shaded earth p10 22.8 before, 23.0 now), so the cause is the setts decal asset. **E9's setts remake must pass the dawn town frame at the gate.**
- **Open, not light (routed):**
  - At the closest close-up spot, her face is lit more by the key than the fire, and the moon edge is subtle on skin. Both pass the gate. If the owner wants more: key 1.45, fire 1.1, a tighter rim.
  - The eyes' catchlight at _02/_03 (face lead).
  - A blue sheen past the far pauldron (glow).
  - The camp lantern's acid-yellow grass: `LampColor` #ffc890 in `ZoneView.cs` is every road lamp. The amber camp lantern is E7's.
  - The camp's frosted moonlit grass p95 (Frost).
  - The defocused campfire behind the Look reads as a flat cutout (camp props).
- **Perf:** hub ABAB (`survivorsunchained_inputs\env_perf1\g1\hub_A*/B*`): G1 is not slower. The single-run fps drop against E3 (lf_hi 165 to 136, hub 112 to 88, GPU flat) is machine load: A (integration) 80 then 114 fps, B (G1) 112 then 125, GPU 4.2 ms in all four. Tests 1017/0/8; the teach run showed and answered 11/11.
- **Next: E4** (canopies, foliage, firs, tufts), built to the painted look (`docs/handoff/art_style.md`). Then E5, E6, E7, E9, each its own MR.

## DONE (env lead 8, 20 Oct): E3 passed judge 4, MR READY; next is the art-style frames, then E4
- Branch `env-3` (pushed). Scratch and briefs: `survivorsunchained_inputs\scratch_env8\` (ground_g brief and scripts, e3_judge4_brief.md, perf/abab.sh and final.sh). Frames and numbers: `env_e3\g\` (numbers.md); verdict `env_e3\judge4erdict.md`.
- **Solver G (b96cfb10):** the setts mud reads as mud: hue about 33 against the stone's 22, saturation 0.22-0.25, 30-32% darker, low sheen, its own grain. At night the pebbles take the road's dew (night_04 pale pebbles 13 -> 1). The town_01 pool cut is confirmed. New switches: `--setts-collar`, `--setts-mud-tone/-sat/-spec`, `--scatter-night-dew`, debug views 26 (mud) and 27 (collar).
- **Judge 4: DONE,** with one fall back: the post collars read as round mud pads at the dummy and the bench, so `--setts-collar` defaults to 0 (a476f7b8, checked at 1:1). The mud layer still gathers dirt at everything that stands.
  - Closed as known: night_02's straight setts corner; wear, sunk stones and moss that don't read in the open street; the shimmer.
  - Notes for the painterly re-texture: the cells are evenly sized and the joints evenly dark (add big flags and small fill stones, vary the joints); make the mud opaque and matte over the buried edges; carry the wear lane in the albedo.
- **Perf (Release, `env_perf1\e3\`):**
  - Low Ford 1440p high: fps min/median/max 140/165/216 (E2 131/180/199), GPU median 5.4 ms (5.0).
  - Low Ford 1080p medium: 151/204/304 (117/226/323).
  - Waystation day 1440p high: 112 fps. The GPU is at 4.2 ms, so the frame is CPU-bound (render CPU 3.2 ms), not the ground's doing.
  - The ground flip ABAB against c7c45928: G 1.08/0.99 ms against D's 1.07/0.98, so the restage costs nothing. The absolute number is over the 0.90 target, but c7c45928 measures the same, so the rise is drift plus integration.
  - Routed to perf: shadow draws (play about 730, cinematic 1440-1492), the median fps drop since E2, and the hub's CPU-bound frame.
- **Checks:** tests 1012/0/8; the teach run showed and answered all 11 moments.
- Routed, not E3's: the moonlight streak at night_04 (lighting); tufts and firs (E4); rocks (E5); water (E6); bedroll (E7); buildings, roofs, the well and stall models (E9); the grey NPCs (crowd).

## Paused here (env lead 7, 19 Oct night): E3 setts restage WIP (de5d9902); next: finish F's list, judge 4, perf, MR
- Worktree `.claude/worktrees/env-3`, branch `env-3` (pushed; only .import/.uid churn uncommitted). Scratch, briefs and scripts: `survivorsunchained_inputs\scratch_env7\` (ground_d/e/f, bisect, e3_judge2/3 briefs, ground_d..f briefs). Frames: `survivorsunchained_inputs\env_e3\{d,e,judge2,judge3}\`.
- **Rounds:**
  - D c7c45928: judge 1's fixes.
  - E 18bd75e3: judge 2's fixes.
  - **Judge 3 (FINAL, `env_e3\judge3\verdict.md`)** closed everything except the setts.
    - Closed as known: the 11 px verge ramps, dawn_00's 14% sun ruts, the soft pale patches, the town wet rims, and judge 2's closures (the night_05 1.15 target, the eggs).
    - Two cuts: the beaded pebble rows on the rut shoulders (dawn_04/night_04), and the town_01 gutter pool.
    - The setts restage was approved by main.
- **Solver F WIP de5d9902 (brief `scratch_env7\ground_f_brief.md`, scripts `scratch_env7\ground_f\`).**
  - Built:
    - a 4 m sett tile in 3 variants at 1024 (VRAM per map 16.8 -> 4.2 MB). Its sources (height, stone ID, wear, mud, moss masks) are in `tools/assets/setts_src/`; re-bake with `env_ground.py --only setts --bake`;
    - shader mud in the joints near the well, stalls, posts and walls, sunk and missing stones, wear, moss in the shaded joints (`--setts-mud/-reach/-moss`, `--ground-debug 25`);
    - the pebble rows replaced by loose pebbles (the scatter sequence changed);
    - the gutter pool only on the setts;
    - a `townjit` shot set (shimmer).
  - Measured: stone median 0.24 m (max 0.43), 23-25 cm in frame; mud on 12-13% of the boxes, NOT yet browner; the pebble peak is lower at dawn, but night_04 has more pale specks (frost on the new pebbles?); shimmer about zero.
  - **WARNING:** E's frames and perf may have used stale 2K imports (a plain run doesn't re-import). Run `scratch_env7\ground_f\imp.sh` before any shot or perf run.
- **Left, in order:**
  1. One medium solver finishes F's list: browner mud (25-35% darker and browner), post rings, the night_04 pale specks at 1:1, confirm the pool cut, shoot town_day_00/01/02 + dawn_02/night_02 + dawn_04/night_04 to `env_e3\f\`, numbers.md, and the perf ABAB against c7c45928's shader+setts textures (target ground 0.90 ms or less; absolute numbers drift ±0.15 ms, see `scratch_env7\bisect\run2.log`/`run3.log`), dotnet test.
  2. **Judge 4** (su-lead-max xhigh, foreground) on town_day_00/01/02, the setts in dawn_02/night_02, and night_04 for the pebble cut, against judge 3's "Rulings" (template `scratch_env7\e3_judge3_brief.md`). It's the restage's only round: fall back or close, no further rounds.
  3. Perf (`tools/perf/run.py`, 1440p high fps min at least 131; baseline `env_perf1\e2\`), the full dotnet test, the teach run once, then "MR READY env-3@<commit>" to main.
- **Owner's art-style note (19 Oct, via main):** a painterly-realism style exploration starts right after E3 and will likely re-texture the paving. So keep the sett tile re-bakeable from its masks (above); no polish on the albedo's fine micro-detail.
- Routed, not E3's: shadow draws 488 -> 749 after the integration merge (perf); the night_04 moonlight streak through a canopy gap (lighting); tufts (E4), firs (E4), rocks (E5), water (E6), bedroll (E7), buildings (E9).

## Paused here (env lead 6, 19 Oct night): E3 mid fix round C; next: finish C's open items, then judge 2
- Worktree `.claude/worktrees/env-3`, branch `env-3` (pushed, clean apart from .import/.uid churn; its own assets junction; imported). Briefs: `survivorsunchained_inputs\scratch_env6\` (ground_a/b/c briefs, e3_judge1_brief.md, the measure scripts in ground_a/, ground_b/, ground_c/). Frames: `survivorsunchained_inputs\env_e3\` (a, b, judge1, c). Baseline: `godot/.shots/e3r0_*`. Shots: `python tools/scratch/env/shots.py <round> dawn night town_day` (points at env-3).
- **Built:**
  - Solver A (140fa9c0..ca0d83f0):
    - our own ground materials (`tools/assets/env_ground.py`; the Poly Haven sets are raw grain only; provenance and credits done);
    - the 4-layer shader with height blends, anti-tiling and macro;
    - `GroundPaint.cs`: the road, rut, wet, gutter and puddle mask; grass is cleared off the road;
    - the setts tile;
    - the black slashes are gone.
  - Solver B (00791e0d, 79f36205):
    - frost by sky exposure (the `ground_frost` global in project.godot, driven from Atmosphere.cs; `--frost*` switches);
    - the meadow's three scales;
    - `Scatter.cs` + `scatter.gdshader`.
  - Ground GPU 0.72 ms at 1440p (budget 0.8). Tests 994/0/8 at 79f36205.
- **Judge 1 FAILED** (`env_e3\judge1\verdict.md`, 10 fixes). Fix round C is WIP at **fcffea02**, frames `env_e3\c\e3c3_*`. Every fix is built; the measured state:
  1. Ruts: DONE (19-22% darker in shade, 15-25% in sun).
  2. Dawn frost: DONE (shaded hue 171-219 degrees, none lilac).
  3. Hand-back: PARTLY (p95 74.7 against 72 or less). The decal thaw is now 0.3 s in GameCinema.cs ~1487. Next: retire C01's frost decals before the hand-off, or tone the road under the lamp.
  4. Camp-clearing edge: PARTLY (median 0.62 m against 0.7 or more). Next: `--clearing-soft` 2.2.
  5. Setts-to-grass edge: built, not proven.
  6. Setts grime, gutter, weeds and wear lane: built, but the town mask numbers are unreliable. Fix the classification in `scratch_env6\ground_c\measure_c.py`. The rim highlight is down 33% against a target of 50%.
  7. Puddles: built (but on dirt, not the setts). Next: put them in the setts gutters.
  8. Meadow: built, not measured.
  9. Edge stones: cheap try built, not looked at. Cut them if they still read as eggs.
  10. Close-up: road to meadow luma 1.26 against 1.15 or less. Next: lift the meadow or lower `--frost-soft`.
- **RISK, check first:** the scatter rose to 58.8k pieces and 487k tris at the Low Ford (from 4.4k) with the tree litter. Run `--perf-flip scatter` at 1440p, and cut the litter if it costs more than 0.15 ms.
- **Next, in order:**
  1. One medium solver finishes C's open items above, and writes `env_e3\c\numbers.md` and `dotnet test`.
  2. Judge 2 (xhigh, su-lead-max, foreground): the failed frames only, against judge 1's fixes. Brief template: `scratch_env6\e3_judge1_brief.md`.
  3. At most one more round (the cap is 3), then close the rest as known.
  4. Perf with a runner (`tools/perf/run.py`, 1440p high fps min at least 131; baseline `env_perf1\e2\`).
  5. Full tests, the teach run once, then "MR READY env-3@<commit>".
- Routed, not E3's: the tuft rows of identical cards at the close-up (E4 grass), the firs (E4), rocks (E5), water (E6), bedroll and chest (E7), buildings (E9).

## Now (env lead 5, 19 Oct): E2 DONE, MR READY; next E3
- **E2 is at MR READY** on env-2 (integration merged at fe27b26e). Briefs and tools: `survivorsunchained_inputs\scratch_env5\`. Verdicts: `env_e2\judge1\verdict.md`, `env_e2\judge2\verdict.md`.
- **What E2 shipped:**
  - The fog-blotch fix (frost thaws at hand-back).
  - The flame kit.
  - The camp fire, rebuilt (4a01da0e). Sparks are 0.4 m streaks.
  - The road and ford lamps (518b64bc, 0aa4faca, 4c83162d).
  - The crypt roof on our own slate (2afa524d, 31bbc871). The Poly Haven photo left the repo; the raw copy and its hash are in `survivorsunchained_inputs
aw_materials
oof_slates_02\`.
  - The crypt door (258cec72): our own candelabrum, warm candles with a light, the skull in bone colour, the Barrow's green light as a soft pool. terrain.gdshader now glows blight veins only on true blight, which also removes the faint vein glow at the Waystation.
- **Judges:** judge 2 passed the fire, the sparks, the flame-kit look, the ford lamps at the play camera, and dawn. The crypt door hit all four targets in its last round, closed by main without a third judge.
- **Closed as known (at the cap):** the road lantern at the close-up camera (an even peach box, its flame floating about 60 px above the burner). Ford lamps at the close-up were never shot. The ford flame's body is S 0.48, against a target of 0.5 or more.
- **Routed, tracked, not closed (whole-frame NOs; main, 19 Oct):**
  - E3: the ground blend.
  - E4: canopies and foliage.
  - E5: rocks and stepping stones.
  - E6: the ford water (blotches, glints, the crescent stuck under her). E6 must also carry the ford lamps' cold pool and reflection.
  - E7: the bedroll, and the camp chest (2.7 m from the fire; its pale trim reads cold).
  - The crowd lead: the grey untextured NPCs.
  - Teaching/VFX: the ember pickup's halo at the close-up.
  - The camera owner: the road lantern blocking her face at the close-up (fade near occluders).
- **Optional polish:** the close-up's grey bark log has even furrows and reads cool; soot the ring stones' inner faces about 15% darker.
- **Checks:**
  - Tests: 994/0/8.
  - Full teach run: all 11 moments shown and answered; it ends at the hand-off to town as designed.
- **Perf (`survivorsunchained_inputs\env_perf1\e2\`, Release, quiet GPU, min/median/max over 20 s windows):**
  - 1440p high: GPU 4.4/5.0/5.8 ms (M1 4.9/5.4/7.6), frame 5.0/5.5/7.7 ms, fps 131/180/199 (M1 107/125/148). Shadow draws: play max 771; one cinematic window (Intro/Boss) at 1710.
  - 1080p medium: GPU 2.6/3.5/4.1 ms, fps 117/226/323, play shadow max 1174.
  - The camp's "4.4 -> 6.1 ms" rise was another Godot running at the same time (fire on/off: 3.87 vs 4.10 ms).
- **Next: E3** (terrain and road; the fixed list below). Start by re-checking the ground blend that judges 1-2 flagged (W2) at 1:1.

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
| E3 | Terrain and road: <= 4 layers a pixel (today 7), height blend, anti-tiling + macro, road into the terrain (ruts, verges, no grass), frost by exposure, wet hollows, base blends, decals and scatter; town cobbles (large varied tile, gutters, puddles) | 1f, 1h | 0.8 ms, 40 draws | 10-14 h | DONE 20 Oct (judge 4) |
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
