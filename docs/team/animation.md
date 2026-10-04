# Animation: status

Branch `worktree-agent-aa4f5fc266b043035`. The brief, history and gotchas are in `docs/handoff/animation.md`. Read that first.

## State

- **In the game:** her 59 clips, unchanged (`godot/art/anim/heroine.res`). A full rebuild in this worktree reproduces them exactly, to within 3e-5.
- **Kimodo:** `tools/anim/kimodo_gen.py` now runs `kimodo_batch.py`.
  - It loads the model and Llama 3 once, then makes 25 prompts, 3 takes each, into `C:/Users/munch/Tools/mocap/kimodo/<name>_<k>.bvh`.
  - It skips prompts that are already made.
  - The prompts now match the game's arts: the vault springs back, and the chain hauls her in. They also cover hits, a hip-shot idle, her walk, and the townsfolk (a man's walk, a woman's, an old man's, arms crossed, talk, cheer, clap, wave, work) and a shamble.
  - A dry run (`--dry`, noise for words) passed here.
  - **The owner runs it in their own terminal:** `python C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\tools\anim\kimodo_gen.py`. This sandbox can't read the HF token. Keep this worktree until it prints KIMODO DONE.
- **Mixamo arts, judged from their raw retargets (side view, `LOOK=pelvis`):**
  - `vault_jump_over`: rejected. It is a sideways speed vault over an obstacle: the hands plant on nothing, and she lands turned 90°. The game's vault has no obstacle.
  - `shield_run`: a usable charge cycle for the bull rush's legs. It has no stop.
  - `greatsword_slide_attack`: a knee slide with the blade raised, then a low sweep and a spin. It could be the haul, but the strike is the wrong blow, at the wrong time.
- **The game's vault (Arts.cs, worth knowing):** the battle's `Aim` is never set in play. Moving, she vaults forward the way she runs. Standing, she springs back from her facing. So she needs two clips. PlayerView picks between them by comparing her travel with her facing.
- **In progress:** `tools/anim/clips/arts.py`, keyed `vault` (a split leap on the run) and `vault_back` (a tucked back spring into a three-point landing).
  - They are first passes and not yet good enough. In the split, the front leg didn't read straight and the arms read as a T-pose; both are reworked but not yet re-judged. In the back spring, the tuck and landing were too shallow; also reworked.
  - They are built only when named (`build.py vault`), so a full build and the game leave them out.

## Next

1. Judge `vault` and `vault_back`: build them, then render sheets from the side, three-quarter and arena views (`review.py her/vault side three --weapon daggers --outfit ranger`). Iterate until they meet the bar.
2. Wire them in PlayerView:
   - choose the vault by travel against facing; standing, turn her to face away from the travel;
   - add an art tail: fade the full shot once the art is over and she moves;
   - for her, skip `OverhandThrow` on the grapple.
   - Check in the game. `--cast` passes push (1,0), which gives the forward vault; a standing test needs `UseAbility(0,0)`.
3. Bull rush: the 0.4 s charge is 9 m at 22.5 m/s. Key it as one fast gait cycle (`gait.pose_at`, warden lean to about 34°, shield square, sword cocked), then a planted shove and the settle.
4. Chain haul: make two clips, `chain_haul` (thrown, yanked off her feet, axe cocked, held) and `chain_strike` (a chop that lands within 0.07 s of arrival, then the recovery). PlayerView plays the strike when the Grapple rush ends.
5. Compare each against Kimodo's takes when they land.
6. Townsfolk: a `folk.res` on the UAL skeleton (same bone names, minus breasts and glutes). Map it in `People.Clip` for unarmed non-heroines only (bosses and guards keep the UAL), and store the walk's natural speed for `PersonView`. Today the UAL plays `Yes` for Cheer and Wave, and `Crouch_Idle` for sitting on the floor.

## Decisions

- Mixamo takes that don't fit the game's action are rejected, not bent to fit. We key the clip, or use Kimodo.
- Unjudged clips never reach the library: HerClips plays anything in it at once.

## Gotchas (new)

- In a fresh worktree, `--import` once can leave `.godot/imported` almost empty (21 files), and then Godot hangs on missing scenes. Run the import again until `heroine.glb-*.scn` exists.
- Commands run from this agent must be plain: no shell variables and no `cd` chains into other worktrees.
