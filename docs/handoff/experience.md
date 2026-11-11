# Handoff: the gameplay experience director

For a fresh successor. Read these first:
1. `docs/team/README.md`: the bar, the turns, and batching shots.
2. `docs/team/experience.md`: the one-page status, which holds what's done, the next steps in order, and the verdicts.
3. `docs/design/STORY_NIGHTS_AND_TIME.md`: the owner's decisions are at its top.

## M6 tutorial (tutorial-m6, lead 4, 10 Nov): STATUS_LINE

**State.** Branch tutorial-m6. Integration (origin/claude/vigilant-galileo-l6jqyx f2c5ac2f8) is in; nothing newer to merge as of this block. Full suite at 23a306734: 2138/0/11. Teach|Prologue tests pass 73/0 at the head. Runs: `survivorsunchained_inputs/scratch_m6/run4..run8/` (run.sh, run.log); shots `godot/.shots/m6r4_*` to `m6r8_*`.

**Done (lead 4).**
- **The day stall (m6r3, m6r4) was autopilot-only.** A dev `daystate` trace (every 2 s in Dawn/Exit under `--on teach`) showed she took the strongbox and then wobbled for 1000 s in the nook at (46-49,-84..-87). GroundPath routing to `road_ambush` at (22,-86.5) never got her out. The wolves' ring was never reached, so neither A13 nor day_gap could queue. A player walks out of there, and the ambush isn't needed for the gate. Fix: Autopilot logs `autopilot: day stuck` after 25 s without 4 m of ground and takes the gate road. In m6r5 the ring sprang at 384 and A13 Leap showed (she was level 4, the Leap on seat 4), then the Waystation.
- **A13b (Shield Charge) does not come in the prologue.** The charge seats at level 5 (taught_builds.json). The autopilot leaves the Low Ford at level 4, and the zone sim's bots reach 5 at the gate off the wolves, which is the last beat, so no pack is left. It already gates on the seat and the next pack within 10 m, so it fires at the first pack after that level-up, in the zones after. Logged as a later-zone beat; no change.
- **A2 swing** was lost "gone" twice: under the move arrow as the Rising closed (m6r4), and at the screen's foot (m6r5). It is now asked until the Intro and tries the four nearest foes. **A4 Resolve now waits on it being seen** (else from the Barrow on). Its `after:` lapsed when the swing's foes fell, so in m6r6 Resolve came 18 s before Swing. m6r7: Swing 65.6, Resolve 67.2, Groundbreaker 78.0. (m6r8 reached the Watch-post at 69.8, before Swing at 74.7, so the fallback moved from the Post to the Barrow; tested, not rerun.)
- **A11b flare** never queued in m6r4: the autopilot spent the lent Flare on C02's hand-back. `GameTeach.HoldFlare` now also holds it at the Warden until A11b is seen (autopilot only). It showed in m6r5 at 181.8. A11b's aim is now every lit lamp, nearest first, with Safe. In m6r5 the nearest lamp was off the top of the screen and the ring sat on the Warden's bar.
- **A13's Leap point** lay 9 m north, at the screen's top edge under the watch's bark (m6r5), then under the tracker at the right edge (m6r6). `OutOfRing` now offers every point that is beyond the wolves, within 5.5 m of her up or down the screen, and on open ground, turned 30 degrees at a time. The Aim's Safe takes the first one well on screen.
- **A Safe target's ring clears the HUD** (`GameTeach.RingFloor` 870 px), both for the things it rings and for a point ringed alone. m6r4's A5 captain ring sat on the Drowned Girl, and m6r7's Leap ring sat on the right-hand figure.
- **The stand clock is retired (the owner, 10 Nov).** `world_tiers.json` `standOn: false`, read by `WorldTiers` (`Tier.Stand` is null, and the rows are kept as `Tier.StandRow`). Story fights (Journey, PostMenu) and maps (MapRun) read none. The arena's director keeps its own stand: it is a different switch, untouched. FighterFeetTests now reads `StandRow`, since the mechanism is kept. In the zone sim, II standing went from 3 falls (worst 8; Post 5, Exit 19, Boss 2) to 3 (worst 4; Exit 18, Boss 2). The clock's falls were the Watch-post ones. The rest is the day's rings, a get-out beat. Noted in `docs/balance/zone_lowford.md`, which the sim regenerated.
- **Tally: out of the demo** (main's ruling: no new HUD area). `Prologue.TallyOn = false`; TUTORIAL_COPY says so. **UI row for later:** a kills-and-gold tally chip on the ARPG HUD (`hud.TallyArea`), then `TallyOn = true`.
- **A5a stays a stub.** skills-p7 (f317a2f37, WickBook.LampOffered/LampLit) is not in integration. Wiring it is lead 2's plan below: TeachSeams.LampOffered set from WickBook.LampOffered.
- TUTORIAL_COPY's A2/A4/A4b/A5 trigger cells now match the build.
- Run 4 order (night): A3 28.6, A1 move 30.1, A4 44.6, A3b 57.9, A4b 83.0, elite, dash, draught, A5 138.7, post, raiser, lamps 209.9; day_charge 335.7.

**Runs m6r6 to m6r8 (the head less the Barrow fallback): the whole prologue lands.** In every one the autopilot finished the Low Ford, ringed the wolves (leap 392-424), reached the town (`prologue.done=True`), and C03 ran. I looked at the 1:1 frames myself:
- Swing rings a near foe.
- Captain and Raiser are ringed on screen, clear of the HUD.
- The Flare rings a lit lamp and the art.
- The Leap point lies beyond the wolves, on screen and clear of the HUD. The red arcs in that frame are the Flare's boom, which the autopilot spends as the ring springs.
- The autopilot still loses some "gone" freezes (Swing, Dash, Captain) because her foes fall before the freeze's gap or a bark ends. Every one came back later. Elite, Dash and Draught all showed in m6r6 and m6r7.

**No flow judge (my call, per the brief: only on a bet on PASS).** Under "would this frame ship in a AAA game as it stands, watched at 1:1", the frames fail on things outside this lane: the night's darkness (look-l1) and the leap's dark gatehouse. Every callout is placed and timed right, but I would not bet on a whole-frame PASS. The flow wants the owner's own play of demo-arpg1.

**Known, not fixed.**
- With `--fixed-fps 30` the game runs about 2x real time, so read-arrow timings (2.5 s real) hold freezes about twice as long in game seconds. A2's late show is partly that.
- Freezes answered by a key repeat the key in the hint ("LMB to swing" under "Hold LMB to swing"). This is the Teach system's overHint pattern, kept.
- The scene's darkness belongs to the look lane, not this one.

**Cost.** Lead 4 used about 0.24M. The lane is about 1.58M.

## M6 tutorial (tutorial-m6, lead 3, 10 Nov): HANDOFF READY at the commit carrying this block. Not MR READY: the callout fixes need run 4, then the frames, the judge and the MR.

**State.** Branch tutorial-m6 at 695ea5965 plus this block. Built; the Teach|Prologue tests pass 73/0. The full suite has NOT run. Integration is NOT merged since lead 2. Nothing is judged.

**Done (lead 3).**
- Run m6r3 (after 3cbf175c3): the HUD is lit after the dawn page. C04a measures 74/55, the day 40-67.
- The dawn page was black (m6r2: `story_sb_dawn_a/b` all zeros). GameStory.Storybook now hands its bars to StoryPlayer. In m6r3 the page measures 53.8 and 55.4 (6af0bff73).
- Teach.cs: an urgent freeze that is due takes the screen from an arrow already read (2.5 s). The test is `AnUrgentFreezeTakesTheScreenFromAReadArrow`.
- Dev aids: `--on teach` prints a once-a-second `teachstate` line before Intro (Prologue.Trace, wired in GameTeach). `--quit-trace` prints the quit's stack.
- Callout triggers fixed to follow the real fight (695ea5965, not yet run). m6r3 showed C01 hands her 4 risen, and the first kill lands at about 25 s, before n_lone wakes.
  - A2 swing: any hostile awake within 7 m in the Wake or Rising, not only n_lone. It had dropped "gone" at 36.5.
  - A3b ember_ring: waits on A3 while a stone is held. It had shown before A3.
  - A4 resolve: her first landed blows, after swing. It had never fired, because n_three died unseen.
  - A4b groundbreaker: any 2 or more in reach before Intro.
  - A5 captain: the nearest woken pack's live captain within 14 m, kept in `teachCap`. It had been lost under the road's line.
- In m6r3 these showed: A3 at 28.6, A7 dash at 113.9, elite, post, raiser, lamps, and day_charge (the boars) at 319.4.

**Next, in order.**
1. **The day (unsolved).** A13 leap, its fallback day_gap, and A13b charge never queued. From about t=330 to 1382, the autopilot circled at Stage.Exit around (48,-85) at wp=9 until `--until` quit. There were no gate-shut PaceNotes and no watch barks in run3/run.log.
   - Check whether the wolves' ring ever closed (`day.RingAt`).
   - Check whether leap and charge are seated. She was level 3 at the Warden; leap needs level 4 and charge level 5. If they can't be seated, A13/A13b can't fire in the demo's prologue: log them as later-zone beats.
   - Decide whether the stall is autopilot-only (the zone sim's bots pass 55/56) and log it. Extend the `teachstate` trace into Dawn and Exit (ring, gate, level, the seated skills, the next pack) to answer all of this.
2. **Run 4.** Use `C:/Users/munch/Desktop/survivorsunchained_inputs/scratch_m6/run3/run.sh` with `--shot m6r4`. Keep `--teach-reset`. Check that A2, A3b, A4, A4b and A5 show, and their order.
   - With `--fixed-fps 30`, arrow timings are real seconds, so game time runs about 2x faster in a run. Drops caused only by that are an autopilot artifact; log them, don't fix them.
   - Check A11b and flare (m6r3's summary had no flare line).
3. **Tally** is queued and dropped all run ("passed"/"notyet"), because `hud.TallyArea` is null: the new HUD shows no kills chip. Either it's a UI row for main, or the callout retires. Tell main.
4. Contact sheets via `tools/half.py`, then my own look. One xhigh su-lead-max flow judge, only on a PASS bet. The brief opens "would this frame ship in a AAA game as it stands, watched at 1:1?".
5. Merge integration (junction rule), run the full suite, push, put MR READY here, and tell main and the inbox.
   - A5a stays a stub unless main says skills-p7's M7a is merged. Lead 2's plan for wiring it is below.
   - Update `docs/story/TUTORIAL_COPY.md`'s triggers for A2/A4/A4b/A5 to match.

**Cost.** Lead 3 used about 0.2M. The lane is about 1.34M of 1.4M: tell main before going further.

## M6 tutorial (tutorial-m6, lead 2, 10 Nov): HANDOFF READY at the commit carrying this block. Not MR READY: one fix needs a rerun, then the frames, the judge and the MR.

**Done (commits b8717560a..3cbf175c3):**
- Integration merged (b8717560a, junction rule kept). Suite: the one red (VergeTests, the day's pack kill: M6's experience stones pay as they land) fixed by a 2 s wait; the touched filters ran 129/0. **The full suite has not been rerun since**: run it before the MR.
- Zone tune, data plus one field (d0e753921). Red Tolly Grasping -> Ironhide (his pull did 0.8 of her life from full, and LampRise resets elites, so a stander fell 10 times in a row there). Kerchiefs levelUp 1 -> 0. A new `followLeash` on a ring's follow (Encounters.cs `FollowLeash` -> SpawnOpts.Home); the wolves' follow is leashed 8 m round its ring, so the Howler no longer kites her to the wall. Sim (docs/balance/zone_lowford.md, 5 bots x 8 seeds at T2, plus T1): through 52/56 -> 55/56 (the one stuck run is careless s6, the known boars' ground wedge). Standing falls median 5 (worst 14) -> 3 (worst 8). Human, deft and plain fall 0. Levels 3 at the Warden and 5 at the gate held. Tried and reverted: wolves n 10 and 8, boars every [6, 8.5], boars and wallow levelUp 0 (cost level 5 at the gate). **The standing bot's last ~3 falls are the M3 stand clock charging a stander by design** (about 1 a run is the night Post: Barrow Knight plus a risen stand-charge, older than M6). Tuning them away undoes M3, so I stopped at 3 and pushed back to main.
- Real Godot run m6r1 (through turn.py, `--shot m6r1 --on teach --quick warden --zone lowford --cines --auto`). Script and log: `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_m6\run1\` (run.sh, run.log). Frames: `godot/.shots/m6r1_*` (git-ignored). Order: sb00, C01, "The Low Ford Road", move 30.1 s, ember_ring 45.7, elite 87.2, post 129.1, raiser 138.2, C02, flare 174.6, Warden banners, C03, sb_dawn mid-zone, C04a, "The Flare goes out", then the day. I looked at the night callout frames (move, ember_ring, elite, post, raiser, flare): each is placed and reads at 1:1, not yet judged.
- **Bug found and fixed, not yet re-run (3cbf175c3):** every frame from sb_dawn on was pure black: the page, C04a and the whole day. The mid-zone storybook (GameStory.Storybook) faded the HUD to black and never lifted it, because the HUD's fade sits above the page and the C04a film took "the black" without clearing it. The page now plays over its own CinemaBars, as SB00 does. HUD fade goes 0 under them, C04a takes the bars (storyBars), and otherwise Unbar() fades the world back in. Dev hooks: `--on teach` shoots story_<id>_a/_b and banner_<title> and logs `banner <title> t=` just before hud.Announce, after every hold. The run's 175 repeats of "This one has a name." were the old hook sitting before the re-defers, not a game bug.

**Callout gaps seen in m6r1 (diagnose in the rerun; the autopilot may cause some):** swing (A2) queued 31.7 and dropped "gone" at 36.9, because the autopilot killed the lone drowned one first. captain (A5) dropped "gone" at 45.3. ember stone (A3), resolve (A4), groundbreaker (A4b) and dash (A7) never queued. The day callouts (A13 and A13b) were never seen, because the day was black and the run quit at about 440 s ("quit: requested (game)"). Decide for each gap whether a real player sees it (fix the beat) or it is autopilot-only (log it as known).

**Next, in order:**
1. Rerun m6r1 (run.sh as is; it takes and gives the Godot turn). Check that the sb_dawn page, C04a and the day are lit, and that the day callouts fire. Diagnose the gaps above.
2. Contact sheets via tools/half.py or PIL; look yourself, then one xhigh su-lead-max flow judge, only if you'd bet on PASS (the brief opens "would this frame ship in a AAA game as it stands, watched at 1:1?").
3. A5a: wire TeachSeams.LampOffered to `WickBook.LampOffered` (static event, Action<CharacterData, string skill, string lampId>) **once main says skills-p7 is merged**. Plan: subscribe in the Prologue constructor and unsubscribe in Dispose(). Store the first (skill, lampId). `Seams.LampOffered = () => lampSkill is {} s && B?.Weapons.FirstOrDefault(w => w.Id == s) is { Slot: >= 0 } w ? $"seat:Skill{w.Slot + 1}" : null`. Use the "every third swing heavy" line only for a lampId ending ".third_blow"; otherwise a generic line. The loot-m9 seams stay stubs until main says loot-m9 merged.
4. Merge the latest integration (junction rule), run the full suite, push, and put MR READY here and to main.

**Cost:** lead 2 about 0.2M of the lane's 1.4M line (the lane is at about 1.14M before the next lead).

## M6 tutorial (tutorial-m6, lead 1, 10 Nov): HANDOFF READY at the commit carrying this block. Everything is BUILT and tested in the fake host. It has NOT run in Godot, been shot, looked at or judged. Integration is NOT merged and the full suite has NOT run.

**Brief and ruling.** The spawn brief is section 5 of docs/design/ARPG.md: the callouts, the cuts, one dawn page, the lent Flare, and the night copy retired. RULING M6 (main, 16:00) accepted the list and an estimate of 0.9-1.1M inside the lane's 1.4M. Helpers stay under 150k each. The dawn page reuses sb00's art (no new art), and a VO row goes to main if needed. Report one line each in `survivorsunchained_inputs\scratch_coord5\inbox.md`.

**The spec is `docs/story/TUTORIAL_COPY.md`** (rewritten): beats A1-A14 with words, moments and targets; the dawn page; and what was kept, reworded and retired.

**The app can now:**
- **A1-A4b:** move, swing, ember stone, the coin's ring, Resolve, then Groundbreaker. They live in `ArpgCallouts(p)` in Prologue.cs. Two new HUD aims: `seat:<Act>` (GameHud.SeatRect) and `resolve` (GameHud.FigureRect).
- **A5-A10:** the captain's plate, the charger's lane with the dash (the Knight's red line is the fallback), the elite's plate, the lit post on the corner map (`map:X,Z` via Minimap.OnDisc), and the raiser.
- **A13/A13b:** the Leap at the wolves' ring and Shield Charge at the next pack. Both follow their real seat, and both skills exist on this branch.
- **Seams:** `logic/Play/TeachSeams.cs` hangs on the zone (`Prologue.Seams`). skills-p7 sets `LampOffered` for A5a. loot-m9 sets `RareOnGround`, `FilterKey`, `FilterChip` and `CommonsOnGround` for A6 and A6b. Until then these beats do nothing.
- **The lent Flare:** she has none until C02. It is lent full at Stage.Boss (`LendFlare`), with A11b after A11. The dawn page takes it (`TakeFlare`, fact `flare.out`), then the banner "The Flare goes out / Lent for the night. It burns again at the Waystation's lamp." shows. The day runs without it. The square lamp lights it for good (`Waystation.SquareLamp`, `flare.lit`, banner "The Flare / Lit for good."). Saves past the prologue and arena runs are unchanged.
- **The dawn page:** `data/storybook/sb_dawn.json` is sb00's first-light plate `ink_p3d`, 9 s, with the `.dawn` line. It plays after C03 and before C04 A through `IZoneHost.Storybook` / `Game.Storybook` (src/Game/GameStory.cs). The dawn card and the traits banner are retired from the draft-off path.
- **Experience stones in story zones:** with the ember off, kills drop stones that rest 0.35 s, fly to her and pay XP as they land (Battle.DropXpStones/PayXp/PayXpStones). They pay the same XP as before, and whatever is left is paid at a zone end, a fall or a film. The journey's first stone is held for A3.
- **Retired:** Move, form, level, By day, F6 volley, F7 red_line, Elites, F8 art, day_hover and day_flare.
- **Reworded:** pack, Shieldmen, tally and Rested.

**Numbers.** The filter suites were green at each step: 215/0/2 at c27ea6462, and Prologue|Journey|Art 198/0/0 at 1e245e31e. The Low Ford zone sim went from 53/56 (the doc) to 52/56 at 48cac8472. That commit also changed two things for the whole game: a scattering drop now stops at colliders, and the Pilot closes on a kiting foe in the campaign. Its suite run is NOT done. Levels are still 3 at the Warden and 5 at the gate. Four runs stick: two at the wolves' Howler at the south edge, one at the boars' wedge, and one undiagnosed (I deft s3). The standing bot falls 5 (worst 14) against 2 with the Flare kept: the day without the Flare is harder for a bot that stands still. That is a design consequence, not a bug, and not yet routed to main. The sim outputs and A/B are in `survivorsunchained_inputs\scratch_m6\`.

**Next, in order:**
1. Merge integration `origin/claude/vigilant-galileo-l6jqyx` (junction rule; the runner saw 20 unmerged commits on her art, and shots need them). Then run the FULL suite and fix anything 48cac8472 moved.
2. A runner plays a real Godot run of the night with `--cines`. Log each callout's id, time and stage, check the order A1 to A11b, and check that sb_dawn plays between C03 and C04 A and the Flare banner follows. H3 gave the command: `--zone lowford --stage day --cines`, or a full start.
3. Shoot one 1:1 play-camera frame per freeze, plus the dawn page. Do your own look at half size.
4. One flow judge, xhigh: the whole-frame AAA question first, then "does each callout come at its moment, aimed at the right thing, in plain words". This judges the flow and words, not the look: any look mark goes to main as a UI row.
5. Tell main in one line: the Howler at the wolves' end is a slow chase without the Flare (zones' call), and the standing bot falls more by day.
6. MR.

**Cost (lead 1):** the lead used about 0.19M. Helpers used about 0.75M: H1 0.12, W1 0.05, H2 0.13, H3 0.13, H4 0.07, H5 0.12, W2 0.07, R1 0.04, H6 0.10. API: $0. Estimate to MR: about 0.3-0.4M (the merge and suite, a runner, the frames, one xhigh judge, one fix round).

## M5 zones and encounters (zones-m5, lead 2, 9 Nov): MR READY zones-m5@e195b0a45 (this line's own commit follows)

**State.** Every M5 item built (lead 1's block below: encounters as data, champions, lamp-posts, death, world tiers, resets, the zone sim). Lead 2 ran rounds 3 and 4 of `Item: M5 first 10 min` (cap raised to 4 by the coordinator). Integration merged at 81b34cd31 (and 7732f83c0 before) (junction rule each time). Suite 1650/0/10 (at ff9c4f616). Zone sim (`docs/balance/zone_lowford.md`): tier II human 8/8 through, 7.2 min play (8.4 with films), kills 176/5/4/1, 16 packs, falls 0 (worst 1), Legendary 8/8, level 3 at the Warden and 5 at the gate; 3/56 runs stuck in the day's Exit (careless/deft, lead 1's known ground wedge).

**Verdicts** (`C:\Users\munch\Desktop\survivorsunchained_inputs\m5_zones\`): r3 FAIL close (`clip_r3\verdict_r3.md`): 2,4,5,7,8,9 closed. r4 FAIL close (`clip_r4b\verdict_r4.md`): Aldric's wake, the Legendary ground beat and card, the push-in, the breather, the pointers and Ashjaw closed; "Would a Diablo player keep walking? Yes, more than in round 3. Fixing marks 1 and 2 makes this a PASS WITH KNOWN." After r4, mark 1 (heart line after Grimtunnel's take) and mark 4 (LEVEL inside the card) were fixed (d7f94b728, 5b842321f) and checked by the log only (clip_r4d: pickup 233.6, heart line 234.2, LEVEL 234.3, Dawn 249.4; no dead air): UNJUDGED. Lead 2 then fixed two bugs the sim caught: a held narration's delay carried into every later line (StoryText BeatGap, 5b842321f), and the Legendary's wait counted one frame in fifteen, so a coat left on the ground held Victory ~5 min (ff9c4f616; the sim had 0/8 through).

**What lead 2 built (the app can now):**
- One story-text channel (`logic/Play/StoryText.cs`): narration and speaker cards in order, never over each other; narration held 2 s before to 3 s after a champion wake (a line up is taken down and re-asked); a held line's delay carries only within one beat (BeatGap 10 s).
- `logic/Play/Zones/ChampionGate.cs`: tutorial cards and LEVEL banners wait near a champion wake (awake within 30 m, predicted wake, scheduled ring waves `Battle.ChampionDueAt`).
- The Legendary staged alone (`Prologue.LegendSpot`, held spoils, the heart beat waits for the pickup, `IZoneHost.StoryClear` gates Grimtunnel behind the heart line; `GameHud.XpHoldUntil` while any screen is open).
- One pack breather (`Battle.HushUntil/LampHush`: 4 s after a lamp, a lamp menu +2 s, 4 s after a rise); resting packs can't be hit inside it. Rise 1.75 m off the post toward the road (`LampRise.RiseSpot`, `lamp_posts.json` "rise"), outside sleeping packs' wake radius.
- Post menu Rest/Leave until `prologue.done` (`PostMenu.FullMenu`; Rest = rise point + heal; the "Rested" toast copy is M6's); tier line hidden until then.
- Champion rims (`champions.json` body.rim hues, `Champions.Look` -> `Enemy.RankRim` -> `Vat.Push` champRim -> `vat.gdshaderinc`); Nan Sallow's label-only "Raiser"; a champion with no affix takes the champion rim (42); Mother Mire moved to sun (-39,-91.5); the Slurry Sow's trail pools spaced and off while asleep (`Ai.TrailSpacing`).
- Lamp-post heads (`src/Game/GamePostHeads.cs`): unlit ember, lit flame + bloom + pool, kindling sparks; the square's lamp a 4.6 m landmark (`waystation.square` landmark/tall).
- Edge pointers notch around the HUD's top-right block (`EdgeMarks.Avoid`); Ashjaw comes out 8 m ahead (`Encounters.Follow`).

**Known (closed at the round cap; named for their owners):**
- M5/M3: a fall doesn't reset awake packs (n_road3 on her ~3 s after the rise); champion plates fade in slowly (Ashjaw ~30% at 1.5 s; UI if the HUD owns it); the dawn frame stacks text (feed cap 2, skull pointers hidden in a lamp breather); Mother Mire's violet rings still overlap; "LEVEL 4" at the kill instant with "The Ford-Warden falls"; a coat badge over her head after the pickup (UI); the autopilot's watch-post chest wedge (tooling).
- Combat/Loot VFX: a hard-edged cracked-earth quad beside the Legendary's beam when the Warden dies on land (r4 new mark 2: feather/depth-fade or skip on land).
- L1: the lamp head mesh, every light energy, the pool vs the zone light, the rim strength and hues. M6: THE LAMP BOARD stays after the road lamp (judge agreed: the bank is a checkpoint); the heart line's copy if it ever moves to dawn.
- Round 2's cross-area notes are in `docs/team/ARPG_NOTES.md` (trees, dappled shadows, damage numbers, gold discs, the Legendary smear, Knight naming).

**Merge notes.** Shared files: Battle.cs, Ai.cs, Entities.cs, Loot.cs, JourneyLoot.cs, Journey.cs, Game.cs (StoryText wiring, ChampionWatch, HoldBanners, PostRest, StoryClear, XpHold; more than ~10 lines now), GameHud.cs, Voices.cs, FoeMarks.cs, EdgeMarks.cs, CrowdView.cs, Vat.cs, vat.gdshaderinc, Zone.cs (logic/Play and logic/World), Lamps.cs, lamps_v2.json, champions.json, encounters.json, lamp_posts.json, Menus.cs, WorldScene.cs. Stray .uid files tracked by a solver (P1Bake.cs.uid, P1Springs.cs.uid, P1PoseProbe.cs.uid): harmless.

**Cost (lead 2):** lead ~0.2M; helpers ~1.0M (3 medium solvers 0.59M, 2 max judges 0.33M, 1 worker 0.05M, 1 runner 0.05M); $0 API.

## M5 zones and encounters (zones-m5, lead 1, 9 Nov): history (lead 2 above ran rounds 3-4 and the MR)

**Start here (lead 2).** Brief: `tools/scratch/coordinator/briefs/M5_zones_lead1.md` and `docs/handoff/lead_brief.md` (the junction rule; NEVER `git reset`, even --soft: a solver's soft reset uncommitted another's work once). Area: `docs/design/ARPG.md` §5, §7. The worktree is green: suite 1613/0/10 (e9174bd85+). Branch tip has every item built. **What is left: judge round 3 (the LAST for `Item: M5 first 10 min`; r1 FAIL medium, r2 FAIL close), then MR READY zones-m5@<sha>.**

**Built (the app can now):**
- **Lay any zone's encounters as data** (`data/content/encounters.json`, `logic/Play/Zones/Encounters.cs`, was DayStretch): phases night/day, packs with captains, champions, waves, ambushes, rings, `after`/`afterSecs` gates (a pack rises out of the road N s after a beat or placed champion is down), `needs` (beats off until a ground feature exists: `ZoneMeta.Features`, e.g. `lowford.pockets`). The Low Ford's night is 10 placed beats (was a procedural horde); its three ground pockets (10 packs, `n_pk1_*`, `pk2_*`, `pk3_*`) wait behind `lowford.pockets` (P5 lead after G2, `briefs/P5_lowford_pockets.md`, ~0.6-0.8M; act1.post1 moves there via lamp_posts.json `moved`).
- **Champions** (`champions.json`, `logic/Content/Champions.cs`): kit affixes (Quaking ring, Charging charge, Grasping pull, Hemming closing; Ironhide, Swift), count by world tier [1,1,2,3], names (PLACEHOLDER copy for the story lead), rank bodies (champion 1.25x + affix tint, captain 1.1x + plate), plates in `src/Ui/FoeMarks.cs` (functional; UI owns the look). Carriers: captain rolls the `champion` source, champions `elite`, via Prologue OnLoot -> `Encounters.Carried`; `"loot": "rare"` floor on n_first.
- **Lamp-posts** (`lamp_posts.json` = the one truth for board posts too; `LampPosts.cs`, `LampRise.cs`, `LampBook.LightPost`): checkpoint posts (no point), dark posts (a board point), door posts light themselves; the post's menu (`logic/Play/PostMenu.cs`, `src/Ui/PostScreen.cs`, `src/Game/GamePostMenu.cs`): travel between lit posts (not before prologue.done), world tier, Lamps bench (respec at a lit post), leave.
- **Death (§7.2):** she rises at her last lit post, whole; champions and bosses heal; the toll `toll.rises`; Low Ford and Verge (no Journey.Fell there now).
- **World tiers I-IV** (`world_tiers.json`, `WorldTiers.cs`; Battle.WorldHealth/WorldDamage in SpawnEnemy; DropCtx Rarity/LegendaryMul/Level in Journey.Drops; maps and arenas excluded; III opens on `act1.done`, IV on `campaign.done`: nothing sets them yet).
- **Resets:** `zone_resets.json` lowford/verge "leave" (clears on entry from another zone, not on load or rise), waystation "never"; wired in Prologue.Day StartDay and Verge.Begin.
- **The draft off in the Low Ford** (`"draft": false`): plain XP, she levels in the night, Douse strips nothing. M6 cuts the callouts.
- **The Ford-Warden's first Legendary** (M9's row done early): `lowford.warden_legendary`, staged (beam, banner, narration).
- **The zone sim:** `dotnet run -c Release --project godot/balance -- zone --zone lowford --bots human,careless,deft,plain,standing --seeds 8 --tier 2 --also 1:human+deft --out docs/balance/zone_lowford.md` (~1 min; `--features lowford.pockets` previews the pockets). Tier II human: 7.4 min play (8.5 with films), kills 170/5/4/1, 16 packs, 4-5 champions, level 3 at the Warden and 5 at the gate, falls 1, Legendary 8/8; quiet between beats 4-6 s; awake-champion wakes 0. Stuck 6/56: day Exit ground-wedging near (49,-86) (Encounters.Route plans at 0.8 m; a 0.45 m try made night wedges, reverted). Open, low.
- **The autopilot** (`src/Game/Autopilot.cs`) walks the beats, lights posts, fights the Warden, stops at the square's lamp in town; `--judge-hooks` (post menu frame), `--fall-once`; named frames (wake_champ_*, wake_capt_*, tell_*, light_*, legendary_*, fall/rise, town_stop). Known: it wedges ~55 s at the watch-post chest (22.3,30.8): tooling.

**Round 3 (the last).** The verdict, word for word: `survivorsunchained_inputs/m5_zones/clip_r2c/verdict_r2.md`. Fix list (mine), worst first:
1. One text channel at a time (dawn narration waits for Grimtunnel's line); the narration band clear of a waking champion; the rise point 1.5-2 m off the post, the post prompt hidden ~2 s after a rise.
2. No tutorial card on a champion's wake (BY DAY before the boars in the dawn breather; LAMP BOARD right after the bank lamp): an engine gate; the copy is M6's.
3. The Legendary alone: >= 2.5 m from her and 2.8 m from the corpse, inside the camera's safe box; other drops' labels and the small LEVEL label held until after the banner.
4. Dark champions: the affix tint as an emissive rim that survives night and shade; Mother Mire wakes in a sunlit patch; one charge ring at a time; Nan Sallow's affix line (decide: the Grave-Caller's raising IS her kit; give her "Raiser" as a label-only affix, or none and say so).
5. Lamp-post states: a lantern head that reads, an ember when unlit, a flame or bloom when lit, a flare of sparks plus a head bloom (not a mottled decal). Name what is L1's.
6. Hold pack wakes >= 4 s after a lamp lights (n_post rose 0.7 s after).
7. The first post's menu: Rest and Leave only until after the Ford.
8. Hide the off-screen skull pointer while a champion is awake on-screen.
9. Town: the square's lamp as a landmark, or end the autopilot at the Last Lamp.
Then one capture (the batch `clip_batch_pace.json` in the coordinator scratchpad `m5\`, plain and `--fall-once --judge-hooks`), and the judge r3 with the same brief shape as r2 (`Item: M5 first 10 min`). PASS or PASS WITH KNOWN -> full suite -> MR READY. On FAIL at r3, close the rest as known and MR (round cap).

**Other owners' notes** (round 1's filed by main in `docs/team/ARPG_NOTES.md`; round 2's new ones are in the verdict file's last section; send them to main in one message).

**Cost:** lead 1 ~0.27M, helpers ~2.4M (8 solvers, 3 workers, 3 runners, 2 explorers, 2 max judges), $0 API. Est. left: round 3 ~0.4-0.5M.


Older blocks: history/experience.md (grep by keyword, never read whole).
