# The den: what a player cannot read today (GAME_PLAN task 7, 22 November 2026)

Package P5, lead agent-a730ef56e5a3de866, branch `look-target` (on the integration head 0c62da9bb). Paper only: nothing here changes the game.

**Sources.**
- The owner's 19 demo notes (19 Nov), word for word, in `survivorsunchained_inputs\scratch_coord15\briefs\K_demo_notes.md`.
- What lane K said it did: `docs/handoff/demo_feel.md`.
- The tooltip data: `godot/data/content/skill_tips.json` and `skills.json`.
- The telegraph data: `telegraphs.json`, and the approved roster in `docs/design/DEN_ROSTER.md`.
- Game-camera films and frames of the den, shot for this page (section 4).

**How each item was checked.**
- Every commit the handoff names is in the build: 33 of 33 pass `git merge-base --is-ancestor`.
- One filtered test run covered the 14 test classes cited below: 118 passed, 0 failed.
- The check was done by su-worker ac2c66f7bd13b5e92; its raw tables are in `survivorsunchained_inputs\scratch_look\clarity_worker_ac2c66f7.md`.
- "Shipped" requires a test or a measured number. Where neither exists, the entry is marked **shipped, no proof**, with the frame that would prove it.
- An item that the build cannot settle becomes a yes/no question for the owner (section 6). It is not guessed into the open list.

## 1. The owner's 19 notes against the current build

| # | Note (short) | State | Evidence | In the den? |
|---|---|---|---|---|
| 1 | Den load "painfully long" | shipped | c9455ed98. Measured: Verge to den, click to control, 92.44 s down to 5.01 s; cold boot to the den 61.2 s down to 9.1 s. No test | yes |
| 2 | Slow opening, create, begin journey | partly | Create 0.07/0.12 s. Begin journey 3.08/2.72 s. Boot card done at 21.4/14.8 s (cold/warm). Not done: the title's own build (Lowford about 4.9 s, first render about 3 s) | no |
| 3 | Hitches (wagon, town, Space, Flare, sound crackle) | partly | Dash hitches gone (0 of 7 slow). Flare press is still 27 ms. Still open: 45-55 ms BattleFx spikes and a GC pause about every 2.6 s. Town lag and the crackle at load were never traced | dash and Flare yes |
| 4 | Dash direction "bizarre" | shipped, no proof | 085ff4e91 (FacePointer: the dash goes to the cursor). No test, no number | yes |
| 5 | Bladestorm: WASD, no target, sound runs on | partly | WardenPressedTests.cs:234 (spins with no foe and steers to the cursor). ResolveTests.cs:149 (Resolve floor 4, above the 3.6 start). The sound stop has no test | yes |
| 6 | Trees and corners block her | partly | ZoneWoodTests.cs:8 (orphan colliders dropped). Not done: trunk-size collision, the named corners | no |
| 7 | Movement not "buttery smooth" | open | Diagnosed on paper only; the fixes are package P2 (tasks 3-5) | yes |
| 8 | Vial refills on kills | shipped | DraughtKillFillTests.cs:31, :42. The fill points are not saved | yes |
| 9 | Flare by day | shipped | PrologueFlareLentTests.cs:135. The town still refuses it | yes |
| 10 | Warden's channel unclear | shipped | WardenFightTests.cs:66, :86. Not checked in the exe | no (Low Ford) |
| 11, 16 | Foes that block forever | shipped | PrologueArpgTeachTests.cs:276; IronboundTests.cs:39, :58 (three blows turned, then cracked 4.5 s). Not checked in the exe | yes (Ironbound champions) |
| 12 | Wallow boars hard to find | shipped | EncountersTests.cs:209 | no |
| 13 | Equip and pick-up sounds bad | open | Handed to the sound lane; needs new recorded sources | yes |
| 14 | "No idea how to light my lamps" | partly | LampsTeachTests.cs:25 (the "Lamp ready" prompt). Lighting out of a fight is in code but untested. **Nothing shows what a lit lamp changes** | yes |
| 15 | Death throws her out of the den | shipped | MapTests.cs:183 | yes |
| 17 | Heroic Leap should clear charges | shipped | LeapDodgesChargesTests.cs:35 | yes |
| 18 | Boars bark too often | shipped | BoarVoiceTests.cs:37, :49 (a 30 s pack went from 23 voices to 9) | yes |
| 19 | Minimap keeps the last den | shipped | MapTests.cs:216 | yes |

## 2. Tooltips: what the keys do not say

Tooltips come from `skill_tips.json` (built by `logic/Rpg/SkillTipModel.cs`). When a skill has no entry there, the first sentence of its `skills.json` description is used instead (SkillTipModel.cs:106). The slice's Warden (`taught_builds.json`) has:
- pressed skills: Sunder (key 1), Heroic Leap (key 2, level 4), Bladestorm (key 3, level 5) and Shield Charge (key 4, level 9);
- kindled: Groundbreaker, Iron Vow and Watch Bell;
- also: Dawnpulse (an offer) and Falling Wall (the level 15 union).

| Missing or unclear | Why it matters |
|---|---|
| **Flare has no skill card.** Its only player text is in `Boons.cs:334-340` | The signature move, and nothing tells the player what the key does |
| **The dash has no card or tip** | The owner: "I don't know hwo to target my dash directioni" |
| **Bladestorm's line is incomplete.** It does not say that the spin needs Resolve to start, that it steers to the cursor, or that it works with no foe | The owner: "i actually don't know how bladestorm works.  is it the power that charges in the hair?" |
| **The kindled lines contradict each other.** Groundbreaker, Iron Vow and Watch Bell say "Lights up ...: press it", while Dawnpulse says "Fires itself" | The player cannot tell auto from pressed. Round 9 (BUILD_DIRECTION) moves autos to a node or support, so these lines are rewritten with P4's skill page anyway |
| What a lit lamp does (item 14) | The lamps' own tips were not checked here |

## 3. Telegraphs: den moves with no shared tell

`telegraphs.json` holds four shared kinds: ring, charge, pull and closing. The table below joins that file with the approved roster's "its own attacks, telegraph" column (`DEN_ROSTER.md` section 1).

| Den move | Tell today |
|---|---|
| The kit charge (wolf, runner, boar) and the Pack-Mother's Drive | `charge` (shared) |
| Runner lunge 7 m, alpha lunge 9 m, Whitethroat lunge 8 m, boar charge 10 m, Old Tusk's three charges | Their own line, with a 0.6-1.1 s windup (roster column). Not one of the shared kinds |
| Wolf and alpha contact bite | None, by design (the roster: "no tell") |
| Blighted death burst (0.5 s fuse), slurry poison trail, the Blight Mother's trail, split and burst | No tell found in either source. **Needs a frame** (section 4) |
| Howler haste howl (9 m ring, every 8 s) | No ring mark found; it is not the shared `ring`. **Needs a frame** |
| The re-cut's new moves: Ironback slam (1.3 s windup), blighted lob (0.6 s aim), Whitethroat's Yip | No entry yet. They belong to P3, and P3 should give each one its tell when it builds them |

## 4. What the game-camera films show

(Filled from the den films shot for this page: see the paths below.)

## 5. The open list, ordered for M2

(Written after section 4.)

## 6. Yes/no questions for the owner

1. The den now loads in about 5 s from the Verge (it was 92 s). Is that still too long? (An unbuilt option, building the den ahead while in the Verge, would cut about 1.5 s more.)
2. Is "the power that charges in the hair" her Resolve? Should Resolve show on her, as well as on the HUD?
3. Should the Flare work in town? (Today the town refuses it.)
4. Are the equip and pick-up sounds wanted before the demo? (Item 13 needs newly recorded sources.)
