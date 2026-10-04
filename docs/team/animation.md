# Animation: status

Branch `worktree-agent-a1e3002b800ee55ac`. Agent a1e3002b800ee55ac has handed off; a successor reads `docs/handoff/animation.md`.

## State (2026-10-04)

- **Her clips:** 68 in `godot/art/anim/heroine.res`, all listed in `tools/anim/manifest.json`.
  - `death_back`: struck from in front, she goes over onto her back. PlayerView chooses it by where the killer stands. Debug: `--die T [--behind]`.
  - C01's `lie_side_wake`, `sit_back_heels` and `reach_coals` (`clips/story.py`), judged on sheets only.
- **The crowd's own motion** (`tools/anim/crowd.py`, packed into `folk.res` for both kit bodies):
  - the Risen lurch at the crowd's pace (`lurch`, `lurch_armed`);
  - the casters' rally (`rally`, `rally_armed`).
  - The wolf's howl is a `cast` role in `Beasts.cs`.
  - The VAT cache is v9.
- **Townsfolk:** 20 clips in `folk.res`, unchanged.
- **Tool:** `godot/tools_scenes/crowd_sheet.gd` draws any crowd kind's role as a contact sheet.
- **Tests:** 539 pass.

## Kimodo, for the owner

- **To run:** double-click "Run Kimodo" on the Desktop, once this branch is merged into the main checkout.
- **Order:** it makes these first, then the rest:
  1. lie_side_wake, sit_back_heels (C01; keyed versions exist, the takes are for comparison);
  2. rise_stiff, bend_lift (C02's Warden);
  3. kneel_shoot, slam (combat's crossbowmen and heavies);
  4. kneel_fall (C03), flask_drink (C04).
- **Safe to stop:** prompts already made are skipped, so it can be stopped and run again.
- **Total:** 30 of the 55 prompts are still to make.

## Clips for the cinematics (af7a79bc783cca7bc)

- **Landed** (play as `her/<name>`): lie_side_wake, sit_back_heels, reach_coals. Still to be judged in C01 itself.
- **To key by hand:** the nod, the exhale and the shiver.
- **Waiting on Kimodo:**
  - C01: letter, kneel_to_stand_snap, take_from_log, cup_hands.
  - C02, the Warden on the kit male skeleton: lie_arm_up, rise_stiff, wade_drag, bend_lift; bowed_turn for the drowned.
  - C03: kneel_fall, reach_flinch.
  - C04: wade_out, sun_face, flask_drink, walk_uphill, unfold_arms, ladder, well_bucket, child_run.
  - Grimtunnel: burst_hug, sniff, laugh, dive. He is on the lampling rig, so these need a Beasts.cs composition or a retarget.

## Next

1. Corpse variety for the experience director: die, die2 and die3 per crowd rig, the risen and the wolves first. They'll wire the pick by seed.
2. The male hero's library: "him/", `hero.res`, masculine carriage. hero.glb is pushed on `worktree-agent-ae2de192cce8298ca@6df994d`.
3. The cinematics' hand-keyed clips, then their Kimodo clips.
4. Combat's kneel_shoot and slam once Kimodo has run.
5. Polish: chain_strike's crouch on landing, and a heavier flinch over runs.

## Key decisions

- **Ill-fitting takes are rejected.** Mixamo and Kimodo takes that don't fit the game's action are not bent to fit, so the arts, her backward death and the dead's walk are keyed.
- **Clips are made per skeleton:** hers, the kit women's, the kit men's, and his next.
- **Casts play from their own start.** One generic rally covers every person caster until each has its own; slammers keep their windup.
- **Unjudged clips stay out of full builds** (`JUDGED` sets), because HerClips plays anything in her library at once.

## Notes for other areas

- **Combat:** CrowdView's cast time is `e.AnimT`, and the raise resets it (agreed).
- **Performance:** HerPose's cached bone indices are kept.
- **Main session:** the owner's Kimodo run is the only blocker for most of the cinematics' motion.
