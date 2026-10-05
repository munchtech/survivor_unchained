# Handoff: animation (the heroine, the hero, the crowd, the townsfolk, the cinematics)

For the next animation lead in Survivor Unchained. Read `docs/team/README.md`
first, then this page, then `docs/team/animation.md` (the one-page status).
Written by agent a435f4dd0ac80df75, branch `worktree-agent-a435f4dd0ac80df75`,
which took over from a1e3002b800ee55ac (and before it aa4f5fc266b043035).

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

You own character animation in `godot/` (Godot 4.5.1 .NET), with the tools
in `tools/anim/`. That covers:
- her clips (`her/`, `heroine.res`);
- the male hero's clips (`him/`, `hero.res`);
- the townsfolk's clips and the crowd's own motion (`folk/`, `folk.res`): the dead's lurch, the casts, the falls, the slam;
- the beasts' composed motion (`Beasts.cs`);
- the cinematics' clips and gestures.

How to work:
- Judge everything on contact sheets and in the running game, at full resolution, as the player sees it (the default camera, 1920x1080).
- Reject takes that don't fit the game's action; don't bend them to fit.
- In `godot/src/Actors/` change only animation mapping and playback. Hair, face, skin and outfits belong to others.
- Keep `cd godot/tests && dotnet test` green (600 pass on integration).
- Commit and push your branch at milestones; the main session merges it. Open no PRs.
- Use British spelling. Comments are short prose saying why.
- Don't stop to ask.

## 3. Done (all pushed and merged, newest last)

848fab2, 8b2b54f, 72ab9a8, d7b091e, f73db3f, then two status-page commits (bd97e7f).

- **Corpse variety** (`tools/anim/crowd.py`, "the fallen"):
  - Every kit body bakes three falls: `die` (struck in front, over onto the back), `die2` (to the knees, onto the face) and `die3` (a heap on the side). Each is 0.8 s; the crowd compresses a death to 0.78 s and holds the last frame as the corpse.
  - `_armed`: the weapon is laid flat with the hand, and a shield lies on the forearm (left twist 1.0). The armed side-fall is mirrored onto the left side (`_mirrored`), so the shield arm is the lower one.
  - `_pistol`: a crossbow lies on its flat, the thumb up.
  - `FolkClips.Deaths(woman, armed, pistol)` names them; `Vat.BakePerson` bakes the roles; `VatAsset.Deaths` and `Death(k)` exist.
  - Wolves, boars and lamplings each have three falls, composed in `Beasts.cs`.
  - The experience director wired the pick (`CrowdView.DeathOf`): by seed, stepped when the nearest body of the same kind within 1.5 m lies alike. They will judge a 30-body frame.
  - The VAT cache is v11.
- **The hero's library** (`build.py --body hero` → `art/anim/hero.res`, 71 clips, `him/...`):
  - His skeleton is `tools/anim/data/hero_skeleton.json`, dumped from `hero.glb`.
  - `keyed.Rig(sk, body="him")` sets his feet wider (`feet_out` 0.045); `soul.feet_of` takes it back off captured feet.
  - `gait.manly`: square hips (30% of her roll), more shoulder turn, elbows out, a heavier drop.
  - `retarget.lean_neck` bows his neck 10° into retargeted takes (the 100STYLE idles threw his head back).
  - His own arcanist break (a hand kneading the back of his neck) and `catch_breath` are placed from his own knees and head.
  - In the game: `OwnClips` (Her, Him) replaced HerClips' library half, and `Person.Own` is hers or his. People, PersonView and PlayerView play either. `HerClips` keeps only the naming helpers (Calling, Kind, Swings, Heavy). `Calling` reads `him:<calling>` too.
  - Seen with `--quick warden --sex male --body hero`.
- **Gestures** (`clips/story.py`, `godot/src/Actors/Gestures.cs`):
  - `nod`: the head down 8°, held 0.4 s.
  - `exhale`: the shoulders settle over 1.2 s, then hold until the next cue.
  - `shiver`: the shoulders up 4 cm, a double tremor.
  - The meta `"layer": "gesture"` makes `PersonView.Cue` lay one over whatever plays, adding each bone's change from frame 0.
  - Both libraries have them. Judged laid over `sit_log`.
  - Cinematics has placed them in its handoff: the nod in C03 3b, the exhale in C01 8 at 1.2 s and in C04 A5, the shiver in C04 A5. Timeline cues use `"do": "anim"`.
- **The slam, keyed** (`crowd.slam`, `slam_armed` in `KEYED`; f73db3f): unjudged and unmapped (see §4).
- **Tools:**
  - `CrowdSheet` now takes `ROLE` as a comma list (cells take them in turn), `YAWSTEP`, `SIZE` and `LOOKY`.
  - `anim_review.gd` takes `MODEL=hero` (his clips are `him/`) and `GESTURE=clip GESTUREAT=s [HOLD=1]`.
  - `build.py` takes `--body hero`.

## 4. Next, in order

1. **The slam.**
   - Build it: `python tools/anim/folk.py slam`. A fresh checkout's `out/folk` is empty, so run `folk.py --no-pack` once first, or the pack drops the townsfolk's clips.
   - Map it: in `FolkClips.Crowd` add `"Slam" => Named(woman, armed ? "slam_armed" : "slam")`. In `Visuals.cs` give kerchief_brute (its `Fight(...)` has `cast: null`) and skeleton_minion (its `Shamble(...)`) `cast: "Slam"`.
   - Timing (combat's SlamSpec windup is 1.0 to 1.1 s): the gather; the fists overhead by 0.7 s; a hang to 0.9 s; the fists into the ground at 0.95 s; held to 1.5 s. CrowdView plays casts from `e.AnimT`.
   - Judge it on `CrowdSheet` (`VISUAL=kerchief_brute ROLE=cast N=10 STEP=0.1`) and in the game: mb_barn_door (kerchief_brute, Scale 1.7) and mb_the_heap (skeleton_minion, Scale 2.1). Then bump `Vat.Version`.
   - Combat agreed this timing. The lampling's slam (Grimtunnel) would be a `Beasts.cs` composition.
2. **Kneel-to-shoot.** Combat's aim windup is merged:
   - the aim is `EnemyState.Casting` with `e.Cast == CastKind.Aim`, `e.Anim = Windup` and `AnimT = 0` at its start;
   - it lasts 0.55 s on levy_crossbow, mb_old_quarrel (the Scorpion) and mb_levy_sergeant, the shooter facing `e.LungeX/Z`;
   - then it shoots, with `e.Anim = Attack` and `AnimT = 0`.

   Steps:
   - **CrowdView** (`Draw`, `case EnemyState.Casting`): when `e.Cast == CastKind.Aim`, play the role "aim" if the asset has it (else "windup") with `t = e.AnimT`. Today a Casting creature plays "cast" if baked, else "windup" looping on `time`.
   - **Bake:** add an "aim" role in `Vat.BakePerson`, from `Visuals.Clips` (a new `Aim` field, or keyed off the crossbow). Bump the version.
   - **Clips** (in `crowd.py`, both sexes):
     - `kneel_aim`: drop to the right knee and bring the crossbow up to the eye, in 0.55 s, then hold. Kimodo `kneel_shoot_0` (1.3 to 2.2 s into the take) is a good reference: retarget it with `try_takes.py` and key yours from it, or cut it with `generated.make(..., warp=...)`.
     - `kneel_shot`: the release, the kick up through the arms and the shoulder, and the rise back to standing (about 1.1 s). It is the "attack" role for those kinds.
   - **Visuals:** add a `kerchief_crossbow` visual (kerchief_hooded's look, with `Held { Right = "crossbow" }`) and ask combat to point levy_crossbow and mb_levy_sergeant at it. skeleton_rogue already holds a crossbow.
   - Judge in the game at the default camera with `--horde 8:levy_crossbow`.
3. **The cinematics' Kimodo clips.** The owner's run is complete: three takes of every prompt in `C:/Users/munch/Tools/mocap/kimodo/<name>_<n>.bvh`.
   - Judge whole takes on the scratch `try_takes.py` (§7). Turn the good ones into clips through `generated.TABLE` (warp, place) or key from them.
   - Order: rise_stiff and bend_lift (C02, the Warden on the kit man), kneel_fall (C03), flask_drink (C04), then C01's letter, kneel_to_stand_snap, take_from_log and cup_hands, and C04's rest.
   - Grimtunnel's (burst_hug, sniff, laugh, dive) are on the lampling rig: compose them in `Beasts.cs`.
   - Story clips hold at the end (`"hold": True`), go in `story.JUDGED` only once judged, and are named as the cinematics lead asks.
4. **Polish:**
   - `chain_strike`'s low landing crouch reads as a kneel.
   - A heavier flinch while running: a `Gestures` gesture fired with the hit would layer cleanly over the run.

## 5. Decisions and why

- **Three falls per body; weapons laid flat.** One spread-eagle pose printed thirty times read as a pattern. Swords left standing on end in the corpses read as white pillars at the game's camera.
- **The crowd's falls are slack.** No hand goes out to break a fall, and the head lolls. These are the dead or the dying, not stuntmen.
- **His clips come from her code with a man's numbers, not from her clips.** Her line-walking hip sway and contrapposto read as feminine on him. `HerPose` stands down for `him/` clips (Native = 1), so his `NeckPitch` 22 is only for library clips.
- **Gestures are additive** (each bone's change from frame 0), so one nod serves any pose, either body and any calling.
- **The slam is keyed; Kimodo's slam takes were rejected.** They were a shrug, a twist and a stoop, not two fists brought down from overhead.
- **Kneel-to-shoot needed an aim in the sim.** The bolt used to leave the moment its timer ran out, so a kneel could only come after the shot. Combat added the aim, which is also a telegraph you can step off.
- Earlier decisions (keyed undead lurch at the crowd's pace, her keyed backward death, one clip set per skeleton) are in this page's git history.

## 6. Failures and why

- **The face-down corpse looked propped on its arms** (a push-up). The kit's shoulder joints sit 7 cm behind the chest joint, so face down they stood high. Fixed by drawing the clavicles forward (protraction) and bowing the neck.
- **Hands keyed both ways in one clip jumped.** Some keys used `arm()` (chest frame) and others `pos` (character frame), and Track switches the frame at the nearest key, so a fall turns the chest 90° under the pole. Give pos keys `"frame": "char"`, or run the keys through `crowd._in_char`.
- **The side-lying shield stood on edge.** The upper forearm can't come down level. Hence the mirror to the left side when armed.
- **A slam with the hands "at the ground" floated at 0.19 m** until the squat was deepened (pelvis 0.40, hips pitched 56–60°).
- **A 22° neck bow** (the library's figure) was too much for his own mocap idles. 10° is right.

## 7. Gotchas

- **Fresh worktree:**
  - `godot/assets` checks out as a text file. Replace it with a junction to `public/assets` (PowerShell `New-Item -ItemType Junction`), then run `git update-index --assume-unchanged godot/assets`.
  - Copy the `*.import`/`*.uid` files under `public/assets`, and `godot/.godot` (robocopy), from a worktree that has them. Then run `--import` in the background; it takes minutes.
  - Copy `tools/anim/out/{clips,folk,hero}` too, or rebuild with `--no-pack` first: every pack takes every JSON in its out folder.
- **`--import` dirties hundreds of tracked `.import` files.** Run `git checkout -- "*.import"` before committing. Never commit `.uid` or `.import` churn.
- **This sandbox refuses** `cd ... && git`, `git -C`, variables in command paths, and multi-line python heredocs that the isolation check can't parse. Write patch scripts to the scratchpad and run them plainly; use Edit for single files.
- **The VAT cache `user://vat` is shared by every worktree.** Bump `Vat.Version` when a bake changes, and pass `--vat-fresh` while iterating.
- **Death timing:** CrowdView plays `die` in `Ai.DieTime * 0.62` = 0.78 s, compressing longer clips, and the corpse is the last frame.
- **Casts** (rally, howl, slam, aim) play from `e.AnimT`. Windups loop on `time`.
- **Bash** blocks `sleep N; cmd`. Use background runs and wait for the notice.
- **Scratch tools** (mine were in the session scratchpad; each is short to rewrite):
  - `stick.py`: PIL stick figures of a `crowd.KEYED` clip (side, front, top, game views), with the lowest joint per frame. The fastest way to catch ground penetration.
  - `csheet.py`: runs `CrowdSheet` for several `visual:role` rows and tiles them.
  - `hsheet.py`: rows of `review.sheet` with `MODEL=hero|male|female`.
  - `game.py`: the game at 1920x1080 with `--shot`.
  - `try_takes.py`: whole Kimodo takes onto her, him or a kit body as `k_<prompt>_<n>` (`generated.make`). Delete the `k_` JSONs and repack after.
- **A local test of the corpse pick** was a three-line patch to CrowdView. It's no longer needed: the director's DeathOf is merged.

## 8. Collaborators

- Main session: `main`.
- Experience director (ad1f5623590e09883): corpse pick and the 30-body judgement.
- Combat (a1d4562f44c7f6feb): the aim windup is done; the slam timing and the `kerchief_crossbow` visual are agreed.
- Male hero (ab82cbe99e2937ddd): told about `him/`. Rebuild his library after any rig change (re-dump `hero_skeleton.json` with `anim_skeleton.gd`).
- Cinematics: the lead af7a79bc783cca7bc handed off; read `docs/handoff/cinematics.md` and its successor's status page.
- Performance: keep HerPose's cached bone indices.

## 9. Read first

1. `docs/team/animation.md`, then this page.
2. `tools/anim/crowd.py` (the lurch, the rally, the slam, the fallen and `_in_char`/`_held`/`_mirrored`).
3. `godot/src/Actors/CrowdView.cs` (the Casting case), `Vat.cs` (`BakePerson`, `Death`), `FolkClips.cs`, `Visuals.cs`, `Beasts.cs`.
4. `godot/src/Actors/OwnClips.cs`, `Gestures.cs`, `PersonView.Cue`.
5. `tools/anim/keyed.py`, `gait.py` (`manly`), `build.py` (`BODIES`), `retarget.py` (`lean_neck`), `clips/generated.py`, `kimodo_gen.py`.
