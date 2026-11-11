# Motion plan: every clip of hers, the P4 pipeline, and Stage B

A1 Stage A (motion director, 5 Nov 2026).

What this page draws on:
- The rules: `MOTION_BIBLE.md`.
- The facts: `docs/design/motion/inventory.json` (every clip she plays: 115 built and 30 UAL names), `measures.json` (today's idles, measured) and `tools.md` (the checked tool and licence table).
- The per-clip table: `docs/design/motion/plan_table.md`, generated from the inventory by the A1 plan script (backed up to `survivorsunchained_inputs\motion_a1\plan.py`).

The owner's rule: "upgrading by redoing if needed and not just trying to patch whats already there". Nothing is kept because it is already there.

## 1. The inventory, by disposition

| Disposition | Clips | What it means |
|---|---|---|
| **REBUILD** | **98 + 10 new = 108** | The core set, re-authored to the bible on the new rig through the pipeline: every calling's town and fight idle and its breaks, walk, run, sprint, stops, the dash and the arts, every attack and cast, hit, death, get-up, the creation shows, the title's sit_log, and the Flare press. The 10 new ones are 8 town breaks (2 a calling, R5.2), the Warden's Iron Vow brace (replacing UAL Sword_Block) and a hit from behind. |
| **RETARGET** | **10** | The long tail, moved by the global-match retarget and judged at its shot. Cinematic one-offs (cup_hands, letter, take_from_log and 2 more) and 7 UAL CC0 one-offs with no own clip yet (Spell_Simple_Enter, Sitting_Idle_Loop, PickUp_Table, Roll, two jumps, Punch_Cross). |
| **CUT** | **37** | 14 built clips the game never plays: the C01 lying and kneeling clips, nod, exhale and shiver, flask_drink, wade, walk_tired, walk_uphill, chain_strike (cut by the owner), flare_burns_twice. They are re-made through the pipeline only when a film or skill cues them. The other 23 are UAL names that her own clips now cover; a test asserts no UAL name reaches her. |

**Licence finding:** 16 of her clips are 100STYLE (CC BY 4.0, which needs credit). They are every fight idle, every town idle, flask_drink, wade, walk_tired and walk_uphill. Under the owner's no-credit rule they cannot ship: the 12 idles are REBUILD, the 4 others CUT. Kimodo (11 walks) and Mixamo (the leap) need no credit, but those clips are REBUILD on merit anyway.

**Why so little retargets.** Today's clips are sixty-two passes of keys and fixes, on a 100-joint kit skeleton with no twist chains, a stiff spine, and no breast or glute bones. Measured, every idle but the Warden's town sway moves the pelvis under 2 cm (under 0.6 px at play): that is the rigidity the owner names. A retarget keeps every old fault on a better rig. Retarget is only for what nobody stares at.

## 2. The tool pick (from `tools.md`; no credited output ships)

| Use | Pick | Why | Not picked, and why |
|---|---|---|---|
| In-betweens between our key poses, and steered locomotion | **MotionBricks** (NVIDIA; code Apache-2.0; weights under the NVIDIA Open Model Agreement: "NVIDIA does not claim ownership to any outputs", no credit on outputs). Already in Marionette for one walk. | Its inbetweener takes OUR key poses as targets and fills physically natural motion between them at 30 Hz. That is exactly the bible's form: we author the poses that carry the taste, and it supplies the weight transfer. | Its bundled sample clips are evaluation-only, so it is steered only by our own poses and nothing from those samples ships. |
| Long or constraint-heavy motion (falls, get-ups, airborne arts, cinematic actions) | **Kimodo** (NVIDIA; the same agreement; text + keyframes + end-effector targets + root paths). Installed, the Llama gate already accepted. | Keyframe and root constraints, and game-oriented training data. Its outputs need no credit, and the Llama licence doesn't reach them. | Its SEED checkpoints (whether the BONES-SEED credit reaches them is unverified): use the RP checkpoints only. |
| Performative one-offs | **SAM 3D Body + MHR** (local ComfyUI) on footage we own | Broad gestures for films. | Never for combat timing (jitter, floating contacts). |
| The deepest tail | Mixamo, CMU, Quaternius UAL (no credit) | Rare clips, retargeted. | 100STYLE (CC BY); BONES-SEED (credit, a $1M revenue cap, a $480k commercial licence); DeepMotion (it claims the product); Cascadeur (GUI-only; $96-396 a year; the Indie tier capped at $100k revenue; MotionBricks with our check does its job); Auto-Rig Pro and Rokoko (the retarget is ours, in Marionette). |

**No purchases. No owner action needed.**

## 3. The P4 pipeline: one source, one build, one check, one judge

**The source is one clip spec per clip:** `tools/anim/specs/<clip>.json`, with its key poses in `tools/anim/poses/<set>.json`. A spec holds:
- the clip, calling, kit, layer, loop and length;
- the bible rules it answers, with its bands (pelvis travel, sway cycle, breath period, cadence, contact, hold and cancel frames);
- the keys (time, named pose) and the in-between engine and seed;
- the layers (breath, sway, contrapposto, gait list and yaw, overlap chain);
- the contacts (a hand on the hip, the pommel, the staff, with time windows), the props and their mounts (the sword hung 12-15 cm lower in town);
- a parent, so variants derive (town or weapon variants, the `_run` uppers, mirrored stops).

A judge's note changes a spec, a pose or a bible band, then the clip rebuilds. Nothing is hand-fixed on a packed clip.

**The build is one command:** `python tools/anim/build.py <clips...>`, rewritten as a thin front over Marionette's motion core. For each spec:
1. The key poses are mapped from the base rig to SOMA (one calibrated map, built from P1's `skeleton.json` landmarks).
2. MotionBricks fills the in-betweens through the keys (Kimodo where the spec says so).
3. The result is retargeted onto the base rig: limbs by direction, the spine spread over five joints, twists left to runtime.
4. The bible layers run, then foot lock and the contact solve (two-bone IK to the spec's contacts).
5. The clip is written to the game contract (the clip JSON plus heroine_clips.json: speed, steps, layer, contact, hold, cancel).
6. Godot packs it (anim_pack.gd).

The same spec builds on any body on the base: her, or an NPC with its own proportions.

**The check is one command:** `python tools/anim/check.py <clips...>`. Every row of the bible's §14 is a number with a pass band: foot lock, contacts, self-intersection (arms against torso and breasts, weapons against her), idle life, the rest S-curve, tension, head stillness, cadence at the game speed, overlap delays, attack frames, the play-read in px. It runs on the packed clips (what the game plays) and fails loudly. The judge never sees a clip that fails the check.

**The judge is the motion judge**, on game shots (`tools/turn.py take godot "motion-a1: <what>"`). It asks the whole-frame question, "effortlessly badass?", at the play camera and the close-up, 1:1, at max for core motion (idles, runs, main attacks) and xhigh for the rest, one judge per calling slice on one sheet.

**The runtime (game C#):**
- R6.2's springs on the breast, glute, braid and skirt bones, with parameters per kit as data (HerJiggle generalised);
- twist and share drivers (P1's laws);
- grips by weapon type (fistfit's standard);
- one combat change: the sim fires a swing's damage at the clip's contact frame, scaled by attack speed. Today "contact" is read by no C# and the damage does not follow the clip. This goes to the combat lead with the Warden slice.

### What lives in Marionette, and what stays in tools/anim (the owner: "make marionette the pipe")

| Stage | Lives in | Why |
|---|---|---|
| The base rig (P1's 124-bone skeleton becomes Marionette's rig) | Marionette | One rig for her and every NPC on the base (P1, P3). |
| Pose authoring (IK handles on the base rig, the bible's bands shown live) and the spec editor (keys on a timeline) | Marionette (Animate panel) | The owner's click path, reusable on any body ("the app can now pose a clip and build it"). |
| The motion core: base-to-SOMA map, the MotionBricks and Kimodo bridges, retarget, layers, foot lock, contacts, the check | Marionette `tools/motion/` (Python, called by the server for the app and by the game CLI for batches) | ONE implementation: the app's preview runs the same build, so nothing drifts between a JS preview and a Python build. |
| Preview at the play and close-up cameras | Marionette gamelook | Already mirrors the game's shaders and cameras. |
| The specs and poses (the source of truth) | game repo `tools/anim/specs`, `poses` | Shipped data is versioned and pushed. Marionette has no remote. |
| build.py and check.py (batch fronts), the pack, heroine_clips.json, game shots, tests | game repo `tools/anim` | They need Godot and the game's data. Tests assert the spec schema, the check bands, and "no UAL name reaches her". |
| Runtime springs, drivers, grips, the contact-timed damage | game C# | Engine side. |

**Risk:** Marionette has no remote, so the motion core would live in an unbacked repo that the game's build depends on. Fix: give Marionette a private remote before Stage B, or vendor the core into the game repo at each merge.

## 4. The long tail (P1's retarget list, re-costed)

P1 listed five pieces of work for the old skeleton's clips:
- (a) global-match retarget;
- (b) the UAL library baked onto the new skeleton;
- (c) the keyed Rig and skeleton JSON regenerated;
- (d) bone-name audit across about 30 C# files, grip_spec, fistfit, arms_local and the cinematics cues;
- (e) hero and folk untouched.

With 108 clips rebuilt, (a) and (b) shrink to 10 clips (~0.05-0.1M). (c) is replaced by the motion core. (d) stays (~0.15-0.25M, a worker plus a test). (e): the folk and crowd rigs are decided at Stage B's end, since P3's base rig shares the skeleton, so the folk can run the same pipe. Long tail total **~0.2-0.35M**.

## 5. Stage B: the plan and its cost (after P1's bare-shape gate; its own brief from this page)

Order:
1. **The pipeline:** the spec schema, the pose tool, the motion core (map, bridges, retarget, layers, check), the build and check fronts, the contact-timed damage. The proof is one clip end to end: idle_warden_town, the owner's sway rebuilt to R4.2's band. **~1.2-1.6M.**
2. **The Warden slice** (about 27 clips: town and fight idles and breaks, walks, runs, sprint, stops, the sword trio, the brace, bull_rush, dash, hit, death, get-up, warden_show, the Long Cut press), shot at the game cameras, one max judge on the slice. **~1.0-1.4M.**
3. **Reaver, Arcanist, Stalker**, about 22 clips each. The pipeline repeats, so the cost falls: **~0.6-0.9M each, ~1.8-2.7M** together.
4. The long tail and cuts, **~0.2-0.35M**; then the folk and crowd decision, **~0.1M**.

**Stage B total: ~4.3-6.2M tokens.** API $0 (judges as subagents), light GPU turns (MotionBricks and Kimodo), about 40-60 h of wall time across the four slices. The per-clip table sums to about 4.7M with no learning curve; the range assumes the variants build from their parents' specs.

**What a clip costs once the pipeline exists** (reported as "P4: the app can now X; this clip cost Y; the next costs about Z"):
- a town idle: ~70k the first, ~40k the next;
- an attack: ~90k the first of its weapon class, ~40k the next, ~15k for a `_run` variant;
- a locomotion cycle: ~60k a calling, ~20-35k a variant;
- a retarget: ~10k.

## 6. Risks

- **MotionBricks on our key poses.** The base-to-SOMA map must carry our poses into its target format, and it decides transition length itself. If it fights the bible's frame counts (attacks), those clips use authored keys with a spline in-between plus the overlap layer, and MotionBricks serves locomotion and idles only. The Warden proof clip shows which.
- **The game contract changes** (contact-timed damage, per-calling run speeds without playback stretch) touch combat. They are routed to the combat lead with the Warden slice.
- **The boards are direction, not final art.** Where a board and the bible disagree, the text governs (the bible's last section).
