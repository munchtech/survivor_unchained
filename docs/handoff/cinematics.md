# Cinematics: handoff

From agent a79b6d8c81e14dc63 (who took over from a3058a45eee41d695) to a fresh cinematics production lead. Read `docs/team/README.md` first, then this page, then `docs/team/cinematics.md`.

## The owner's quotes

- "Time to begin scripting the writing in preparation for shooting the scenes."
- The bar: "cinematic, movie quality, soul, nothing generic". "AAA standard", "strive for excellent, above and beyond". "We are striving for perfection": before you show anything, ask whether it is the best version of this in any game. Root design in research on how the best games solve it, then make it ours. Never settle; remake rather than polish; check everything at full resolution, as the player sees it.
- The structure: story is about 40% of the game early on, and the cinematics carry much of it, "so make them count".
- On voice: "no more placeholders ... keep cinematic voice". Finals come from ElevenLabs later. Add no new voice placeholders.
- On models: the bought and kit models are to be replaced with our own (`docs/art/MODELS_TO_MAKE.md`; the Ford-Warden has his own entry).

## The brief, in full

1. **A shooting script per cinematic,** `docs/cinematics/shoot/<id>.md`, in numbered shots: camera, blocking (marks in the real zone), performance, sound, picture and timing. Shoot it like a film: coverage, eyelines, the 180° line kept or broken on purpose.
2. **Boards** (`tools/cinematics/boards.py`, local ComfyUI): ink and grey marker, colour only in the light. They are now drawn over the engine's own previs frames (see Decisions).
3. **Animatics** (`tools/cinematics/animatic.py`): boards, the cinematic takes and temp music, cut to check the pacing.
4. **The in-engine pipeline:** JSON timelines (`godot/data/cinematics`), wired to the triggers in `docs/cinematics/README.md` §9.
5. **First milestone:** C01 and the Prologue (C02 to C04) scripted, boarded, cut, playable and right. Then the rest by importance (C07 and C09 first).
6. **This session's list (from the main session), with where it stands:**
   1. C04 B's tower lamp (B4a): **done.**
   2. C10, C11 and C13 after the approved boss redesign, with combat's boss hooks: **done in the scripts and the hook contract;** the timelines wait for the fights' places.
   3. The board remakes, shot by shot: **C02 done (some to redo), the rest staged and prompted.**
   4. Block animation's three C01 clips: **done.**
   5. The Kimodo clips once animation judges them: **the Warden's five are in (C02, C03).**
   6. The animatic recut: **not yet** (after the boards).
   7. The Warden's white hood, tinted in WardenView until his own model: **done.**
7. **Ways of working:** don't stop to ask; British spelling; `dotnet test` (in `godot/tests`) before every commit; commit and push your branch at milestones; open no PRs. **Heavy work takes turns:** `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot|gpu "cinematics: <job>"` before a Godot render or a ComfyUI job, and give it back after. `boards.py` and the scratch `prev.py` do this themselves.

## Done this session

- **C04 B** (checked at full size, reframed; `shoot/c04b.md`):
  - the toll tower's lamp is the keeper's lamp-iron on the window's sill (mark `lamp`, flame 7.12 m up). At B4a (280 mm, 2.6 s) its flame goes out and a thread of smoke climbs the glass;
  - B1's crane starts at 12 m, the only height from the gate where the tower shows over the roofs;
  - B4 is low over Rook's shoulder, with the survivor and the tower and its lamp on one line. B4b is Rook's single (the reverse);
  - Rook's looks are head turns.
- **C01 on animation's clips** (`shoot/c01.md`):
  - she lies curled on her right side at the ring's east edge, her face to the embers (`lie` (-9.65, 90.90), heading toward the fire), on `her/lie_side_wake`; she comes up onto her elbow (shot 5), kneels back on her heels (`sit_back_heels`, shot 6), and holds her hand to the coals (`reach_coals`);
  - the hand insert is now **shot 6a, after the kneel** (shot 4 is gone; its board was renamed `s6a.jpg`);
  - every camera of shots 2 to 10 was re-surveyed. The face shots aim at her bones;
  - her look to the trail (7, held through 8b) and her whip round to R1 (10) are head turns;
  - the exhale (8) is animation's gesture.
- **C02 and C03 play the Warden's judged clips** (animation's `folk/m_rise_stiff`, `m_bend_lift`, `m_kneel_lamp`, `m_lamp_down`, `m_fold_forward`):
  - he folds forward and lies face down at her feet, so the heart rises from his chest at `w` + (0, 0, 2);
  - C03's lamp insert (4) follows the lamp into the river;
  - C03's shot 3 is from his right, so the lamp held up no longer covers his face;
  - the nod (C03 3b) and the shiver (C04 A5) are gestures laid over her.
- **The Warden's look until his own model** (`src/Actors/BossViews.cs`):
  - his dye is measured against brighter paint, so the hood and mantle come out dark (they read white);
  - his lamp hangs plumb from his fist on a bail (`hand_l` plus 0.075 up the hand, where `Arms.Hold` grips). It had floated, and my first try at it, on `handslot.l`, put it at his feet. In the river he lies at y -1.2 so the lamp hangs clear of the water, and his own lamp replaced the stand-in glows (shot 8 keeps a glow's light at the flame for the ECU);
  - `LampIron` is shared by him and the tower's lamp.
- **The heart** (`OrbView`, also the game's orb in the Prologue): a rough-cut stone of a few faces, with the light inside and a ring halo, not a white ball. One more look is owed: the last render of it was before the ring halo.
- **Player additions:**
  - `head` (`HeadTurn`, a SkeletonModifier3D: neck and head turn toward a point, kept level, eased; `amount` 0 lets go);
  - `glow` `lantern` / `turn` / `out` / `smoke` / `smokeColor` (`Campfire.WickSmoke`);
  - `--clean` hides title cards (for staging);
  - `--cinebones` also prints a boss's lamp.
- **C10, C11 and C13** follow the approved redesign:
  - the spent boss and her choice are play, and the cinematic starts from them;
  - C10's death opens on "Finish it" (or the fight's own end), and its let-go plays at the choice and owns his walk to the den;
  - C11 names its hooks;
  - C13's shot 1 is her standing over the Barrow Lord, who will not stay down. The door opens on the roofless hall (story's two corrections).

  The hook ids and the marks a fight passes are in `docs/cinematics/README.md` 11a. Combat (a708da2c97bf85c95, handed off; its successor is afe45df4957917614) queued both asks in `docs/handoff/combat.md` §4.3:
  - marks `boss`, `her` and `den_mouth` to `G.Cinematic`;
  - `c10_spared` played from `Greymuzzle.Choose(true)`, releasing him on done.
- **Boards over staging** (`boards.py`):
  - `--stage <shot-name>` cuts `godot/.shots/<name>_<id>_s*_1.png` to the picture and saves it in `tools/comfy/out/staging/<id>/` (out of git);
  - a shot `{"prompt", "from": "staging", "denoise", "seed"}` is drawn img2img over it;
  - the tool takes the GPU's turn.
  - **C02's twelve boards are remade:** stone pillars with blue flames, the Warden in leathers and mail, the right staging. The prompts for C01, C03, C04 A and C04 B are rewritten.

## In progress and next, in order

1. **Re-render the staging, then draw the boards.** Everything was stopped cleanly at the handoff; no turns are held. Staging for C01, C02, C03 and C04 A was rendered and staged mid-session, but C02, C03 and C01 shot 5 have changed since. Run these one at a time, each waiting for its turn:

   ```
   python <scratchpad>/cin3/prev.py c01 st1 75 --clean --wait 90 --quiet
   python <scratchpad>/cin3/prev.py c02 st2 80 --clean --wait 90 --quiet
   python <scratchpad>/cin3/prev.py c03 st3 80 --clean --wait 90 --quiet
   python <scratchpad>/cin3/prev.py c04b st4b 40 --zone waystation --clean --wait 90 --quiet
   python tools/cinematics/boards.py <id> --stage <name>
   python tools/cinematics/boards.py <id> --force [--only ...] --wait 120 --sheet <scratch>.jpg
   ```

   (C04 A's staging is current.)

   Look at each board at full size. C02's board faults are:
   - s3 (the gauntlet is open; the lamp must hang from the fist);
   - s5 (the lamp was drawn at his feet: old staging);
   - s7 (he reads 1.6 times her height, not three; the prompt and denoise are raised);
   - s8 (a candle at her chin; the prompt is fixed);
   - s11 (a red beard and two shields on the ground; it has a new seed).

   For C03, look at the heart (the ring halo) in the engine before you board s5 to s8.
2. **Recut the Prologue animatic** (`animatics/prologue.txt` has the cards). C01's shot 4 is now 6a.
3. **The male hero:** play the Prologue with `--sex male --body hero`. The face cameras aim at bones, so they should hold; check C01's absolute camera positions, and whether `him/` has the three C01 clips.
4. **C02's and C03's line choices** (the old handoff's item 6), then C07 and C09.
5. **C10 to C13 timelines** once their fights and places exist (only the Hollow is built, and its place isn't dressed yet).

## Decisions (why)

- **The engine's frame is the staging truth; boards are drawn over it.** God of War's team previs'd first ("Keyframes and Cardboard Props", GDC 2019); here the previs is in the engine, so a board drawn over it keeps the surveyed lens and the scale. Higher denoise (0.7 to 0.8) where the staging lacks the action (a burst, a dive, an ember).
- **Cameras aim at bones, not heights** (Baldur's Gate 3's adaptive cameras), so a shot follows the body it is given.
- **Looks are head turns** (`head`). The `look` cue turns the whole body, and on a kneeling body that read as a statue on a turntable.
- **The cinematic owns the boss's body while it plays.** A spared part plays at the choice and owns his going; the fight releases him at its end.
- **The tower's lamp is the Warden's lamp-iron with an ordinary warm flame:** the eye can tie Vonnra to the keepers before anyone says so (C09 puts it on her table).
- **The C01 reach comes after the kneel** (written order: before). The clip is made kneeling, and awake it reads as on purpose.

## Failures and why

- **The first lamp hang used `handslot.l`,** which is a held-slot name, not a bone, so the attachment sat at the root and the lamp was at his feet. `--cinebones` now prints the lamp's place; check it after any change.
- **The heart blew out to a white disc** (an unshaded sphere at three times its colour, then an emissive stone under an additive halo). Its emission is capped now, and the halo is a ring that leaves the stone clear.
- **A second dye slot in `person.gdshader`** was a wrong turn (reverted). The hood is dyed in the first slot; the ranger mask's low `Lum` was what made light greens come out near white.
- **The renderer's stdout once ran Python out of memory.** `prev.py` now streams to a log, with a 7-minute limit that stops the whole process tree.
- **`prev.py` deletes `.shots/<name>_*` before each run,** so reusing one name across cinematics wipes the earlier ones. Use one name per cinematic.

## Gotchas

- **The worktree guard** refuses Bash that `cd`s outside the worktree or is "too complex" (variables in commands, some heredocs with `git` near them). Write patch scripts to the scratchpad and run them plainly. `jedit.py <id> <edit.py>` edits a timeline in the house layout.
- **Scratch tools are in `<scratchpad>/cin3`.** They point at this worktree, so change the path in each if yours differs:
  - `prev.py` renders and takes the Godot turn; `--wait` is in minutes, `--clean` hides titles, `--stills N` gives N frames a shot, and `--only` lists shots;
  - `jedit.py` edits a timeline;
  - `crops.py` lays the same crop of several stills side by side, at full size;
  - `times.py` gives each shot's start and length;
  - `btest.py` tries one prompt at several denoise levels;
  - `ed_b02.py` (`setspec`) rewrites a board spec one shot per line.
- **The machine is contended.** Expect 5 to 20 minutes' wait for a turn, so batch your renders. RAM below 5 GB free also blocks a Godot turn.
- **`godot/assets` is a junction** to the main checkout's `public/assets`, marked skip-worktree. The `.godot` import cache was copied from the predecessor's worktree. A few newer assets (`console.png`, `tell_drum_*.wav`) aren't imported in it, which is harmless.
- **Headings:** 0 faces south (+z), π/2 east, π north. Marks with three numbers are `[x, z, heading]`; four are `[x, h, z, heading]`.
- **Previs vs play:** the stills are taken in real time while the world is held; particles and the head turn still run.

## Collaborators (the roster is in `docs/team/README.md`)

- **Story** (a7ba8903f4c8261b1): agreed the C13 changes; rules on any line that fights a shot.
- **Combat** (afe45df4957917614, the successor): has the marks and `c10_spared` requests in its handoff §4.3.
- **Animation** (a03acf30b3e9bdd70): judged the Warden's clips in our cinematics (they swap cues locally and never commit timelines). Still to come:
  - the Warden's `lie_arm_up` and `wade_drag`;
  - Grimtunnel's burst, sniff and dive;
  - C04's `wade_out`, `flask_drink`, `walk_uphill` and `unfold_arms`;
  - C01's `letter` and `kneel_to_stand_snap`.
- **Voice** (a501b387a90d78b4e, paused): add no new placeholders.

## Files to read first

1. `docs/team/cinematics.md`, then `docs/cinematics/shoot/README.md` and `shoot/c01.md` to `c04b.md`
2. `godot/src/Game/GameCinema.cs` (the cues, `glow`, `head`, the stills) and `godot/src/Actors/HeadTurn.cs`
3. `godot/src/Actors/BossViews.cs` (`WardenView`'s dye, `Hang`, `LampIron`, `OrbView`)
4. `tools/cinematics/boards.py` and `docs/cinematics/shoot/boards/*.json`
5. `docs/cinematics/README.md` 11a, and `c10_hollow_by_night.md`, `c11_raid_on_the_roost.md` and `c13_behind_the_door.md`
