# Animation: status

Agent a1e3002b800ee55ac, branch `worktree-agent-a1e3002b800ee55ac` (took over from aa4f5fc266b043035). The brief, history and gotchas are in `docs/handoff/animation.md`.

## State (paused for the owner's usage limit, 2026-10-04)

- **Her clips:** 65 in `godot/art/anim/heroine.res`; `tools/anim/manifest.json` lists them.
  - New: `death_back` (keyed, `clips/actions.py`). Struck from in front, she staggers back, sits down hard and goes over onto her back, a knee fallen out. PlayerView plays it when `Player.LastKiller` stands in front of her; struck from behind, or killed by poison or burning, she still falls face down (`death`). Judged on sheets and in the game.
  - Debug flag: `--die T [--behind]` fells her T seconds in.
- **The Risen lurch** (`tools/anim/dead.py`, packed by `folk.py` as `f_/m_lurch` and `f_/m_lurch_armed`):
  - Keyed from the stride solver at the crowd's pace, 2.6 m/s on the skeleton. Captured shambles move at 0.6–1 m/s, against the Risen's 2.7, and the old zombie walk skated.
  - Pitched forward; the left leg dragged round on a hitched hip; the head hung and lolling.
  - One hand reaches like a claw. Armed, the weapon hangs and trails and the free hand reaches.
  - Any kit body asked for `Zombie_Walk_Fwd_Loop` gets it in the bake (`Vat.Clip`, `FolkClips.Undead`).
  - The crowd plays a walk of known pace at the rate its feet need (`VatAsset.Pace`, CrowdView). The VAT cache is v8.
  - Seen in the game with risen, warriors, archers and grave callers.
- **Kimodo, for the owner:** double-click "Run Kimodo" on the Desktop (after this branch is merged into the main checkout). It makes these first, in this order, then the rest:
  1. lie_side_wake, sit_back_heels (C01's wake);
  2. rise_stiff, bend_lift (C02's Warden);
  3. kneel_shoot, slam (combat's crossbowmen and heavies);
  4. kneel_fall (C03), flask_drink (C04).
  Prompts already made are skipped, so it is safe to stop and run again.
- **Kimodo:** 30 new prompts are pushed (f802ed3) and the owner's run is still to come. That run is the only blocker for the cinematics clips and for combat's kneel-to-shoot and slam. The 25 earlier prompts are all made.
- **Merged:** the integration branch and combat's `worktree-agent-ac4ec5bbd2763a0df@71608a4` (their new kinds), so I can test against them. All 532 tests pass.

## Clips landed for cinematics (af7a79bc783cca7bc)

- None yet. They play as `her/<name>`; the Warden's will be on the kit male skeleton.
- C01 prompts: lie_side_wake, sit_back_heels, letter, kneel_to_stand_snap, take_from_log, cup_hands.
- C02: lie_arm_up, rise_stiff, wade_drag, bend_lift, bowed_turn.
- C03: kneel_fall, reach_flinch.
- C04: wade_out, sun_face, flask_drink, walk_uphill, unfold_arms, ladder, well_bucket, child_run.
- Grimtunnel (burst_hug, sniff, laugh, dive) is on the lampling rig and needs a separate retarget.
- To key by hand: reach_coals (upper layer, holds 3 s), the exhale, the shiver, the nod. Their order of priority: lie_side_wake/sit_back_heels, rise_stiff/bend_lift, kneel_fall, flask_drink, the shiver.

## Next

1. Combat's list (their message of 2026-10-04):
   - the wolf's howl, keyed as Beasts.cs `Vat.Moves` on the wolf rig in a "cast" role. CrowdView's Casting state uses `t = time`; it needs time since the cast began (check `Ai.cs` ~l.222/429 for how StateT runs);
   - one generic "rally" (an arm raised and shaken), keyed on the kit bodies, as the cast clip for skeleton_mage, kerchief_hooded and kerchief_enforcer;
   - kneel-to-shoot (Kimodo `kneel_shoot`) for skeleton_rogue, and a `kerchief_hooded` variant with a crossbow;
   - the two-handed slam (Kimodo `slam`) for kerchief_brute and skeleton_minion; the lampling's slam is a Beasts.cs composition.
2. The cinematics' hand-keyed clips (above), then their Kimodo clips when the run lands.
3. Polish: the strike's crouch on landing; a heavier flinch layered over runs.
4. The male hero (ae2de192cce8298ca): his own library from the same code. Planned as `build.py --body hero` → `hero.res`, prefix "him/", with masculine carriage. Waiting on his skeleton (hero.glb on their branch, dumped by `anim_skeleton.gd`).

## Key decisions

- Mixamo or Kimodo takes that don't fit the game's action are rejected, not bent to fit. The Kimodo knockdowns are a stuntman's break-fall (squat, sit, roll), so her backward death is keyed instead.
- The dead's walk is keyed to the crowd's speed rather than captured. Feet that skate fail at any distance.
- Clips are made per skeleton (the kit's women and men differ from the library's by up to 23° at the neck).
- Unjudged clips stay out of full builds (`arts.py` `JUDGED`); HerClips plays anything in her library at once.

## Gotchas found this session

- In a fresh worktree, sheets render blank:
  - `godot/assets` checks out as a text file; replace it with a junction to `public/assets`, then run `git update-index --assume-unchanged godot/assets`;
  - copy the `*.import` and `*.uid` files under `public/assets` from a worktree that has them, then run `--import`.
- `folk.py` and `build.py` pack every JSON in their out folder. A fresh checkout has none, so build everything once with `--no-pack` first. `folk.py` now refuses to pack when a name matches nothing.
- VAT bakes are cached in `user://vat`, which every worktree shares. Use `--vat-fresh` when a clip changes and the version doesn't.
- In `--shot` runs, real-time timers outrun game time: the fall to the Waystation comes about 0.5 s after death.

## Notes for other areas

- Combat: the lurch drives every undead kind that uses the zombie walk, and CrowdView's walk rate now follows `asset.Pace` when it is known.
- Performance: HerPose's cached bone indices are kept.
