# Lane G item 4: body B becomes her body, the costed plan (lead 3, 16 Nov 2026)

To coordinator #15 before any build. Nothing here is built. Facts: `lane_g_plan_facts.md` (lead 2) plus this lead's reads (named per step).

**The owner, 16 Nov 2026, word for word:** "Restart B now"; at the A|B bare-shape gate: "Yes to B"; "this is devastating.  marionette is the whole pipeline for building things"; "the goal was to be able to generate armor pieces with meshy or whatever in marionette that just fit on the character - saving lots of time in building them".

Units: tokens in M (a lead round with helpers ~0.3-0.7M; a max judge ~0.13M). Credits: Meshy. Every judge is a fresh su-lead-max at the game cameras, 1:1.

## DECIDED (the owner, 16 Nov 2026, word for word): "also comit b to the demo". B is her default before the 20 Nov demo (timing A below, the owner's call). Owner's picks: Q2 retire the plate sets; Q3 the three callings refit on one judged sheet before the flip; Q4 vambraces, then a pauldron; Q5 TRELLIS.2 first, Meshy per piece with the owner's yes. Step 7 is lane D's (it adds `--body` itself, on lane G's B numbers). The fallback to A holds until the flip gate passes.

## Lead 3's verdict on timing (overruled by the owner): flip RIGHT AFTER the demo, with everything built and judged behind `--body p1` before it

The demo is due 20 Nov (RESUME.md:109), four days out. A flip before it needs steps 0, 3, 4, 5a, 6 and 7 done and judged in about three days, while lanes A and D are still changing the inputs those steps consume. The case is in "Timings" at the end. What runs now is additive and leaves A's default bit for bit. The flip is then a one-gate day, about 21-22 Nov.

## What B lacks today that the plan must supply (found in this read)

1. **A's runtime helpers do not run on B.** People.cs:404-440: under `--body p1`, B gets P1BlendBase, the counter, the turn, P1Laws, P1Jiggle and HerFaceLife. HerJoints, HerShoulder, HerRaise and HerScap are A's only. So lane D's armor-only hinge bones (thigh_hinge_{l,r}, hiptasset_hinge_{l,r}, the centred V-tasset hinge, pauldron_hinge_{l,r}, all in rig_helpers.json and driven by HerJoints) do not exist on B. Their pivots are A-space numbers. Example: the pauldron hinge pivot is (.1914, 1.4786, -.0307). B's joints sit elsewhere (Harrington hip centre 19 mm forward; neck_01 at C7, Head at the skull base: PIPELINE P1 ledger 3).
2. **The kit is built on A.** kit_build.py:30 has `BODY = heroine.glb`, `her_a()` reads A's inverse binds, and the cast cache keys on A's verts. piece_ship's `body_follow_post` lands on heroine.glb and stamps `body_sha1`/`body_glb` from A.
3. **B's gear is git-ignored build output** (`/godot/art/gear/out/`, .gitignore:60). It is not on any branch. `gear_fit.py build --body godot/art/people/body_p1` remakes it. P2 lead 16 built and judged only the 9 plate-top units on B. The four callings' 30 slot rows, the 4 lod units and the other armor pieces were never looked at on B.
4. **Clips.** `body_p1/{clips,her_clips}.res` are the bridge, baked offline from A's `heroine.res` (bake_clips.sh: A plays each clip, P1Retarget.Map per frame). `p4_clips.res` is absent from body_p1, so no P4 overlay runs. If one were published, any same-name P4 clip would replace lane A's new clip on B (P1Body.cs:117, P4Overlay.Plan).
5. **Lane A (aim-move) is B-aware.** PlayerView.cs:268/483 uses IsB and takes B's libraries. PersonView.cs:697 goes through `P1Body.Bone` for the spine and neck. The limb filters are by limb names, which B shares. aim-move changes `godot/art/anim/heroine.res`, `heroine_clips.json` and the clip generators (run.py, sword.py, idle.py, prowl.py and others).

## The steps, in order

### Step 0. The body as an input to every game gear tool (needed for any flip; the A path bit for bit)
- `kit_build.py --body <glb>` (default heroine.glb). The joints come from that glb's inverse binds. `body_sha1` comes from the given glb. Cast cache keys include the body's sha1, not `V[:50]`.
- `piece_ship.py --body <dir>`: `body_follow_post` onto the given body, with the install's `body_glb` stamp per body. `--check` reads each row against its own body.
- Hinge pivots made bone-relative. Each pivot becomes an offset in its parent bone's rest frame, written once from A's numbers, so A gets the same pivot bit for bit and B gets its own joint's.
- B runs the helpers. P1Laws reads rig_helpers.json's armor-only helpers by bone name, after B's laws. It never touches her skin weights. Parity test like hinge_parity: A's HerJoints and B's P1Laws give the same hinge angle for the same pose.
- Acceptance: A's outputs are sha1-same with no flag (kit units, piece_ship installs). Hinge parity is 0.0000 deg on A. dotnet and pytest stay green.
- **Cost:** 2 su-worker jobs (flags 0.1M; hinge port and tests 0.15M), lead 0.05M, **~0.3M, 0 judges, 0 credits. Risk low.**
- **When:** kit_build.py is lane D's live file (demo-armor only). The flag change lands on demo-armor at a quiet point (lane D's own worker, by main's word) or after demo-armor merges. The P1Laws hinge port touches only P1Laws.cs and its test, so it can run now on body-b.

### Step 1. Marionette's body stage and gear stage as the pipe (what moves, and in what order)
**1a. Gear stage, decided by a bake-off (first, because it is the owner's goal).** Two fit engines exist. The game's `tools/armor/gear_fit.py` binds every vertex to a base TOPOLOGY triangle and evaluates on any body of the base. It carries two months of rules: tuck, joins and bridges, rigid plates, blend-shape carry, lod and shadow units. Marionette's `fitted` kind (`attach.py author --kind fitted --base`, fitbind/fitgates/hidemask) has rigid islands, one-sided clearance, the carrier and gates. Its gaps: no drawn silhouette gate, no base bend strips with the piece on, and the hide mask is not wired (HANDOFF_RND.md:91).
- Bake-off on B, three units: a strap top (plate_top_plain), a rigid plate (a cuisse), a cloth slot row (warden). Run gear_fit build and fitted on each. Compare gear_wear skin fails, fitgates bend and clip, and one in-engine look. The better engine becomes Marionette's gear stage, and the loser's good rules are ported into it (Marionette direction: bake-off, improve not preserve).
- What then moves out of `tools/armor` into the gear stage: the fit (bind/build), cover and pose_tuck, the gear_wear sweep (as a fitgates row), piece_ship's follow, top_bar, and kit_build's chart primitives as an authoring kind that takes `--base`.
- What stays in the game: `tools/armor/drop.py` (the import from `Marionette/generated/to_game/armor`), HerWear/ArmorIndex/GarmentTuck at runtime, the runtime helpers (HerJoints, P1Laws), and finishes and shaders.
- Rule from the re-seat finding (4f8b0cb11): a stage reads only tracked inputs, never Marionette scratch.
- **Cost:** bake-off ~0.5M (one su-lead-high solver, a runner), 1 max judge; the move after the pick ~0.4M (2 workers, lead check), 0 judges (acceptance by number: the moved engine rebuilds the same units sha1-same, or within 0.1 mm). **~0.9M + 1 judge, 0 credits. Risk medium** (gear_fit's rules are many, and tests pin them: 141 armor tests).

**1b. Body stage (a port: no pixel changes).** What moves out of `tools/body` (191 tracked files) into Marionette's body stage:
- loopplan.json + build_topo/topo_build;
- check.py with its bend strips;
- wrap, the sliders, correctives and the rig;
- topo_bake and the frozen R&D inputs (`tools/body/base/rnd`);
- publish_p1.py, as an export to `generated/to_game/body` plus a game-side `tools/body/drop.py` that writes `godot/art/people/body_p1`.

What stays in the game: bake_clips.sh (Godot), the gate shoots, P1Body and P1Laws.
- Acceptance, the round_40h pattern: Marionette's `body build her` reproduces round_39d sha1-same on body.glb, play.glb, rig.json, play_rig.json, pieces.glb/json. check.py exit 0, forms 68/68, the moved pytest 35/0, carried_target 94/0.
- Needs: a Marionette worktree and branch of lane G's own. The Marionette checkout is on `rnd-1` with 4 uncommitted edits that are not ours.
- **Cost:** 2 su-worker rounds (move, path rewire) ~0.4M, a runner (rebuild ~1 h, checks) ~0.05M, lead ~0.15M. **~0.6M, 0 judges, 0 credits. Risk medium** (cross-repo paths: the 16 Nov sweep broke the build once by deleting scratch it read; 1.7 GB out dir).
- **Order: after the flip.** It changes no pixel, so it never blocks a gate, and the flip's source does not move under it. It can run alongside 2.

### Step 1c. Marionette's rig and animation stage (added 16 Nov on the owner's word)
**The owner, 16 Nov 2026, word for word:** "marionette is supposed to handle animations as well.  its a one stop shop for generation and rigging and animating".

**What Marionette has today:**
- **Motion core** (`Marionette/tools/motion`: soma, rig, retarget, footlock, clip, cli). It reads SOMA motion (Kimodo or MotionBricks BVH) and retargets it onto B's skeleton as P4 clips. The game's `tools/anim/p4.py` imports it, and B's skeleton and the SOMA map live there as data (`tools/body/rig/b_skeleton.json`, `soma_to_b.json`). This is the stage's seed, and it already targets B.
- **NPC rigging:** the base-fit rig for people; UniRig and SkinTokens for creatures (local, MIT).
- **R&D rig and cloth work:** rebind, springsim, the X14 rig rounds.
- **The 1 Nov retarget fix:** the character's own neck and spine kept, the hands kept out of the hips (NPC clips).
- **Not there yet:** keyed-clip authoring (her game clips are procedural keys on A's rig, `tools/anim/clips/*.py`, `keyed.py`, `gait.py`) and any Godot pack step.

**What moves in, in order:**
- **R1. B's rig as stage data, inside the body stage (with 1b).**
  - What moves: `tools/body/rig`, `rig_map.py`, `weights.py`, `weights_topo.py`, `correctives.py`/`correctives.json`, `rig_drive.py`, `p1_rig_fixture.py`.
  - What it covers: the ~124 bones, the weights in body.glb/play.glb, and the correctives and girdle law in rig.json/play_rig.json.
  - What stays in the game: the runtime laws (P1Rig, P1Laws), as the readers of rig.json.
  - Acceptance: 1b's sha1-same rebuild of rig.json, play_rig.json and both glbs, and p1_rig_fixture parity with P1Rig.
  - **Cost:** ~0.3M on top of 1b, 0 judges. **Risk low-medium.**
- **R2. The runtime helpers as rig-stage data.** A's helper SPEC (`tools/anim/helpers.py`, rig_helpers.json) and lane D's armor hinges, with each body's pivots derived by the stage, not hand numbers.
  - Acceptance: the hinge parity fixtures on A and on B.
  - **Cost:** ~0.2M, 0 judges. **Risk low.**
  - **When:** after demo-armor merges, because it holds lane D's spec.
- **R3a. The clip bridge as a stage tool.**
  - What it is: `P1Retarget.Map` (A's clip onto B per frame) and the blend base ported to Python in Marionette, writing B's clip keys. A thin Godot pack step writes clips.res and her_clips.res, as `p4_pack.sh` does today.
  - What it retires: `bake_clips.sh` and `P1BakeRun.cs`.
  - Acceptance: on every clip in `p1_clips.json`, per frame, every bone within 0.01 deg and 0.01 mm of the script's bake; `clipcheck.py` green.
  - **Cost:** one su-lead-high solver + a worker + a runner, ~0.6-0.8M, 0 judges (by number). **Risk medium:** Godot's sampling and interpolation, track paths, and the her_clips meta all need parity.
- **R3b. Her clips authored on B's rig directly.** The keyed generators write B's bones (the role map for the spine). The bridge and A's loaded skeleton retire, and P4 becomes the stage's other input.
  - A1 designs it (PIPELINE P4).
  - **Cost:** ~1.5-2.5M + 2-3 motion judges against the owner's words: "run = whole body, live sword arm" and "Prowl must actually ship, no locked elbow". **Risk high:** every gait is retuned.
  - **When:** after the flip and after R3a.

**Can step 4's rebake (after aim-move merges) run through the stage?** Only if R3a has passed its parity by then.
- The script route costs ~0.05M (one runner).
- The stage route costs R3a's ~0.6-0.8M first, then ~0.05M per rebake after that.
- aim-move is due to merge within days, very likely before R3a exists. My call: run this rebake by the script. If R3a is ready by then, run both and diff them: the aim-move rebake becomes R3a's acceptance test, with no extra cost. Every rebake after R3a runs through the stage.
- **Order:** R1 with 1b (after the flip); R2 after demo-armor merges; R3a after the flip, alongside 1a; R3b after R3a.
- **Step 1c total:** ~1.1-1.3M with 0 judges (R1, R2, R3a), plus R3b ~1.5-2.5M + 2-3 judges.

### Marionette stage list (the owner, 16 Nov: "remember to always keep marionette looped in for anything were building in modeling rigging animating so we can reproduce it")

Every build stage for her on B, rerunnable from source, with the body as an input. A hand fix is allowed only when it lands in the source Marionette rebuilds from (the owner, 16 Nov: "well it can be fixed by hand if the fix ends up in the body in marionette.  you know?  specific stuff on per npc basis obv is different").

- **Lane A (movement and animation):** `tools/anim/clips/prowl.py`, `tools/anim/clips/run.py`, `tools/anim/clips/sprint_stop.py`; `tools/body/bake_clips.sh`; `tools/anim/fit/fr.py`, `tools/anim/fit/carry_read.py`, `calf_radii.py` (path to confirm), `tools/anim/fit/ana10.py`, `tools/anim/fit/t10.py`, `tools/anim/fit/runsame.py`; `godot/logic/Play/SideCarry.cs` with `tools/anim/fit/carry_targets.json` ("runtime_body_constants").
- **Lane D (armor):** `kit_build` (path to confirm); `tools/armor/piece_ship.py`, `tools/armor/piece_blender.py`, `pin_shipped` (path to confirm), run with B's blend `body_p1_built.blend` (path to confirm) and `AREOLA_OUT=0`; `tools/armor/cover.py`; `tools/armor/wearcheck.py --confirm`; runtime hinges (A: `godot/src/Actors/HerJoints.cs`; B: `P1Laws` (path to confirm; referenced from `godot/src/Actors/HerWear.cs`, `HerLod.cs`) via `godot/art/people/rig_helpers.json`); `GarmentTuck.Over` by built_on (`godot/logic/Rpg/GarmentTuck.cs`).
- **Lane G (her body):** `b_clip_json.py` (path to confirm), `b_build_blend.py` (path to confirm), `tools/anim/helpers.py --body p1`, `p1_hinge_parity_fixture.py` (path to confirm); the gear refit recipe rules in `tools/armor/rigid_roles.json`: hang_rule + studs, a_blend/a_leads, close-view standoff, tuck depth, group fit. Parked, off by data: STACK, stack_tucked, cup_rule, band_end, a_points.

### Step 2. The generated-piece route: Meshy or a local generator, fitted onto B through Marionette, no hand fitting
The route (✓ exists, ✗ missing):
1. Concept: ChatGPT route or Krea, free. Then a max concept judge. ✓
2. Generate: TRELLIS.2, local in ComfyUI, free, while we learn the route. Once the route is smooth, Meshy/Rodin/Tripo first, each spend needing a yes (the owner, 16 Nov). Meshy only on main's word, on a judged concept (`tools/meshy/cli.cjs gen --kind prop --no-texture`, 20 credits; retex 10). ✓
3. Clean: forge `prop_bake.py` (reduce and rebake), smartmesh remesh, HoloPart split into parts, delight; drop body fragments the generator baked in. ✓ (built for props and NPCs, not yet run on armor; HoloPart's install was binned 16 Nov, so reinstall it with `tools/forge/holopart_setup.sh`, or ask the owner first)
4. **Place: ✗, the core gap.** A generated piece floats in its own space and scale, and `author --kind fitted` needs it standing on `--base` at rest. A new `attach.py place <piece> --slot forearm_l --base body_p1/body.glb`:
   - landmark registration onto the slot's region (base_landmarks.json), then a similarity fit;
   - a non-rigid wrap of the piece's inner surface onto B's skin shell at the slot's clearance;
   - the outer form kept (only the inner shell is laid);
   - the mirrored partner made from one side.
5. Author: `author --kind fitted --rigid <plates> --hide`, with rigid islands riding a named hinge (data: the step-0 helpers). ✓ except hinge riding ✗.
6. Gates:
   - fitgates bend/silhouette/clip;
   - a clip sweep on B over idle, run, sword_heavy, leap (lane D's measure: skin through the piece by more than 2 mm = 0);
   - mirror median <= 5 mm;
   - triangle budget per tier.

   ✓ partly: the clip sweep over the game clip set on B and the drawn silhouette gate ✗.
7. Repaint: to the kit's finishes (outfit_materials.json, metal_finishes.json: the cel look), not the generator's PBR. ✗ (glue)
8. Export: to `generated/to_game/armor`, then the game's drop.py, then an index row (ArmorIndex.GearDir on B). ✓ drop, ✗ fitted-to-index export.

Later, onto the female roster: F2 (not started) wears the same pieces through the carrier, X20, bar PROBE_X20.md:118-134. The carrier's limits: no gloves or boots (hands and feet), no helm (head at mouth level), no closed sleeves. So the kit's gloves, boots and helm on F2 are an open gap of their own.

**First proof piece: the vambrace pair.**
- Generated from lane D's own kit concept (kit 01_turnaround), so the judge compares it like for like with lane D's hand-built vambrace, which judge round 2 kept.
- One main bone with twist tests the rigid/bend split. The pair tests the mirror. It reads at the play camera. It carries no chest or sex-appeal risk on the route's first run.

**Acceptance (all of it):**
- No hand edit on any output: every fix goes in the tool or its data.
- Skin through the piece by more than 2 mm = 0 over idle, run, sword_heavy, leap on B.
- A rigid plate bends 0 (max strain <= 1%).
- Mirror median <= 5 mm.
- Triangles within ±20% of lane D's vambrace.
- One max judge at 1:1 (close front and back, play camera, a run hold): reads at or above lane D's vambrace on the same concept.
- Concept-to-in-game logged at <= 0.3M tokens for the piece.

**Second proof, the real test of "just fits": one pauldron.** By hand on A it took 15 solver rounds. If the route places and fits it at the judge's bar with at most one fix round, the route is proven.

- **Cost:** place tool ~0.5M (one su-lead-max solver + a worker); route glue (repaint, export, clip sweep on B) ~0.25M (2 workers); proof 1 run ~0.3M; judges 2 (concept 1, piece 1) + 1 spare round; proof 2 ~0.4M + 1 judge. **~1.5M + 3-4 judges. Credits: 0 with TRELLIS.2; 30 per piece (20 mesh + 10 texture) only if TRELLIS fails it and main says yes. Risk high** (generated meshes come non-manifold, with fused body parts and wrong scale; placing on the shoulder is the hard one).
- **Order:** after step 0 (the hinge riding) and 1a (the gear stage it lands in). Starts the day after the demo.

### Step 3. Her starter outfits refit on B (P2)
- The units: the four callings' 30 slot rows + 4 lod units (godot/art/people/armor_index.json) and 10 armor pieces (godot/art/armor/armor_index.json).
- The run: `gear_fit.py bind` + `build --body godot/art/people/body_p1`, which exists today. Then the gear_wear sweep and fixes at the source.
- Known faults:
  - the plain plate top fails at play (51/2130);
  - strap fins sit ~2 cm above the shoulder line (P2 l16 OPEN 1);
  - the gilded gold reads matte tan.
- Then an in-engine shoot on B: the 4 cameras + run/sword holds, A|B. ONE max judge per sheet.
- **Cost:**
  - **Warden (the demo calling):** ~0.5M (solver round for the fails, runner, sheet) + 1 judge.
  - **Reaver, ranger, arcanist:** ~0.4M + 1 judge (one sheet).
  - **The plate sets:** ~0.25M + 1 judge if kept, or 0 if retired (P2 lead 16: "takes a new kit, not a revision"; lane D's kit is that kit). Open question 2.
- **Total ~0.9-1.15M + 2-3 judges, 0 credits. Risk medium.**
- **When:** the Warden now, behind the flag (no lane touches gear_fit). If 1a's bake-off picks fitted, the refit reruns through the stage after the flip by command.

### Step 4. Her clips on B's rig (her_clips.res); lane A's aim-move
- **How B takes lane A's clips:** by the bridge, unchanged. When aim-move merges into integration (main says when), body-b merges integration and a runner reruns `bash tools/body/bake_clips.sh`. That remakes clips.res and her_clips.res from A's new heroine.res, then `clipcheck.py` runs on B.
- No clip is hand-touched on B. A stays loadable offline as the bridge's source until P4 (clips authored on Marionette's base rig, A1's design) retires the bridge.
- `p4_clips.res` stays unpublished, or A's run would be replaced on B (fact 4).
- **The risk the judge must look at:** B runs no HerShoulder, HerRaise, HerScap or HerJoints. B's girdle law and correctives do that work. So the owner's motion words read differently on B: "run = whole body, live sword arm" and "Prowl must actually ship, no locked elbow" (15 Nov).
- Check: an A|B motion sheet at the play camera (run, sword strikes, Prowl idle, held frames) + a short film. ONE max judge.
- **Cost:** runner 0.05M, sheet 0.1M, judge 1. If B's shoulder reads worse in the new sword clip: a solver round on B's girdle law, ~0.3M + a re-judge. **~0.3-0.75M + 1-2 judges, 0 credits. Risk medium.**
- **When:** before the demo, run on today's clips to find B's motion faults early. Again after aim-move merges, once.

### Step 5. The hair re-attach (P1Body.Rebind)
- **5a, for the flip.** Keep the runtime rebind (HairSway.cs:137: A-skinned hair rebound onto B once at load). It fits because B's head is A's head at A's world rest. Check braid, ponytail and pixie on B at the 4 cameras + motion: sway, ear shapes, no gap at the nape. This goes in the flip sheet, with no judge of its own. **~0.1M.**
- **5b, after.** Marionette's hair stage binds the hair to B's skeleton offline. The post steps, in order: heroine_ear_shape --follow-only, heroine_shape_falloff, heroine_pixie_ear --style, heroine_hair_cut_ends.py. The runtime Rebind is then retired.
  - Acceptance: the offline-bound hair equals the runtime-rebound hair per frame, <= 0.1 mm, on the three styles.
  - Cost: **~0.25M, 0 judges. Risk low.**

### Step 6. The default flip (P1Body.cs:35)
- `On` becomes B unless `--body a`. A is kept loadable for the clip bridge and as the fallback. Also: People.cs:116's default, every lane's harness flag, and the tests.
- Gate: the whole-frame 1:1 game-frame gate. Her on B in the Warden outfit, with hair, the kit and motion: town, den and play camera, A|B. ONE max judge, then the owner's yes.
- **Cost:** worker 0.1M, runner suite 0.05M, shoot and sheet 0.15M, judge 1. **~0.3M + 1 judge + the owner's gate. Risk:** the tuned numbers of lanes D and E shift, so each re-measures once on B.

### Step 7. Lane D's kit (demo-armor) re-shipped onto B, the body an input to its recipes
- After step 0 and demo-armor's merge:
  - `kit_build.py --body godot/art/people/body_p1/body.glb` for the 8 pieces (kit_bodice, kit_belt, kit_boots, kit_brief, kit_gloves, kit_helm, kit_pauldrons, kit_vambraces);
  - `piece_ship.py --body body_p1`;
  - the hinges on B (step 0).
- Then rerun every clearance lane D runs (idle, run, heavy sword, leap; bodice to pauldrons; brief to belt; skin to each piece). Reshoot lane D's judge set on B. ONE max judge A|B, kit on A against kit on B.
- The A-space numbers in the recipes (kit_hips pivots (±.115, 1.125, .075), outlines and apexes tuned on A's surface) move to bone-relative or landmark-relative data in step 0. Without that move this step is a re-tune, not a re-ship.
- **Cost:** worker 0.15M (numbers to landmarks), runner sweeps 0.1M, fix rounds 1-3 × ~0.3M (B's girdle law moves the clavicle differently, so the pauldrons and bodice carry the risk), judges 1-2. **~0.55-1.15M + 1-2 judges, 0 credits. Risk medium-high.**
- Long term: the recipes become the gear stage's authoring kind (1a) and take `--base`, so F2 is the same command.

## Cost table

| # | Step | When | Tokens | Judges | Meshy | Risk |
|---|---|---|---|---|---|---|
| 0 | the body as an input (kit_build/piece_ship `--body`, bone-relative pivots, hinges in P1Laws) | P1Laws port now; flags at D's quiet point or after D merges | ~0.3M | 0 | 0 | low |
| 1a | gear stage: bake-off gear_fit vs fitted on B, the winner moves to Marionette | after the demo | ~0.9M | 1 | 0 | medium |
| 1b | body stage: tools/body moved, sha1-same rebuild | after the flip | ~0.6M | 0 | 0 | medium |
| 1c | rig and animation stage: R1 B's rig (with 1b), R2 helpers as data, R3a clip bridge in Python (parity), R3b clips keyed on B | R1/R3a after the flip; R2 after D merges; R3b after R3a | ~1.1-1.3M + R3b ~1.5-2.5M | 0 + R3b 2-3 | 0 | low-medium; R3b high |
| 2 | generated route: place tool + glue, proof 1 vambraces, proof 2 pauldron | after 0 and 1a | ~1.5M | 3-4 | 0 (TRELLIS.2); 30/piece only with main's yes | high |
| 3 | starter outfits on B: Warden; other callings; plate sets if kept | Warden now behind the flag | ~0.9-1.15M | 2-3 | 0 | medium |
| 4 | clips on B: rebake after aim-move, motion judge | probe now; once after A merges | ~0.3-0.75M | 1-2 | 0 | medium |
| 5 | hair: 5a check in the flip sheet; 5b offline bind | 5a with 6; 5b after | ~0.1M + 0.25M | 0 | 0 | low |
| 6 | the default flip + whole-frame gate | after the demo | ~0.3M | 1 + owner | 0 | medium |
| 7 | lane D's kit re-shipped on B | after D merges | ~0.55-1.15M | 1-2 | 0 | medium-high |
| | **To the flip (0, 3 Warden, 4, 5a, 6, 7)** | | **~2.05-3.1M** | **4-6** | 0 | |
| | **The pipe (1a, 1b, 1c, 2, 3 rest, 5b)** | | **~4.75-5.2M + R3b ~1.5-2.5M** | **5-7 + R3b 2-3** | 0-60 | |

## Timings

**A. Flip before the demo (by 20 Nov).**
- Work: steps 0, 3 Warden, 4, 5a, 6 and 7, ~2.05-3.1M + 4-6 judges, packed into ~3 days. Add the re-measure tax: lanes D and E each re-run their tuned numbers on B (~0.3M each), and lane A re-checks its motion on B (~0.2M). **~2.85-3.9M + 5-7 judges.**
- What it does to lane D: its judge round 3 (pending) and every clearance are on A's surface with A's HerJoints hinges. Their pivots are A numbers, so its next judge waits for steps 0 and 7, or it is judged twice, on A and then on B.
- What it does to lane A: aim-move is on merge hold, so B's clips would be baked twice, today's and A's new ones. The motion judge for the owner's "live sword arm" and "Prowl" words runs on B's girdle law, never yet judged in motion.
- What it does to lane E: the den and town looks were measured on A's skin. The bare judge already named a shared fault: the town sun washes the torso paler than the face.
- Risk: **high.** A failed B judge on 19 Nov leaves the demo half-moved. The flag goes back to A cheaply, but the kit would then exist in two builds.

**B. Flip right after the demo (~21-22 Nov).**
- Now, behind the flag, touching no lane's files: step 0's P1Laws hinge port, step 3 (Warden) and the step-4 probe on today's clips. After the demo: steps 0's flags, 7, 4's rebake, 5a and 6 in one run, then the pipe (1a, 2, 1b, 5b).
- **~2.05-3.1M + 4-6 judges to the flip.** Lanes D and E re-measure once, after their demo work is locked (~0.5M), with no re-measure inside the demo.
- Risk: **low for the demo.** B is the default 1-3 days after it.

**Verdict: B.** The work to the flip costs the same either way. The only difference is a ~0.8M re-measure tax and high risk landing inside the demo's last three days, on the two lanes whose output is most visible on her. Doing the safe parts now keeps the flip to a single gate.

## Open questions for the owner
1. **Timing:** B in the demo at the cost and risk of A (about +0.8M and a real chance the demo ships half-moved), or B the day after the demo (my verdict)?
2. **The old plate sets** (10 pieces, judged CLOSE; P2's lead: "takes a new kit, not a revision"): retire them now that lane D's kit is the new kit, or refit them on B (~0.25M + 1 judge)?
3. **The other three callings** (reaver, ranger, arcanist): the flip makes B every calling's body. Build all four by command and judge them on one sheet now (~0.4M + 1 judge), or hold them out of play until their slices?
4. **The first generated proof piece:** the vambrace pair from lane D's concept (my pick: like-for-like with a hand-built piece), with a pauldron as the real test; or a torso piece first?
5. **The generator:** ANSWERED (16 Nov): TRELLIS.2 while learning the route; once the route is smooth, Meshy/Rodin/Tripo first, each spend needing a yes. (Old question: TRELLIS.2 locally first, Meshy only if it fails a piece.)

## For main (not the owner)
- Lane G needs a Marionette worktree and branch of its own for 1a, 1b, 2 and 5b. The checkout is on `rnd-1` with 4 uncommitted edits that are not ours.
- Step 0's kit_build/piece_ship flags touch lane D's files: by lane D's worker at a quiet point, or after demo-armor merges. Main decides.
- Tell lane G when aim-move merges (step 4's rebake).
