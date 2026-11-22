# The den's roster: what it does, how the genre does it, the re-cut (21 November 2026)

The owner, 21 Nov: "the way the mobs are now is too derivative of when we were a survivors roguelike.  everything just charges and it gets annoying.  clear speeds feel unfun.  its a fun effect sometimes, but its like all our stuff does over and over". Tests GAME_PLAN decision 17. Labels: **[O]** observed in code, **[D]** documented by a public source, **[I]** inference, **[R]** recommendation. Paper only: nothing built or measured. **Approved by the owner, 22 Nov: "I approve den roster".** The build is package P3 in `docs/team/HANDOFF_BRIEFS.md`.

## 1. Today (observed from code)

**The main finding [O]: "everything charges" is literally true, and the cause is not the enemy table.** In every woken den pack, `MapRun.Press` (`godot/logic/Play/Zones/MapRun.cs:386`) hands every non-elite foe that has no ranged attack to `PackKit.Tells("charge")` (`Play/Zones/PackKit.cs:38`). That is every rank-and-file wolf, boar and runner. Each one casts the telegraph kit's charge (`data/content/telegraphs.json`): a 1.1 s wind-up, a lane 16 m long and 2.6 m wide, then a 0.25 s dash. A caught charge takes 0.40 of her max life times the tier's kit 2.0 (0.8 before armor) and knocks her down for 0.9 s. The first charge comes 1.2 s after the pack wakes and each next foe follows 0.9 s later. After that each foe repeats every 5-7 s times kitEvery 0.4, which is 2.0-2.8 s (`world_tiers.json` tier 1; dungeon charts are tier 1, `Maps/Charts.cs:52`). Two caps hold it back: at most 2 fodder lanes live near her, and landings come at least 1.5 s apart (`Sim/Tells.cs:259`). So while a pack is up, a 16 m red lane lands on her about every 1.5 s. On top of that come the foes' own runs (boar charges, runner lunges) through the charge director, at 2 at a time (`MapRun.cs:227`). The stand clock is off (`standOn: false`).

**Which foes the den fields [O].** The den runs as a tier-1 chart, which opens only the first two "stretches" (`Charts.Kinds`, `Maps/Charts.cs:219`; roster in `Maps/MapOffers.cs:72`). So its packs hold only **wolf, boar and wolf_runner** (weights 5 : 2 : 2.5), and its altar guardians are only **Old Tusk and Whitethroat**. The blighted wolf, slurry sow and howler are gated to later tiers. Greenbelly is gated too, and Ironback is never fielded in the den. GAME_PLAN A3's "the den's six" are not what the code fields. A pack is 4-8 foes × room factor × 0.85 (`MapRun.Place:302`): one main kind, with every third foe of a second kind. A magic pack (25%) or rare pack (10%) adds a leader, the open kind with the most health that has no ranged attack: at tier 1 that is a boar with Signs.

Her run speed is 5.15 m/s (measured). Speed ratios below are each foe's walk over hers; Pack kinds walk ×1.1 while more than 5.5 m out (`Sim/Ai.cs:324`).

| Foe | Kind | Closes by | Speed vs her | Its own attacks, telegraph | Shares with others |
|---|---|---|---|---|---|
| wolf (Longtooth) | Pack | fans to a slot 4 m round her, then closes | 5.3 (1.03, 1.13 far) | bite every 0.9 s, no tell | **kit charge**, contact bite |
| wolf_runner (Ridge-Runner) | Orbit | walks a 6 m ring round her | 5.6 (1.09) | lunge 7 m, 0.7 s line; bite | **kit charge**, a line run |
| boar (Thicket Tusker) | Charger | walks in, charges a lane | 3.2 (0.62); run 13 m/s | charge 10 m, 0.9 s paw + line; tree = stunned | **kit charge**, a line run |
| wolf_blighted* | Chase | straight in | 4.4 (0.85) | death burst 2.4 m, poison, 0.5 s fuse | kit charge (if fielded) |
| boar_slurry* | Chase | straight in | 2.6 (0.50) | poison trail pools | kit charge (if fielded) |
| boar_ironback* (elite) | Chase | straight in | 2.6 (0.50) | bite only, 300 hp | none: elites are exempt from the kit |
| wolf_howler* | Ranged (no shot) | holds 4.4-6.8 m, strafes | 4.0 (0.78) | haste howl 1.25× every 8 s, 9 m ring | none: it counts as ranged, so no kit charge |
| wolf_alpha (Greymuzzle) | Pack | as the wolf | 5.4 (1.05) | lunge 9 m, 0.6 s line | a line run |
| mb_old_tusk | Charger | as the boar | 3.3 (0.64) | charge 11 m ×3 (chain), 1.0 s | a line run |
| mb_whitethroat | Orbit | ring | 5.8 (1.13) | lunge 8 m; calls 4 runners | a line run, a ring |
| mb_blight_mother* | Chase | straight in | 4.0 (0.78) | poison trail, death burst 3.2 m, splits into 3 | poison ground, burst |
| Pack-Mother (boss_pack) | scripted (`Play/Bosses/ArenaBosses.cs:32`) | the Drive | 5.4 (1.05) | Drive = the kit charge ×1.5 (a 24 m lane) every 14 s, after spawning 7+ wolves in a crescent 10 m out; Hamstring cone; Moon-howl: lanes across her every 1.6 s for 8 s; last phase: 3 chained lunges, Shake cone, a ring of 12 wolves 14 m out | a line run ×3 kinds, wolves spawned round her |

\* Not fielded in the den today (tier gate).

**How fights start [O].** Packs are mostly not survivors-style. Each pack is set down out of sight when she comes within 46 m, and it rests there. It wakes when she comes within 14 m (or hits it) and wakes only its own pack (same home, `Sim/Battle.cs:1265`). Once awake it hunts her up to 1.6 × its 24 m leash (38 m from home), then goes home. Halls get a pack every 11-16 m. **[I]** At a 14 m wake range, hall packs that close can wake one after another, which reads as streaming. **Two survivors leftovers remain [O].** (a) Killing the altar's miniboss starts "The Hunt" (`MapRun.cs:452-545`): three waves 17 s apart of 9-15 foes. They spawn in a ring 10-13 m round her (or a line 14 m off), already awake, with the charge director's spikes on (many lanes at once). (b) The boss spawns wolves round her twice.

**What repeats [O].** The 16 m red charge lane is cast by every den rank-and-file foe, three kinds run a line of their own, and the boss's two signatures are lanes. Contact bites without a tell are the only other pack attack at tier 1. **Her kit repeats it too [O]** (`data/content/taught_builds.json`). Shield Charge (key 4) is a charge. Heroic Leap (key 2) is a gap-closer, and the dash is a third line move. Only Sunder (key 1: reach 3, a 220° arc, a 7 m line) and Bladestorm (key 3: radius 3.5) stand and fight. **[I]** The feel the owner names comes from the kit tells: the same lane, from every foe, every 2-3 s, at 80% of her life. Clearing is unfun because each kill is interrupted by a lane she must dash. Most of her damage is close-area, but the pack never stands still inside it.

## 2. How the genre does it (documented)

- **Rarity and pack shape (PoE 1) [D]:** Normal monsters are the most common and come in large packs. Magic monsters have one or two modifiers and come in smaller packs. Rares have up to four modifiers and come alone or with a pack of normal or magic monsters. Source: https://www.poewiki.net/wiki/Monster (the wiki's own text, as the search index quoted it; a direct fetch was blocked).
- **Rarity and pack shape (PoE 2) [D]:** Most monsters in a pack are normal, though a whole pack can be magic. Only one or a few in a pack are rare, almost always the pack-leader type. Source: https://poe2wiki.net/wiki/Monsters and https://poe2wiki.net/wiki/Rarity (quoted the same way).
- **PoE 2 intent [D]:** PoE 1 is "often proactive, kill things before they kill you", while PoE 2 is "being designed to be reactive". Combat should not be "emitting 500 projectiles a second and covering the entire screen". Monsters are built with extremes ("a white monster could have ten times the amount of life as another white monster"), and boss mechanics are "all telegraphed, you can dodge". Source: Jonathan Rogers, PAX West 2023, https://maxroll.gg/poe/news/pax-west-path-of-exile-2-interview-with-jonathan-rogers
- **Diablo 4 [D]:** "Each monster should now have its own clear role and own identity when fighting". Champion rarity was reworked to form champion packs, and "Elites now spawn with minions that inherit some of their affixes". There are 20+ new monster affixes, and "monster packs will also group up less". Source: "The 2.5.0 PTR: What You Need to Know", https://news.blizzard.com/en-us/article/24242857
- **Last Epoch [I]:** I found no public source on its pack building. Do not treat its internals as known.
- **Aggro and leash [I]:** I found no source. My reading of play in all four games is that packs idle where they stand and wake on approach or on a hit. They do not stream from across a map, except in a mechanic the player starts on purpose (PoE's Breach and Legion, D4's Helltide and hordes).
- **What makes clearing feel good [I]:** Fodder dies in one or two hits, so whole groups fall to one area skill at the same moment. A few foes per pack ask for a reaction (a ranged foe, a slow heavy, a leader with modifiers). Telegraphed moves are rare enough to read. All of this is inference: the sources above give only the reactive aim and "clear role and identity".

## 3. The re-cut (recommendation)

**[R] The fix that matters, first:** stop the kit charge tells in the den. In `MapRun.Press`, make `may` false in dungeons, or stop handing packs to `PackKit.Tells`. That one change takes the lane off every foe. The data changes below then give each foe its one move. Every new move here uses an existing spec (`SlamSpec`, `RangedSpec` with `Lob`, `AuraSpec`, `SummonSpec`). No new Behavior kind is needed. All of it stays inside the den's fiction (STORY_BIBLE 383: sick wolves, the Dig's slurry), so no non-beast foe is needed. **[R] Open all six for the demo:** give the den's chart enough open stretches (tier 5) or a den-only kinds list, so blighted, slurry, howler and Greenbelly appear.

| Foe | Role | Approach | Its one move | Taken away |
|---|---|---|---|---|
| wolf | line melee, the body of a pack | Pack: surround at 4 m, close, bite | none: it is the pack's weight; it dies to two Sunder cuts | the kit charge |
| wolf_runner | fodder swarm | Chase, fast (5.6), health 26→14 | none: it arrives first and dies to one cut, in fours | Orbit, its lunge, the kit charge |
| wolf_blighted | ranged, stays back | Ranged, 7 m | coughs slurry: a Nature `Lob` with a 0.6 s aim, no ground left; its death burst stays (bursts chain) | the kit charge |
| boar | **the charger: the one foe that keeps the charge** | Charger, slow walk | paw 0.9 s, then a 10 m lane; a tree stuns it | the kit charge (its own charge is the only lane) |
| boar_slurry | slow area-denial tank | Chase 2.6 | poison trail pools (the den's one ground effect) | the kit charge |
| boar_ironback | the heavy, a rare pack's leader | Chase 2.6 | a ground slam: `SlamSpec` range 3, 1.3 s wind-up, radius 2.8, ×1.5 | none: it gains the slam |
| wolf_howler | support, kill first | Ranged (hangs back, strafes) | the haste howl (as now) | nothing |
| wolf_alpha | magic pack leader | Pack | wears 1-2 Signs, no line | its lunge |
| mb_old_tusk | miniboss: the charge, shown big | Charger | charges three times running (as now) | nothing |
| mb_whitethroat | miniboss: the ring | Pack (not Orbit) | calls 4 runners round her, then a "Yip" haste on them (`AuraSpec`) | Orbit, her lunge |
| mb_blight_mother | miniboss: the burst | Chase | trail, split into 3, death burst (as now) | nothing |
| Pack-Mother | the boss | script | keeps the Drive (the boar's charge at boss scale, every 14 s) | the last phase's 3 chained lunges (keep Shake and Hamstring); Moon-howl's lanes become slurry drops (circles) |

**Pack recipes [R].** At most one telegraphed foe per three:
1. Hunting party: 4 wolf + 2 runner + 1 boar.
2. Sick pack: 3 wolf + 1 blighted + 1 slurry sow + 1 runner.
3. Called pack: 1 howler + 4 runner + 2 wolf.
4. Tusker ground: 1 Ironback (leader) + 1 boar + 4 wolf.
5. Rare: recipe 1 or 3 led by an Ironback or alpha with Signs.

These replace "one main kind, every third a mix" in `MapRun.Place`.

**[R] "The Hunt":** its waves walk in from the event room's mouths as recipe packs, not in a ring at her feet, with no spikes.

**Repetition rule [R]:** in the den, each telegraphed move (charge, slam, lob, howl, poison ground, death burst) belongs to one kind, and no more than one foe in three in a pack carries one; the rest walk in and trade blows. **Pushback [R]:** decision 17's "no behavior on more than about a third of a pack" should count telegraphed moves only. Genre packs are mostly one normal kind (section 2), and that is what lets one area skill drop a group together.

**Clear-feel targets [R], proposals for the owner's play to confirm.** Measure them with the balance harness's `dungeon` command and the bots.
- A recipe-1 pack dies in 6-10 s with the four skills at par gear. Today: to be measured before the change.
- At least 50% of a melee pack is inside one Bladestorm or Leap (radius 3.5 m) at its first landing, and at least 40% of a pack's deaths fall within one 1.5 s window.
- At most one red lane on screen in a normal pack fight, and no more than one lane every 8 s on average. Today: one about every 1.5 s.
- About a pack every 14 s of walking, as now (`MapRun.cs:89`).
- Today's survival bars stay: the stand-still bot falls in 80%+ of runs, the late human clears 70-90%, the deft bot 95%+, from `dungeon_fights.json` "about". The threat moves from lanes to bites, the slam and the lob. If the stand-still bot stops falling, add foe damage before adding any tells.

**Build cost [R].**
- Files to change:
  - `Play/Zones/MapRun.cs`: Press gating, Place recipes, the event's spawn points.
  - `Content/Enemies.cs`: the den rows above.
  - `Maps/MapOffers.cs` or `Charts.cs`: the den opens all six.
  - `Play/Bosses/ArenaBosses.cs`: the Pack-Mother's last phase and Moon-howl. This class is shared with Greymuzzle's story night, so the change needs a den-only switch.
  - `data/content/dungeon_fights.json`: a re-tune.
- Tests to re-cut:
  - `DungeonFightTests` (the never-dodge bot falls before the ruler; level and seed cases).
  - `MapTests` (14 tests, pack counts and placement).
  - `DungeonTests`, `BossTests` (the Pack-Mother).
  - `ArenaTests`, `ChampionsTests`, `EncountersTests`, `MassGraceTests` and `StandSwingTests` use the kit charge. Arenas and story fights keep the kit, so these should only need a check that they are untouched.
- If it must fit in 2 lead sessions:
  - Session 1: the Press gate, the six open, the Ironback slam, the blighted lob, the runner health, the recipes.
  - Session 2: a re-tune to the bars above, and the tests.
  - Cut first: the Pack-Mother changes, the Hunt's spawn points, and Whitethroat's re-cut. Each is its own small change for a later round.
