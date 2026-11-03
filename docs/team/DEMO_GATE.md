# The demo gate (Experience 11, 3 November 2026)

The only backlog until the demo ships (`DEMO_PLAN.md`). Every item below is a step on a first-time player's path, played at 1920x1080 on integration 5aca7a1b6 (worktree demo-1). Evidence frames are half-size copies in `docs/experience/demo_gate/`; the full runs are in demo-1's `godot/.shots/` (names below) and their logs in the Experience 11 scratch (`demo11\logs\`).

## What already works (played, not assumed)

- **The first-time path runs clean, start to finish: 21 minutes, 125 frames, 0 exceptions** (`b_path`: a fresh save, title, creation, SB00 played live, C01, the prologue Wake > Rising > Road > Ambush > Post > Barrow > Ford > the Ford-Warden > Victory > Dawn, C04, into the Waystation). Every teach callout fired and was shot (15 lessons, `b_path_teach_*`).
- **Title and creation:** the title, all four callings on "Who sits here?", the origin page, the Look for each calling and the hair page (`a_title`, `a_new0_*`, `a_look_*`). With a save on disk the title offers Continue (`h2_title_saved`).
- **The Waystation by day:** every screen opens and closes: Mother Rook (rest: sleep until morning, wait until nightfall), Rook's storeroom (the stash), Brannoc, Harlan's shop, inventory, character sheet, journal, the town map, the Wayfinder's table, the arts page, the pause menu with Save (`a_town_open_00..11`). Talk prompts show (`a_town_talk_prompt_talk_1`). The day clock turns to dusk and night, and at night the tracker sends her to the table ("Tonight: The Wayfinder's table / Answer the night: hold N", `night_tracker_table.jpg`).
- **The table into a night and back:** a click on "Enter the arena" pulls her into the Deep Shaw, the opening Great Blessing, the arena with its 30:00 clock (`table_click_into_arena.jpg`, `c5_click_pick`), even with a fast pick during the entry fade (`g1_fastpick`). A full tier-1 night on the autopilot: 31 minutes, the Pack-Mother at the half hour and down in about 80 s, "The Deep Shaw is won", then the endless "Beyond" (`e1_night_*`, 0 exceptions). The won result ("The night is held") and the fallen one ("The Ember Gutters") both return her to the Wayfinder's table, saved there (`result_won.jpg`, `result_fell.jpg`, `back_at_table.jpg`). A reload lands her at the table and the table offers again (`f2_reload`, `f3_table2`).

So nothing on the player's path is BROKEN. The gate is three things a first-time player would miss or not find, plus the Lamps screen already in flight, plus the tools the gate needs to replay itself.

## The gate, ranked

| # | Class | Area | Item | Evidence | Smallest fix that passes |
|---|---|---|---|---|---|
| 1 | CONFUSING | experience (words), ui (pin) | **By day nothing points at the Wayfinder's table.** On arrival and for 10 minutes of day the tracker names only Mother Rook ("Mother Rook, outside the Last Lamp, hears all the talk"); the table appears in the tracker only at night. A player who doesn't know the table exists never finds the arenas, the heart of the demo. | `day_tracker_no_table.jpg` (b_path_25), `day1_dawn_after_10min.jpg` (b_path_39) vs `night_tracker_table.jpg` | A standing Waystation objective once the prologue is done, by day too: "The Wayfinder's table, by the east gate: tonight's arenas" with its minimap pin (the night's line already exists in `GameClock.WithTonight`; show it from arrival). |
| 2 | CONFUSING | experience (words), ui (pin) | **After an arena's boss falls, nothing says how to leave.** The tracker reads "The Pack-Mother is down: the night is held / Stay as long as you dare / The Pack-Mother comes again in 12:12"; the way out (`ArenaRun` `way_out`, a ring where the boss fell) is named once in a passing announcement, in the dark Deep Shaw, with the crowd still coming. The autopilot never found it in 6 minutes of Beyond. | `won_no_way_out_line.jpg` (e1_night_70) | A tracker line from the win: "Leave by the way out, where the Pack-Mother fell", with its minimap pin and an edge-of-screen arrow while it's off screen. |
| 3 | MISSING | cinematics (storybook) | **The lore intro is off.** `godot/data/storybook/sb00.json` has `"live": false`, so a new game opens on black, then C01. Played live it runs clean, 89 s, into C01 (`b_path_00..03`). | `sb00_plays.jpg` | Ship the demo build with `live: true`. The owner's p6 note (the fire-to-water pan, 71-81.5 s: "a good start") goes after the demo; it works as it stands. |
| 4 | MISSING | ui (Lamps build 2, Phase 0) | **The Lamps screen in town is the old arts page** (Bull Rush's ranks); the board pages exist only behind `--board`. Already in flight as Phase 0 (Lamps build 2, one max judge and a merge). | `arts_default.jpg`, `lamps_board_flag.jpg` | Lamps build 2 merges, functional and clean, as `DEMO_PLAN` Phase 0 says. No new work. |

Counts: BROKEN 0, MISSING 2 (one already in flight), CONFUSING 2.

## The gate's own tools (experience; needed for Phase 3 and every replay)

The autopilot can play the prologue and a night but not the town loop, so this gate needed hand-built runs to cross the table, and the owner's evening (Phase 3) can't be pre-checked by a machine. Each is a capability the next replay reuses:
- **T1. The autopilot crosses the table:** in town it walks to the Wayfinder's table, opens it and takes the first sheet (today it closes every overlay, so `--open maps` dies under `--auto`). Reuse: `tools/` replay of the whole loop in one command.
- **T2. The autopilot takes the way out:** after the win and N seconds of Beyond (`--leave-after N`), it walks to `way_out` and presses Use, so a night ends on its result and back at the table.
- **T3. `--pull` with `--auto` holds a black screen for the whole night** (the fight runs behind it: 12 minutes of black in `c2_night1`, again in `c6_pull_auto`; `harness_pull_auto_black.jpg`). A player's click (`c5_click_pick`) and a fast click (`g1_fastpick`) lift, so it is the harness, not the game. Likely cause: the autopilot's same-frame blessing pick against `GameHud.Pull`'s completion, which re-blackens after `Fade(0)`. Fix in `GameHud`: a `Fade(0)` cancels a pending pull, so no later pull completion can hold the black.
- **T4. Saves under test:** every quick run writes `Save("new")` into the shared `user://saves`, so another lead's run can replace a save under test (it happened here). The replay tool snapshots the saves folder after its run and reloads with `--load <file>` (as `demo11\run.py` does with `snap` / `load_snap`).

## After the demo (by area; works, but less than AAA, or later scope)

Every open later list in the handoffs and RESUME's top section was sorted (138 items; raw pull in the Experience 11 scratch, `later_items.txt`). **None is on the gate:** none stops or confuses a first-time player. In flight and staying in Phase 0: UI 29's MR (fingers repaint, one max judge), Classes 21 (warden T4 at 256 seeds, Act 1, the types band, the MR), Lamps build 2 and the Lamps §14 MR.

- **Combat / classes:** tier 1 has no stakes: the autopilot never fell under 93% life across the whole 31-minute Deep Shaw night (`e1_night.log`), as Experience 10 found for the Verge days; the owner's Phase 3 evening is where to feel whether the first night needs a teeth pass. A first table night is 30 minutes before its boss: a pacing call for Phase 3, not a gate. Shield Bash hitstop may be long. Toll has no data beyond `Journey.Day.RiseAgain`.
- **Arena art / env:** the Deep Shaw grade crushes canopy shade to near-black (~20% of frame; `deep_shaw_t1_midnight.jpg`); the table also offers the Gallows Ruts (ruts, not at grade) on day 1, which the scope accepts. Road puddles at Verge day read as slabs; flat charcoal lattice domes, flat signpost planks and bedroll; rooftops can cover her at the town camera (`b_path_36`); the Ford's far treeline and camp dressing; the painted-realism remakes (setts, iron, amber lantern, firs, camp floor).
- **Experience:** day 1's clock waits until a trouble is taken from Rook, so a player who walks past Rook stays at "Dawn, Day 1" (10 minutes observed); with gate item 1 the table needs no night, so this is pacing. The arena opens with the Great Blessing over the entry black, before she has seen the place (`c5_click_pick_01`). The won result's "what you took out" column is empty (known).
- **UI:** the ward buff glyph floats bare; Warden seat fills wash out glyphs; the tracker's "!"; a glyph relief pass; day loot-label flood and a tutorial popup at +1 s; `dg_keeper_check.py` out of date; damage numbers stack "400!" over "40!".
- **VFX:** auto-attacks "not yet effortlessly badass" (the sweep's weight, the Disc's speed); Warden skill later list (slab rock material, a dust wall that reads, Rebuke day flare, barrier shimmer); Long Cut known list (ray-like sweep, no shadow swing, day ash, cast spike p99 +5.6 ms); Road Toll and One Arrow barely show; Burns Twice notes; ember glows on the crowd; the Flare a dark ball at night; the arcanist's staff light (`FindChild("arm:mage_staff")` likely never matches).
- **Rendering:** the crowd-under-lamp list (falloff, dead bodies' floor, material separation, cool fill, her own rim); the Long Cut night seam light and pale b6 fill; brick-red SSS line and forehead bloom in C02/C03; the C02 blue grade flattening him.
- **Animation:** the Long Cut breath beat and f0 pop; death and lunge directions, corpses sinking, frozen walkers; the Ford-Warden's lunge pose and knee stretch.
- **Face / outfits (frozen for the demo):** the skin defaults under cool keys, crown and braid in lit close-ups, inner ear; strap trim, pauldron edges, the cup colour, the reaver cord kinks, the C01 s8 glint and braid tab; the arm routes A-C (waiting on the owner), armor R1/R2 clips and the owner-angle reshoot.
- **Cinematics:** C04 A0 and A8b; the C01/C04 reshoots after the outfit merge; the s6 title card into s8; "THE FORD-WARDEN" labelled before his s11 reveal; C02/C03 framing notes (s1, s2, s7, s11).
- **The Ford-Warden (boss tier, after the demo by scope):** the whole `warden_boss.md` list (beard, lamp fist, capelet, cape cloth, hood, silt, gauntlets, concept judge, Meshy, the six frames).
- **Story / voice:** Act 2 and Act 3 data; the narrator's placeholder take and the stale C04 take; the voice route one character at a time.
- **Owner:** the Burns Twice sound is unheard.

## Phase 2, by area (rough)

- **Experience:** items 1-2 (two tracker lines and their pins) and tools T1-T4: about one session, at medium for the code.
- **Cinematics (storybook):** item 3, one data line plus one replay of the opening: a fraction of a session, with whoever merges the demo build.
- **UI:** the pins and the edge arrow for items 1-2, if Experience can't place them with the existing tracker and minimap: a fraction of a session. Item 4 is Phase 0.
- **Arena art, combat, classes, story, animation:** nothing on the gate.
