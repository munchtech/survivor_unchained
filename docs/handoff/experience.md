# Handoff: the gameplay experience director

For a fresh successor. Read these first:
1. `docs/team/README.md`: the bar, the turns, and batching shots.
2. `docs/team/experience.md`: the one-page status, which holds what's done, the next steps in order, and the verdicts.
3. `docs/design/STORY_NIGHTS_AND_TIME.md`: the owner's decisions are at its top.

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
