# Handoff: the gameplay experience director

For a fresh successor. Read these first:
1. `docs/team/README.md`: the bar, the turns, and batching shots.
2. `docs/team/experience.md`: the one-page status, which holds what's done, the next steps in order, and the verdicts.
3. `docs/design/STORY_NIGHTS_AND_TIME.md`: the owner's decisions are at its top.

## Experience 10 (exp-10 lead, 28 Oct): fixed list DONE, MR READY

**State:** all five items closed; exp-10 merged with integration 47c99dae; the full test run is the last check before the MR.
- **1. Act 1 DAYS playtest:** a new headless measure, `dotnet run -c Release -- verge-day --seeds 12 --stages 1:1:0,4:2:2,4:2:3,8:4:4 [--bot deft] [--callings ..]` in godot/balance (Harness/VergeDaySim.cs, 9b5fadbf; ~30 s). It runs the Verge's day packs at Verge.Level() in three setups: OLD (1/2/3 slots, no Hands), NEW, and NEW without the Hands. Result: days play 0-15% faster, and HP lost per pack drops from ~7% to ~4%. Packs were already trivial before the change (lamplings 0%, 3-5 s kills from L4). Sent to main for Classes 15: the Axe Gyre reaver can't survive day 1; the L1 calling skill was never granted (Classes 15 granted it on classes-15@e7417546, in its MR1); the stalker's Hand never fires by day (P8). Main logged "Verge days have no stakes" as a later item. **Owed after Classes 15 MR1 lands:** one verge-day re-run (main asks). Tables: scratch `exp10\s1\verge_day*.md`.
- **Prologue Ambush:** an idle player loses 35% (212 to 138), inside 25-40%. The normal pilot loses 6%.
- **2. "Ember fills this":** keeps its box on the bar's run (her hair to the Flare cup). A bare point on the crest failed two xhigh judges ("can't tell what 'this' is"), and judge r2 picked the box (GATE YES). The arrow now drops plumb onto a wide box (Callout.Lands).
- **3. The lock lesson** is now "The ember's count / Hold Alt to see the ember's level, and how far it is to the next." Target "card": GameHud.TeachCard holds the numbers card up while the callout shows, bracketed via XpCardArea; EmberLockArea is gone. Judge r1 PASS.
- **4. Callout rings** fit the Drowned Girl: Flare = DgRiver.FlareR; dash = DgSmall.RingD/2 at DashMid; flask = half its height at DraughtMid; default seat = SeatD/2. Judge r1 PASS on sizes. Small boxes (a seat) are landed on at the top middle only (r2 fix, checked at 1:1). **With UI 20 (main relayed):** the rings cross the SPACE/R/Q key plates, the rings' colour, an optional crest trace.
- **5. Zoom pop:** already fixed by 2719e93c and judged SHIP (Experience 8); closed.
- **Scratch:** `exp10\` in coordinator 31372078's scratchpad (pace5.py for exp-10, briefs, logs amb1, v1-v4), backed up to `survivorsunchained_inputs\scratch_exp10\`. Frames: `godot/.shots/v1-v4_teach_*`.
- **Cost:** worker 44k, runner 40k, solver 122k, judges 56k + 49k; API $0.

## Experience 9 (play-1 lead, 27 Oct): MR5 fix round done, re-judged; MR5 READY

**State:** the MR5 fix round (12 items) built, the xhigh re-judge (aebd7397) gave A and B SHIP WITH FIXES (small); its three fixes built (df36280d); a full run v8 on the final code. This was i15's and i14's last round: anything later is a new list.
- **Built:** elite/chest/pack tips re-timed, the Barrow line waits for the pack tip (e11df505); the Knight lives through 2 windups; L4 talk cut; L1 lock after the 2nd rise's draft, no crowd gate (ec6c92a5, 33c8d478); F2 aims at `chain_fill` (Instrument.ChainFill); F7 rings the Knight + arrow on his lane, the wall case fixed (open-ground test now uses a wall's faces, not its box; the Knight narrows when stuck out of sight) and F8 shows while the Grave-Caller stands (his arrival fills her Flare once; the autopilot holds the Flare for it) (1b130e90); the draught lesson under 70%, no "she must be seen" wait, gap 3, held off the Knight's windup/lunge + 1.5 s (df36280d).
- **Ambush stakes** (36a8658f..24aeacb2, df36280d): opening volley x1.5, ditch dead x1.3, 24 foes held, and a steer in `Prologue.AmbushMul` via `Battle.FoeHitMul` (x0.25 when she loses >1.2%/s; x2.5 when she stood still 3 s and loses <0.9%/s in the first 30 s, off after she drinks). Idle loses 27-29% by +30 s (amb21-23), the dodging pilot 7.5-10% (n13-14). Judge: the steer is acceptable while no hit numbers show on her.
- **Closed as known:** the F7 arrow tip lands on her figure (reads "you're on it").
- **Routed (with the MR):** the Knight's white flash (VFX/model); the dark blue night frames (env). UI 16's "Knight low in frame" was the old v4 frame; v6 has him mid-frame.
- **Scratch:** `survivorsunchained_inputs\scratch_play6\` (briefs, pace5.py, logs amb*, n*, v6-v9). Frames `godot/.shots/v6_*`, `v6b_*`, `v8_*`.
- **Cost:** worker 64k + 44k, solvers 189k + 151k (3.7 h of runs), judge 131k, API $0.

## Experience 8 (play-1 lead, 27 Oct): PAUSED (coordinator wind-down); MR5 judged, ONE fix round left

**Paused here (Experience 8, 27 Oct); next:** run the fix round in scratch `play5\brief_mr5fix.md` (12 decided items) on ONE fresh `su-worker` (or a medium su-lead-high for items 11-12, which need digging). Then ONE xhigh re-judge of only the changed frames (F2, L1, F7, the Post tips, F8, the draught if it fires) plus the ambush HP numbers, then one full shot-free run, tests, and MR5 to main. This is i15's last round (the cap): anything still open after it closes as known. Integration f09f6d81 is merged in (5ae3fdb1). Tests 1130/0/8. No turns held, no helpers running.
- **Built since Experience 7:**
  - Item 14 + F7 (89d2a819, 81b93b42, 203ed65a): lessons L1 lock, L2 tally, L3 minimap, L4 talk; the Ember explanation in order; Callout `Quiet`/`Still`; `--auto talk`.
  - New GameHud accessors `PromptArea`, `MinimapArea`, `TallyArea`, `EmberLockArea`: the merge point with UI 14.
  - F7: the Knight's holds are bounded and his first lunge is forced at close range (26faaf13, 2b4ac60f, 993a94af: `Enemy.LungeMin`; `pace knight windup/watch` log lines).
- **Judge (xhigh, combined, a16ec7c2):**
  - C, the zoom pop: SHIP.
  - A, i15 round 2: SHIP WITH FIXES, close. No stakes yet: v4 and v5 ran at 212/212 the whole Prologue. Tune the Ambush with `--auto idle` until an idle player loses 25-40% HP; the draught lesson fires under 70% HP.
  - B, i14 + F7: SHIP WITH FIXES, close. Cut L4; move L1 to the 2nd rise; F7 rings the Knight, with the arrow at her spot on the lane; space the Post's tips; F2 aims at the filled links; the chest tip loses its E chip; F8 (art) never shows in time.
  - Every fix is in the brief.
- **F7 status:** f7e is within target (the windup came 11.5 s into the Post). f7f is the wall case: no clear ray, so the first freeze was dropped "gone, notyet". That's brief item 12.
- **Routed (tell main with the MR):**
  - The red-line telegraph reads salmon, not red (combat VFX).
  - The freeze dim leaves night frames near black (UI).
  - The lock shows her own level by day with no word (UI; it matters from night 2).
  - Pink-skinned figures in the town's top left (NPC).
  - The "RAV CUTWELL" label is clipped at the top edge (UI).
- **Scratch:** `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\9c583f93-c0ad-4a2d-8f37-a803f39d38c2\scratchpad\play5\`, backed up to `survivorsunchained_inputs\scratch_play5\`. It holds pace5.py (env STOP, BASE=hub, AUTO), the logs v4, v5 and f7a-f, and the briefs i14, f7fix, mr5fix and judge_mr5. Frames are `godot/.shots/v4_*` and `v4b_*`.
- **Cost this session:** solver 201k, worker 57k, judge 151k, API $0.

## Experience 7 (play-1 lead, 26 Oct): PAUSED (coordinator wind-down); MR4b MR READY (db2f125a, sent); MR5 mostly built

**Paused here; next:** MR5 at play-1@5ce39cac+this doc, tests 1074/0/8, no turns held. Built:
- **Item 15 (pacing)** f2da898a..1e5deea3 + judge fixes 5ce39cac. Judge i15 r1 (xhigh, play4\judge_i15.md): SHIP WITH FIXES, close; all fixes applied (dash freezes at 4 m with bolt marks and a dodge line; draught waits only for a freeze (`Callout.Urgent`); the Road's dead fall away, coins at the wagon tail, the objective set at the trap, 0.8 s silence; spacing from a line's end; the shield tip from the trap with new copy; unvoiced lines up >= chars/17 s CENTRALLY in `Game.Say`; no spawns in Road/ToFord/Road2's first 6 s). v3 timeline in play4\logs\v3.pace; frames `godot/.shots/i15t_*`. Round 2 = ONE xhigh judge on the i15t frames (no draught frame in the seeded run; v3.pace has it at 192.3 s, HP 87) combined with the zoom strip below and item 14.
- **Zoom pop** 2719e93c: the room ray (new `logic/Play/CameraRoom.cs`) sees past thin posts, passes over low colliders (drawn top cached), glides in log distance; 14.85% -> 3.29% a frame max. Strips play4\strip_zoom_before/after.png, unjudged: a lamp post now passes in front of her for a few frames (a thin-occluder fade would be polish, likely close as fine).
- **Perf tail** (CLOSED AS KNOWN): C02 start 91-138 ms cold (cast 16-22 ms + first cues 31 ms + 117 pipelines on the first draw; only an offscreen pipeline warm would cure it, at a cut it hides); 319.7 s not reproducible; 345/891 s outside our code on a shared GPU. Diagnostics in dce862db (`--perf` prints a cinematic start's sections).
- **Open, NEXT:** item 14 (UNBLOCKED: the owner picked HUD A2, bottom-center layout kept): teach the minimap + map key, check the talk prompt appears at an NPC (`Style.KeyCap` + name; autopilot never talks: script a walk-up), the padlock "4" and kill/gold counters, Ember in plain words (TUTORIAL_COPY "The Ember explanation"); audit text `survivorsunchained_inputs\play1udit_au1.md` item 14. Also F7 (the Knight's red-line lesson) never shows in real runs (old): fix in the same pass. One medium solver, then the combined judge, then the full run, MR5.
- Scratch play4\ (briefs, pace.py, cam.py, jumps.py, strip.py, logs). Cost this session: solvers 191k+165k, worker 88k, judge 114k, runner 30k.

## Experience 6 (play-1 lead, 26-27 Oct): PAUSED (coordinator wind-down); MR4 sent at ea5f1cc2; MR4b (s5+s6) built, checks left

**Paused here; next:** MR4b = the Prologue's freezes, commits b18d9c53 (s5) + 9a13fc74 + 6af708cb (s6), tests 1070/0/8, full shot-free run s6full: 61 frames over 33 ms (mr4b 165), 5 over 100 (was 12). Done: cinematic starts (her double built ahead on a worker `--no-double-ahead`, the dawn thaw's sun map baked ahead, C02's cast files and each cinematic's boss+extras built ahead `--cast-ahead off`; C04 A 2.43 s -> 49/59 ms, C03 351 -> 31/65, C02 1212 -> 28 then 125 ms); the "draft" hitches were TEACHING CALLOUTS (`Callout.Place` ~6000 spots, each allocating a Bezier list: 325-400 ms -> ~10 ms, same placement). LEFT, in order: (1) the no-look pixel check of the ahead-built cast: C02 and C04 A at fixed fps seed 1, on vs `--no-double-ahead --cast-ahead off`, vs a HEAD-vs-HEAD floor (sh4/sh5/cmp.py; a worker job); (2) check the arrival frames 1160/119/90 ms at 459.4-459.6 s against the travel fade (behind full black = known; visible = hold the fade-in a few rendered frames); (3) optional: C02's 2nd frame 125 ms (13 figures entering the tree + 47 pipelines: add them hidden a few frames early); then merge integration (82c1f68e heroine repack; junction rule; import), full test, MR4b. Then MR5 (items 14+15). s6's run used `--stale-ok` (play_perf_s.py). Cost MR4b: s5 202k, s6 183k (medium), API $0.

**MR4 (frame time), MR READY at play-1@06c7db76 (integration merged, imported; tests 1070/0/8; full shot-free Prologue run mr4b clean, no errors):**
- s1 ade3d9ea: the Waystation's pieces built on a worker during C04 A, one step a frame (`Slices.Paced`; `--ahead-main` = old path). C04 A: 0 new frames over 33 ms (was ~20 of 100-224). Hold behind the black 2.2 -> ~1.0 s (one ~0.9 s frame: her outfit 256 ms, Waystation.Begin 214, 900 pipelines). CLOSED AS KNOWN: the screen is static black; a split needs her figure built ahead via `HerWear.Live` (s3's plan) if UI ever animates the hold.
- s2 368f6085: GC pauses cut (Godot Variant/StringName wrappers surviving young GCs: HairSway, HerFaceLife, OwnClips, Controls, Instrument); `Atmosphere.GradeLut` on workers (bytes identical). Editor runs use .NET 10 via GodotPlugins' rollForward, so csproj GC settings don't apply in our runs; exports run net8.
- s3 c80fdae3: flipbook atlases loaded ahead, the draft backdrop warmed, HerJiggle string churn. s4 9b1075dc + fa8a5373: folk shadow merge (`FolkShadow.cs`, shadow draws -86%), off-screen folk animation held (-2.4 ms with 16 folk), walkers built on a worker (`WalkerView`), a draft rehearsal (`GameMenus.RehearseDraft`; the hub's first draft 80+85 -> 36+45 ms, closed as known). Switches: `--folk-shadow off --folk-lod off --walker-later off --draft-rehearse off --folk-churn S`.
- No-look-change checks (w1): grade LUT 0 bytes differ; her close-up frames vs the old files at the noise floor; Waystation arrival vs `--ahead-main` spread jitter only (sheets in scratch play3\w1\).
**Next (s5, brief in scratch play3\brief_s5.md):** the shot-free run found freezes at cinematic STARTS: C04 A 2.43 s (+326 ms), C02 1.21 s, C03 351 ms (~240 MB allocated each), and the Prologue's first drafts 382/325 ms (the rehearsal doesn't cover them). Then MR5 = items 14 (UNBLOCKED by UI 12: teach minimap, lock, counters, Ember plainly; talk prompt = Style.KeyCap + name label, looks are UI's) + 15 (Experience 4's notes below). Routed: the play camera's ~30% zoom pop in Animation's side strips: likely `FollowCamera.Place`'s `room` (a 2D raycast on Battle.Collision, GameCloseUp.cs ~30, snaps in at rate 14 on any collider incl. low props): diagnose with a camera log.
**Scratch:** `...\fce3bb46-...\scratchpad\play3\` (tr.py, perf.py, play.py, play_perf.py = no --shot, frames/cut/corr.py, trtrace2.py, sh4/sh5.py, cmp.py; `..\alloctool` = s2's trace reader). Shots mode saves PNGs that cost 300-800 ms a frame: never read hitches from a `--shot` run.

## Experience 5 (play-1 lead, 26 Oct): PAUSED for the coordinator's wind-down; MR4 freeze WIP at 69338d30 (NOT mergeable)

**Paused here; next:** finish MR4's freeze (below), then the folk LOD, then the full test and MR; then MR5 (item 15, Experience 4's notes below). Integration merged at 0a447b24 (docs only, no import needed). No turns held. Item 14 still on HOLD for UI 11 (`a00a39b9f159396f9`).

**MR4 freeze, WIP 69338d30 (medium solver a5323c4b, 192k).** The Waystation is now built ahead during C04 A (`Game.Prepare`/`BuildAhead`/`PumpAhead`, new `src/World/Slices.cs` step runner, `Prologue.Dawnbreak` calls `G.Prepare("waystation")`; ZoneView/Dressing.Props/OwnWalls as steps; GroundPaint.Ahead; MapScreen.DrawAhead; Prefetch.Ahead; Travel waits behind the black via WhenBuilt). Tests 1054/0/8.
- Before (repro tr0): build frame 7.46 s, then 1.62 s (the map's first drawing, `MapScreen.Drawing`, not pipelines). C04 A already had 79/127/93 ms frames of its own.
- After (tr2): build frame 2.41 s (EnterPlay 2082 ms: `Waystation.People` 1567, her outfit 292), next frame 57 ms. **But C04 A now has ~20 frames of 100-224 ms from the ahead-steps: do not merge until fixed.**
- Fast repro (2 min): `play2/tr.py NAME --zone lowford --cine c04a --prepare waystation@24 --travel waystation@40 --perf-warm 2 --perf-for 40`; `frames.py NAME 33` lists slow frames; `trtrace.py`, `sscope.py`, `sslong.py FILE "Game._Process" 150` for dotnet-trace trees.
- NEXT, in order (each measured with the repro): (1) long ahead-steps: OwnWalls' ground SetPixel loop (214 ms; float[] on a worker + CreateFromData), prop file loads one per step (find the slow ones), flora 128, scatter 109, GrowGrass 186 (Randf), landmarks 237, OwnWalls.Furnish 157, `OwnWalls.Take`'s ResourceLoader.Exists 281 ms (cache it). (2) EnterPlay in one frame: load and hold the townsfolk's parts during the build ahead (`Waystation.People`, `Arms.Make` 232); reuse her PlayerView when `Loadouts.Look` is unchanged; C04 B's cast rebuilds her (`GameCinema.Cast` "CineSurvivor" 244-310 ms): a spare figure matched by look. (3) pipelines (~910 on the build frame): measure whether the main thread waits; add the scene in pieces behind the black. (4) Check the Waystation looks the same at arrival, then the full play.py run.
- Acceptance (unchanged): fade start to first play frame no frame over 100 ms (stretch 50), hold at most ~2 s past the fade, C04 A no new frame over 33 ms.
- Spawn the next solver fresh with this list (the old one was at budget). A loading indicator during the hold, if needed, is UI 11's look.

**Folk LOD (not started):** mixers off off-screen (VisibleOnScreenNotifier3D, generous AABB), small parts' shadows off or one merged shadow caster per folk (HerLod.Merge pattern; persons built in People.cs / NpcPackage.cs), ABAB with flipstat.py (flips anim, people). Real play after C04 has 4 folk, the quick start 15.

## Experience 4 (play-1 lead, 26 Oct): MR3 MR READY (d6868600); MR4 diagnosed, HUD part fixed (54e83e86), the rest NEXT

**Start here (Experience 5).** Scratch: `<coordinator scratchpad>/play2/` (play.py, play_fixed.py = play.py at `--fixed-fps 60`, perf.py = the hub straight from launch with `--perf`, flipstat.py NAME = an ABAB flip run's in/out means, ease_sheets.py, `*_stale.py` = copies with `--stale-ok`).
- **Merge integration first.** turn.py now refuses play-1 as STALE (an integration commit came in). Follow the junction rule: `cmd /c rmdir godotssets`, merge, remake the link, then `--headless --import`.
- **An import is needed after every merge.** A stale cache broke the hub build with a missing own:crock.

**Owner and coordinator (26 Oct):**
- The HUD and UI visuals are placeholder until **UI 11** (worktree ui-11, SendMessage id `a00a39b9f159396f9`) finishes.
- The split: UI 11 owns how each element looks and where it sits; we own when it shows, what it says, and the flow. Sign-off goes both ways, and neither side edits the other's code without asking.
- No judge rounds on how any tip, ring, chip, card or marker looks. Judge flow, timing and wording only.
- Audit item 14 (minimap, talk key, counters, Ember in plain words) is on HOLD for UI 11, which will say when the HUD settles. Item 15 is ours (below).

**MR3, canopy fade: DONE, MR READY play-1@d6868600, sent to main.**
- Motion judge e2 (xhigh; 6 bursts of consecutive 1/60 s frames caught mid-ease via `--canopy-log --canopy-burst N,K` under `--fixed-fps 60`): the ease band and the half-faded holds SHIP at 1:1.
- It found crowns whose axis sat behind the lens plane flashing over her for 3 frames. Now any crown within 1 m of the lens is cut, eased over the 1.5 m before it. Rejudge e3: SHIP.
- Tests 1054/0/8.
- town_o_03 subtitle: asked Env 17 (aa34beda274ad4169) for the frame, no reply yet. Speech is a 2D CanvasLayer, so a tree can't draw over it. Main says: if it's low contrast over foliage, give the line a backing (that's now UI 11's look); if it's a mid-fade catch, close it.

**MR4 findings (the hub straight from launch, `perf.py`; numbers noisy run to run, GPU shared, so trust only ABAB flips):**
- Hub frame is 14-22 ms, CPU-bound (GPU 3-3.6 ms). The new wall-clock cuts in Perf (`cut: physics / tail (queue) / draw / after`) place the old "unaccounted ~6 ms" in two spots:
  - Godot's message queue: controls' _Draw after QueueRedraw, plus skeleton updates.
  - The renderer's draw: about 2 ms over its measured CPU time, which is GPU sync.
- **HUD, ABAB:** 5.0 ms a frame (queue 3.4 + draw 1.3), and in ALL play, not just the hub. Fixed in part at **54e83e86** (worker): minimap marks pooled, redraw on change; the queue is down about 1.9 ms.
  - Still per-frame because they breathe by Time: the dash glass while ready, the chain glow with heat, a ripe socket rim, the bezel's day ember.
  - UI 11 took "the HUD under 1 ms, redraw on change, no per-frame node churn" as hard constraints for its rebuild.
- **Folk, ABAB with 15 folk out in the quick start (real play after C04 has 4):**
  - Animation (`--perf-flip anim`): 4.7 ms total, about 0.3 ms a folk (mixers 1.7, skeleton queue 1.2, draw/skin setup 1.7).
  - Drawing (`--perf-flip people`): 3.2 ms, with +105 draws and +510 SHADOW draws (about 33 shadow draws each: many outfit meshes, each casting into the sun cascades and the lamps).
  - All three (anim, people, labels): 7.9 ms.
  - Her (visibility only): 1.6 ms.
- **NEXT for frame time (code, ours):**
  1. Folk animation LOD: mixers off when off-screen (VisibleOnScreenNotifier3D), a lower rate when far.
  2. Folk shadows: one merged shadow caster per folk (her HerLod.Merge does this for her: "23 shadow casters into 1"), or no shadows from small parts.
  3. Re-measure with `flipstat.py` (flips anim, people, hud, her). Folk art itself belongs to NPC/Marionette (baked dressed NPCs will be single meshes); say so to main.
- **NEXT for the 6 s freeze:** nothing built yet. The facts:
  - `Prologue.Finish` calls `G.Travel("waystation")` (Game.cs ~735). It fades 0.8 s, then `EnterZone` builds synchronously, a 7.6 s frame (ground+water 2.1-2.3 s, props files 0.9 s, props 1.6 s, textures 0.4-0.56 s; 1041-1126 pipelines on first draw). Then C04 B plays.
  - The black hold shows a static caption, so it reads as a hang. Her outfit is rebuilt (250-310 ms) at every cinematic hand-back.
  - Plan:
    a) preload the Waystation's files (ResourceLoader.LoadThreadedRequest) during C04 A at Low Ford (27 s);
    b) split EnterZone's laps over frames behind the black, with something that moves (ask UI 11 for the loading look);
    c) a pipeline prewarm: render the hub from the C04 B and play cameras behind the black before the fade-in;
    d) stop the outfit rebuild at hand-back when nothing changed.
  - Measure with `--perf h1`-style real runs (play.py with `--perf NAME --perf-warm 8 --perf-for 2600`; the window lines and `built in` laps).
  - Art causes go to main with numbers, for Env 17.

**MR5 = audit item 15 only (go):**
- Health is full until 2:46, so dash and the draught are taught with nothing to dodge. Add a real threat in the Ambush (Prologue.cs `case Stage.Ambush`, ~694).
- The Road (4 s) and ToFord (6 s) are skipped. Give the Road a short lore or loot beat: the Road ends at `p.Z < cart.Z + 7`, Prologue.cs ~670.
- Space the lessons. No new HUD visuals.
- Copy is in our voice, logged for Story in docs/story/TUTORIAL_COPY.md.
- Judge on flow, timing and wording (xhigh) with a play.py run.

**UI elements the tutorial depends on (sent to UI 11 and main asked for it here; what each must communicate):**
1. Callout, Freeze/Arrow/Panel (Callout.cs, Teach.cs, GameTeach.cs): a ring on the target (world ember, HUD pale, lamps cold blue), a title, 1-3 lines. Says: look here, what it is or how, paused, how to go on.
2. Off-screen marker: says one of them is that way (the lamps).
3. Dash-ready form (GameHud.DashLit, Round.Form, Licks, FormGlyph): says your next dash is your calling's art. It must not look like a callout highlight.
4. Key chips ({key:X} in copy, TipLine.Chip): the bound key, readable on the tip bar.
5. Tip line: one optional fact, then it fades.
6. Teaching cards (Panels.cs v.Teaching): choose one, and what each does in a line. No reroll, banish, skip, recipe or shared reasons.
7. Ember chain and padlock (Instrument.cs): gathered ember fills it, full means rise and pick a skill, and the number is tonight's rise.
8. Ember halo on the ground: pick this up.
9. Channel tip and cast bar ("Break his spell" / "Raising the drowned: break it!"): stop this now, with the tool that's ready.
10. Boss bar with the lamps: the lamps shield him.
11. Red line ring (F7): get off this line.
12. Level card (F12): N levels kept for good, skills were lent, press C to choose N traits.
13. Interaction prompt ("[E] Talk Chid"): you can talk to them. Unverified, because the autopilot never walks up to anyone.

## Experience 3 (play-1 lead, 26 Oct): MR1+2 MR READY (sent to main at 9f3b6c8e); MR3 canopy fade built, motion re-check NEXT

**Start here (Experience 4).** Scratch: `<coordinator scratchpad>/play2/` (play.py, play_burst.py, logs, judge_b1 crops).
1. **Import first:** integration 6d8c2e92 (Env E9d) is merged in (0c658800) with new assets: run `Godot_console.exe --headless --path godot --import` (~4 min) before any shot. One untracked .uid was set aside in `play2/uid_backup/`.
2. **MR3, the canopy fade** (solver commits 10741942, 943c0eec; tune 34f1bca2). kit.gdshader OWN_FOLIAGE: a tree whose crown covers her or the ground within `canopy_fade.x` m of her (on screen, at her distance) fades whole by the house fade's dither; the lower trunk stays (per-species crown_lo/hi/r/keep in data/flora_species.json); shadows kept; play camera only (`KitLook.CanopyView`). Switches `--canopy R,E,G|off`, `--canopy-log` (CPU mirror, prints the blocking trees).
   - Judges: the stills (c3_* vs h1_*) SHIP at 7 m / 0.85 (it asked 6 m / 0.80). The MOTION judge (burst b1_*: `SHOT_FROM=143 python play_burst.py NAME 0.05 24`) FAILED the dithered ghost: a screen-door patch over her ember-lit ground and frame-to-frame sizzle (crops `play2/judge_b1/`, p2223.png).
   - Applied its quick fix, NOT yet re-shot: crowns cut 100% once eased, ease 1.5 m (`canopy_fade` = (6, 1.5, 1, 1) in project.godot).
   - NEXT: re-shoot in motion (movie mode `--write-movie <file>.avi --fixed-fps 60`, or a burst) covering an ease-in AND an ease-out; judge (xhigh); full test; MR. If the ease band still sizzles, the judge's preferred fix is alpha blend (alpha ~0.2, depth write off) with a shadows-only copy.
3. **Also on MR3 (coordinator, 26 Oct):** subtitles show through a tree in Env 17's town frame `town_o_03` (UI/text draw order): find the frame in Env's shots and fix it with MR3.
4. **Sent to Env 17** (aa34beda274ad4169): the tree list. Five spruce trunks stand in the road at z 63-70: (-3.7, 63.2) (-7.9, 69.9) (-5.6, 69.4) (-6.6, 66.9) (-8.0, 64.3); the rest are covered by the fade. Roofs (au1 6): the h1 hub run shows E9c's house cutaway already clears them, so it is closed.
5. **MR4 baseline (h1 run, `play2/logs/h1.log`):** the Waystation built in 7608 ms (ground+water 2067, props files 949 + props 1574, textures 405, landmarks 231, grass 171, the rest 242) plus pipelines. Her outfit is rebuilt (250-310 ms) at EVERY hand-back (the "her outfit" laps after each cinematic). Hub windows: p50 11.6-13.2 ms against main 3.4-3.7 + render 3.2-3.4 + gpu 3.0 ms, so ~6 ms is unaccounted (engine side: animation mixers, skeletons, physics, navigation? Godot's Performance monitors). The 0.1% and max (230-630 ms) are the shot captures every 20 s, not the game. Perf is noisy while other leads use the GPU (38% GPU use with no game running): measure ABAB. Then MR5 (audit 14, 15).

**MR1+2 round 3 (commits after 134c320f):** judge r3 (xhigh): all 7 frames SHIP (frames `survivorsunchained_inputs/play1/r3/`). Fixes:
- The Flare's great blessings leaked on a test profile: `GameTeach.Taught` read the profile before `--teach-reset` cleared it (the Teacher is lazy). `Taught` now builds the Teacher first.
- Callout rings round a HUD part are pale (`Callout.OnHud`, `Mark(..., pale)`); a lit dash form wears flame licks and the calling's badge (`Round.Licks`, `FormGlyph`), animating through freezes (`ProcessMode.Always`); the ring round a lit dash stands 18 px out (`GameHud.DashLit`). Form copy "When your dash is aflame, it's a charge / ...".
- Channel: `Prologue.ChannelTip()` shows at a channel's start only with an answer ready, naming only what's ready; title "Break his spell"; cast bar "Raising the drowned: break it!"; the RISE bark 1.3 s after the tip (`riseBarkIn`).
- Teaching panels drop the recipe, "Fits your build" and any reason every card shares; card bodies keep their last two words together.
- Tips take inline keycaps: `{key:I}` in a tip's text (`TipLine.Chip`, a small SubViewport). Pack tip broken at sentence ends.
- Callout `Aim.Cold` (ice-blue ink), `Aim.WordsNear`, `Aim.ShunBig` (words off bosses): the lamps use all three. Red line ring kept off the chest (`KnightLane`).
- Tests 1051/0/8.
**Polish routed to UI (judge r3, not blocking):** great-blessing footer rows at uneven heights (anchor reason + tag rows); gray "not in your build" tags read as disabled (style alike or drop); env: forest near-black outside her light pool.
**Run variance seen:** red_line and draught can go untaught in a run (queued, dropped "notyet": likely canopy over the Knight/her); the canopy fade (MR3) should help; re-check in its run.
**Next:** MR3 canopy whole-tree fade (kit.gdshader OWN_FOLIAGE; hub run first for the roofs), the tree list to Env 17; MR4 Waystation freeze + frame time; MR5 audit 14 and 15.

## Experience 2 (play-1 lead, 26 Oct): MR1+MR2 judged twice (history; round 3 done by Experience 3)

**Worktree/branch** as Experience 1 below (junction to the worktree's OWN `public/assets`; to remove the link use PowerShell `cmd /c rmdir godot\assets` from the worktree, since bash's `cmd //c rmdir` failed). Integration 126b1d9e is merged in. Import cache is fresh. Run tool: `<coordinator scratchpad>\play2\play.py NAME EVERY COUNT --teach-end` (one godot turn, about 9 min to dawn). It logs `teach ...` and now `tip <id> t= keys= text=` lines, and shoots `NAME_teach_<id>_1.png` and `NAME_tip_<id>_1.png` into `godot/.shots/`.
**Done (commits 3145c709, 200aeb30, a2a06a12, plus the copy doc):**
- au1 4: the channel tip had a dead key, because Act.Ability became Act.Flare on 11 Oct and her calling's art now rides the dash (Forms.cs). The tip now names Bull Rush and the Flare. A new F6b `form` callout in the Ambush. The dash ring glows ember when the form is ready (`Round.Form`), and the gray "Bull Rush: ready" note under the Q orb is gone.
- au1 9: the lamps callout says how. Callout rings keep out of the top-right HUD corner (`GameTeach.HudCorner`).
- au1 10: F8 waits for "Your pack" to clear. The Knight doesn't begin its first lunge far from her or under another callout, and holds it once while F7 waits.
- au1 2: the opening is spread. The great blessing gets its own panel 40 s into Rising, and dash comes after it. Timeline in m2: 0:45 / 0:46 / 0:53 / 0:55 / 1:21 / 1:39 / 1:51 road / 2:09 form.
- au1 3: `Battle.FlareGreatsHeld` keeps Flare blessings out until F8.
- au1 13: F12 and its banner now give the counts and tell traits from skills (`Callout.Mark` picks the word marked in ember).
- au1 17: a line rests 300 s per NPC (`NpcActor.LineRest`). au1 20: the lanes log.
- Judge round 1 fixes: the blessing kicker is keyed on holding a great blessing, no summon blessings before a summon, teaching panels hide Reroll/Banish/Skip, keys read 1-N, and lamps2 no longer re-fires every frame.
- Tests 1051/0/8 before round 1.
**Round 2 judge (m3 frames): level SHIP; all round-1 asks landed; 6 FIX.** Fix next, in this order:
1. **Called Shot (a Flare blessing) was still offered at 1:21.** `b.FlareGreatsHeld` is set at Prologue.cs ~1157 and read at LevelUp.cs:293. Find which path still adds FlareGreat: maybe another offer builder for the GreatRoles Answer slot, or setup running on another Battle. Also change the great block's `o.Why.Add("Your calling's own")` to "Suits your calling".
2. **The form glow can't be told apart:** a callout's HUD-target spotlight is ember too (`hud.Spotlight`). Make the callout highlight neutral (pale), and give `Round.Form` ready a look of its own (flame licks or a horn badge). Re-break the form lines: "When your dash glows, it's a charge / that throws the dead aside. / Big ones stop it, but they're stunned, / and their spell breaks."
3. **Channel tip:** show it only once the form or the Flare is ready. Hold the Warden's "RISE..." bark until the tip settles. Use one name: cast bar "Raising the drowned: break it!" (Prologue.cs channel case) and title "Break his spell".
4. **First draft:** hide "Fits your build" and the "Evolves:" lines on teaching panels (Panels.cs, `v.Teaching`). "all the way round" -> "sweeps the whole front of you" (Butcher's Cleaver text).
5. **Pack tip:** an inline [I] chip (hint text has no inline keys today: `TipLine`), with breaks at sentence ends.
6. **Lamps:** the off-screen markers are orange flames but the lamps are cold blue (recolor the markers); drop the card lower-left, off the Warden.
Routed by the judge: Combat card copy (Cold, Then Not tail; "fire" -> "strike"); UI (rarity row floats, dim italic objective, Night icon at dawn, bottom-right counters over bright planks); Env (no visible flame in the lit lamps); Rendering (ferns cover her at the form freeze).
**The m3 run found:** with the Knight's first lunge gated on her distance (8 m), a kiting run never saw F7 and the Post ran 140 s. Gate removed (commit after d9748814). m4 confirms the fix: F7 showed on its first windup (199.9 s) and the art freeze followed at 214 s.
**Tests:** PrologueTests updated (the first rise brings its card alone). Full suite 1050+1 green after that fix. Run the full suite before the merge.
**Still open from judge 1:**
- The red_line ring sits at the lane's far end by the chest. Order `KnightLane()` points away from L("chest").
- The pack tip's "I" chip is dark (`GameHud.HintKeys`, UI).
- "Cold, Then Not" tail copy (Combat).
**Then:**
- MR3: canopy whole-fade per tree instance in kit.gdshader (`see_parts`, OWN_FOLIAGE). Re-check whether E9c's house fade already fixed au1 6 in a hub run.
- MR4: Waystation 6 s freeze. The audit log breakdown: ground+water 1.8 s, props 1.5 s, her outfit built twice (about 0.5 s), 1126 pipelines. Fix with a black-hold pipeline prewarm before the fade-in. Hub p50 13-15 ms against main 4 + render 4.6 + gpu 3.5: diagnose with a medium solver, art causes to main for Env 17.
- MR5: au1 14 and 15.
**Routed (tell main):** night exposure crushes her and the dead at 1:1 and she blows out under the gallows lantern (Rendering); blobby canopies, flat crates, gray boulders and graves (Env); the "blocked" floater collides with the Warden's bark (UI); the zone header reads "Night" at dawn (UI); the Q orb shows the calling's bull icon for the Flare (UI).

## Experience 1 (play-1 lead, 26 Oct): step 1 MR READY, the audit done, step 3 (fixes) next

**Worktree** `.claude/worktrees/play-1`, branch `play-1` (from integration f91a13ca). `godot/assets` is a junction to this worktree's OWN `public/assets` (skip-worktree): never stash, reset --hard or checkout .; before merging integration, `cmd /c rmdir godot\assets`, merge, remake it. Import cache is current. Commit named files only (the .import/.uid noise stays out). Tests 1046/0/8.
**Scope (coordinator brief):** playability of the path from new game to Act 1. Env 16 owns env art, Face 41 and Body 12 own her: route their items to main in one line.
**Step 1, DONE, MR READY play-1@3cf21c2b** (the owner's 25 Oct butt-shot note). C04 A: the old A8 became A8a (a 3/4 front full figure at head height, for the reeds and sun lines, with a soft sinking ember) plus A8 (over her shoulder at shoulder height; she walks off 5 s in; `top` moved to -71). A1s is her front 3/4. The dawn now comes up under the lines (atmosphere preset `playdawn`), and the ford lamps dim with it. Code: `PlayerView.Still` (no idle breaks while a cinematic holds or hides her), nova `plain` -> `BattleFx.Sinking`, GameCinema `playdawn`. Four xhigh judges, all camera SHIP. The doc is `docs/cinematics/shoot/c04a.md` "As it plays now". Frames are in `survivorsunchained_inputs/play1/`. Scan of the other cinematics: no other low rear shots.
**Step 2, DONE:** the audit `survivorsunchained_inputs/play1/audit_au1.md`: 20 ranked items with their owners and sizes, and the fix order at the end. Run tools (backed up): `survivorsunchained_inputs/scratch_a44c2c21/play1/` (`play.py NAME EVERY COUNT [args]` is the full real-play run, one godot turn, ~9 min to the hub; `shoot.py RUNS.json` and `jedit.py c04a ed_X.py` are the cinematics tools; all point at play-1). The autopilot now walks to the Waystation at Dawn (e84d289d).
**Step 3, NEXT (start here):** the fixes in the audit's order, small MRs, each re-run on its stretch. (1) Items 4, 9 and 10: the "[ABILITY]" key name unresolved on the boss banner plus a Bull Rush callout; the lamps callout says how and aims clear of the HUD; YOUR PACK out of the Knight fight; the red line held until its callout shows (`Prologue.cs Callouts()`, `logic/Play/Teach.cs`). (2) Items 2, 3 and 13: spread the opening six lessons; Flare before the Great Blessing; the level copy. (3) Items 5 and 6: the canopy and roof cutaways. (4) Item 7: a loading screen and pipeline pre-warm. Judges: teaching frames at xhigh (whole-frame gate).
**For main / the owner:** SB00 (the storybook lore intro) is OFF (`sb00.json` `"live": false` since 19 Oct, waiting on its painted plates), so a new game opens on black, then C01.

## Teaching pass round 2 (teach-1 lead, 19 Oct): rounds 2-3 judged, fixes built, the MR next

**Worktree** `.claude/worktrees/teach-1`, branch `teach-1`. Integration merged twice (fd5271bc; 470c3293 with env 1 E1). Commit named files only: the `*.import`/`.uid` noise and the local clip pack (`godot/art/anim/heroine.res`, `heroine_clips.json`, `tools/anim/manifest.json`, rebuilt here by `tools/anim/build.py`) are NOT committed. Tests 993/0/8.
**Built:** the callout queue (`logic/Play/Teach.cs`), freeze and aims (`src/Game/GameTeach.cs`), the drawing (`src/Ui/Callout.cs`); F1-F10 and F12 in `Prologue.cs Callouts()`.
**Verdicts** (`survivorsunchained_inputs/teach1/`): judge1 (r1 1/11), round2/verdict.md (r2 0/10: the dim), round3/verdict_fixes.md (r3, the cap: F3, F4 PASS; the callouts pass in F2, F5, F6, F10, their gate fails are the WORLD; seven small fixes, all built and checked by the numbers). Final frames: `teach1/final/`.
**Since r1:** world dim ~30% with her own soft pool, HUD whole; damage numbers, trails and sparks hidden under a freeze (`BattleFx.Frozen`); the camera holds in a freeze; F2 brackets the whole chain (slots and buttons over it at 20%, heat fills from the left); F4 no arrow; F7 waits for a windup in the open with the Knight in view (`Aim.Open`, `Aim.Seen`, `GameTeach.InOpen`, per plant for flora scatters) and rings the lane clear of her; F8's copy says what a Flare is, in three rows; F9 rings a lamp only well inside the screen, the others get an edge marker (a ringed glyph with a tip), copy "Three lamps guard the Warden..."; her keep-out covers what she holds; ground embers get a warm breathing halo (`shaders/ember_halo.gdshader`, faded by ALPHA so fog paints no square).
**Autopilot:** at the Post it circles until F7 is read, then closes on the Knight (`Autopilot.cs`, `Game.OpenGround`); before that it walked off and the run stalled.
**MR READY** (19 Oct): the final xhigh check on HER 11 frames (`teach1/final_her/`, sheet_11.jpg) passed the callouts everywhere; F10 (she hid under a roof slab) fixed with Aim.HerSeen and re-shot. Gate fails left are the world (routed below). Earlier rounds' frames showed the male hero by mistake (no --sex female). Open, not blocking: world barks show dimmed during a freeze (hide them like damage numbers); F1 may ring an ember with a mob over it.
**Run:** from godot/, under a godot turn: `Godot_v4.5.1-stable_mono_win64_console.exe --path . --resolution 1920x1080 -- --quick warden --sex female --auto --teach-reset --teach-hurt --teach-end --shot teach --cines --until 1500 --count 0` (`--teach-diag` logs the cover checks; 10-35 min depending on the GPU). Frames `godot/.shots/teach_teach_<id>_1.png`.
**For the MR and other leads:** F8 teaches the Flare on Q (the story writer reconciles the F8/F13/F9 copy in docs/story/TUTORIAL_COPY.md). The Knight and the Grave-Caller can't die until their callout shows (caps 48 s, 30 s); F7 can be missed if the fight stays under cover (the cap lets the Knight die). Elite lanes draw through roofs game-wide (combat). Slot icons come from the skill's painted icon (HUD). Routed world items (r3): white fog blotches over the Low Ford Road (environment: the largest gate failure); lamps blow out to a white disc with blue bloom (lighting); the opening cinematic's frost decal left on a flat prop in play (cinematics); card UI "1-4 Choose" with three cards, Moonbrand's text cut, orphan words (UI); the Q orb's percent on its sigil (HUD); light squares round Thornbloom's brambles, likely the same fog-on-quad fault in `BattleFx.Skills.SkillGround` (VFX).

## The owner, in their words

- "We are striving for perfection." Improved is not the bar: ask whether this is the best version of the moment in any game, and root it in how the best games solve it.
- "Endless is truly endless."
- Full pages pause rarely, and "are often not the best choice".
- Story nights: "smaller arena", "proper arpg end bosses", no endless.
- Time "passing should probably happen".

**Standing decisions:**
- A lost story fight wakes her at Chid's a day on.
- Redcowl can be spared or killed.
- One rise in Act 1; after that, only with the rise skill.
- Story is about 40% of the early game.
- The endgame is PoE-like maps plus survivors arenas.

**Working rules:**
- Only 3 to 5 leads run at once.
- One Godot turn per batch of shots: look once, then fix in one pass.
- Handoffs are lean, at about 500k tokens.

## The brief

You own how the game feels to play, end to end: pacing, readability, the day clock, the story fights' flow, what the screen says and what is noise. Play it on the autopilot and in scripted runs, judge it at 1920×1080, then fix it yourself or brief the owning lead in short writing: what's wrong, the evidence, the target, how it's judged.

**Branch:** `worktree-agent-a9f0d6c64d891d56d`. The main session merges it; open no PRs. Run `dotnet test` in `godot/tests` before each commit.

## Collaborators (roster in `docs/team/README.md`)

- **Combat** `a739d6792d21f5efd`: the story fights. 52d202f2 and later are not yet judged.
- **UI design** `a4fdbc49786ba8b7f`: the dial and the fall at 2378e165; the result screens.
- **Story** `a7ba8903f4c8261b1`: all the words.
- **Paused:** skills `abc6bbe020c7fe287` and arena art `aba487928a1515c93`. Their asks are on the status page.

## Failures and gotchas

- **A fresh worktree has `godot/assets` as a 16-byte stub.**
  - Fix it: delete the stub, make a junction to `public/assets` (PowerShell `New-Item -ItemType Junction`), run `git update-index --skip-worktree godot/assets`, then `--headless --import` (about 4 minutes).
  - A checkout can turn the junction back into a stub, and the game then renders black frames or throws in `Dressing.PartsOf`. Check `(Get-Item godot\assets).LinkType`.
  - Once, deleting the stub through git removed `public/assets`. `git checkout -- public/assets` brings it back.
- **Copy `.godot` from an older worktree** to skip the full import.
- **Godot runs `.godot/mono/temp/bin`.** Run `dotnet build SurvivorUnchained.csproj` in `godot/` after every change.
- **To judge someone's unmerged work, use a local `exp-judge` branch,** then return to your own branch and delete it.
  - Skills' branch conflicts with loot's code, so leave it out.
  - Revert regenerated `.import` files before switching branches.
- **The shell guard** refuses compound git commands, `cd ..` followed by git, and runtime-built sed. Write a small Python script in the scratchpad instead (`gist.py`, `branches.py`, `contains.py`).
- **The autopilot** never answers a story fight's spare/finish offer (the Roost stalls), and takes the first card of every draft. A drafted Cold, Then Not rises her on its own. Use `--auto idle` to see the fall card.
- **Quote commit ids only from git.**

## Tools (scratchpad `experience/`)

- `play.py NAME -- [game args]`: a run at 1920×1080 and 60 fps, with the log in `logs/`.
- `batch1.sh`: one turn holding all three fights whole (`--on boss --until 720`), the fall, the dial, the Verge, loot and map results.
- `gist.py NAME`: a run's health by time, its tagged moves and its exceptions.
- `sheet.py`, `tsheet.py`, `crop.py`, `keep.py` (frames to `docs/experience/`).
- `wait_for.py`.
- Turns: `turn.py take godot "experience: <job>" --wait 30`.
- **Game switches:**
  - `--night ID`, `--stage N`, `--on boss`, `--die T1,T2`, `--choose rise|letgo`;
  - `--clock S`;
  - `--loot [legendary]`, `--hoard N`, `--strongbox`;
  - `--open mapresult [--fell]`, `--perf-off taa`.
