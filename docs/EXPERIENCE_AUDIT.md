# The experience audit (draft one)

What holds Survivor Unchained back from the best of its genre, as a player lives it. Ranked
by how much each thing costs in feel and in keeping a player. **Draft one:** stopped at the owner's
usage limit, before the boss and the endless phase were seen on screen. Those, the plan's briefs,
and a clean measure of frame times come next (see `docs/team/experience.md`).

## How it was played

- **On screen, at 1920×1080:** the title; creation; the prologue on the game's autopilot,
  `--auto` (four minutes, the Ford-Warden, the dawn); the Waystation by day; every hub screen;
  the draft; the result; 25 minutes of a tier-1 arena (the Risen), with a frame every 30 s.
  Evidence frames are in `docs/experience/`.
- **In numbers:** the balance harness (`godot/balance`), with these sweeps:
  - 64 arenas, plain bot, greedy and random, all four callings, tiers 1–2 at their level, the
    table's oaths, up to an hour past the win;
  - the same 64 after the pacing change;
  - 64 more at tiers 3–4;
  - the horde benchmark.
- **Caveat:** the GPU was shared at 100% (ComfyUI, the voice placeholders, two other agents'
  game windows), so frame times are not yet trustworthy.

## The ten findings, ranked

### 1. The night has no shape (pacing): partly fixed

- **Evidence:**
  - The horde grew in a straight line, from 40 to 217.
  - The four turns came round in a fixed order every 60–85 s.
  - The stretch before the boss was the second easiest of the night: only 2–9% of runs dipped
    below half health there.
  - In the arena on autopilot, the warden at tier 1 lost no health in 25 minutes (212/212 to
    minute 20). The plain bot wins 94% at tiers 1–2.
- **Against the best:** Vampire Survivors swings its crowd tenfold within minutes. Halls of
  Torment and Risk of Rain build towards their bosses.
- **Done (`ArenaPacing.cs`):**
  - a sawtooth into 10, 20 and 28;
  - a breather after each turn;
  - the herald as a duel on a thinned field, then a flood;
  - a hush before the boss;
  - no turn twice running;
  - a chest in every three turns;
  - each people's own question at 6, 17 and 26 minutes, with a tell first.

  Win rate and ember are unchanged (94%, ember 53). The field now swings as designed (171 alive
  into the herald, 225 in the long push, 126 in the hush).
- **Still wrong:** more creatures did not mean more danger (0% dipped below half in the long
  push), because fodder dies in 0.1 s. Combat's charge director now spikes while
  `pacing.Building` holds and calms in breathers. Re-measure together.

### 2. The run's best moments land flat (feel)

- **Evidence:**
  - A chest opens on touch into one line of text (`ArenaRun.OnPickup`).
  - An evolution is a nova, a flash and 0.3 trauma.
  - The boss's death is a 140 ms hit-stop, the same order as one heavy blow.
- **Not built:** none of the earlier feel study's tier-one suggestions exist in the code
  (`docs/feel/SUGGESTIONS.md` S-02 to S-10, checked):
  - XP ladder;
  - ducking;
  - level-up resolution;
  - dash buffer;
  - flowing bars;
  - particle priority;
  - multi-kill swell;
  - the chest sequence;
  - the evolution ceremony.

  There is no rumble.
- **Against the best:** Vampire Survivors' chest pauses, spins, plays its own music and pays one,
  three or five. That is the genre's best-known dopamine beat.

### 3. You can't see her (readability)

- **In the arena** the heroine is a speck at 31 m, recognisable only by her red hair
  (`arena_lost_in_the_disc.jpg`):
  - opaque, flat, lime-green ground effects swallow her;
  - the dead lie in heaps the same colour as the living;
  - bursting dead throw primitive spheres and cylinders (`Gore.cs`) that litter the field like
    eggs and chalk;
  - a crypt block hides the herald's fight.
- **In the prologue** giant tree canopies cover her (`prologue_trees.jpg`).
- **In the hub** the camera sits behind roofs, and the cut-away tunnel reveals a wall
  (`hub_roofs.jpg`).
- **The owner's centrepiece** is the hardest thing on screen to find.

### 4. Onboarding: two levels at once, words on words

- **Two levels at once:** a minute into the prologue, the ember is level 4 and drafting while a
  banner says "LEVEL 3 – a new trait can be chosen (C)". That is the character level, paid per
  kill outside arenas (`Journey.Killed`), so two levelling systems teach themselves at once
  (`prologue_two_levels.jpg`).
- **Words on words:**
  - the Ford-Warden's two barks print over each other (`prologue_barks_overlap.jpg`);
  - "blocked" words stack;
  - the chest and the dead watchman share one spot, so the prompt read the book again and again
    (the autopilot looped there).
- **What works:** the tutorial cards (Move, Dash, the road north, By day) teach in play; the
  prologue is about four minutes on autopilot.
- **No threat:** the first two minutes of the prologue never touched the autopilot.

### 5. The hub loop: what a night pays, and why go back

- **What a night pays:**
  - the result is two text lists (`result_screen.jpg`);
  - gear comes from a list of nine plain items (`ArenaRun.PlainGear`);
  - a tome from a table win only 35% of the time;
  - XP for time survived.
- **The run select:** the Wayfinder's table is three small text cards with no stated reward
  (`table_cards.jpg`).
- **Run length:** every arena is 30 minutes, whether a story night, a table map or an ember
  scar.
- **Reactivity:** the town says one line about your nights (the Wayfinder's, keyed to
  `arena.won`). Hades' house reacts to every run.
- **Pausing:** full pages pause the world everywhere (`GameMenus.cs` sets `SimPaused`). The
  owner's decision is to pause only in arena combat.

### 6. Choice is expression, not survival, below tier 4

- **Survival:** a random drafter wins as often as a greedy one: 91–94% against 94–97% at tiers
  1–2, and 88% against 88% at tier 3. Only at tier 4 does the plain bot fall (62–69%).
- **Expression:** choice changes the build's shape. Evolutions are 4–5 for greedy against 2–3
  for random, and boss time to kill 70–79 s against 82–101 s.
- **Cards:** 76 a night, six in the first minute.
- **Against the best:** Brotato's and Hades' choices decide whether you live by the mid game.

### 7. Moment-to-moment variety

- **Turns:** four generic turns until now. There are no "treasure goblin" or other surprises.
- **Arenas:** they read as one flat field of mud and lilac stone with a few props, whatever their
  name (`arena_empty_start.jpg`). "The Ashen Fen" looks like no fen.
- **The first minute:** nearly empty. The autopilot had 0 kills at 30 s and 3 at 60 s; the horde
  spawns 24–29 m out.

### 8. Long-term goals and replay

- **What exists:** tiers, oaths sworn by the table, the codex, "longest night" and the endless
  phase (combat: truly endless, with the dark's oaths and the boss returning).
- **No player-chosen difficulty ladder:** nothing like Hades' Pact of Punishment, Brotato's
  danger levels or Dead Cells' boss cells.
- **No account-level unlocks or quests:** nothing like Halls of Torment's hundreds of quests or
  Vampire Survivors' unlocks.

### 9. Sound and music (read from code; not heard)

- **The score** is synthesised as it plays: pads, a plucked line and a frame drum
  (`Music.cs`). The best of the genre are known by their scores.
- **The sound effects** are layered Kenney recordings and synthesis. The feel study's sound items
  are unbuilt.

### 10. Performance (to re-measure)

- **The simulation is cheap:** 0.63 ms a tick at a horde of 300, 1.75 ms at 900.
- **Frames:**
  - 10–20 ms in the arena, with spikes of 37 ms and 136 ms;
  - 23–26 ms in the Waystation with nothing fighting;
  - about 25 s from launch to the first frame.

  All of these were measured under GPU contention.

## The plan (draft one)

| # | Item | Owner | State |
|---|---|---|---|
| 1 | The night's shape: sawtooth, breathers, herald duel and flood, the hush, the people's own questions | experience | **done** (`ArenaPacing.cs`) |
| 1b | The danger rising with the shape: charge spikes in build-ups, calm in breathers | combat | **done** by combat (`e9e591d`); re-measure together |
| 1c | The people's questions filled with the new kinds as they unlock | combat | next |
| 2 | Moments: the chest as a sequence, the evolution as a ceremony, the boss's death as the peak (slow motion), ducking, XP ladder, multi-kill swell, level-up sound, dash buffer, rumble | experience | next |
| 3 | Readability: a camera that starts close and pulls back as the horde grows; whole occluders fade (trees, crypts, roofs); the dead darken and sink; real bone and skull gibs; ground effects that never fill with a flat disc | experience (effects with combat told) | next |
| 4 | Onboarding: the prologue's character experience banked and paid at the dawn ("what the night taught you"); one bark at a time; prompts that never share a spot | experience; bark queue to UI | next |
| 5 | The loop: the result as the run's story and a reward reveal; the table shows what a map pays; story nights shorter than table nights (decision below); the town reacts to your nights (facts by me, words by story); pause only in arena combat | experience, UI, story | next |
| 6 | Choice that decides survival from tier 3 | combat | brief to send |
| 7 | Arena identity: each theme its own ground, props and landmarks | unowned (art) | escalate |
| 8 | A difficulty ladder the player swears (oaths as Heat), and account quests and unlocks | experience with combat | design next |
| 9 | Music: a composed score | owner | escalate |
| 10 | Performance: a clean measure; the town's cost | experience | next |

## For the owner (recommendations)

1. **Music.** The procedural score is the one part of the game no amount of tuning makes AAA.
   - **Recommended:** a composed score (licensed or commissioned), with local generation only
     as placeholders.
2. **Story nights' length.** Recommended: story arenas as 20-minute nights with the same shape
   compressed (`ArenaPacing` scales), and table maps at 30. Four story beats at 30 minutes each
   is two hours of arena gating the story.
3. **Arena art.** No lead owns the arenas' look; it needs one (or the UI art lead's
   pipeline turned to ground and props).
