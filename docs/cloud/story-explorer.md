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

(Filled in from the full run below.)
