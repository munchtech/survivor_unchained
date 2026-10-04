# The experience audit (draft two)

What holds Survivor Unchained back from the best of its genre, as a player lives it. Ranked
by how much each thing costs in feel and in keeping a player. **Draft two** adds the
owner's answers (the structure, the music, a new arena art lead) and the plan they reshape. The
boss and the long night on screen, and clean frame times, are being taken now.

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

## The structure (the owner's decisions, 4 October)

> "story should be 40% of the game early on, end game is two types of arenas - permanent and our
> normal arenas. permanent is our arpg build maps like poe and the normal arenas are for mindless
> survivors fun"

**Early on, story is about 40% of play.**
- **Story nights:** 20 minutes. They are the same night at 1.5 times the speed: one night clock,
  and ember gain × 30/Minutes, so the build at a story boss matches a table boss's. Combat is
  building it; the pacing already scales. Table nights stay at 30 minutes.
- **The 40% is measured, not guessed.** The journey will keep time by mode (day story, story
  night, table night, map), and the explorer and the harness will report the share. The target
  is 35–45% of Act 1's time in the story.

**The endgame is two kinds of arena.** Combat owns their mechanics; the shape and the loop
are mine:

| | **Nights** (the survivors arenas) | **Maps** (the permanent ARPG build maps) |
|---|---|---|
| The fantasy | the hum: the brain off, a horde that melts | the build: gear and skills read, planned and proven |
| Power | the ember, from nothing, cards | the character, kept: gear, day skills, arts, attributes, levels |
| Length | 30 minutes (story nights 20), then the long night for as long as you dare | 8–12 minutes: one zone, a boss at its heart |
| Starting one | the Wayfinder's table or an ember scar, with nothing to prepare | a map item set on the table's atlas, prepared for |
| Difficulty | tier, the table's oaths, and oaths you swear for more (a ladder like Hades' Heat) | the map's tier and its affixes (oaths rolled on the item, or added by crafting) |
| What it pays | XP for time, materials, the codex, tomes, the night's chests | gear (the main loot), maps of the next tier, atlas progress |
| The long goal | the longest night; the highest heat; every people's boss beaten at each tier | the atlas: regions lit, tiers climbed, map bosses, completion bonuses |
| Death | the night ends; what was earned is kept | the map is spent; the character keeps everything |

**How the two feed each other:**
- nights pay materials and kindling that craft and roll maps;
- maps pay gear whose kindled affixes feed the nights (SKILLS_DESIGN §10, "day feeds night");
- the codex and the bestiary fill from both.

**A map's shape (the target to build to):**
- three to five linked areas, like a small Verge, with packs placed by day's rules;
- a kill or a find every 10–20 s, and a pack every 20–40 s of walking;
- one event (a shrine, a strongbox held for 20 s, a rare with a Sign, a lost cart);
- the map's boss in the last area, then its chest and the next map.

**When maps open:** at the end of Act 1's story (Vonnra's fortune), as the Wayfinder's atlas.
The Act 1 beta shows the first tier, so the endgame can be tasted.

## What the music must do, beat by beat (for the owner's score)

The owner will work on the music. Until then the procedural score stays. This is what each beat
asks of the music, so the cues can be written to it.

| Beat | What the music must do |
|---|---|
| Title, by the fire | the game's theme, alone and low: one instrument, the fire under it; it should make you want to stay |
| Making a survivor | the theme's bed, unhurried; a small lift as each step is taken |
| Prologue: waking, the dead rising | almost nothing, then a pulse as the ground opens: dread before action |
| The road and the ambush | the first combat cue, light: it must leave room for the tutorial's words |
| The Ford-Warden | the first boss theme: big, old, sad (the Watch's dead keeping a ford) |
| Dawn | release: the theme in full for the first time, as the ember goes out |
| The Waystation by day | a town: warm, a little shabby, human; changes by hour |
| Conversation | ducked under the voice (already); a character's motif may rise where the writing turns |
| The Verge by day / at night | the wood's quiet; at night a low drone with the ember scars' pulse in it |
| Pulled into a night | a swell and a cut to silence on the black, then the night's first drum |
| A night's dusk (0–2) | the arena's bed: low, steady, the people's colour in it (wolves' horns, the dead's drum, lamplings' picks, Kerchiefs' whistles) |
| Building into a landmark | layers added bar by bar: the music should tell you something is coming before the screen does |
| A herald | the people's motif, heavy; it stays until the herald falls |
| The flood after it | the fullest the music gets before the boss: the hum, a groove you can mow to |
| A breather | strip back to the bed for twenty seconds; never silence |
| Midnight's great blessing | a held chord through the choice, resolving on the pick |
| The long push (25–28½) | the climax of the night's score: the densest layers, rising |
| The hush (28½–30) | everything drops to a single drum or drone under the sign's light; it should feel held, not empty |
| The boss | the people's ruler's theme, its own for each of the four; a change at each phase |
| The boss falls | a stinger and a release (the way out opens): the night's theme resolved |
| The long night | the score grows harsher every five minutes as the dark swears an oath; no end, no resolution |
| A chest, an evolution, a level | stingers over the bed: the chest a rising reel; an evolution the night's theme in brief; a level a short rise that lands on major |
| Death | cut to near silence, one low note; the bed returns under the result |
| The result | the night's theme in brief, calm: what you take out |

## The plan

| # | Item | Owner | State |
|---|---|---|---|
| 1 | The night's shape: sawtooth, breathers, herald duel and flood, the hush, the people's own questions | experience | **done** (`ArenaPacing.cs`) |
| 1b | The danger rising with the shape: charge spikes in build-ups, calm in breathers | combat | **done** (charge director); re-measure together |
| 1c | The people's questions filled with new kinds as they unlock; minibosses outside the hush and the duel | combat | in hand |
| 1d | Story nights at 20 minutes: one night clock, ember × 30/Minutes, turns spaced to match, words that don't say "half hour" | combat (clock), story (words) | in hand; I check it on screen |
| 2 | Moments: the chest as a sequence, the evolution as a ceremony, the boss's death as the peak, ducking, XP ladder, multi-kill swell, level-up sound, dash buffer, rumble | experience | next |
| 3a | Her, readable: a camera that starts close and pulls back as the horde grows; a ring or silhouette when she is covered; whole occluders fade; the dead darken and sink; real bone and skull gibs | experience | next |
| 3b | Skill effects that never fill with a flat disc (Blightfield, Hallowed Ground, Dawnpulse); champions' death blasts sized down | skills (`a8bafe3cd8a229639`) | in hand there; sizes agreed with me |
| 3c | Arena identity and readability: each theme its own ground, props and landmarks; nothing tall where the fight is; the ground a quiet stage for the horde | arena art (new lead) | brief sent when it starts |
| 4 | Onboarding: the prologue's character experience banked and paid at dawn; one bark at a time; prompts that never share a spot; the first minute of a night not empty | experience; bark queue to UI | next |
| 5 | The loop: the result as the night's story and a reward reveal; the table says what a map pays; the town reacts to your nights; pause only in arena combat | experience, UI (`ac76f400913a109cd`), story | briefs sent |
| 6 | Choice that decides survival from tier 3 | combat | brief sent |
| 7 | The two endgame arenas: nights and maps, as above | combat (mechanics), experience (shape and loop), UI (atlas), crafting (map items) | design sent |
| 8 | The 40% measured: time by mode, reported by the explorer and the harness | experience | next |
| 9 | Music: the score to the beats above | owner | noted |
| 10 | Performance: clean frame times; the town's cost | performance (`a9586a5171413db0b`) | numbers sent |
