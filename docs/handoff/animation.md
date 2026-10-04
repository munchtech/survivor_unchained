# Handoff: animation (the heroine, her arts, the townsfolk)

For the session that carries on character animation in Survivor Unchained.
Read `docs/team/README.md` first, then this page, then `docs/team/animation.md`
(the one-page status). Written by the animation lead in worktree
`agent-aa4f5fc266b043035` (branch `worktree-agent-aa4f5fc266b043035`).

## 1. The owner's bar (quotes)

- "AAA standard", "strive for excellent, above and beyond - not just good
  enough"; "not polish, perfection"; never settle: remake rather than polish.
- "Do we have soul?" ... "one game in a million, not one soulless game of
  many". For animation: "movement with personality, specific to her and to
  each calling: a signature idle, the way she draws a weapon or catches her
  breath, small human details. Stock-library motion fails, however clean."
- Motion "weighty, characterful, readable at the game's camera".
- Sex appeal and the male gaze drive the heroine, "tho not at the cost of
  looking bad". The tone is 18+ (mature, not explicit).
- Context: "accurate, efficient, on track, manage and engineer context.
  deliberate. clean over chaos".

## 2. The brief, in full

Own character animation in `godot/` (Godot 4.5.1 .NET). Research, design
and build her clips (`docs/ANIM_RESEARCH.md`, `docs/ANIM_DESIGN.md`,
`tools/anim/`), judge them as an animation director from rendered sheets
and in the running game, wire them in with the Universal Animation Library
(UAL) as the fallback. In `godot/src/Actors/` change only animation mapping
and playback (hair, face, skin and outfits belong to others). Keep
`cd godot/tests && dotnet test` green. Commit and push your branch at
milestones; the main session merges it; no PRs. British spelling.

This session's brief (from the coordinator, in order):
1. Merge `origin/claude/vigilant-galileo-l6jqyx`; read the team page and the
   predecessor's handoff.
2. Retarget the downloaded Mixamo clips: the townsfolk batch onto the
   townsfolk; the vault, bull rush and chain haul onto her. Judge every clip
   on contact sheets and in the game at full resolution.
3. Kimodo: the owner runs `python tools/anim/kimodo_gen.py` in their own
   terminal (this sandbox cannot read the HF token: never try to). Judge its
   BVHs when they land.
4. More browser downloads need the owner's Save click: batch them and
   message the main session first.
5. Keep `docs/team/animation.md` as the one-page status; hand off past
   about 500k tokens of context.

## 3. Done (all pushed)

Commits on the branch, oldest first: 2a569db Kimodo batch; 3f5057d status
page; 67647bd vault pair; 29df4a4 bull rush and chain haul; 2ecc563
townsfolk library.

- **Kimodo** (`kimodo_gen.py` + `kimodo_batch.py`): one run loads the model
  and Llama 3 once and makes 25 prompts, 3 takes each, into
  `C:/Users/munch/Tools/mocap/kimodo/<name>_<k>.bvh`. Prompts already made
  are skipped. `--dry` tests without the text encoder. The owner's run
  finished: all 75 takes exist.
- **Her arts** (`tools/anim/clips/arts.py`, keyed). The game's numbers are in
  `godot/logic/Sim/Arts.cs`:
  - `vault`: a split leap; she vaults forward when moving (0.32 s in the air;
    the view lifts her 2.2 m).
  - `vault_back`: a tucked back spring into a three-point landing, when she
    vaults standing (the game then springs her back from her facing).
  - `bull_rush`: 9 m in 0.4 s; one `gait.pose_at` stride cycle with warden
    carriage pitched hard, then a keyed plant, shove and settle.
  - `chain_haul`: the grapple hauls her at 28 m/s (0.08-0.4 s); a flown pose
    held until she arrives.
  - `chain_strike`: played by PlayerView when the haul ends; the blow lands in
    its second frame.
- **PlayerView**:
  - picks `vault`/`vault_back` by her travel against her facing and turns her;
  - holds her facing while in the air;
  - `ArtTail` fades an art's landing or shove into her run once she moves;
  - the grapple throw uses her own `throw` clip.
- **Townsfolk** (`tools/anim/folk.py` makes `godot/art/anim/folk.res` and
  `folk_clips.json`; `FolkClips.cs`; `People.Clip`):
  - Clips are named `f_`/`m_` + walk, idle, talk, arms_crossed, sit_chair,
    sit_floor, cheer, wave, work and pick_up.
  - They play for unarmed kit bodies (`Person.Kit`, `Person.Folk`, set in
    `PersonView`), and the walk runs at its natural speed.
  - Checked in the Waystation by day.
- **Pipeline fixes**:
  - `generated.make` takes travel out before looping (the seam spread used to
    swallow it).
  - `loop="cycle"` closes a take that is one whole cycle.
  - `anim_review.gd` renders kit bodies (`MODEL`, `PARTS`, clips `folk/...`).
  - `--cast T --still` in `Game.cs` casts standing.

## 4. In progress / next

1. **A backward death for her.** Kimodo `knockdown_0..2` are strong: a fall
   back onto the back, a roll, then rising. Take the fall and hold it, as a
   `death_back`; PlayerView could choose by the side the killing blow came
   from.
2. **Her walk**, if the town ever shows her walking (today she runs, slowed).
   Candidates: Kimodo `her_walk_*`, or Mixamo's feminine walk retargeted onto
   her with `loop="cycle"`.
3. **Crowd shamble** from Kimodo `shamble_*` for the undead. The crowd is
   VAT-baked through `Vat.cs` with UAL names via `People.Resolve`, so it needs
   a library on the kit skeletons there and a `Vat.Version` bump. Combat is
   adding crowd tints in `CrowdView`; I agreed they make that edit.
4. **Polish**: `chain_strike`'s low crouch reads as a kneel; a heavier
   full-body flinch layered under runs; Kimodo `kneel`/`shrug` for story beats.

## 5. Decisions and why

- **Rejected Mixamo takes:**
  - the vault ("Jumping Over Into Combat") is a sideways vault over an
    obstacle: hands planted on nothing, landing turned 90°;
  - the shield run has no stop;
  - the greatsword slide's blow is the wrong one at the wrong time.

  We key what the game's timing needs.
- **Kimodo's arts lose to the keyed ones:** a small hop, a walk-paced shove,
  no flight. Its townsfolk motion is good and is used.
- **One clip set per skeleton.** The kit women's and men's rests differ from
  UAL1's (neck up to 23°, clavicles and feet about 10°), so each folk clip is
  retargeted to `tools/anim/data/folk_female_skeleton.json` and
  `folk_male_skeleton.json`.
- **Folk clips play only for unarmed kit bodies.** Guards and bosses keep the
  library's armed clips, and `Vat` uses `People.Resolve`, so the crowd is
  untouched.
- **`arts.py` keeps a `JUDGED` set**, so unjudged work never reaches a full
  build: HerClips plays anything in her library at once.

## 6. Failures and why

- Reading the HF token: the sandbox denies it (do not try).
  - The owner's first run failed because `.cache/huggingface/token` was a
    folder; the main session fixed that.
  - Kimodo's "UNEXPECTED/MISSING lora keys" and "multiple adapters"
    warnings are harmless: reproduced with a tiny model (scratch
    `peft_check.py`, not kept), the adapter merges exactly.
- First keyed passes: the split leap's front leg read bent and the arms read
  as a T-pose; the back spring's tuck and landing were too shallow. Fixed by
  measuring with FK and rendering front, side and three-quarter views. A
  landing hand cannot reach the ground unless the torso pitches about 75°:
  her arms are short against her legs.
- A fresh worktree's first `--import` left `.godot/imported` nearly empty, and
  Godot then hung on missing scenes (reviews timed out). Re-run the import
  until `heroine.glb-*.scn` exists.

## 7. Gotchas

- **This agent's sandbox refuses complex shell lines:** no shell variables,
  no heredocs with some patterns, no `cd` into other worktrees, no for-loops
  around Godot. Write a Python script in the scratchpad and run it plainly.
- **Merges abort on untracked `.uid` files** the import generates: delete the
  listed ones and merge again. Never stage `.import`/`.uid` noise; stage
  files by name.
- **Full rebuilds are deterministic** (diffs under 3e-5), so
  `python tools/anim/build.py` reproduces `heroine.res` exactly.
- **Packing packs every JSON in `tools/anim/out/clips`.** Judging clips (k_*,
  m_*) must be deleted and the library repacked before committing; check that
  `heroine.res` is about 4 MB, not 17.
- **Game pictures:**
  `--quick <calling> --sex female --zone verge --time day --art <id> --cast T [--still] --cam 16 --shot NAME --seconds S --every 0.0333 --count N`.
  - Shots land in `godot/.shots/`.
  - `--zone arena` opens a blessing draft first; the Verge by day is clear.
  - For the grapple, add enemies: `--horde 24 --dist 10 --spread 1 --cast 2`.
  - The town is `--zone waystation --time day --at 0,1`.
- **The battle's `Aim` is never set in play:**
  - the vault goes the way she pushes, or back from her facing when she stands;
  - `--cast` pushes (1,0).
- **Kimodo takes:** `C:/Users/munch/Tools/mocap/kimodo/<prompt>_<k>.bvh`
  (profile `soma`). `kimodo_gen.py` lists the prompts and what each is for.

## 8. Collaborators

- Main session / coordinator: `main` (SendMessage).
- Combat lead: `ac4ec5bbd2763a0df` (crowd tints in `CrowdView`, more enemy
  defs on existing rigs).
- Voice: `a2da9a388ceb1b987`.
- Outfits, hair, face and skin belong to the main session and the art agents
  (`tools/assets/`, `godot/shaders/`).

## 9. Commands

    python tools/anim/build.py [names]                 her clips (full build: everything judged), packs heroine.res
    python tools/anim/folk.py [names]                  the townsfolk's clips, packs folk.res
    python tools/anim/review.py her/<clip> side three --frames 10 --step 2 --weapon daggers --outfit ranger
    MODEL=female PARTS=Female_Peasant_Arms,... python tools/anim/review.py folk/f_walk side
    python tools/anim/kimodo_gen.py [names] [--dry]    (the owner runs it; this sandbox cannot read the token)
    cd godot/tests && dotnet test

## 10. Read first

1. `docs/team/animation.md` (status), `docs/ANIM_DESIGN.md` §4.6-4.7 and §7
2. `tools/anim/clips/arts.py` and `tools/anim/folk.py`
3. `godot/src/Actors/PlayerView.cs` (arts and `ArtTail`), `FolkClips.cs`,
   `People.cs` (`Clip`, `Person.Kit/Woman/Folk`), `PersonView.cs`
4. `tools/anim/clips/generated.py` (`make`, loops), `tools/anim/retarget.py`
5. `tools/anim/keyed.py` (pose controls), `tools/anim/gait.py`
