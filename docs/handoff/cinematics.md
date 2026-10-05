# Cinematics: handoff

From agent a3058a45eee41d695 (who took over from af7a79bc783cca7bc) to a fresh cinematics production lead. Read `docs/team/README.md` first, then this page, then `docs/team/cinematics.md`.

## The owner's quotes

- "Time to begin scripting the writing in preparation for shooting the scenes."
- The bar: "cinematic, movie quality, soul, nothing generic". "AAA standard", "strive for excellent, above and beyond", "Do we have soul?". Never settle; remake rather than polish; check everything at full resolution, as the player sees it.
- The structure: story is about 40% of the game early on, and the cinematics carry much of it, "so make them count".
- On voice: "no more placeholders ... keep cinematic voice". Finals come from ElevenLabs later.
- On models: the owner wants the bought and kit models replaced with our own. A models planner is writing `docs/art/MODELS_TO_MAKE.md`, and the Ford-Warden has his own entry there.

## The brief, in full

1. **A shooting script per cinematic,** `docs/cinematics/shoot/<id>.md`, in numbered shots. Each shot gives:
   - the camera (framing, lens, height, move, cut motivation);
   - the blocking (marks in the real zone);
   - the performance (an existing clip, a Kimodo prompt, hand-keying, or face beats);
   - the sound (VO ids, music, SFX);
   - the picture (light, atmosphere, VFX, subtitles);
   - the timing.

   Shoot it like a film: coverage, eyelines, and the 180° line kept or broken on purpose.
2. **Boards,** made locally with ComfyUI (`tools/cinematics/boards.py`), in ink and grey marker with colour only in the light.
3. **Animatics:** boards, the cinematic VO takes and temp music, cut to check the pacing (`tools/cinematics/animatic.py`).
4. **The in-engine pipeline:** JSON timelines (`godot/data/cinematics`), wired to the triggers in `docs/cinematics/README.md` §9.
5. **First milestone:** C01 and the Prologue (C02 to C04) scripted, boarded, cut, playable and right. Then the rest by importance (C07 and C09 first).
6. **Ways of working:** don't stop to ask; use British spelling; keep tests green; commit and push at milestones; open no PRs. Free ComfyUI's models after your batches, and never kill it. Ask the main session to have the owner run Kimodo when prompts are ready.

## Done this session

- **The animatic was watched through,** shot by shot. About 35 of its 54 boards are weak; the list is under Next.
- **Subtitles** (bfecf70, agreed with the story lead):
  - `CineLines.Subtitle` drops a lower-case (parenthesis), the VO pipeline's direction, and "sung" sets italics;
  - a capitalised one (C13's translations) stays;
  - the text in `dialogue.json` is untouched, so the takes still match;
  - the animatic does the same.
- **C02 to C04 are surveyed on the real sets and wired into the game.** They are previs pass 1, with stand-in motion; the details are in their shooting scripts.
  - **C02** at the ford, in place of `RunIntro`. The fight's Warden is spawned on `warden_end` by `warden_up`.
  - **C03** where the Warden falls, in place of `RunVictory`'s staging:
    - the zone passes `w` and `her` as marks;
    - Grimtunnel is spawned by the cinematic (tagged and neutral), and surfaced and burrowed by zone events;
    - the hand-back runs `Taken()` and `Dawnbreak()`.
  - **C04 A** on the north bank (or 25 s later, with a south variant on the fact `prologue.dawn_south`). Its `douse` event calls `Douse(false)`.
  - **C04 B** on the first arrival at the Waystation, with its own Rook (`rook_cine` hides the zone's).
  - Tests: C02's wiring is tested both ways. The Prologue tests pass without a screen.
- **Shooting scripts** for C02, C03, C04 A and C04 B are written from the timelines as they play, each with its changes from the written script and the reasons. The table in `shoot/README.md` is updated.
- **Player additions** (`src/Game/GameCinema.cs`, `logic/Cinema/CineFile.cs`):
  - casts: `boss` (the cinematic's own WardenView), `extras` (a crowd, cued together with a `stagger`) and `orb`;
  - cues: a `lamp` cue (glow and lit, for a boss or an orb);
  - `place` can `tilt` a body;
  - a `glow` can carry a `light`;
  - a `move` to an `abs` place goes through the water or the air;
  - spawns take `tag` and `neutral`;
  - atmosphere blends can run part of the way (`k0`, `k1`; a skip lands on `k1`);
  - the cue's `Actor` is a real field;
  - name plates and barks are hidden while a cinematic plays;
  - `--stills N` saves N frames of every shot, to judge motion;
  - `Game.CanCinematic`.
- **Fixes:**
  - `LayToIdle` no longer loops (`People.IsCycle`);
  - the Warden's lamp is an open iron cage with its flame showing (it was a solid box);
  - the C03 sounds `kneel_water`, `sink`, `lamp_out`, `heart_hum`, `burst`, `sniff` and `groan` are made in `Sfx.Cine` and in the animatic;
  - the story lint counts a cinematic's `when` facts as reads.
- **Merged** the integration branch. One conflict, in `Prologue.Douse`: the experience lead's dawn level-up is kept, and the caption is cut when C04 A has said the lines.

## Next, in order

1. **C04 B's B4a check (needs Godot).** Check that the toll tower's lamp sits in the tower's upper window. Run:

   ```
   python <scratchpad>/cin2/prev.py c04b s5 40 --zone waystation --only B4a
   ```

   The window is at about (30.9, 7.9, -6.6) and is set in three places in `c04b.json`: the mark `window`, the B1 `glow` and B4a's camera. Then render all of C04 B and look at it at full size.
2. **Remake the weak boards.** Use the engine stills as staging (img2img on Krea from the previs frames), so the Warden's scale and the framing match the surveyed cameras. Describe the Warden as a hooded giant in a ranger's leathers and old mail, not a robed wizard. Use no Victorian street lamps: the posts are square stone pillars with a cold blue flame in an iron cup, and there are no bridges at the ford. The weak boards:
   - **C01:** s2 (a dress, not her armour), s8 (an MS, not a CU), s8b (the head is cropped at the eyes), s10 (she sits rather than whips round), s11 and s12 (she is drawn twice; the fire is high, not embers);
   - **C02:** s1, s5, s9 and s11 (street lamps), s3 (two panels), s4 (an MS, and a frame border drawn in), s7 (scale), s10 (white trousers, colour) and s12;
   - **C03:** s1 (no blow), s5 (not a giant), s6 and s8 (the heart is held), s9 (no burst), s10 (no heart), s11 (crawls rather than dives), s12 (bridges) and s13 (twice);
   - **C04 A:** A1 (walks into the river), A4 (no ember, and a photographic background), A5 (no breath), A6 (frame lines), A7 (an MS, not a CU) and A8 (twice);
   - **C04 B:** B3 (they cheer), B4 (Rook smiling), B4b (stained glass) and B5 (twice).
3. **Block animation's three C01 clips** (`her/lie_side_wake` 7 s, `her/sit_back_heels` 6 s, `her/reach_coals` 4.2 s; merged, in `heroine.res`), in place of the log-sitting stand-in in C01's shots 2 to 8b:
   - `lie_side_wake`: she lies on her right side, head toward -X, facing +Z, and comes up onto her right elbow. Set her `lie` heading so that +Z faces the fire;
   - `sit_back_heels`: from that pose to kneeling on her heels, hands palm up before her lap;
   - `reach_coals`: the right hand goes out low, palm down, and stays.

   Re-survey with `--cinebones`, reframe every face shot to the kneeling eyeline, and then update `shoot/c01.md`.
4. **Recut the Prologue animatic** once the boards are remade. The command is:

   ```
   python tools/cinematics/animatic.py c01 "card:..." c02 "card:..." c03 "card:..." c04a "card:..." c04b --crf 28 --out docs/cinematics/shoot/animatics/prologue.mp4
   ```

   The exact cards are in `animatics/prologue.txt`. The timelines' new cameras don't change the animatic's clock, only the boards do.
5. **The Warden's look.** His ranger hood doesn't take the dye and reads white under the moon. He is to be remade (see `docs/art/MODELS_TO_MAKE.md`). Until then, tell whoever owns `WardenView` (`src/Actors/BossViews.cs`), or tint the hood there.
6. **C02 and C03's line choices** (in the engine): try C03's shots 1 and 2 from the east side, so the line isn't crossed. Check C02's shot 9 against a camera on the west.
7. **Then C07 and C09,** by the brief's order.
8. **Note from story (a54dc034ed29f2e02), 4 October: the owner approved the redesign below.** Story fights end on her choice where the story offers one, so two endings now need shooting:
   - **C11 has a spared ending.** At Redcowl's knee she chooses "Spare him" or "Finish it". The death part plays only if she finishes it, and "Finish it" is now the blow (shot 1). The spared part is new in `docs/cinematics/c11_raid_on_the_roost.md`, "Spared", six shots:
     - his line at the knee, `cin_raid_on_the_roost.spared` (four variants);
     - he gets up on the sewn leg and shoulders the axe;
     - `cin_raid_on_the_roost.flit`, "...Up, my lot! Boots on! We're flitting!";
     - his people part and he walks off without limping.

     The conversation's entry plays `spared` once `redcowl` = `spared`. Combat applies the outcome first, then plays the hook.
   - **C10's let-go is her choice.** "Let him go" or "Finish it" come after shot 3 (`c10_hollow_by_night.md`, "Variant: let go").
   - **C09 gives the first chart.** `vonnra.f_door` is shorter, and the new `vonnra.f_chart` lays a chart on the table: "That would be ten gold, traveller. This once, no charge." It's shots 12b, 12c and 16b in `c09_fortune.md`. The chart arrives by data whether or not the cinematic plays.
   - **Combat's hook ids:** combat's StoryNight tries `{cinematic}_arrival`, `_end` and `_spared` where `CanCinematic` finds one. Name the real ids when you build C10 and C11.
   - **A lost story fight** no longer comes to at the place. She wakes on Chid's bench the next morning, and his conversation opens with a narrated waking for that fight (`chid.carried`). Nothing to shoot unless you want it.
9. **The combat lead's boss redesign, now approved (see 8)** (a708da2c97bf85c95, `docs/design/STORY_BOSSES.md` on `worktree-agent-a708da2c97bf85c95@228394c9`). Once it is approved:
   - **C13's shot 1** changes. The fight now ends with her laying the Barrow Lord down: she stands over him in a pale-blue circle for 3 s (holy does it twice as fast), and he will not stay down. He rises inside her reach, and the hand plays. "The blow. He does not fall." becomes "she stands over him, and he will not stay down". The rest of C13 stands.
   - **C10** may gain a choice. Where the let-go's facts hold, she chooses with two prompts, "Let him go" or "Finish it"; today it happens on its own. Story is confirming.
   - **C10 to C12** are otherwise unchanged. Each fight still needs its two boss hooks (`docs/cinematics/README.md` 11a, arrival and end), which the runtime will call.

## Decisions (why)

- **The cinematic owns the boss's body while it plays.** The zone hides its own and takes him back at the cinematic's end mark. One body is ever on screen, and the fight starts where the picture ended.
- **C03 is framed relative to where he falls,** with her always put 4 m south of him behind shot 1's close framing. The cameras are offsets, so they hold wherever the fight ends.
- **Gameplay stays in zone code,** reached by `event` cues (spawns, burrows, Douse, the Apply effects). A skip still does what lasts.
- **The dawn is one sunrise across two cinematics.** C03 takes it a fifth of the way, the road holds it there, and C04 A finishes it with `k0` 0.2.
- **Stand-in clips are picked by bone checks,** not by name:
  - `Spell_Simple_Idle` tilted onto his back puts the left hand up out of the river;
  - `Idle_Torch` holds the left hand's lamp up;
  - `Fixing_Kneeling` is the kneel;
  - `Death01` falls backward, so the heart rises 2.4 m north of where he knelt.
- **C04 B has its own Rook** a step off the inn's wall, because every frame of her and the square from her real spot sits inside the inn.
- **Subtitles strip only lower-case parentheses.** That is VOICES' rule: a capitalised one is words to show.

## Failures and why

- **The cue's `actor` was lost.** `CineCue.Actor` was a computed property, so System.Text.Json kept the key out of `[JsonExtensionData]`, and every `"actor"` cue fell back to her. It is now a settable property.
- **`LayToIdle` looped** (its name contains "Idle"), so the Warden lay down again after getting up.
- **The heart's light blew out Grimtunnel at close range** (16 per glow). The cinematic orb now uses 6 per glow.
- **Atmosphere names are lower-case** (`dawn`, `night`). "Dawn" throws, and the cue fails with a warning.
- **First camera guesses landed inside trees and walls** (C04 A's ELS, the Waystation's inn). Survey with `_survey.json` before you frame.

## Gotchas

- **The worktree guard** refuses Bash commands that `cd` outside the worktree, or that are too complex to verify. Write files with the Write tool and run single `python <abs path>` commands. `python <scratchpad>/cin2/jedit.py <id> <edits.py>` edits a timeline in the house layout.
- **`_survey.json`** is a scratch cinematic (the tests skip ids starting with `_`). Point its `zone` at the set and render it with `prev.py _survey sv <until> [--zone Z]`.
- **The "THE LOW FORD ROAD" title** shows over previs stills under `--quick`, but not in play.
- **Previs vs play:**
  - in `--cine` previs there is no fight, so the zone's own Warden is asleep at home; `warden_cine` and `ford_clear` hide it;
  - Grimtunnel's surfacing is ticked by the zone's `Frame` (`grimByCine`), because the world is held.
- **Never commit `.import` and `.uid` files.** Add files by name. `godot/assets` is a junction to the main checkout's `public/assets`, marked skip-worktree. The `.godot` import cache was copied from the predecessor's worktree.
- **Headings:** 0 faces south (+z), π/2 east, π north.

## Collaborators (the roster is in `docs/team/README.md`)

- **Story:** a73ca9d35d0c487a9. They agreed the subtitle rule, and they rule on any line that fights a shot.
- **Animation:** a435f4dd0ac80df75. From Kimodo, still needed:
  - the Warden's `lie_arm_up`, `rise_stiff`, `wade_drag`, `bend_lift` and `kneel_fall`;
  - Grimtunnel's burst, sniff and dive (a lampling-rig composition or a retarget);
  - C04's `wade_out`, `flask_drink`, `walk_uphill` and `unfold_arms`;
  - to key by hand: the nod, the shiver and the exhale.
- **Voice:** a501b387a90d78b4e (paused). Add no new placeholders.
- **The models planner:** `docs/art/MODELS_TO_MAKE.md` (the Warden, the lamp-iron, the heart as a faceted stone).

## Files to read first

1. `docs/cinematics/shoot/README.md`, then `shoot/c02.md`, `c03.md`, `c04a.md` and `c04b.md`
2. `godot/data/cinematics/c02.json` (the boss, extras and glow cues in use)
3. `godot/src/Game/GameCinema.cs` (the cast kinds, `Do`, `Finish`) and `logic/Cinema/CineFile.cs`
4. `godot/logic/Play/Zones/Prologue.cs`: `StartIntro`, `WardenUp`, `OnWardenDown`, `GrimUp`, `GrimDown`, `HeartGone`, `FirstLight`, `CineEvent` and `Douse`
5. `godot/logic/Play/Zones/Waystation.cs` (`Begin`, `CineEvent`)
6. `<scratchpad>/cin2/prev.py` and `jedit.py`
