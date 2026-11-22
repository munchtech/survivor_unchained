# Survivor Unchained: evidence-based game plan (21 November 2026)

Status: a proposal for the owner. Nothing in the game was changed, installed, bought, deleted or restarted to write it. This file is uncommitted.
Evidence notes with file and line references: `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_devplan\STATE.md`.
Marionette is audited by its own session (started 21 Nov, deliverable `C:\Users\munch\Desktop\Marionette\docs\RECOVERY_PLAN.md`). This plan only says what the game needs from it (section E).

How to read the tags:
- **[O]** observed this session in code, data or frames (mostly by audit agents; three frames by me).
- **[D]** documented in project files, not re-checked.
- **[I]** my inference. **[A]** an assumption. **[R]** a recommendation. **[P]** a proposal that interprets a brief line that is not yet a specification.
- Web sources: **[V]** opened this session, **[N]** found by search but not opened (treat as unverified).

---

## A. Recommended direction

### A1. Verdict

The game is not held back by asset quality. It is held back by the minute of play: moving, hitting, understanding and choosing have never passed your own playtest, while most of the effort went into things that cannot be seen at the game camera.

- Every playtest verdict names feel, clarity and fun [D]: "too clunky to hook me" (3 Nov), "standing still" (4 Nov), "had no idea what the skills did ... nothing really felt satisfying" (10 Nov), "the movement feels bad. it does not feel buttery smooth in looks or feel" and "yeah this is just no fun. :(" (19 Nov).
- The largest costs were elsewhere [D]: body and arm rebuilds (about 9.65M tokens by 5 Nov, then a restart on 16 Nov), at least 49 face leads, a den look that ran at least 19 judged rounds and merged at "CLOSE", an art-color lane where 10 of 12 rounds failed.
- At the dungeon camera the heroine is about 70 px tall at 1080p [O, frame of 16 Nov]. Sub-millimeter ridges, pleats and face work do not reach the screen.
- The movement defects you felt on 19 Nov were diagnosed the same day in `docs/handoff/demo_feel.md` (item 7) and never fixed [D].

So the shortest credible path is: **feel first, then clarity, then the look at the real camera, then one build choice and one story beat, all inside the den.** No new systems are needed for that. The engine, the 60 Hz sim, the den, the Warden, the Lamps and Wicks design and the story bible are kept.

### A2. The five decisions that matter most

1. **Movement becomes a measured target.** Path of Exile 2 parity is defined by a 60 fps capture of the real game, and our build is compared to it frame by frame. The known defects are fixed first.
2. **The look gets a target painted at the game camera.** Your color reference is a close, low 3/4 illustration; the game is seen from 62 degrees at 24 m. The gap in today's frames is value grouping and shape size, not grading or stroke shaders. More shader rounds stop.
3. **Progression is kept and shown, not grown.** The design already is a Path of Exile + Last Epoch hybrid (Lamps board + per-skill Wicks with Turns + supports). The demo hides the part where they interact. The slice shows one of each.
4. **The story lands through one built moment.** One beat, in the world, without close-up cinematics, picked by the owner from three short pitches drawn from the bible. (The first proposal, a beat built on the toll, was scrapped by the owner on 21 Nov: "this toll thing sounds bad scrap it".)
5. **The way of working changes.** One critical lane at a time, a frozen spec before any judged work, round caps that are not raised, and your play session as the gate.

### A3. The vertical slice (exact scope)

One den run, played from a camp at its mouth, about 8 to 10 minutes.

| Part | In the slice | Not in the slice |
|---|---|---|
| Hero | The Warden heroine on body B until the body test (decision 14) decides, the one starter armor set as it is | Other callings, the male hero, further face or armor rounds on B |
| Place | The den (`hollow`), procedural rooms from `godot/logic/Maps/DungeonGen.cs`, plus one small camp screen (start, one NPC, a lamp-post) | Low Ford, the town, the Verge, other dungeons, arena mode, endgame maps |
| Foes | The den's six (wolf, blighted wolf, boar, runner, slurry boar, howler), one miniboss per run, the Pack-Mother. Re-cut by role so not every foe rushes her (decision 17) | New foes, the Ford-Warden boss |
| Skills | Four pressed skills on four keys (Sunder, Heroic Leap, Bladestorm and a fourth set in task 8), dash, the vial. No auto slot. Groundbreaker becomes a node: "every 3rd attack groundbreaks" (the owner, 21 Nov; decision 15) | Stances, Unions, the other 40 skills |
| Build [P] | Each of the 3 skills' Wicks with one Turn reachable in a run; one support socket with 3 supports that drop in the den; the first stretch of one Lamp road | The rest of the 574-lamp board (present, not the focus) |
| Loot | Pieces of the one set drop over several clears (your replay hook, 15 Nov), plus existing items | New armor sets |
| Story [P] | One beat for the den and camp, picked by the owner from three pitches (decision 12). Not the toll | Cinematics, storybook plates |
| Sound | As merged (lane F) | New music systems |

Why this slice: you already chose the den (15 Nov) and every part exists. It exercises each defining quality once: movement, combat, look, a build choice, an emotional beat. It is small enough to finish to your bar.

### A4. Scope against resources

Your direction on 15 Nov was "Keep full scope". The record says the resources do not support that at your quality bar: weekly usage hit 100 % on 19 Nov [D], single look lanes ran 19 rounds, and one calling of the planned set is built. I recommend cutting breadth (one place, one calling, one armor set, three skills) and keeping the bar. Breadth returns after the slice passes, using the reuse tests in milestone 5 to pick production methods that scale.

---

## B. Evidence and project assessment

### B1. What I could and could not do

- **Inspected:** the repo's team docs, design docs, owner notes, coordinator state files, game code and data (through five audit agents, with file and line references), three frames viewed by me.
- **Not run:** the game, Godot, Blender or any test. Your brief forbade restarting systems. Test counts and performance numbers are the docs' own.
- **Not seen:** any video of play. Motion claims rest on code reads, your words and the 19 Nov diagnosis.
- **Browsed:** partly. Several pages refused automated reading. Each source below is marked opened or not.
- **Not audited:** Marionette (its own session), how Low Ford, the town and the Verge are built, global illumination, day and night.

### B2. Constraints

Known [D]: one owner plus AI agents; RTX 5080 16 GB, 32 GB RAM, 164 Hz screen; Godot 4.5 C#, Forward Plus; US; 18+ tone; Meshy credits scarce; weekly model usage capped.
Unknown: target platforms and minimum hardware, a ship date or budget, whether a controller is a first-class input, the voice-over plan, your screen's resolution.

### B3. The pattern in the record

| Date | Your verdict [D] | Where effort went around it [D] |
|---|---|---|
| 3 Nov | "doesn't show enough to hook me, is too clunky to hook me, and visually doesn't hook me" | Face (49 leads), body P1, style lead (5-6M tokens) |
| 4 Nov | "i'm still struggling to see any gameplay other than just standing still" | Body rebuild ("remake over patch") |
| 10 Nov | "had no idea what the skills did ... nothing really felt satisfying" | Body B, armor on A then re-fit to B |
| 19 Nov | "the movement feels bad ... no fun" | Den look (19+ rounds), art-color (10 leads), armor (15 judge rounds for one outfit) |

Three causes repeat [I]:
1. **The gate asked the wrong question.** `DEMO_GATE.md` admits the gate "asked whether a player can get through ... and never whether they would want to" [D]. 3,081 tests cover logic and data; none covers feel, pacing or fun [O].
2. **Judges without a fixed target.** The coordinator's own finding: "the lane chases numbers each judge invents, and they drift" [D]. `PIPELINE.md:8`: "a judge's notes become the next lead's list, and the list never ends" [D].
3. **Parallel lanes on moving foundations.** Armor was fitted to body A and re-fitted to B; a body change forced 211 clips to be rebaked [D].

What worked [D]: lanes with a number (den load 92.4 s to 5.0 s, GC pauses 5.1 s to 0.19 s per 140 s), cheap lanes (sound: one Sonnet lead), and your scope cuts of 15 Nov.

### B4. Audit by area

**Movement, input, camera: IMPROVE. Confidence high on the defects, medium on the size of the gain.**
- Evidence [O]: `godot/src/Game/Controls.cs`, `WorldScene.cs`, `FollowCamera.cs`, `godot/logic/Sim/Battle.cs`, `godot/src/Actors/PlayerView.cs`; [D] `docs/handoff/demo_feel.md`.
- Fit: the foundation is right. Fixed 60 Hz sim with drawn-position interpolation, a 120 ms input buffer, WASD plus cursor aim, six-way legs.
- Main problem: five known defects, all unshipped. (1) Camera lead of about 2.5 m, damped: about 1 s of scroll after a stop, about 2 s of drift on a reversal. (2) Facing follows the cursor with a 0.1 m deadzone and no hysteresis, so facing and dash flip with a still mouse. (3) Hit-stop freezes the pose but not the position: she slides 0.3 to 0.55 m. (4) Dash exit curves about 0.4 m off the held line. (5) Velocity reaches 95 % in about 214 ms and turn rate caps at 840 degrees per second, both soft.
- Camera as built [O]: perspective (not orthographic), field of view 34, pitch 56 to 64 degrees by zone (dungeons 62 at 24 m), no rotation, no player zoom. I do not assume this from the genre: it is what the code does, and your 15 Nov rule keeps it at the Path of Exile and Diablo standard. Path of Exile 2's camera is reported fixed [N]; its pitch and distance are unmeasured.
- Also [O]: two facing truths (the sim faces velocity, the view faces the cursor); the dash has charges and aims at the cursor, while Path of Exile 2's roll is reported to have no cooldown and follow the held direction.
- Why improve, not replace: none of the defects comes from the architecture. Each is a constant or a small rule.
- Missing: a frame-level Path of Exile 2 reference; a film of our build.

**Animation: KEEP the runtime, SIMPLIFY the authoring. Confidence medium.**
- Evidence [O]: one AnimationTree blend tree, stride-phase matching, six directional run clips, no leg IK; `tools/anim/manifest.json` (115 clips made, 75 planned); six clip sources.
- Problem: cost and fragility of clips (23+ judged rounds for one hang pose [D]), not the runtime. Your 15 Nov note (rigid sword arm, only the legs move) reached "CLOSE", not pass [D].
- Recommendation: freeze the clip list to what the slice plays; judge only in a game-camera film; make no new clips until movement passes.
- Missing: I did not read `docs/handoff/animation.md` or the motion plans; cost per clip is unknown.

**Combat and readability: IMPROVE. Confidence high that it is the second problem.**
- Evidence [D]: your notes of 10 and 19 Nov ("i actually don't know how bladestorm works", "i also have no idea how to light my lamps", "why do some monsters block nonstop"); [O] `godot/data/content/telegraphs.json`, `hit_stop.json`.
- Problem: the player cannot tell what a skill does, where a dash goes, or why a foe will not die.
- Recommendation: a clarity pass inside the den before any new content.
- Missing: which of lane K's items 4, 5, 8 shipped (I did not check each).

**Rendering and look: SIMPLIFY and retarget. Confidence medium-high.**
- Evidence [O]: about 200 shaders, three screen passes (`CelLib.cs` material rewrite, `InkPass.cs` line, `FxAfter.cs` effects after the grade), three anti-aliasing regimes by zone, 1,554 command-line flags of which 332 are `--den-*`; [O, by me] the three frames.
- Fit: the pieces work and are cheap (den 3.4 to 4.5 ms of GPU on the RTX 5080 at 1080p [D]).
- Problem: the look is tuned per zone by flags against targets that move. In the frames, the den is mid-value brown on mid-value brown with a 70 px heroine that does not separate; the art-color round reads as even speckle with flat tree tops and flat stones. Your reference gets its beauty from big shapes, three clear value planes and light sources, drawn close and low.
- Recommendation: stop grade and stroke rounds. Paint the target over a real game frame, then fix value and shape in assets and materials.
- Missing: I viewed stills only. Shipped-game sources for this claim are not opened (B5).

**Environment: KEEP the den, INVESTIGATE the method before building a second place. Confidence medium.**
- Evidence [O]: `DungeonGen.cs` (reusable layout); `DungeonDress.Set.cs` (paintings projected along the fixed camera onto proxies, den-specific).
- Problem [I]: a second environment needs new paintings and re-tuning of about 330 flags. The method is unproven for reuse and breaks if the camera ever rotates.
- Recommendation: test reuse once (milestone 5) before any breadth.

**VFX: KEEP for the slice, SIMPLIFY authoring after. Confidence medium.**
- Evidence [O]: 19 `BattleFx` files, 11,316 lines, no particles, each skill written in code; `godot/data/look/fx_language.json`; [D] Sunder's crescent measured at 0.064 contrast on warm ground, hit paint "blends with world marks".
- Problem: effects are costly to add and some do not read. 45 to 55 ms spikes come from this code or from pipeline compiles [D].
- Recommendation: fix reading and spikes for the slice's four skills; later prove one new skill can be made from data alone.

**Characters and assets: no more rounds on body B; the body itself is an open question (decision 14).** Body B and the one armor set are in, and more polish rounds on them do not change a 70 px figure. The same fact cuts the other way: B was built for close-ups the game does not show, and that difficulty was paid again in every step after it (hip, belt and rib hand patches, 15 judge rounds for one outfit, 211 clips rebaked) [D]. The owner (21 Nov): "if we never need to zoom in - the body can be simpler.  if its simpler - it animates better and has precise measurements for armor etc." A simpler body built for the game camera is tested once the look target exists, through Marionette. Pipeline questions belong to the Marionette session.

**Progression: KEEP, show it. Confidence high on the diagnosis.**
- Evidence [O]: `docs/design/BUILD_DIRECTION.md`, `BUILD_UNLOCKS.md`, `godot/data/content/` (44 skills, 574 lamps, 16 Turns, 8 supports, 10 Unions), `godot/src/Ui/LampBoard.cs`.
- Fit: the hybrid you asked for is already designed. Lamps are the shared board (Path of Exile side); Wicks are a small tree per skill ending in a Turn that changes the skill (Last Epoch side); supports are socketed gems.
- Problem: content is far ahead of legibility, and the demo (levels 1 to 8) cuts supports and Unions, so the hybrid is never felt. A rank rule disagrees between `godot/logic/Rpg/SkillBook.cs:154` and the design doc.
- You said on 3 Nov: "lamps is promising! heavy customization and build diversity and exploring is great to have". The direction is right.

**Narrative: KEEP the bible, BUILD one beat. Confidence medium.**
- Evidence [O]: `docs/STORY_BIBLE.md` (1,626 lines), about 6,600 dialogue strings, voice-over all placeholder, no code for the toll, and `godot/data/content/demo.json` hides all story.
- Problem: the demo ships no story, and the strongest idea is unbuilt.

**Performance: IMPROVE, small. Confidence high.** Worst warm frame 53 ms, 1,856 pipelines at warm-up, GC 3.5 ms about every 2.6 s [D]. "Buttery" on a 164 Hz screen needs steady frames as much as good curves [I].

**Process and tests: SIMPLIFY. Confidence high.** See B3. About 15 coordinators, `RESUME.md` at 713 KB, `tools/scratch` about half of 6,700 tool files [O].

### B5. Research

Path of Exile 2 (reference version: the live 0.5.x patch, to be confirmed in the game on capture day; 0.5.0 reported live 29 May 2026 [N]):
- 0.3.0 patch notes [V, partly]: holding the dodge roll button goes into a sprint after the roll (read verbatim); the penalty on skills usable while moving falling off faster was read only through a summary. https://www.pathofexile.com/forum/view-thread/3826682
- WASD is the default scheme with click-to-move kept [N, PC Gamer]. The character faces the cursor and strafes or backpedals [N, player forum posts; no official statement found].
- Dodge roll: no cooldown, follows the held direction, cancels skills, not invulnerable [N, poe2db.tw/us/Dodge_Roll].
- **Unknown without frame-level footage:** facing when only moving, turn rate, start and stop frames, roll distance and length, the size of the move penalty, cancel and buffer windows, camera pitch, distance and look-ahead. I found no source for the internal implementation and claim none.

Reference footage (the owner chose public footage on 21 Nov: "Use public footage"). Found in a YouTube search listing on 21 Nov; **none has been watched yet**, so frame rate, patch and control scheme are as the titles claim until task 2 checks them:
- Official, shows the WASD scheme, old build (about 2 years): "Path of Exile 2: Mercenary Gameplay Walkthrough", Path of Exile channel, 12:23. https://www.youtube.com/watch?v=mU7mLtj7nxU
- Cancel windows on Warrior skills, WASD against mouse, chaptered per skill (about 10 months old): "Animation Canceling by Walking in PoE2, WASD vs Mouse", Gobbo, 1:26. https://www.youtube.com/watch?v=mX8XgeX0VYk
- Movement explained move by move (about 2 years old): "Path of Exile 2!! | WASD Movement Breakdown", MrLlamaSC, 9:35. https://www.youtube.com/watch?v=0sHeOGW9lt4
- Long melee play without commentary (about 7 months old, so likely 0.4.x): "Path of Exile 2 - Warrior Gameplay Walkthrough (Act 1-4) No Commentary", CaptainCigar. https://www.youtube.com/watch?v=kafVcaU7S0w
- Titled 4K 60FPS, no commentary (about 1 year old): KG Evil-Ash, https://www.youtube.com/watch?v=jpPo8H9zEI8 ; a short Warrior boss fight, DarkLight, https://www.youtube.com/watch?v=jefJa9gL8Lo
- A 0.5 Warrior build guide with commentary (about 4 months old), for current-patch motion: Massify Gaming, https://www.youtube.com/watch?v=e_7EwDqhMWI

What public footage can and cannot settle [I]:
- **Can:** the shape of motion from its first visible frame (time to full speed, stop, reversal, roll distance in body lengths and its length in frames), facing and strafe behavior, which skills let her move, cancel timing where a clip shows it, camera pitch, distance and look-ahead measured from the picture.
- **Cannot:** the delay from key press to first motion (no clip found shows inputs), the exact settings and patch of each clip, and anything a 60 fps upload hides between frames. So input delay is judged on our build alone (D1), and no number from a clip older than 0.5 is trusted until a 0.5 clip agrees with it.

Last Epoch: up to 5 specialized skills, each with its own tree [N, maxroll]; a developer post says one designer hand-builds each skill tree over several iterations [V by the research agent]. https://forum.lastepoch.com/t/making-last-epoch-skill-design/78179

Techniques:
- Godot physics interpolation [V]: move interpolated nodes on the physics tick, reset interpolation after a teleport, the camera may need its own interpolation. https://docs.godotengine.org/en/4.6/tutorials/physics/interpolation/using_physics_interpolation.html
- Pillars of Eternity update 79 [V]: backgrounds as 2D renders with depth, normal and albedo passes, which only hold under an orthographic camera at the right angle. This is the known limit of our den's projected set. https://eternity.obsidian.net/news/update--79-graphics-and-rendering-
- Painted looks built from authored art and value design rather than screen filters [N, none opened]: Guilty Gear Xrd (GDC 2015, https://www.gdcvault.com/play/1022031), Hi-Fi Rush (GDC 2024, https://gdcvault.com/play/1034251/3D-Toon-Rendering-in-Hi), Marvel Rivals art director interview, Diablo IV art blog.
- Readability rules [N]: Valve's Dota 2 character art guide (the page loaded without its text) and Riot's VFX style guide (the link now redirects). I use their commonly cited principles as hypotheses to test, not as established fact.
- AI-assisted asset workflows: only vendor blogs found. No credible production evidence. Our own tests decide.

### B6. Five questions

1. ANSWERED 21 Nov: "Use public footage". (Asked: would you record about 10 minutes of Path of Exile 2 at 60 fps with an input overlay.) Parity is judged against the public clips listed in B5, with the limits stated there.
2. ANSWERED 21 Nov: "yes as poe2 is reported to do". The dash follows the held WASD direction. (Asked: the held direction or the cursor.)
3. ANSWERED 21 Nov: "sure?" A soft yes, to be confirmed when the slice start is shown. (Asked: may the slice drop Low Ford, the town and the Verge and start at a camp by the den with a mid-level Warden.)
4. ANSWERED 21 Nov: "this toll thing sounds bad scrap it". The toll beat is out of the slice. Correction for the record: I had described it to the owner wrongly (a death for each lit lamp). The bible's rule 6 (`docs/STORY_BIBLE.md:66`, the owner's canon pick of 11 Oct) is that each time the survivor falls and rises, one person in the valley quietly dies, and nobody says so until Act 3. My beat would also have shown that twist in the open. Still open: does rule 6 itself leave the story, or only the slice beat? Nothing in the bible was changed.
5. ANSWERED 21 Nov: "not worried about that, but controller input is great as well as pc - its both". No minimum hardware target for now. Controller and keyboard with mouse are both first-class; D1 applies to both.
6. ANSWERED 21 Nov: "we don't zoom in for her anymore.  thats the kind of thing were looking to cut to be more realistic - other arpgs never do that, we won't either". The closest she is shown is the game camera. (Asked: what is the closest she is ever shown.)
7. The owner's lean, 21 Nov, not asked by me: "I think our hybrid auto skill and non hybrid skill is probably too confusing.  we can make an auto support gem but we should just copy normal arpg skills probably - there are some auto things and auras but maybe not a key thing.  stances and unions are already things that set us apart". And: "groundbreaker would be like a node you know? every 3rd attack groundbreaks." Asked whether to make "every skill is pressed" the rule, the owner answered: "i mean not every single one.  just mirror what others do.  auras can exist etc". See decision 15; written into `docs/design/BUILD_DIRECTION.md` as Round 9.

---

## C. Creative and technical decisions

Effort unit [A]: one **lead session** is one lead agent working to its context budget with its helpers. Past art lanes cost 1.5 to 2.5M tokens per lead [D].

| # | Decision | Approach [R] | Rationale and evidence | Tradeoff | Smallest test, limit, pass and stop rule | Fallback |
|---|---|---|---|---|---|---|
| 1 | Movement target | Parity with Path of Exile 2's WASD scheme, measured frame by frame from the public clips in B5 (the owner's choice, 21 Nov) and a matching capture of our build | You named it the benchmark. Written sources leave the key numbers unknown (B5) | No input timing, mixed patches, lower confidence than our own capture | The same 12 moves found in the clips and shot in our build, frame counts side by side. Limit: 1 lead session. Pass: each unknown in B5 has a number with its clip and timestamp, or is marked "cannot be read from footage". Stop: if two clips disagree by more than 2 frames on a move, that number is not used | The owner records 10 minutes later, only for the numbers the clips could not give |
| 2 | Movement fixes | Fix the five known defects behind flags, then tune to decision 1's numbers | Diagnosed 19 Nov, unshipped [D]. Cheap, no new system | May expose animation flaws the float was hiding | You play a grey room for 10 minutes, old against new, blind. Limit: 2 lead sessions. Pass: you pick new and say it is smooth. Stop: if you cannot tell them apart, the cause is elsewhere, go to decision 5 | None needed: each fix is a flag |
| 3 | Dash rule (direction DECIDED by the owner, 21 Nov: the held direction) | Follow the held WASD direction or stick; with nothing held, go toward the cursor (stick: her facing). Test charges against no cooldown | You called the cursor dash "very bizarre" (19 Nov); the benchmark is reported to use the held direction [N] | Changes encounter balance if cooldown goes | A/B in the same grey room. Limit: half a lead session. Pass: you can call the direction before pressing, 10 of 10 | Keep cursor dash but draw a ground arrow while it is ready |
| 4 | One facing truth | The sim carries aim and move directions separately; the view only draws them | Two systems today [O]; hit-stop slide comes from the same split | Touches tested sim code | Existing sim tests stay green plus a new slide test (0 m during hit-stop). Limit: 1 lead session | Keep the split, freeze position in the view during hit-stop only |
| 5 | Frame pacing | Trace a full den run in the shipping build, attribute every frame over budget, fix the top causes (pipeline warm-up, `BattleFx` allocation) | Worst warm frame 53 ms [D]; you named lag 6 times on 19 Nov | Longer first load if more is pre-compiled | The trace itself. Limit: 2 lead sessions. Pass: criteria in D1. Stop: when the next cause costs more than 1 session for under 1 hitch per run | Accept spikes only in the first 5 s after a load |
| 6 | Look target | A paint-over of 3 real den frames at the game camera, approved by you, then frozen as numbers | Reference and game differ in viewpoint and scale [O]. Lanes without a frozen target drifted [D] | The den's projected paintings may need repainting to the new value plan | 3 paint-overs. Limit: 1 lead session, 2 rounds with you. Pass: you say "this is the game". Stop: after 2 rounds, pick the closest and name the gap | Use your reference's palette only, with the value plan from D3 |
| 7 | Look method | Reach the target through value grouping, larger shapes and light in assets and materials. No new screen pass, no new flags | The frames' gap is not grading (B4). The brush pass was already rejected [D] | Less "filter" character in stills | One den room, before and after, in a 10 s film at 1:1. Limit: 3 rounds, cap not raised. Pass: D3. Stop: at the cap show you the film and the 3 remaining gaps; you decide | Hero-only fix: a light rim and a quiet, darker ground disc under characters |
| 8 | Environment method | Keep the den as merged. Decide the method for more places only after a reuse test | Projection is tied to one camera and one set of paintings [O], [V Pillars] | Delays new places | Milestone 5: a second room theme using existing rules and zero new flags. Limit: 2 lead sessions. Pass: you accept it at the den's level | The post-demo bake-off you already planned (meshes, splat-to-mesh, painted cards) |
| 9 | VFX reading | Rank every effect: your hit, their telegraph, then ambience. Brightest and most saturated in that order | Sunder's crescent at 0.064 contrast [D] | Some effects get plainer | A 10 s film of a 12-foe fight; you name each skill and each danger. Limit: 2 lead sessions | A ground-color-aware tint per zone for the two worst effects |
| 10 | Skill movement rules | One data row per skill: free, slowed, planted, or drawn toward the cursor (Bladestorm) | Your Bladestorm note; `godot/data/content/cast_move.json` exists but is off [O] | Per-skill balance | Bladestorm follows the cursor with no keys held; Sunder's slow matches decision 1's numbers. Limit: 1 lead session | Keep today's single rule and special-case Bladestorm |
| 11 | Progression in the slice [P] | Keep Lamps, Wicks, supports. Show one Turn, one support socket and a few lamps in a single run by starting mid-level | The hybrid interaction is cut from today's demo [O] | Skips the level 1 to 5 teaching ladder in the slice | After a run you can say what your last 3 choices changed. Limit: 2 lead sessions. Stop: if you cannot, fix the telling (tooltips, before and after preview) before adding any node | Supports only (drop the Turn) if two systems confuse in 8 minutes |
| 12 | Story beat [P] (the toll beat was SCRAPPED by the owner, 21 Nov) | An author lead pitches three beats for the den and camp from the bible, one plain paragraph each, each told in play (a line from someone at the camp, a thing found in the den, the boss's last words). The owner picks one | The owner: "this toll thing sounds bad scrap it". That beat also showed a twist the bible hides until Act 3 (`docs/STORY_BIBLE.md:66-76`) [D]. The bible already holds the model: the Ford-Warden, dying, asks "whether it is morning" (`docs/STORY_BIBLE.md:30-31`) [D]. Supergiant's in-play narration [N] | The slice has no story until the pick | Three pitches on one page. Limit: half an author session for the pitches, 1 author session for at most 40 lines, 1 session to wire. Pass: D7. Stop: if the built beat does not land, rewrite it once, not the system | A narrator line over play at the boss's death |
| 13 | Way of working | One critical lane; a frozen spec before judged work; cap of 3 rounds, never raised by the lane; your play as the gate; every art task proves itself in a 1:1 game-camera film | B3 | Slower in appearance, fewer parallel lanes | Run milestones 0 and 1 this way and compare cost per accepted change with November's lanes | Two lanes only when they share no files and no foundation |
| 14 | The body. **STILL OPEN (22 Nov); the commit that said "B stays" was this session's over-reading of a relay.** The first test body lost on looks at gate 1 (the owner, 22 Nov, to the Marionette session, on a sheet of B beside it at the game camera: "eh - b looks a lot better.  can we use its exact measurements to make armor work as well? or was that something that was specific to a less complicated model?"). That test body was a low-detail copy of B, so the verdict is on that build, not on the idea (the owner, minutes later: "well I wasn't against completely changing our body...not trying to look the same.  I don't know if that is what made it worse or not.  were trying to work smarter not harder - does that matter?"). The skeleton and the clips are open too (the owner, 22 Nov: "it might need a new skeleton and new animations.  thats the whole reason were doing these audits.  if we have a bad foundation we need to change it"), so "KEEP the 124-bone rig" in the next column no longer holds. Decided: "the face obviously no matter what dosn't need to be extensive anymore". Meanwhile B's named rings are measured at rest and over her clips so armor is built to numbers. The Marionette session owns this decision and reports a proving session running (a new body on the current skeleton without helpers, in motion beside B, an engine frame, the corset carried to other body shapes with no refit); no results yet, and nothing here is checked from the game side. The rest of this row is the 21 Nov plan. (STARTED 21 Nov on the owner's word: "where is the new body being developed? that will make gearing easier and may even look better with less as its designed to be viewed from game view not close"; the test decides) | A simpler heroine body built for the game camera: its own low, even topology with named measurement rings (bust, waist, hip, limbs) so armor is built to numbers. Bust, hips and butt are pushed past realistic so they read at 70 px; everything else stays plain (the owner, 21 Nov: "a simpler one with exaggerated "sex assets" but overall very clean and easy to manipulate and gear?"). KEEP the 124-bone rig and its joint positions. Detail level set by the game camera and nothing closer (the owner, 21 Nov: "we don't zoom in for her anymore"); a character or inventory screen shows her at a modest size with the same model. Built in the Marionette session (worktree `Marionette_body0`, branch `body0-1`) beside its gear route, which stays first; gear re-fits on whichever body wins (the owner to that session, as it relays: "gear first, but we may be changing our body still I believe") | She is about 70 px tall at the camera [O]; B's close-up detail made fitting, deformation and judging hard for no visible gain [D]; the look target may change her shape language [I]. The owner, 21 Nov: "the whole point of these audits is to see if we didn't need things to be so difficult" | Her look at any close shot gets plainer; the Warden set is refitted; NPC bodies follow the same method | Started 21 Nov in the Marionette session: shape, measurement rings and rig bind first, since none of that depends on the paint look; skin paint follows the look target (decision 6). The owner sees the bare shape at the game camera before gear is fitted. Then the simple body against B by (a) a blind film at the game camera, (b) the Warden set fitted with zero hand patches, (c) the 12 movement shots with no deformation faults. Limit: 3 lead sessions, in the Marionette session. Pass: equal or better at the camera and the fit needs no patches. Stop: at the limit, keep B | Keep B and simplify only what is fitted to it (gear built to measured rings on B) |
| 15 | Skill kinds (the owner, 21 Nov: mirror the genre) | Do what other ARPGs do: "i mean not every single one.  just mirror what others do.  auras can exist etc". Most skills are normal pressed skills; auras, summons and triggered effects exist the way the genre has them. Retire only what is ours and confusing: a skill offered both ways ("kindled"), and the three auto slots as a separate layer of the bar. "Auto" becomes one support gem: socketed in a skill, the skill fires itself on a simple rule, at a cost, and frees its key. Auras are a few always-on skills paid by reserving a resource, with no key. Auto skills granted by items become plain effects written on the item. Today's auto skills become nodes on the tree that add a trigger to what she already presses (the owner, 21 Nov: "groundbreaker would be like a node you know? every 3rd attack groundbreaks."). What sets the game apart: stances and Unions, with Wicks and Lamps | The owner: "I think our hybrid auto skill and non hybrid skill is probably too confusing ... we should just copy normal arpg skills probably ... stances and unions are already things that set us apart". The design's own pushback named the layer count (`docs/design/BUILD_DIRECTION.md:43`) [D]; the three-kind rule is in `godot/logic/Rpg/SkillBook.cs:69-74` [O] | Loses the build that plays itself; the bar rule, the taught builds and their tests are re-cut | Paper first: one page listing every current skill with its new kind (pressed, aura, or cut) and what the auto gem does to it. Limit: half a lead session. Pass: the owner approves the page. No code before that; the slice needs only four pressed skills | Keep auto slots for auras only, with no kindled forms |
| 16 | Tool versions (the owner, 21 Nov: "we should consider updating our blender and godot they are versions behind") | Upgrading is settled; the only questions are when and what breaks (the owner, 21 Nov: "we shouldn't be planning on never upgrading our blender or godot as they will continue to update and we don't want to be trapped not updating"). Standing rule (my proposal): each new stable release of Godot and Blender gets a side-by-side trial at the next milestone boundary, so a milestone never starts more than one stable release behind. Never a blind switch in the middle of judged work. **Godot:** try 4.7.2 in its own worktree after task 1's movement baseline exists and before tasks 3 and 5 start, so movement is measured and fixed on the same engine. **Blender:** the Marionette session owns a side-by-side trial (new version installed beside the old, one full pipeline run on each). No download or install before the owner's go-ahead | The game is on Godot 4.5.1 (`Godot.NET.Sdk/4.5.1` in the csproj) [O]; the latest stable is 4.7.2, published 18 Aug 2026 (GitHub releases) [O]. This machine's Blender config folder is 4.5 [O]; the Blender skills repo is written for 5.2 LTS and later (its author's statement) [D]. From the official release and upgrade pages (godotengine.org/releases/4.6/ and /4.7/, docs "Upgrading to Godot 4.6" and "4.7") [D]: 4.6 adds an IK framework (two-bone IK and others, useful for foot plant and hands on weapons); glow now blends before tonemapping and is "significantly brighter", and volumetric fog is brighter, so the painted look needs a re-tune; scene files change format on first save (large diffs); C# breaks on some AnimationPlayer members. 4.7 gives each render pass its own environment buffer, stops clamping in LinearToSRGB, flips a Jolt world-boundary sign, changes keyboard and mouse device ids, and breaks C# on `Animation.length` (float to double). The pages say nothing about compositor effects, frame pacing or input latency, so only the trial can answer those. The `godot-skills` repo was read (14 of 27 skills in full): mostly generic practice written for 4.7; its `api_lookup.py` and `migrate_scan.py` are worth using in the trial, and its skills are safer to give to leads after the upgrade because they name APIs that 4.5.1 lacks | Custom compositor effects, shaders and the C# bindings are where an engine upgrade usually breaks [I]; a week lost here delays the movement work | One lead session: the C# build is clean, the test suite passes, the den's perf trace and the 12-shot movement numbers are equal or better than on 4.5.1, and a game-camera film shows no change in the look. If the fixes need more than that one session: list what broke and make the upgrade the first task after the slice, with a date. Staying on the old version is never the outcome | Upgrade at the first milestone boundary after the slice, with the breaks already listed |
| 17 | Enemy behavior (the owner, 21 Nov: "the way the mobs are now is too derivative of when we were a survivors roguelike.  everything just charges and it gets annoying.  clear speeds feel unfun.  its a fun effect sometimes, but its like all our stuff does over and over") | Re-cut the den's foes by role, the way ARPG packs are built: most foes walk in and trade blows, some hold range, one heavy winds up a readable slam, and the charge belongs to one foe as its telegraphed special. Packs wait where they stand until she comes near; they do not stream to her. A repetition rule: in a zone, one behavior or effect has one home, and no pack is made of a single role. Use the behavior kinds the code already has before writing new ones | The enemy table already has 11 behavior kinds (`godot/logic/Content/Enemies.cs:29`) [O]. **The cause is one shared rule, not the roster** [O]: in every woken dungeon pack, `MapRun.Press` (`godot/logic/Play/Zones/MapRun.cs:394`) makes every ordinary foe without a ranged attack cast the pack kit's charge. The roster page (`docs/design/DEN_ROSTER.md`, 22 Nov) reports each foe casts it every 2.0 to 2.8 s at the den's tier, about one red lane every 1.5 s after the caps, on top of the boar's, runner's and boss's own lanes; her own kit (Shield Charge, Heroic Leap, the dash) is line moves too. Packs already wait and wake at 14 m; the survivors leftovers are the Hunt's ring spawns and the boss's wolf spawns. At tier 1 the den fields only wolf, boar and runner (the page's finding, not re-checked here) | The den's fights and their tests are re-tuned; density and drops move with clear speed | Paper first: `docs/design/DEN_ROSTER.md`, one page: what each den foe does today (from code), how the genre builds packs (sourced), the re-cut roster, and clear-feel targets. Limit: half a lead session for the page, 2 lead sessions to build once the owner approves it. Pass: the owner plays the den and says clearing is fun; at most one foe in three in a pack has a telegraphed move, and each telegraphed move belongs to one foe kind (the page's correction: genre packs are mostly one ordinary kind, which is what lets one area skill drop a group) [A]; proposed targets: a pack dies in 6 to 10 s, half a pack fits inside one Bladestorm or Leap, at most one lane every 8 s. Stop: one re-tune after the first play, then cut foes rather than add systems | Keep the six and change only the approach: walk in by default, the charge on one foe |

---

## D. Quality and acceptance criteria

All numbers are proposals. Assumed rig [A]: your PC (RTX 5080 16 GB, 32 GB RAM, 164 Hz), 1920 x 1080, the shipping export, one den run (`hollow`, level 6) after its first load. Numbers marked (ref) are set from the Path of Exile 2 capture, not invented here.

**D1. Movement**
- Start, stop, 180 degree reversal and roll each match the reference within 1 frame at 60 fps, counted from the first frame of visible motion (ref).
- Key press to first visible motion on our build: at most 3 frames at 60 fps (50 ms) [A]. Public footage shows no inputs, so this one is an absolute target and not a comparison.
- Every movement criterion passes on both a controller and keyboard with mouse (the owner, 21 Nov: "its both").
- After a stop, the camera is still within 6 frames (0.1 s). After a reversal there is no visible drift.
- With the mouse still, facing does not change. During hit-stop she moves 0 m.
- You can say where the dash will go before pressing it, 10 of 10.
- Zero frames over 16.7 ms in the run after the first 5 s; 99.9 % of frames under 2 times the median frame time.
- The gate: you play 10 minutes and call it buttery, unprompted by numbers.

**D2. Animation**
- Judged only in film at the game camera, at full speed and at quarter speed.
- Feet do not slide more than about 5 cm per step at run speed [A; today's figure is unknown].
- In a run, the sword arm and torso visibly move at 70 px height (your 15 Nov note).
- Every attack shows wind-up, contact and recovery that you can tell apart; contact matches the hit frame.

**D3. Visual cohesion**
- Three value groups hold in any frame: ground darkest and quietest, characters lighter and more saturated, effects brightest.
- Blur test: with the frame blurred by about 8 px, the heroine, every foe and every danger mark can still be found.
- Greyscale test: the heroine's average brightness differs from the ground around her (3 body widths) by at least the margin measured on the approved paint-over, in 90 % of sampled frames.
- No new `--den-*` flags. A second room theme reaches the same result with none (milestone 5).
- The gate: in a blind A/B of 10 s films, you choose the new frame.
- The owner's ruling, 22 Nov 2026, on how foes read on look option C: "Dark, pale rim, ink line (Recommended)". The option's text: wolves stay near-black charcoal with a thin pale rim light and an ink outline; she and the danger marks are the light, warm things; the rule gets rewritten to say so. (Recorded here; the first bullet above is not rewritten yet.)

**D4. VFX**
- The existing budget in `docs/design/FX_LANGUAGE.md` holds (at most two hues per effect; hit brightness and bright-pixel limits).
- Each player skill's main shape contrasts with the den ground by at least 5 times Sunder's measured 0.064 [A, to be calibrated on the paint-over].
- No effect hides a danger mark. No effect causes a frame over budget.

**D5. Combat readability**
- After one use, you can say what each skill does. Each has a tooltip with its numbers.
- After each death you can say what killed you.
- A blocking foe shows when its guard is up and when it drops; common foes die in a time you call fair [A: target set after the balance bots are re-run].

**D6. Progression**
- Each choice changes something you can see or feel within 30 s of play (a Turn changes the skill's shape; a support changes its behavior).
- After a run you can name your last 3 choices and what each did.
- Two runs with different choices feel different to you.

**D7. Emotional impact**
- The next day, without prompting, you can say what happened in the den's story beat and how you felt about it.
- No close-up cinematic is used to get there.

---

## E. What to stop, keep and simplify

**Added 21 Nov, the owner's cuts:**
- **No zoom-ins on her.** "we don't zoom in for her anymore.  thats the kind of thing were looking to cut to be more realistic - other arpgs never do that, we won't either". So: every character check and judge runs at the game camera only; the close cameras used in past body, face and hair gates are retired; no work is accepted for a view the game does not ship. Face, hair and skin detail is set by what reads at about 70 px.
- **No auto-skill system of our own** (decision 15): skills work as in other ARPGs. Most are pressed; auras and triggered effects exist as the genre has them; "auto" can be a support gem or a node.
- **The toll beat** is out of the slice (decision 12).

**Stop (for the slice; nothing is deleted):**
- New body, face, hair and armor rounds. Body B and the one set are in.
- Grade, stroke and day/night rounds in the art-color lane. Its round 9 stays unjudged; only its frozen-spec tool is carried forward.
- Raising judge caps. Adding `--den-*` flags. Making new animation clips. Adding lamps, skills or foes.
- Polish on Low Ford, the town and the Verge. Cinematic and storybook look rounds.
- Judging stills or close-ups for anything seen in play.

**Keep:**
- The 60 Hz sim with interpolation, the input buffer, timer-driven attack beats, data-driven hit-stop, the six-way run set.
- `DungeonGen`, `InkPass`, `FxAfter`, the school palettes, `tools/style/demo_look_check.py`, the fixed camera (your 15 Nov rule).
- Lamps, Wicks and Turns, supports, the loot system, the balance bots, the 3,081 tests.
- The story bible. The sound lane's way of working. `docs/team/PIPELINE.md`. Lane K's habit of before and after numbers.

**Simplify:**
- Look tuning: one small look profile per zone in data instead of hundreds of flags; approved den values baked in.
- Anti-aliasing: test one regime for all zones (three today).
- VFX: new skills from data, once the slice's four read well.
- Judging: a frozen spec, a film, three rounds, then you.
- Docs: this plan and per-lane state files are the working set; `RESUME.md` is history.
- The legacy web stack at the repo root looks unused since 27 Oct [I]. Mark it, decide later.

**What the game needs from Marionette (for its session, not audited here):**
1. Gear that fits the heroine's body without hand patches (B today; the simpler body if decision 14 passes).
2. One NPC taken from input to the game on a shared body with no hand finishing.
3. A check at the game camera (62 degrees, 24 m, the cel materials), since a generic viewport does not show what the game shows.
4. Nothing new for the slice. The slice must not wait on Marionette.
5. **The body is open, leaning yes to a simpler one (decision 14).** My first answer on 21 Nov was "no new body"; the owner pushed back and was right: that answer defended the cost already paid and did not ask whether the difficulty was needed. Marionette's audit reports that no asset has gone through it end to end and no generated gear has been fitted on B (reported by that session, `C:\Users\munch\Desktop\Marionette\docs\RECOVERY_PLAN.md`, not read by me). A simple, measured body is the natural first asset to take through the pipe. Rules: the 124-bone rig and joint positions are kept so the 115 clips and the movement work carry over; the four-body roster (13 Nov) stands and is made the same way (one topology, measured variants); it starts after the look target is approved; movement work runs on B meanwhile. If Marionette's audit says the rig itself should change, that comes to the game plan first.

---

## F. Milestones and dependencies

No dates. Effort is in lead sessions [A] plus your time.

**M0. References and baselines**
- Purpose: stop arguing from taste. Deliverables: the Path of Exile 2 capture table, a matching film and trace of our build, a frame-time trace of a den run, three approved paint-overs with a frozen look spec.
- Needs: the public clips in B5 and your pick of paint-overs.
- Done when: every unknown in B5 has a number or is marked unreadable from footage, and the look spec exists as a file with a reference image.
- Effort: 2 to 3 lead sessions; 15 to 20 minutes of yours (the paint-over pick).
- Risk: the clips do not show a move cleanly or disagree. Fallback: you record only those moves.

**M1. Movement that feels right**
- Deliverable: a grey den room in the shipping build with the fixed movement, dash rule and camera.
- Needs: M0's movement numbers (the five known fixes can start before them).
- Work: decisions 2, 3, 4, 5, 10.
- Done when: D1 passes and you say so after 10 minutes.
- Effort: 4 to 6 lead sessions; 3 short play sessions.
- Risk: it still feels wrong after the fixes. Fallback: the comparison film shows which of curve, animation or frame pacing differs; fix that one. Do not rebuild the controller.

**M2. A fight you understand and enjoy**
- Deliverable: a full den run with readable skills, foes and boss.
- Needs: M1.
- Work: decision 9, tooltips, guard tells, vial on kills, respawn at the entrance, effect spikes.
- Done when: D4 and D5 pass in your den run.
- Effort: 4 to 6 lead sessions.
- Risk: the fight reads but is not fun. Fallback: tune foe mix and pacing with the balance bots before touching systems.

**M3. The look at the camera**
- Deliverable: the den at the approved target.
- Needs: M0's look spec. It may run beside M2 because it shares no files with it.
- Work: decisions 6 and 7.
- Done when: D3 passes.
- Effort: 3 to 5 lead sessions, cap of 3 judged rounds.
- Risk: the method cannot reach the target at 70 px. Fallback: decision 7's hero-only fix, and the gap goes to M5's method test.

**M4. One build choice and one story beat**
- Deliverable: the slice start state, a support socket and a Turn in play, the camp and the story beat you picked.
- Needs: M2 (skills must read before they are changed), your pick from the three story pitches (task 9).
- Work: decisions 11 and 12.
- Done when: D6 and D7 pass.
- Effort: 4 to 6 lead sessions including one author session.
- Risk: two systems in 8 minutes confuse. Fallback: supports only.

**M5. The slice gate and the reuse tests**
- Deliverable: the slice build; your two full runs; two tests that decide how breadth is made: a second room theme with zero new flags, and one new skill from data alone.
- Needs: M1 to M4.
- Done when: you would show the slice to someone else, and both reuse tests have a yes or a no.
- Effort: 3 to 5 lead sessions.
- Risk: a reuse test fails. That is a result: it names the method to replace before more places or skills are built.

After M5, breadth is planned from what the reuse tests showed.

---

## G. Immediate tasks for a development agent

All paths below were checked to exist on 21 Nov unless marked. Heavy runs go through `tools/turn.py`. Shoot output goes in `godot/.shots/`.

**1. Baseline our movement**
- Objective: numbers and a film for start, stop, reversal, strafe, dash and a hit-stop, as the game is today.
- Inputs: `godot/src/Game/MotionProbe.cs` (read it first; I did not), `godot/src/Game/WorldScene.cs`, `docs/handoff/demo_feel.md` item 7.
- Work: script the 12 moves; log per tick position, drawn facing and camera look point; record at 60 fps with inputs shown.
- Artifact: a table and a film under `survivorsunchained_inputs`, raw frames in `godot/.shots/move_baseline/`.
- Validation: the numbers reproduce the 19 Nov diagnosis (about 1 s of scroll after a stop, 0.3 to 0.55 m of slide).
- Done: table, film, and a one-page reading of them. Limit: 1 lead session. If it fails: if the numbers do not match the diagnosis, report the difference before any fix.

**2. Path of Exile 2 reference from public footage**
- Objective: fill every unknown in B5 that footage can show.
- Inputs: the clips listed in B5 (watch each first; none was watched when this plan was written), the same 12 moves as task 1.
- Work: for each clip, confirm what the title claims: 60 fps playback, WASD (she strafes or backpedals), and the patch (from the upload date and the interface). Find each of the 12 moves and count frames by stepping the player one frame at a time. Measure distances in body lengths and the camera from the picture. Prefer 0.5 clips; use older ones only where a 0.5 clip agrees.
- Do not download videos without the owner's word; stepping frames in the player is enough for counts.
- Artifact: `docs/design/POE2_MOVE_REF.md` (new): the table, each number with its clip, timestamp and confidence, and the list of what footage could not show.
- Validation: two clips agree within 2 frames on a move before its number is used.
- Done: every unknown has a number or is marked unreadable. Limit: 1 lead session. If it fails: list the moves that need the owner's own 10 minute recording, and ask for only those.

**3. Fix the five known movement defects behind flags**
- Objective: remove camera float, facing flip, hit-stop slide, dash exit curve; firm up acceleration and turn rate.
- Inputs: `godot/src/Game/FollowCamera.cs`, `godot/src/Actors/PlayerView.cs`, `godot/logic/Sim/Battle.cs`, `godot/src/Game/WorldScene.cs`, `godot/data/content/hit_stop.json`.
- Work: one flag per fix, defaults unchanged until the owner picks.
- Artifact: a branch, task 1's table re-run with each flag, an old and new film.
- Validation: tests green; slide 0 m; camera still within 6 frames of a stop.
- Done: the owner's blind A/B. Limit: 2 lead sessions. If it fails: stop and compare against task 2's table to find which measure differs.

**4. Dash rule A/B**
- Objective: a dash whose direction the owner can predict.
- Inputs: `godot/src/Game/WorldScene.cs` (dash direction choice near line 315), `godot/logic/Content/Abilities.cs`, `godot/logic/Sim/Battle.cs`.
- Work: held-direction rule behind a flag; optional no-cooldown variant.
- Artifact: a build with both, switchable in play.
- Validation: the owner calls the direction 10 of 10.
- Done: the owner's pick is the default. Limit: half a lead session. If it fails: add the ground arrow fallback.

**5. Frame pacing trace and fixes**
- Objective: no frame over 16.7 ms after load on the stated rig.
- Inputs: `tools/perf/run.py`, `docs/handoff/demo_feel.md`, `godot/src/Fx/BattleFx.Skills.cs` and its sibling files.
- Work: trace a full den run in the shipping export; list every long frame with its cause; fix the top causes.
- Artifact: before and after traces, a cause table.
- Validation: D1's frame criteria.
- Done: criteria met, or the remaining causes are listed with their cost. Limit: 2 lead sessions. If it fails: report which cause needs an engine-level change.

**6. Look target at the game camera**
- Objective: an approved picture of the den as it should look, and a frozen spec.
- Inputs: three real den frames at 62 degrees and 24 m at 1080p; the owner's reference `survivorsunchained_inputs\scratch_coord15\owner_frames\owner_ref_night_day_colors_19nov.webp`; the spec tool, which exists only at `.claude/worktrees/agent-a4d7d9ecb5b5bf562/tools/look/look_spec.py` with `docs/design/look_spec_ref_19nov.md` beside it (bring those two files over, nothing else from that branch).
- Work: paint over the frames (the imaging route the owner already allows); keep camera and scale untouched; measure value groups from the approved one.
- Artifact: `docs/design/look_target_den.md` (new) with the images and numbers.
- Validation: the owner says "this is the game" about one of them.
- Done: spec frozen. Limit: 1 lead session, 2 rounds. If it fails: take the closest and write the gap down.

**7. Clarity pass list for the den**
- Objective: know exactly what a player cannot understand today.
- Inputs: `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_coord15\briefs\K_demo_notes.md`, `docs/handoff/demo_feel.md`, `godot/data/content/skills.json`, `godot/data/content/telegraphs.json`.
- Work: check each of the owner's 19 notes against the current build; mark shipped, partly, open; add missing tooltips to the list.
- Artifact: a checked list in the lane's state file.
- Validation: each "shipped" has a frame or a test.
- Done: the open list is ordered for M2. Limit: half a lead session. If it fails: an item that cannot be checked from the build goes to the owner as a yes or no question, not into the open list by guess.

**8. Slice start state [P]**
- Objective: one run that contains a Turn, a support and a few lamps.
- Inputs: `godot/data/content/demo.json`, `wicks.json`, `supports.json`, `godot/logic/Rpg/SkillBook.cs` (rank rule at line 154), `docs/design/BUILD_UNLOCKS.md`.
- Work: write the proposal as data on paper first: level, points, which supports drop; settle the rank rule mismatch. Skills are four pressed skills on four keys with no auto slot shown (decision 15): name the four. Groundbreaker is a node, "every 3rd attack groundbreaks" (the owner, 21 Nov): propose it as the slice's one Turn, since it is a choice the player sees and feels at once.
- Artifact: a one-page proposal for the owner. No code before the owner's answer to question 3.
- Validation: the proposal fits in one 8 to 10 minute run on paper (count the choices and when each appears).
- Done: approved or changed by the owner. Limit: half a lead session. If it fails: fall back to supports only (decision 11).

**9. Three story beat pitches, then the script [P]** (the toll beat was scrapped by the owner, 21 Nov)
- Objective: a beat for the den and camp that the owner wants, before a line is written.
- Inputs: `docs/STORY_BIBLE.md` (the den's own material, the camp's people; not rule 6), `godot/data/content/dialogue.json`, `godot/src/Audio/Music.cs`.
- Work: an author lead writes three pitches, one plain paragraph each (what happens, who says it, why it should move you), each told in play with no close-up. After the owner's pick: at most 40 lines and the in-world staging.
- Artifact: `docs/design/SLICE_STORY_BEAT.md` (new): the three pitches, then the picked script.
- Validation: consistent with the bible; spoils no later twist; no close-up needed.
- Done: the owner picks a pitch, then approves the text. Limit: half an author session for the pitches, 1 for the script. If it fails: one rewrite, then the narrator fallback.

Order: 1 and 2 were started on 21 Nov (the owner's go-ahead). 3 and 5 can start next. 6 waits on the owner's pick. 4 follows 3. The body test (decision 14) was started on 21 Nov in the Marionette session (shape, rings and rig first; its paint follows 6). The Godot 4.7.2 trial (decision 16) starts when task 1's baseline is in. Added 21 Nov from a workflow the owner sent (a Godot developer's zone-building loop, r/TopologyAI; its videos were not viewed): when the task 6 painting of a den room is approved, cut each prop out of it as a clean reference image and keep the painting as the placement target at the same camera. This costs no credits. Turning those references into meshes waits for the environment bake-off after the slice.

**Task 1's baseline is in (22 Nov) [O, measured by the task 1 lead; not re-run].** Branch `move-baseline` @ `998aa9f48`, merged into the integration branch at `a710f612c` (the owner, 22 Nov: "Yes, merge it"; the game builds and 3081 tests pass after the merge); the per-shot CSVs are in `raw\` beside the table, reading and an 87 s film in `survivorsunchained_inputs\scratch_devplan\task1_move_baseline\` (`TABLE.md`, `READING.md`, `move_baseline_film.mp4`). Frames are 60 fps; her top speed is 5.15 m/s. Against the PoE2 reference:

| What | Ours | PoE2 (public clips) |
|---|---|---|
| Start | 90% of top speed in 9 frames, 99% in 19 | Full speed in 1 to 3 frames, no ramp |
| Stop | 19 frames over 0.26 m | 2 to 3 frames, no slide |
| Camera | Leads her by 1.52 m at a run; after a stop it scrolls on for 0.95 s to 90% and creeps to 2.0 s (1.58 m, 117 px); after a quarter turn it is still moving 100 frames later | Keeps her mid-frame, no lead or trail |
| Reversal | Turned in 3 frames, full speed in 12, overshoot 0.02 m | No reading |
| Dash | Starts on the press, 11 frames, 5.5 m; on keyboard and mouse it always goes to the cursor, never the keys; on a pad it follows the left stick | A roll from rest: about 0.45 s, about 4.7 heights (one clip) |
| Strafe, backpedal | Full forward speed, no penalty | No reading |
| Swing while moving | Slows her to 0.70x | No reading |

What this changes: the camera is the largest gap and is fixed first in task 3, then the start and stop ramps (both several times slower than the reference). The dash reading confirms decision 3 (it ignores the held direction today). Open: shot 12 (the hit-stop slide, 0.3 to 0.55 m in the 19 Nov diagnosis) has no numbers, because the harness's stand-in foe vanishes a tick after it spawns; task 3 starts by taking that shot in a den room with a real pack. Not measured: foot slide, the 164 Hz screen, the shipping export.

**The PoE2 reference is closed (21 Nov).** Public footage is used up after two passes, and the owner cannot record ("i don't have poe2 so I can't do that for you"). Nobody asks the owner for a PoE2 recording again. Movement targets for tasks 3 to 5: start, stop and camera lock use the measured numbers in `docs/design/POE2_MOVE_REF.md` (two clips agree); the roll from rest uses the single-clip number as a starting value; the other eight shots (reversal, quarter turn, strafe, backpedal, circle, roll at run, roll across the aim, heavy hit while moving) get our own targets, derived from the measured ones and marked as inferences (example: a reversal takes no longer than a stop plus a start, 6 frames, with no slide). The owner's play on a controller and on keyboard with mouse is the gate for those eight. 7 to 9 are paper work that can fill gaps without touching the critical lane's files.

---

## H. Hand-off: this session plans, other sessions build (the owner, 22 Nov)

The owner, word for word: "well we are still planning right? we are already going a little far into implementation.  we need the plan and then begin implementing in other session(s) because honestly some of them may need fable if they are too difficult, and I may use an opus orchestrater etc"

**The rule.** This session writes and keeps the plan. It starts no build work. Each package below is started by the owner in its own session (or under an orchestrator), from this page and the files it names.

**What this session already set in motion** (so nothing is a surprise):
- Measuring only: task 1, the movement baseline. Its harness is on branch `move-baseline` (worktree `.claude/worktrees/agent-a68576a7b7b07decd`), not merged. It ends with a table of numbers and changes no game behavior (the harness is a dev flag, off by default).
- Downloaded, not used: the Godot 4.7.2 .NET editor at `Desktop\Godot_v4.7.2-stable_mono_win64`.
- In the Marionette session, not here: the simple-body test (session 2 of 3, toward the bare-shape sheet) and the gear lead on the corset.
- Paper only: `docs/design/DEN_ROSTER.md`, `docs/design/POE2_MOVE_REF.md`, `docs/design/BUILD_DIRECTION.md` Round 9.

**Packages.** "Model" is my recommendation by the kind of difficulty: open-ended work that crosses systems or rests on feel goes to Fable; work with a frozen spec and a measurable pass goes to Opus; waiting and measuring goes to runners.

| # | Package | Delivers | Spec to start from | Kind of difficulty | Model | Depends on |
|---|---|---|---|---|---|---|
| P1 | Godot 4.7.2 trial | A yes/when on the upgrade and the list of breaks | Decision 16 | Specified and measurable; the custom screen effects are the unknown | Opus lead | Task 1's baseline table |
| P2 | Movement | Tasks 3, 4, 5: the five known defects, the dash rule, frame pacing | Section G tasks 3 to 5, D1, `docs/design/POE2_MOVE_REF.md`, `survivorsunchained_inputs\scratch_devplan\moves12.md` | Feel across input, sim, animation and camera; the hardest package | Fable lead for 3 and 4; Opus for 5 (trace and fix); runners for the takes | P1's verdict, task 1's table |
| P3 | Den roster re-cut | The shared charge gated off in dungeons, six foes with one move each, pack recipes | Decision 17, `docs/design/DEN_ROSTER.md` (approved by the owner, 22 Nov: "I approve den roster") | Specified by the page; logic and tests; a re-tune that needs the owner's play | Opus lead | Nothing: the page is approved. Shares no files with P2 as far as the page and the harness report show |
| P4 | Skills | A one-page list of each skill's new kind, then the bar rule and four pressed skills | Decision 15, `BUILD_DIRECTION.md` Round 9, task 8 | The page is design judgement; the code is specified once the page is approved | Fable or an author lead for the page; Opus for the code | The owner's approval of the page |
| P5 | Look target and clarity | Paint-overs at the game camera for the owner's pick, prop references cut from the pick, the den's clarity list | Tasks 6 and 7, decision 6 | Taste; then a paint and light system if the pick needs one | Opus lead with the image route; Fable if the look system stalls after one round | The owner's pick |
| P6 | Story beat | Three pitches, then the script and wiring | Task 9, decision 12 | Writing | Author lead (Opus at max) | The owner's pick |
| P7 | Body and gear (body, skeleton and clips all still open, 22 Nov) | The Marionette session's proving results, then the owner's pick of body and skeleton; gear built to measured rings with no hand patches on whichever body wins | Decision 14; Marionette's own pages and state | Deformation, fit, and what a new skeleton costs in clips | Opus leads in the Marionette session; a Fable solver if a joint fails twice | The owner's pick after the proving results |
| P8 | Blender upgrade trial | A yes/when and the list of breaks | Decision 16 | Specified | Opus or Sonnet lead in the Marionette session | None |

**Orchestrator.** An Opus orchestrator is enough: every package has a spec, a limit and a pass test here, so its job is order, merges, and the disk and worktree rules, not design. Send a package to Fable when an Opus lead has spent one honest session without passing its test, or when the spec itself is in doubt. Never spend that on more rounds of the same approach (B3).

**Order.** P1 first (short, and it decides which engine P2 is done on). Then P2 as the one critical lane. P3 can run beside it. P4's page, P5's paint-overs and P6's pitches are paper and wait only on the owner's picks. P7 and P8 run in the Marionette session.

**Waiting on the owner:** the look-target pick; the story pick; the skill-kind page (once written); the body and skeleton pick, after the Marionette session's proving results. My reading, not checked item by item: movement's tasks 3 to 5 (the defect fixes, the dash rule, frame pacing) are camera, sim and performance work and do not depend on the skeleton; any item in task 3 that turns out to be clip or rig work waits for that pick.

**Briefs:** `docs/team/HANDOFF_BRIEFS.md` holds a ready-to-paste brief for each package and for an Opus orchestrator, plus the common rules to paste with each (the owner, 22 Nov: "Yes, write them"). The plan wins where a brief differs from it.
