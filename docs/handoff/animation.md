# Handoff: animation (the heroine, the crowd, the townsfolk, the cinematics)

For the next animation lead in Survivor Unchained. Read `docs/team/README.md`
first, then this page, then `docs/team/animation.md` (the one-page status).
This was written by agent a1e3002b800ee55ac, branch
`worktree-agent-a1e3002b800ee55ac`, which took over from aa4f5fc266b043035.

## 1. The owner's bar (quotes)

- "AAA standard", "strive for excellent, above and beyond - not just good
  enough". "Not polish, perfection." Never settle: remake rather than polish.
- "Do we have soul?" The aim is "one game in a million, not one soulless game of
  many". For motion: "movement with personality, specific to her and to each
  calling: a signature idle, the way she draws a weapon or catches her
  breath, small human details. Stock-library motion fails, however clean."
- Motion should be "weighty, characterful, readable at the game's camera".
- Sex appeal and the male gaze drive the heroine, "tho not at the cost of
  looking bad". The tone is 18+ (mature, not explicit).
- Context: "accurate, efficient, on track, manage and engineer context.
  deliberate. clean over chaos".

## 2. The brief

You own character animation in `godot/` (Godot 4.5.1 .NET), with the
tools in `tools/anim/`. That covers:
- her clips;
- the townsfolk's clips;
- the crowd's own motion (the undead, beasts' casts);
- the cinematics' clips;
- next, the male hero's library.

How to work:
- Judge everything on contact sheets and in the running game, at full resolution.
- In `godot/src/Actors/` change only animation mapping and playback. Hair, face,
  skin and outfits belong to others.
- Keep `cd godot/tests && dotnet test` green; 539 pass.
- Commit and push your branch at milestones; the main session merges it.
  Open no PRs.
- Use British spelling.
- Don't stop to ask.
- Kimodo: ask the main session to have the owner double-click "Run Kimodo"
  on the Desktop. It runs `tools/anim/kimodo_gen.py` from the main
  checkout, so your branch must be merged there first. Prompts already made
  are skipped, and the `FIRST` list is made first.
- Browser downloads need the owner's Save click: batch them and warn the
  main session first.

## 3. Done (all pushed, newest last)

f802ed3, a9fa480, b2a69f6, 3053106, eeadae6 and 809c358.

- **Kimodo prompts:** there are 55, and 25 of them are made. The 30 new ones cover:
  - the cinematics C01 to C04;
  - combat's `kneel_shoot` and `slam`;
  - `death_back`/`death_front` (to compare with the keyed ones) and `shamble_lurch`.
  The owner has not run them yet. `FIRST` puts C01's wake, the Warden, combat's two, `kneel_fall` and `flask_drink` first.
- **`death_back`** (`clips/actions.py`): struck from in front, she staggers back, sits down hard and goes over onto her back, a knee fallen out.
  - PlayerView chooses it when `Player.LastKiller` stands in front of her facing.
  - From behind, or killed by poison or burning (`FellTo`), she plays `death` (face down).
  - Debug: `--die T [--behind]`.
- **The Risen lurch** (`tools/anim/crowd.py`, `f_/m_lurch[_armed]` in `folk.res`):
  - keyed from the gait solver at the crowd's pace (2.6 m/s on the skeleton);
  - the left leg dragged round on a hitched hip, the head hung, one hand reaching like a claw (armed: the weapon trails).
  - Kit bodies asked for `Zombie_Walk_Fwd_Loop` get it (`FolkClips.Crowd`, `Vat.Clip`).
  - `VatAsset.Pace` lets CrowdView play a walk at the rate its feet need.
- **The crowd's casts:**
  - the wolf's howl, a `cast` role in `Beasts.cs` (`Vat.Moves` over its idle);
  - the rally (`crowd.py`, `f_/m_rally[_armed]`), the `Cast` clip for every person visual except kerchief_brute and skeleton_minion, which wait for their slam.
  - Casts of their own play from the cast's start: CrowdView uses `e.AnimT`, and Ai.cs resets it for the raise. Combat agreed both edits.
- **C01 clips** (`clips/story.py`), judged on sheets only:
  - `lie_side_wake` (on her right side, up onto the elbow);
  - `sit_back_heels` (to kneeling on her heels, looking at her hands);
  - `reach_coals` (a hand out over the fire, palm down, held).
- **Tool:** `godot/tools_scenes/crowd_sheet.gd` (`CrowdSheet.cs`) draws any crowd kind's role as a contact sheet, baked as the game bakes it:
  `VISUAL=wolf ROLE=cast N=6 STEP=0.2 YAW=90 CELL=1.6 W=1800 H=500 LIFT=10 OUT=x.png godot --path godot -s res://tools_scenes/crowd_sheet.gd -- --vat-fresh`.
- The VAT cache is v9.

## 4. Next, in order

1. **Corpse variety** (the experience director, ad1f5623590e09883):
   - Every risen corpse lies in one spread-eagle pose. Make "die", "die2" and "die3" per rig: on the back, face down, crumpled on the side.
   - People: keyed in `crowd.py` and mapped in `FolkClips.Crowd`; the bake (`Vat.BakePerson`) needs the extra roles.
   - Wolves: `Vat.Moves` in `Beasts.cs`.
   - Their offer is to wire the pick by seed in CrowdView and LayOut themselves.
   - Judge: in a 30-body frame, no two neighbours share a pose. Bump `Vat.Version`.
2. **The male hero's library** (ae2de192cce8298ca):
   - His body is `godot/art/people/hero.glb` on `worktree-agent-ae2de192cce8298ca@6df994d`: 65 UAL bones, a T-pose, pelvis at 1.118, 1.98 m tall.
   - Dump his skeleton: `anim_skeleton.gd -- tools/anim/data/hero_skeleton.json res://art/people/hero.glb`.
   - Make `build.py --body hero` produce `hero.res` + `hero_clips.json`, prefix "him/", with a `HisClips` like HerClips.
   - Give him masculine numbers: a wider stance, no contrapposto or hip sway, heavier weight. Re-solve and re-judge the four arts on him.
   - They will add HisPose (the pelvis offset, fingers, arms clear of his lats) for library clips.
   - Agreed: her clips play on him only as a stopgap.
3. **The cinematics** (af7a79bc783cca7bc):
   - key the nod (head down 8°, held 0.4 s), the exhale (the shoulders settle over 1.2 s) and the shiver (the shoulders up 4 cm, a fast double tremor);
   - judge the C01 clips in the cinematic itself (`--cine c01`);
   - retarget the Kimodo clips when they land. The Warden's go on the kit male skeleton (`folk_male_skeleton.json`). Grimtunnel's (`burst_hug`, `sniff`, `laugh`, `dive`) are on the lampling rig, so compose them in `Beasts.cs` or retarget onto its mixamo bones.
   - The full list and the prompt names are in `docs/team/animation.md`.
4. **When Kimodo lands:**
   - `kneel_shoot` for skeleton_rogue and kerchief_hooded (combat also wants a hooded body with a crossbow);
   - `slam` for kerchief_brute and skeleton_minion (the lampling's slam is a Beasts.cs composition).
   - Judge every take on sheets: `try_takes.py`-style scratch, see §7.
5. **Polish:** `chain_strike`'s low crouch reads as a kneel; a heavier flinch layered under runs; her town walk if the town ever needs it.

## 5. Decisions and why

- **Kimodo's knockdowns were rejected for her death.** They are a stuntman's break-fall (squat, sit, roll back), not a collapse, so `death_back` is keyed.
- **The undead walk is keyed at the crowd's speed.** Captured shambles run at 0.6 to 1 m/s against the Risen's 2.7, so at any distance they skate.
- **One rally for every caster until each has its own.** Combat asked for one generic gesture. Slammers keep their windup so the slam reads.
- **The howl stands planted.** Lowering the wolf's hips sank its paws into the ground, because `Vat.Moves` shifts bones and does no IK.
- **Story clips are made per performance, held at the end** (`"hold": True`), and named as the cinematics lead asked. They go in `JUDGED` only once judged.
- **Her clips stay hers.** The male hero gets his own library from the same code; her motion on him would read wrong.
- Older decisions are in the git history of this page (aa4f5fc's handoff): one clip set per skeleton, folk clips only for unarmed kit bodies, and the arts keyed.

## 6. Failures and why

- **Sheets rendered blank in a fresh worktree:**
  - `godot/assets` checks out as a text file (a symlink). Replace it with a junction to `public/assets`, then `git update-index --assume-unchanged godot/assets`.
  - Copy the `*.import`/`*.uid` files under `public/assets` from a worktree that has them, then `--import`.
  - Copying another worktree's `godot/.godot` saves a long import.
- **`folk.py <name>` with no match packed an empty library.** It now refuses. Both `build.py` and `folk.py` pack every JSON in their out folder, so a fresh checkout needs a full `--no-pack` build first (her library takes about 7 minutes).
- **A first `CrowdSheet` hung:** the root viewport has no settable `Size`, so it now draws into a SubViewport.
- **Finger keys:** a preset name in one key and a dict in another crash `keyed.build` ("'str' object does not support item assignment"). Keep each finger control the same shape on every key (`story._f`).
- **The first lurch** read as a march, with the arms hanging behind (the chest is pitched forward, so "down" in its frame is behind). The first rally swung the weapon out to the side on the way up.

## 7. Gotchas

- **This agent's sandbox refuses complex shell lines:**
  - no `cd` into the shared checkout;
  - no multi-file python heredocs that edit several files (split them, or use Edit);
  - write scratch scripts in the scratchpad and run them plainly.
- **Scratch tools** (in the old scratchpad; easy to rewrite):
  - `try_takes.py`: whole Kimodo takes onto her as `k_<take>` in `out/clips`;
  - `folk_try.py`: onto kit bodies;
  - `sh.py`: multi-view boards with `LOOK=bone ZOOM=`;
  - `game.py`: runs the game for shots;
  - `tile.py`: crops and tiles shots;
  - `crowd.py`: runs CrowdSheet.
  - Delete judging clips (`k_*`, `*_k_*`) and repack before committing.
- **The VAT bake cache** is `user://vat`, shared by every worktree: pass `--vat-fresh` when a clip changes without a version bump.
- **In `--shot` runs, real-time timers outrun game time:** after death, the fall to the Waystation comes about 0.5 s later. Take death shots in the first second.
- **Game pictures:**
  `--quick warden --sex female --zone verge --time day [--horde N:kind,...] [--dist D --spread S] [--die T] --cam 9 --shot NAME --seconds S --every 0.1 --count N`.
  Shots land in `godot/.shots/`.
- **The review camera does not follow root travel.** Use `LOOK=pelvis` (or `--place pin` for judging takes).
- Merging other leads' branches is fine when you need their content; the main session merges anyway.

## 8. Collaborators

- Main session: `main`.
- Cinematics: af7a79bc783cca7bc (`docs/team/cinematics.md`, `godot/data/cinematics/c01.json`).
- Combat: the successor of ac4ec5bbd2763a0df (`docs/handoff/combat.md`).
- Experience director: ad1f5623590e09883.
- Male hero: ae2de192cce8298ca (`docs/team/hero_male.md`).
- Performance: a9586a5171413db0b (HerPose's cached bone indices; keep them).

## 9. Read first

1. `docs/team/animation.md`, then this page.
2. `tools/anim/crowd.py`, `tools/anim/clips/story.py`, `tools/anim/clips/actions.py` (`death_back`).
3. `godot/src/Actors/Vat.cs` (`BakePerson`, `Clip`, `Pace`), `CrowdView.cs`, `FolkClips.cs`, `Beasts.cs` (the wolf's roles), `Visuals.cs`.
4. `tools/anim/keyed.py` (pose controls), `tools/anim/gait.py`, `tools/anim/folk.py`, `tools/anim/build.py`.
5. `tools/anim/kimodo_gen.py` (the prompts and `FIRST`).
