# The story explorer

A bot that plays the story through the game's own logic, taking every choice
it can reach, to find what reading the files cannot: softlocks, dead ends,
endings no road reaches, and the story contradicting itself. It complements
`godot/tests/StoryLint.cs`, which reads the story whole without playing it.

Code: `godot/tests/Explorer/` (the engine) and `godot/tests/StoryExplorerTests.cs`
(the tests and the allow-list).

## Running it

```
cd godot/tests
dotnet test                                    # the quick run goes with everything (about 7 s)
dotnet test --filter StoryExplorerTests        # only the explorer's tests
STORY_EXPLORE=full STORY_EXPLORE_OUT=/tmp/explore.md \
  dotnet test --filter The_whole_story         # the whole of it (about half an hour); report to /tmp/explore.md
```

The full run can be tuned with `STORY_STATES` (states expanded per survivor,
default 6000) and `STORY_BEAM` (states kept per layer, default 16).
`STORY_PROBE=N STORY_ROOTS=K dotnet test --filter StoryExplorerTests.Probe`
runs the first K survivors of the full run for N states each and prints what
they reached. Use it when tuning.

Three tests:

- **A quick play of the story finds nothing new** (every `dotnet test`): two
  survivors (warden/hunter/male, arcanist/scholar/female), past the prologue
  the way the game's `--zone` skips it, 220 states each, to day 4. It also
  checks that the bot is still really playing: it must start at least 10
  conversations, reach 60 dialogue nodes and write 15 journal lines.
- **What the explorer reaches is what playing the steps reaches**: the
  explorer takes short cuts (below). This test replays several of its deepest
  states step by step on one live zone and checks that each lands on the same
  journey, so every trace in a report replays.
- **The whole story explored finds nothing new** (`STORY_EXPLORE=full`):
  every calling × every background (sixteen survivors, alternating sex),
  each played through the prologue, 6000 states each, to day 8, with
  softlock confirmation.

### When it fails

The test output lists each new finding with its survivor and its trace, a
numbered list of every step from the start ("Visit: The Last Lamp", "rook.hub:
\"I need a bed.\"", "Sleep at the inn"). Either fix the content, or, if the
finding is how the story is meant to be, add it to `Accepted` in
`StoryExplorerTests.cs` with the reason. A key ending in `*` accepts every
finding that starts with it. The quick run only fails on findings it can be
sure of from a short look: crashes, broken choices, unfilled text, dead ends
and contradictions seen directly. Claims about every road (a softlock, a
gate that can never be met, a thing asked for after it is gone, a
conversation that only goes round) are made only by the full run.

## How it plays

From a new journey (`Journey.Begin` with a calling, background and sex), it
plays the prologue with a survivor nothing can hurt. That survivor goes
where the night's script waits for it, puts down what stands up, and opens
and reads what is there. The quick run skips the prologue the way the
game's `--zone` does. From the Waystation, in every state, it tries:

- **every interactable** the zone offers (`ZoneRuntime.Interactables`, `When`
  holding and `Locked` clear), walking up to it first so whatever notices you
  there notices you. That covers talking, doors, gates, the board, chests,
  cages, the pump and the night's story fights;
- **the zone's named places** not already beside an interactable (the Verge's
  `Approach` triggers: the Hollow, the Roost, the sinkhole);
- **every open choice** in a conversation, through `DialogueRunner`, with the
  game's own handling of `action`s (`GameMenus.Choose` and `DialogueAction`):
  shops, the bed, the stash, the Wayfinder's table, the fortune and the
  services;
- **shops**: buying any story item it does not carry, and selling the
  story's quest items and materials (stock rolled with every chance coming
  up);
- **the bed**: sleep to the next day (to the day cap), or wait for nightfall;
- **arenas**, from the night's story fights, the ember scars, rematches and
  the Wayfinder's first map, both won and lost, through `Arenas.Won` and
  `Arenas.Finish`, then back to where it was pulled from;
- **fights**: each group of creatures in a combat zone (by tag, else by
  family) killed outright with the kill credited (`Battle.KillEnemy`, so the
  zone's `OnKill` and the journey's experience run), their drops picked up;
- **a fall**, through `Journey.Fell` and back to the Waystation as the game does;
- **props**: striking each tagged collider group (`OnHitProp`), and setting
  fire to it when the survivor carries a fire skill (the powder, the
  brambles);
- **the survivor**: picking a trait the story asks about when one is owed;
  wearing or taking off gear whose tags the story asks about.

After each step outside a conversation, the world runs on a few seconds
(`Step`, `Frame` and the host's put-off callbacks) so that fuses burn, people
go where the hour sends them and delayed lines come due. Nothing fights back.

### States, hashing and traces

A state is the journey (character and world, saved), what is open (walking
about, a conversation at a node, a shop, the bed, the table, an arena) and
the zone's own memory: cages opened, camps roused, fires lit, who is out,
what is still alive. The zone's memory is read by reflection over the zone
runtime's fields, its interactables, the lights, the hidden pieces and the
living creatures. States are deduplicated by a hash of all of that. For the
hash, feelings and gold round to the nearest five (the gates ask in fives
and tens), experience counts only as the level, and deeds are a set. The
dialogue nodes already read and the map's fog are left out, since nothing
asks about them.

The search is breadth-first, a layer at a time. When a layer is too wide it
keeps the most promising states (those that reached something nothing had
reached yet, then those furthest into the story). Every state keeps the
step that reached it and its parent, so every finding comes with its whole
road, replayable.

The short cuts that keep it affordable:

- A zone visit is the journey as it arrived plus the steps since. Replaying
  them rebuilds the zone exactly. When a state's zone is found to be as
  fresh as a new visit would make it, the visit begins again there, so the
  replays stay short.
- One built zone is tried many ways: the journey is swapped for a fresh copy
  before each try, and the zone is rebuilt only when a try changed it.
- A conversation or a screen needs no zone: the journey alone, with the
  dialogue runner set at its node.
- The colliders are built once per zone and copied, not built again.

## What it checks

| Kind | What |
|---|---|
| `softlock` | A quest that settles on some road (any survivor) and here stays active at one point in its journal, never moving on anywhere explored from there. A search of its own (400 states, unpruned) must also fail to move it. The prologue not finishing is also a softlock. |
| `deadend` | A line whose choices are all shown locked (Escape only takes an open way out, so the game is stuck). A conversation offered whose every entry condition fails. A stretch of a conversation every choice leads back into, with no way out. |
| `contradiction` | A fact that was `dead` and is something else. Someone dead talked to. A settled quest settled again differently, its outcome rewritten, a journal line taken back out, or the quest vanishing. A purse below zero, a stack of none, a feeling past ±100. A story item asked for (by a locked choice) after it was sold or given up, when nothing explored gets it back. |
| `broken` | A choice that takes a thing the survivor does not have, costs gold they do not have, or tells someone of a deed that has not happened. All are checked on a copy, change by change, as the choice would apply them, and the same goes for the rules due at dawn. Also: a `goto` to a missing node, an `action` the game does not know, a shop on someone with none, a conversation offered that does not exist. |
| `text` | A `{fact:...}` token with no value where it is shown, braces left unfilled, a line with no words. |
| `gate` | A respect or affection gate that can never be met: where the survivor can start (the best background), plus every raise in the content (deeds once each, once-only choices once, anything that can come again unbounded), adds up short. |
| `unseen` | A gate the content could add up to, but no road explored got there. Reported, never failed. |
| `crash` | The game's logic throwing (the chapter's page and the tracker are worked out at every step to catch these). |

## What it cannot do

- **It does not fight.** Fights are won by fiat and never forced on it, and
  arenas are reckoned without being played (a win counts as the full half
  hour survived, a loss as half). A route that is only dangerous, or a
  fight lost where the story expects it won, is not seen. Nemeses are never
  made, because a fall by fiat has no killer to carry anything off.
- **It walks by teleport.** It never wanders past something on the way to
  somewhere else, and only the named places and interactables are visited.
- **It does not use the stash or consumables** (tomes, cures), and does
  not spend attribute points. It only buys and sells story items, and the
  shops always roll their best.
- **Gossip runs on a fixed roll** (0.5): news of a deed told with spread 2
  or more reaches the next person; nothing else does by chance.
- **Days stop at a cap** (4 quick, 8 full), and the search keeps a beam. So
  "not reached" means "not reached by this search", not "unreachable".
  Softlocks, gates and lost items are checked as claims about every road
  only in the full run, and a softlock is confirmed by its own unpruned
  search.
- **The prologue** is played one way (every optional thing opened and read).
  The prologue's script stages are read from `Prologue.Now` to know where to
  go, so a new stage in it will need a line in `Playthrough.Night`.
- **Zones are known by name** in `Playthrough.Make` (lowford, waystation,
  verge), as `Game.Make` knows them. A new zone needs one line there.
- **Act 1 only**, as the content is now.

Everything else is read from the game as it is: interactables, places,
conversations, choices, gates, items, rules and quests. New content is
explored without changes to the explorer.

## Coverage and findings

From the full run on 3 October 2026, on the main branch's content as merged
then (`claude/vigilant-galileo-l6jqyx` at 9d42f0c): sixteen survivors, each
through the prologue, about 28 minutes. **It passes: no softlock, dead end,
contradiction, broken choice, unfilled text, crash or impossible gate.**
The quick run passes too.

### What the numbers mean

"Not reached" means the search did not get there. It does not mean the
story cannot. The long Act 1 routes (the cure, the cages, the ledger, the
Roost's crates, Jory) take forty to a hundred steps of exactly the right
choices. A beam search that tries everything reaches most of them only
partly. Those routes are played end to end by `RouteTests.cs` (B1–B8,
K1–K16, L). The explorer's job is breadth: every choice it can reach, every
check on every state. So read the unreached lists as a map of where the
search ran out, except where a note below says otherwise.

- **Ten conversations nobody plays yet.** `cin_*` (`cin_drowned_fire`,
  `cin_first_light` and the rest) are the cinematics' lines
  (`docs/cinematics/README.md`). Nothing in the game starts them yet, so no
  road reaches them; they account for most of the unreached nodes (148 of
  411). When the cinematics are wired, the explorer will play them wherever
  the game does, with no change to it.
- **`jory`** is only offered once the teamsters are home (the three cages
  opened, or a bluff at the Roost). The explorer opens all three cages when
  it is set there (checked by hand), but in the full run no road combined
  the Roost's crew put down with all three cages in one visit. K1 and K3
  cover it.
- **`dig.pump = running`** is asked about and never written. Harmless: every
  condition that asks for it also accepts the fact being unset, and the code
  treats unset as running.
- **The open threads** `below`, `lamps` and `vault` never resolve in Act 1.
  That is by design (STORY_BIBLE §6 and the chapter's page), so the explorer
  does not call them softlocked: it only calls a quest stuck when it
  settles on some other road.
- `blightward_mask` (Wenna's mask, behind the gate below) and
  `wolfhide_cloak` (Brannoc's cloak, for five pelts and thirty gold) were
  never held.

### Findings and proposed fixes

None fail. Two gates (three choices) were shown and never opened on any road explored,
though the content can add up to them. They are reported as `unseen`, for
the writers to judge:

1. **Wenna's mask** (`wenna.first#5` and `wenna.hub#5`, "That beaked mask on
   the wall...", `data/content/dialogue.json`): affection 20 or more. Best
   seen: 5. Her affection comes from "I brought bitterroot." (+12, three
   roots each time, not once-only; three grow on the green stream per Verge
   visit, only while it is poisoned), and from news of the teamsters freed
   (+10 to everyone who hears it). So the mask takes two bitterroot
   deliveries before the cure, or one and the cages opened. A survivor who
   cures the stream first, and never frees the teamsters, can never earn it.
   **Proposed:** if that is not meant, lower the gate to 12 (one delivery
   opens it), or let `wenna.root` lead to the mask the first time. Replay:
   the run's report below gives the road to where the gate was first shown.
2. **Keegan's supper** (`keegan.hub#7`, "It's late. Have you eaten?"): respect
   30 and affection 15, at night, after `once:dinner`. Best seen: respect
   25, affection 10 (stalker/scholar/female). STORY_BIBLE §11 calls
   Keegan "teased, not opened", an Act 2 route, so out of reach in Act 1 may
   be intended. **Proposed:** if Act 1 should let the most devoted
   survivor in, name the deeds that get her there in WRITING_PASS.md; if
   not, accept it in the allow-list with that reason.

The locked choices never opened (the list in the run's output) are all
explained: Brannoc's and Redcowl's pelt deals want five pelts, which the
search never carried at once (it fights a pack at a time); Redcowl's
"He is not afraid of you" wants his fear; the two gates are the ones above.

### Found while building the explorer, now fixed in it

The first full runs reported things that turned out to be the explorer's,
not the story's. They are fixed, so they do not recur:

- Two caravan "softlocks" were only time not passing far enough in the
  confirming search. The caravan's clock (`caravan.starve`, day 5) moves it
  on. The confirming search now goes far enough to wait.
- A wolf pelt "asked for after it was sold" is renewable. Only quest items
  count as gone now.
- The prologue bot stood at the Watch-post forever: the script moves on only
  once the survivor goes south of it.

## The full run's report

States reached: 639,891 (101,424 expanded, deepest 376 steps), over 16 survivors, in 1665 s.

| Reached | of | |
|---:|---:|---|
| 19 | 30 | Conversations started |
| 263 | 411 | Dialogue nodes reached |
| 531 | 875 | Choices taken |
| 74 | 89 | Journal lines written |
| 5 | 10 | Quest endings reached |
| 3 | 6 | Quests resolved |
| 48 | 81 | Fact values the story asks about, seen |
| 26 | 28 | Story items held |

<details><summary>Conversations started: not reached (11)</summary>

`cin_behind_the_door`, `cin_dig_boils_over`, `cin_drowned_fire`, `cin_first_light`, `cin_forty_one_mouths`, `cin_heart_goes_down`, `cin_iron_marker`, `cin_none_cross`, `cin_raid_on_the_roost`, `cin_road_back`, `jory`

</details>

<details><summary>Dialogue nodes reached: not reached (148)</summary>

`brannoc.cb_wolf_slaughter`, `brannoc.cloak`, `brannoc.irons_after`, `chid.cb_nell`, `chid.cb_nemesis_slain`, `cin_behind_the_door.nondum`, `cin_behind_the_door.redi`, `cin_dig_boils_over.pump`, `cin_dig_boils_over.quiet`, `cin_drowned_fire.bedroll`, `cin_drowned_fire.frost`, `cin_drowned_fire.prints`, `cin_first_light.back`, `cin_first_light.baking`, `cin_first_light.dawn`, `cin_first_light.face`, `cin_forty_one_mouths.them_first`, `cin_heart_goes_down.downstairs`, `cin_heart_goes_down.grateful`, `cin_heart_goes_down.morning`, `cin_heart_goes_down.nobodys`, `cin_iron_marker.verse1`, `cin_iron_marker.verse2`, `cin_none_cross.call`, `cin_none_cross.lie_down`, `cin_none_cross.none`, `cin_raid_on_the_roost.bairns`, `cin_raid_on_the_roost.last`, `cin_road_back.place`, `cin_road_back.wat`, `harlan.ash`, `harlan.cb_jory_knows`, `harlan.cb_sold_dig`, `harlan.jory`, `harlan.jory_now`, `harlan.ledger_early`, `holloway.argued`, `holloway.cb_burned_roost`, `holloway.cb_freed_teamsters`, `holloway.cb_nemesis_slain`, `holloway.cb_tricked_redcowl`, `holloway.defied`, `holloway.ledger_early`, `holloway.ledger_early2`, `holloway.liar`, `holloway.lie`, `holloway.repaid`, `jory.crates`, `jory.first`, `jory.hub`, `jory.salt`, `jory.truth`, `jory.truth_ask`, `jory.truth_knew`, `keegan.say_calling`, `keegan.say_risen`, `keegan.supper`, `keegan.supper_age`, `keegan.supper_ch4`, `keegan.supper_end`, `keegan.supper_hand`, `keegan.supper_letters`, `keegan.supper_read`, `keegan.supper_table`, `keegan.supper_wends`, `maeca.blind`, `maeca.blind2_feet`, `maeca.blind2_let`, `maeca.blind3_m_no`, `maeca.blind3_morning`, `maeca.blind_ask`, `maeca.blind_dark`, `maeca.blind_fire`, `maeca.blind_leave`, `maeca.blind_morning`, `maeca.blind_walk`, `maeca.blood`, `maeca.cb_broke_promise`, `maeca.cb_burned_roost`, `maeca.cb_knelt`, `maeca.invite`, `maeca.say_sella`, `maeca.say_sella_both`, `maeca.say_sella_dunno`, `maeca.say_sella_you`, `maeca.thanks`, `maeca.told_little`, `maeca.told_true`, `maeca.watch_morning`, `maeca.watch_only`, `pell.cb_bribed_snib`, `pell.cb_tricked_redcowl`, `pell.say_woman`, `rav.cb_burned_roost`, `rav.cb_tricked_redcowl`, `rav.leg_held`, `redcowl.ashford`, `redcowl.birds`, `redcowl.crates`, `redcowl.crates_charge`, `redcowl.crates_dig`, `redcowl.crates_keep`, `redcowl.favour`, `redcowl.pell`, `redcowl.pell_given`, `redcowl.pell_hunt`, `redcowl.rav`, `rook.cb_burned_roost`, `rook.cb_freed_teamsters`, `rook.cb_nemesis_slain`, `sella.again`, `sella.cb_burned_roost`, `sella.cb_exposed_pell`, `sella.cb_freed_teamsters`, `sella.cb_tricked_redcowl`, `sella.door`, `sella.door_south`, `sella.door_years`, `sella.free`, `sella.free_ask`, `sella.free_bolt`, `sella.free_decline`, `sella.free_door`, `sella.free_m_downstairs`, `sella.free_m_kiss`, `sella.free_m_who`, `sella.free_morning`, `sella.free_night`, `sella.free_sit`, `sella.free_sleep`, `sella.free_sleep_bed`, `sella.free_stairs`, `sella.free_stop`, `sella.free_want`, `sella.refuse_roost`, `sella.say_keegan`, `sella.say_maeca`, `snib.ember`, `snib.move`, `tam.fetch`, `tam.happy`, `vonnra.risen`, `wayfinder.cb_nemesis_slain`, `wenna.cb_sold_dig`, `wenna.fever`, `wenna.mask`, `wenna.root`, `wenna.tamsays`

</details>

<details><summary>Choices taken: not reached (344)</summary>

`brannoc.cloak#0`, `brannoc.cloak#1`, `brannoc.cloak#2`, `brannoc.cloak#3`, `brannoc.cloak#4`, `brannoc.cloak#5`, `brannoc.cloak#6`, `brannoc.first#1`, `brannoc.first#2`, `brannoc.hub#2`, `brannoc.hub#6`, `brannoc.irons_after#0`, `brannoc.irons_after#1`, `brannoc.nell_gone#1`, `brannoc.nell_slow#0`, `chid.cb_vault2#0`, `chid.first#2`, `chid.lit#1`, `chid.lit#3`, `chid.shrine#1`, `cin_behind_the_door.redi#0`, `cin_dig_boils_over.quiet#0`, `cin_drowned_fire.frost#0`, `cin_first_light.dawn#0`, `cin_forty_one_mouths.them_first#0`, `cin_heart_goes_down.grateful#0`, `cin_iron_marker.verse2#0`, `cin_none_cross.none#0`, `cin_raid_on_the_roost.last#0`, `cin_road_back.wat#0`, `greymuzzle.again#1`, `harlan.ash#0`, `harlan.betrayed#0`, `harlan.betrayed#1`, `harlan.cb_jory_knows#0`, `harlan.cb_jory_knows#1`, `harlan.first#4`, `harlan.first#6`, `harlan.first#7`, `harlan.first#9`, `harlan.hub#10`, `harlan.hub#4`, `harlan.hub#7`, `harlan.jory#0`, `harlan.jory#1`, `harlan.jory_now#0`, `harlan.jory_now#1`, `harlan.ledger_early#0`, `harlan.ledger_early#1`, `harlan.route#0`, `harlan.route#1`, `harlan.what#0`, `holloway.argued#0`, `holloway.argued#1`, `holloway.argued#2`, `holloway.argued#3`, `holloway.argued#4`, `holloway.argued#5`, `holloway.argued#6`, `holloway.argued#7`, `holloway.argued#8`, `holloway.argued#9`, `holloway.arrest#1`, `holloway.caravan2#0`, `holloway.cb_opened_vault#1`, `holloway.defied#0`, `holloway.first#5`, `holloway.first#7`, `holloway.hub#5`, `holloway.hub#7`, `holloway.ledger_early#0`, `holloway.ledger_early2#0`, `holloway.ledger_early2#1`, `holloway.liar#0`, `holloway.liar#1`, `holloway.liar#2`, `holloway.lie#0`, `holloway.maeca#1`, `holloway.post2#0`, `holloway.repaid#0`, `holloway.repaid#1`, `holloway.repaid#2`, `holloway.repaid#3`, `holloway.repaid#4`, `holloway.repaid#5`, `holloway.repaid#6`, `holloway.repaid#7`, `holloway.repaid#8`, `holloway.repaid#9`, `jory.crates#0`, `jory.crates#1`, `jory.crates#2`, `jory.first#0`, `jory.first#1`, `jory.hub#0`, `jory.hub#1`, `jory.salt#0`, `jory.truth#0`, `jory.truth#1`, `jory.truth_ask#0`, `jory.truth_knew#0`, `keegan.ch4#0`, `keegan.ch4#1`, `keegan.hub#7`, `keegan.say_risen#0`, `keegan.supper_age#0`, `keegan.supper_age#1`, `keegan.supper_age#2`, `keegan.supper_age#3`, `keegan.supper_age#4`, `keegan.supper_age#5`, `keegan.supper_age#6`, `keegan.supper_ch4#0`, `keegan.supper_ch4#1`, `keegan.supper_ch4#2`, `keegan.supper_ch4#3`, `keegan.supper_ch4#4`, `keegan.supper_ch4#5`, `keegan.supper_ch4#6`, `keegan.supper_end#0`, `keegan.supper_hand#0`, `keegan.supper_letters#0`, `keegan.supper_letters#1`, `keegan.supper_letters#2`, `keegan.supper_letters#3`, `keegan.supper_letters#4`, `keegan.supper_letters#5`, `keegan.supper_letters#6`, `keegan.supper_read#0`, `keegan.supper_read#1`, `keegan.supper_read#2`, `keegan.supper_read#3`, `keegan.supper_read#4`, `keegan.supper_read#5`, `keegan.supper_read#6`, `keegan.supper_table#0`, `keegan.supper_table#1`, `keegan.supper_table#2`, `keegan.supper_table#3`, `keegan.supper_table#4`, `keegan.supper_table#5`, `keegan.supper_table#6`, `keegan.supper_wends#0`, `keegan.supper_wends#1`, `keegan.supper_wends#2`, `keegan.supper_wends#3`, `keegan.supper_wends#4`, `keegan.supper_wends#5`, `keegan.supper_wends#6`, `keegan.who#1`, `maeca.blind3_m_no#0`, `maeca.blind3_morning#0`, `maeca.blind3_morning#1`, `maeca.blind_ask#0`, `maeca.blind_ask#1`, `maeca.blind_ask#2`, `maeca.blind_ask#3`, `maeca.blind_dark#0`, `maeca.blind_dark#1`, `maeca.blind_dark#2`, `maeca.blind_dark#3`, `maeca.blind_dark#4`, `maeca.blind_dark#5`, `maeca.blind_dark#6`, `maeca.blind_dark#7`, `maeca.blind_leave#0`, `maeca.blind_morning#0`, `maeca.blood#0`, `maeca.cb_broke_promise#0`, `maeca.cold#0`, `maeca.driving#1`, `maeca.gone#0`, `maeca.hub#10`, `maeca.hub#7`, `maeca.hub#8`, `maeca.invite#0`, `maeca.invite#1`, `maeca.invite#2`, `maeca.say_sella#0`, `maeca.say_sella#1`, `maeca.say_sella#2`, `maeca.say_sella#3`, `maeca.signed#0`, `maeca.thanks#0`, `maeca.watch_morning#0`, `pell.ally#1`, `pell.books2#0`, `pell.caravan#0`, `pell.caravan#1`, `pell.hub#1`, `pell.hub#2`, `pell.hub#7`, `pell.smell#0`, `pell.smell#1`, `pell.smell#2`, `rav.back_room_end#0`, `rav.cb_killed_redcowl#0`, `rav.leg_held#0`, `redcowl.ashford#0`, `redcowl.ashford#1`, `redcowl.birds#0`, `redcowl.birds#1`, `redcowl.crates#0`, `redcowl.crates#1`, `redcowl.crates_charge#0`, `redcowl.crates_dig#0`, `redcowl.crates_dig#1`, `redcowl.crates_keep#0`, `redcowl.crates_keep#1`, `redcowl.favour#0`, `redcowl.favour#1`, `redcowl.first#0`, `redcowl.first#4`, `redcowl.first#6`, `redcowl.goods#1`, `redcowl.goods#2`, `redcowl.goods#3`, `redcowl.goods#4`, `redcowl.hub#0`, `redcowl.hub#1`, `redcowl.hub#2`, `redcowl.hub#3`, `redcowl.hub#4`, `redcowl.hub#5`, `redcowl.hub#6`, `redcowl.hub#8`, `redcowl.hub#9`, `redcowl.pell#0`, `redcowl.pell#1`, `redcowl.pell_given#0`, `redcowl.pell_hunt#0`, `redcowl.prisoners#1`, `redcowl.rav#0`, `redcowl.rav#1`, `redcowl.rav#2`, `rook.clerk#0`, `rook.first#7`, `rook.hub#8`, `rook.runs#0`, `rook.runs#1`, `rook.town#1`, `rook.wanted#1`, `rook.wanted#7`, `sella.again#0`, `sella.again#1`, `sella.again#2`, `sella.again#3`, `sella.again#4`, `sella.again#5`, `sella.door#0`, `sella.door#1`, `sella.door#2`, `sella.door_south#0`, `sella.door_years#0`, `sella.door_years#1`, `sella.first#3`, `sella.free#0`, `sella.free#1`, `sella.free_decline#0`, `sella.free_door#0`, `sella.free_door#1`, `sella.free_door#2`, `sella.free_door#3`, `sella.free_m_downstairs#0`, `sella.free_m_kiss#0`, `sella.free_m_who#0`, `sella.free_morning#0`, `sella.free_morning#1`, `sella.free_morning#2`, `sella.free_morning#3`, `sella.free_sit#0`, `sella.hub#5`, `sella.morning#2`, `sella.price#1`, `sella.refuse_roost#0`, `sella.rest_morning#2`, `sella.rest_night_paid#0`, `sella.stairs_rules#1`, `snib.bribe#1`, `snib.ember#0`, `snib.first#1`, `snib.first#2`, `snib.first#4`, `snib.hub#0`, `snib.hub#2`, `snib.hub#6`, `snib.hub#7`, `snib.move#0`, `snib.poison#0`, `snib.what#0`, `tam.again#1`, `tam.cb_killed_greymuzzle#1`, `tam.fetch#0`, `tam.happy#0`, `tam.happy#1`, `vonnra.arcana#0`, `vonnra.arcana#3`, `vonnra.cb_vault3#0`, `vonnra.first#6`, `vonnra.ford#0`, `vonnra.ford#4`, `vonnra.hub#0`, `vonnra.ledger_read#0`, `vonnra.ledger_read#1`, `vonnra.ledger_read#7`, `vonnra.paid#0`, `vonnra.paid#1`, `vonnra.paid#2`, `vonnra.paid#3`, `vonnra.paid#4`, `vonnra.paid#5`, `vonnra.paid#6`, `vonnra.paid#7`, `vonnra.vault#0`, `vonnra.vault#2`, `vonnra.vault#6`, `wayfinder.first#4`, `wayfinder.hub#7`, `wayfinder.oaths#0`, `wayfinder.oaths#2`, `wayfinder.places#0`, `wayfinder.places#1`, `wayfinder.places#2`, `wenna.animals#0`, `wenna.animals#1`, `wenna.fever#0`, `wenna.fever#1`, `wenna.first#1`, `wenna.first#4`, `wenna.first#5`, `wenna.first#6`, `wenna.hub#1`, `wenna.hub#2`, `wenna.hub#3`, `wenna.hub#4`, `wenna.hub#5`, `wenna.hub#6`, `wenna.mask#0`, `wenna.mask#1`, `wenna.root#0`, `wenna.root#1`, `wenna.tamsays#0`, `wenna.tamsays#1`, `wenna.who#0`

</details>

<details><summary>Journal lines written: not reached (15)</summary>

`beasts/pack_led`, `beasts/pump_broken`, `beasts/redcowl_charge`, `beasts/told_holloway`, `caravan/cargo_kept`, `caravan/cargo_lost`, `caravan/cargo_moved`, `caravan/crates_redcowl`, `caravan/crates_sunk`, `caravan/jory_salt`, `caravan/jory_told`, `caravan/ledger_read`, `caravan/pell_given`, `caravan/pell_hunted`, `caravan/survivors_freed`

</details>

<details><summary>Quest endings reached: not reached (5)</summary>

`beasts:cured`, `beasts:exploited`, `beasts:slaughtered`, `caravan:lost`, `caravan:with_kerchiefs`

</details>

<details><summary>Quests resolved: not reached (3)</summary>

`below:Resolved`, `lamps:Resolved`, `vault:Resolved`

</details>

<details><summary>Fact values the story asks about, seen: not reached (33)</summary>

`aldo.buried=true`, `be.crates=burned`, `be.crates=dig`, `be.crates=redcowl`, `be.crates=sunk`, `beasts.outcome=cured`, `beasts.outcome=exploited`, `beasts.outcome=slaughtered`, `beasts.told_holloway=true`, `caravan.cargo=kept`, `caravan.cargo=with_kerchiefs`, `caravan.pell=fled`, `caravan.survivors=rescued`, `dig.pell_cut=true`, `dig.pump=broken`, `dig.pump=running`, `holloway.lied_to=true`, `jory.knows_be=true`, `keegan.supper=true`, `maeca.lover=true`, `nell.buried=true`, `pell.fate=ran`, `pell.fate=taken`, `player.pardoned=true`, `redcowl.ashford_said=true`, `redcowl.last_words=leg`, `sella.free=true`, `sella.free_declined=true`, `sella.told_knowing=true`, `settings.intimacy=full`, `stream.clear=true`, `tam.farm=emptied`, `tam.pa_in=true`

</details>

<details><summary>Story items held: not reached (2)</summary>

`blightward_mask`, `wolfhide_cloak`

</details>

<details><summary>Choices shown locked and never opened (7)</summary>

- `brannoc.first#1`: You have no pelts
- `brannoc.first#2`: Five pelts and thirty gold
- `keegan.hub#7`: She is on duty. She is always on duty.
- `redcowl.goods#1`: Five wolf pelts
- `redcowl.goods#2`: He is not afraid of you
- `wenna.first#5`: She does not know you well enough
- `wenna.hub#5`: She does not know you well enough

</details>

### Findings, as the run printed them

#### `unseen:keegan.hub#7`

"It's late. Have you eaten?" asks keegan respect >= 30 (best seen 25), keegan affection >= 15 (best seen 10), and no road explored got there. File: `data/content/dialogue.json`. Survivor: stalker/scholar/female.

<details><summary>Replay</summary>

```
1. Travel: The Old Road (waystation)
2. Examine: An Iron Pipe (verge)
3. Take: The Coyle Strongbox (verge)
4. Fight and win: redcowl (verge)
5. Fill a bottle: The Green Water (verge)
6. Search: The Coyle Wagons (verge)
7. Examine: A Dead Wolf (verge)
8. Examine: The Sealed Door (verge)
9. Walk to sinkhole (verge)
10. Travel: The Waystation (verge)
11. Read: Notice Board (waystation)
12. board.read: "Step back."
13. Visit: Coyle Trading Post (waystation)
14. harlan.first: "What were you carrying, besides salt and cloth?"
15. harlan.be: "Something else."
16. harlan.hub: "Your six crates are still in the Roost."
17. harlan.crates: "Something else."
18. harlan.hub: "I found your strongbox."
19. harlan.box: "Goodbye."
20. Open: An old trunk (waystation)
21. Visit: Brannoc's Smithy (waystation)
22. brannoc.first: "This was in the Warden's fist at the Low Ford."
23. brannoc.mark: "Goodbye."
24. Visit: Wenna's House (waystation)
25. wenna.first: "I brought you water from the stream."
26. wenna.analyse: "Who would do that?"
27. wenna.who: "Goodbye."
28. Talk: Maeca Barefoot (waystation)
29. maeca.first: "Can the Pack be spoken to?"
30. maeca.speak: "Goodbye."
31. Visit: The Last Lamp (waystation)
32. rook.first: "What's the talk?"
33. rook.rumours: "Something else."
34. rook.hub: "I need a bed."
35. Wait for nightfall
36. Travel: The Old Road (waystation)
37. Walk to hollow (verge)
38. Approach: Greymuzzle (verge)
39. greymuzzle.first: "Kneel, and hold out an empty hand."
40. greymuzzle.show: ""The men in the ravine are no friends of yours. Run with me.""
41. greymuzzle.ally: "Go."
42. Search: Bones (verge)
43. Set the sigil in the door: The Sealed Door (verge)
44. Win the arena: Behind the Sealed Door
45. Examine: Wheel Ruts (verge)
46. Step into the ember: The Scar at the Sealed Door (verge)
47. Win the arena: The Scar at the Sealed Door
48. Look at: The Ground (verge)
49. Walk to hollow (verge)
50. Fight and win: greymuzzle (verge)
51. Walk to sinkhole (verge)
52. Talk: A Lampling (verge)
53. survivor.first: "What moved?"
54. survivor.what: "Leave."
55. Travel: The Waystation (verge)
56. Visit: Watch House (waystation)
57. holloway.first: "Harlan Coyle's caravan. What do you know?"
58. holloway.caravan: "Something else."
59. holloway.hub: "Your watch-post on the Low Ford road. There's a dead man at it."
60. holloway.post: "Something else."
61. holloway.hub: "I've come about the bounty."
62. holloway.bounty: "Hand over the fang."
63. holloway.hub: "That's all."
64. Visit: The Crooked Flagon (waystation)
65. rav.first: "Did anyone come through with news of Coyle's caravan?"
66. rav.clerk: "Goodbye."
67. Choose a map: The Wayfinder's Table (waystation)
68. Take the Wayfinder's first map, and win
69. Visit: The Toll Tower (waystation)
70. vonnra.first: "The sealed door in the Verge..."
71. vonnra.vault: "Did Coyle's caravan pay your toll?"
72. vonnra.ledger: "Pay five gold to see the ledger."
73. vonnra.ledger_read: "Your clerk. Jessop. Where is he?"
74. vonnra.jessop: "Something else..."
75. vonnra.hub: "That coin on the cord at your throat?"
76. vonnra.coin: "Goodbye."
77. Visit: Brannoc's Smithy (waystation)
78. brannoc.cb_killed_greymuzzle: (continue)
79. brannoc.hub: "I've wolf pelts to sell."
80. brannoc.hub: "Goodbye."
81. Visit: Shrine of the Morning Light (waystation)
82. chid.first: "There's a sealed door in the Verge."
83. chid.vault: "Goodbye."
84. Visit: The Last Lamp (waystation)
85. rook.cb_opened_vault: (continue)
86. rook.hub: "There's a grave in the garden behind the shrine. A captain, with his lamp."
87. rook.firstlamp: "Something else."
88. rook.hub: "I need a bed."
89. Sleep at the inn (5 gold): day 2 dawns
90. Talk: Tam (waystation)
91. tam.first: "I'm listening."
92. tam.story: "You did right to tell someone."
93. tam.again: "Anything else strange out at the farm?"
94. tam.tock: "Stay by the well, Tam."
95. Visit: Brannoc's Smithy (waystation)
96. brannoc.nell: "I passed nobody on that road."
97. brannoc.nell_lie: "Goodbye, Brannoc."
98. Choose a map: The Wayfinder's Table (waystation)
99. Take the Wayfinder's first map, and win
100. Talk: Sella (waystation)
101. sella.first: "What do you hear, up there?"
102. sella.hear: "Not tonight."
103. Visit: Coyle Trading Post (waystation)
104. harlan.cb_killed_greymuzzle: (continue)
105. harlan.hub: "I've seen your wagons. The Kerchiefs have them in a ravine off the Old Road, and three men in cages."
106. harlan.roost: "Something else."
107. harlan.hub: "It wasn't wolves. Your wagons were driven off the road."
108. harlan.notwolves: "Something else."
109. harlan.hub: "How did Jory come to drive for you?"
110. harlan.t_harlan: "Goodbye."
111. Visit: The Last Lamp (waystation)
112. rook.say_calling: (continue)
113. rook.hub: "I need a bed."
114. Sleep at the inn (5 gold): day 3 dawns
115. Choose a map: The Wayfinder's Table (waystation)
116. Take the Wayfinder's first map, and win
117. Talk: Dame Keegan Orme (waystation)
118. keegan.first: "The Ford-Warden. The Watch's lamps were feeding it."
119. keegan.warden: "Who'd want it awake?"
120. keegan.who: "Something else."
121. keegan.hub: "The children call you "Professor"."
122. keegan.prof: "Something else."
123. keegan.hub: "Captain Ashe is buried in the garden. Did the Vigil know him?"
124. keegan.ashe: "Something else."
125. keegan.hub: "Your Vigil. Where are the rest of you?"
126. keegan.vigil: "Something else."
127. keegan.hub: "How will you know when I'm ready?"
128. keegan.ready: "Something else."
129. keegan.hub: "Does the handbook say anything about dinner?"
130. keegan.dinner: "Goodbye."
131. Visit: The Last Lamp (waystation)
132. rook.say_woman: (continue)
133. rook.hub: "I need a bed."
134. Sleep at the inn (5 gold): day 4 dawns
135. Choose a map: The Wayfinder's Table (waystation)
136. Take the Wayfinder's first map, and win
137. Visit: The Last Lamp (waystation)
138. rook.hub: "I need a bed."
139. Sleep at the inn (5 gold): day 5 dawns
140. Choose a map: The Wayfinder's Table (waystation)
141. Take the Wayfinder's first map, and win
142. Visit: The Last Lamp (waystation)
143. rook.hub: "I need a bed."
144. Sleep at the inn (5 gold): day 6 dawns
145. Choose a map: The Wayfinder's Table (waystation)
146. Take the Wayfinder's first map, and win
147. Visit: The Last Lamp (waystation)
148. rook.hub: "I need a bed."
149. Sleep at the inn (5 gold): day 7 dawns
150. Choose a map: The Wayfinder's Table (waystation)
151. Take the Wayfinder's first map, and win
152. Visit: The Last Lamp (waystation)
153. rook.hub: "I need a bed."
154. Sleep at the inn (5 gold): day 8 dawns
155. Choose a map: The Wayfinder's Table (waystation)
156. Take the Wayfinder's first map, and win
157. Visit: The Last Lamp (waystation)
158. rook.hub: "Who else has come up the Low Ford road?"
159. rook.ford: "What did she say?"
160. rook.ford2: "Something else."
161. rook.hub: "I need a bed."
162. Wait for nightfall
163. Talk: Dame Keegan Orme (waystation)
164. keegan.cb_opened_vault: (continue)
```

</details>

#### `unseen:wenna.first#5`

"That beaked mask on the wall..." asks wenna affection >= 20 (best seen 5), and no road explored got there. File: `data/content/dialogue.json`. Survivor: warden/hunter/female.

<details><summary>Replay</summary>

```
1. Visit: Wenna's House (waystation)
```

</details>

#### `unseen:wenna.hub#5`

"That beaked mask on the wall..." asks wenna affection >= 20 (best seen 5), and no road explored got there. File: `data/content/dialogue.json`. Survivor: warden/hunter/female.

<details><summary>Replay</summary>

```
1. Travel: The Old Road (waystation)
2. Take: The Coyle Strongbox (verge)
3. Fight and win: redcowl (verge)
4. Fight and win: roost (verge)
5. Examine: An Iron Pipe (verge)
6. Fill a bottle: The Green Water (verge)
7. Search: The Coyle Wagons (verge)
8. Examine: A Dead Wolf (verge)
9. Search: Bones (verge)
10. Walk to sinkhole (verge)
11. Travel: The Waystation (verge)
12. Read: Notice Board (waystation)
13. board.read: "Step back."
14. Visit: Wenna's House (waystation)
15. wenna.first: "I brought you water from the stream."
16. wenna.analyse: "Something else."
```

</details>

