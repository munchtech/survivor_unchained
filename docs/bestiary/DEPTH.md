# Depth: simple to sweaty

"This game can truly be played as simply or as sweaty as the player would
like." This file is about holding that promise: a relaxed player who moves
and lets the build work must be able to finish, and a sweaty player who
reads the horde, builds counters, positions and takes opt-in risk must be
rewarded for it. Low floor, high ceiling, and neither style punished.

## 1. The two players

| | The relaxed player | The sweaty player |
|---|---|---|
| Moves | away from the crowd, round it, toward the ember | to a place chosen for what is coming: a tree before a tusker, the middle of the Ford Rises |
| Reads | the red on the ground when it appears | the creature as it walks in: its role, its Sign, its tell |
| Builds | the cards that look good; whatever the draft offers | toward the people on the table, and against the third question of its mixes |
| Gears | the best item they have | a slayer and a resistance for the people, a flanking affix for the wall |
| Risk | the arena as offered, the way out after the boss | oaths, the higher tier, contested ground, the thief, the half hour and beyond |
| Wants | a good night, the story, a build that hums | a cleaner kill, a higher tier, a deed for a Storied item, a best time |

The plain and deft arena bots are rough stand-ins for the two (`probe/`).
The deft bot only adds three reads to the plain one (off a lunge's lane,
out from under a pot, in on the throwers); a human sweaty player reads far
more, so every gap below is a lower bound.

## 2. What reading buys today (measured)

Plain bot against deft bot, kills a minute / damage taken (% of a warden's
health a minute), same loadout and creatures:

| Creatures · loadout | Plain | Deft | What the read did |
|---|---|---|---|
| Pillagers · Oathblade | 26 / 161 | 1 / 76 | stayed off the fire: half the hurt, almost no kills |
| Sappers · Oathblade | 29 / 188 | 4 / 74 | the same |
| Bowmen · Dawnpulse | 0 / 40 | 29 / 95 | walked to them: from no kills to the median, at twice the hurt |
| Bowmen · Hallowed Ground | 0 / 40 | 44 / 78 | the same |
| Tuskers · Oathblade | 30 / 105 | 24 / 76 | off the lanes: a quarter less hurt |
| Tuskers · Arcweb | 42 / 59 | 40 / 41 | a third less hurt |
| Shield wall · Hallowed Ground | 14 / 110 | 24 / 180 | dived the throwers: more kills, much more hurt |
| Wolves · any | identical | identical | nothing to read: wolves have no tell |
| Fodder · any | identical | identical | nothing to read |

Three things follow.

1. **Reading is a trade, not a free gain.** The deft bot's reads moved
   damage taken and kills in opposite directions in most rows: diving
   throwers costs health, avoiding fire costs kills. That is the right
   shape: the sweaty player is choosing, and a human who chooses well (dive
   when the build can finish the thrower fast, avoid when it cannot) gets
   both.
2. **Today, reading matters only against four roles**: ranged, lobber,
   charger and the elites' lunges. Swarmers, fodder, guards, raisers and
   exploders play the same for a reader and a non-reader, because their
   tells are either absent (wolves) or ask nothing of movement (a guard's
   front is answered by the loadout, not the feet). The roles proposed in
   `ROSTER.md` and the Signs in `COUNTERS.md` §4 are mostly there to widen
   this: each adds a read (the howl, the cart's fuse, the mender's ring, the
   ward's lights).
3. **The perfect dodge is almost never earned by accident.** The deft bot,
   which dashes across lanes only when late, earned 0–2 perfect dodges a run
   against the creatures that lunge. It is the deepest skill expression in
   the game (Duelist's Grace builds on it) and it is invisible to the relaxed
   player, which is exactly right: a ceiling with no floor cost.

## 3. Every system, both ways

How each system lets the same arena be played relaxed or sweaty, and where
its floor and ceiling sit.

| System | Relaxed (the floor) | Sweaty (the ceiling) | Rule that keeps both |
|---|---|---|---|
| Movement | walk away and round; the grace window caps a crowd's bite at ~2.2 blows a second | position for the next threat; herd fodder into balls | no blow from the rank and file that a moving player cannot avoid |
| Telegraphs | step off the red when it shows | dash through it for a perfect dodge; bait charges into trees | wind-ups ≥ 0.6 s at every tier; caps on telegraphs at once (`HORDES.md` §3.2) |
| The draft | take what looks good; a generalist skill carries | draft for the people's question and the mix's third one | no role that only a drafted card answers (no immunities; guards 75–80%, champions 60%) |
| Great blessings | Iron Vow, Bloodthirst, Ember Tithe: work from the first second | Duelist's Grace, Glass Cannon, Momentum: pay for play | always offer at least one blessing of each kind (one safe, one demanding) |
| Arts | one art used when crowded; the movement arts get you out | Shield Bash a raise, Time Slip a wall, Grapple a mender, a lunge slipped | arts are never required: no creature or Sign needs a specific art |
| Gear | the best item they own | a slayer and the people's resistance, prepared by day | the table names the people and their bane before entry |
| Tier | the tier earned | one higher (the table already offers it) | tier adds kinds and Signs before stats (`HORDES.md` §5) |
| Oaths | none, or the one the table hands them | stacked, chosen for their reward | the table says what each asks, gives and what answers it (exists) |
| Champions | kite it while the build works; it is slow | read the Sign, answer it, take the chest | Signs telegraph; at most two; no immunity or reflect |
| Thieves | ignore it, lose nothing | chase it for a purse | it never takes what the player owns |
| Contested ground | a busier arena, if anything easier | set the peoples on each other | offered, never imposed |
| Past the half hour | take the way out; the arena is won | stay for the deeds, the best time, the Storied history | nothing after the win can undo it (today: true) |

### 3.1 Floor and ceiling by tier

What each player should expect, as targets for the balance lab. "Fair
gear" means the gear the day-story has given by that point
(`docs/items/PROGRESSION.md`).

| Tier | Relaxed player, fair gear, no oaths | Sweaty player, prepared, two oaths |
|---|---|---|
| 1 | wins nearly always (≥ 90%); the first arena teaches | wins and stays ten minutes past |
| 2 | wins most nights (≥ 75%) | wins with two oaths (≥ 70%) |
| 3 | wins more often than not (≥ 60%) | wins with two oaths and contested ground (≥ 60%) |
| 4 | wins sometimes (~ 40%): the place to stop and gear up | wins with three oaths (~ 50%) |
| 5+ | not expected to win without preparing | the ceiling: a win is a deed |

The relaxed player's numbers are about the floor: the bot standing in for
them is worse than a person, and story arenas (which every player must
finish) sit at the tier the story sets. A **story fight lost can be taken
again at the table** (`Arenas.Again`): keep that as the floor's safety net,
and never put a story arena above the tier the story's level band expects.

## 4. Auto-pilot viability

A survivors game is often played half-attentively, and that has to stay a
real way to play the first tiers. The test: **can the plain bot, with a
fair gear set and the first card offered every time, win tiers 1 and 2
without oaths?** The balance lab measured it with no gear beyond the
starting kit (`probe/lab/plain_t1-3.md`, 96 runs cut at minute 31): the
plain bot **fell before the half hour in 3–6% of runs** at every tier, and
came to the boss with 37–45% of its health at its lowest. The horde is
already a floor a half-attentive player stands on; what decides the win is
the boss (killed within its first minute in 56% of tier 1 and 2 runs, 34% at
tier 3), which is the `claude/cloud-bosses` session's subject. The deft bot
at tier 2 came to the boss as low (38%) but killed it more often (66%).
Rules that keep the horde's answer yes:

1. **No creature that a build cannot hurt.** Guards cut projectiles by 75–80%
   and never 100%; resistances top out at 50%; champions' guards 60%.
2. **No blow from the rank and file above a quarter of a fair health bar**
   at the tier it appears; no elite blow above half. (Check: a tier-3
   barrow-knight herald's lunge at minute 20, level 13: 22 × 2.68 × 1.5 ×
   1.2 ≈ 106. That is right at half of a level-7 warden's health with fair
   gear; heralds' lunges must not grow further.)
3. **Every telegraphed blow is avoidable by walking** if seen in its first
   half; dashes are for the late.
4. **Priority targets are found for you if you take the right blessing**:
   Hunter's Mark and Mark Prey seek the toughest, and buffers, healers and
   Sign-bearers should count as toughest (`COUNTERS.md` §7).
5. **No time pressure in the base arena.** Pressure that rises when the
   player is slow (Dead Cells' malaise, Halls of Torment's agony) is an
   oath, never the default.

## 5. What the player must be told

Each kind of player needs different information, and the screen is already
full. The rule: **layer it** (a glance, a look, a study), so the relaxed
player sees only the glance and the sweaty player can dig.

### 5.1 Before: the Wayfinder's table

Today the card shows the tier, the map's name, who holds it, who rules it,
"their bane" (the people's leaning affixes), and each oath's name, what it
asks, gives and what answers it (`godot/src/Ui/MapTable.cs`). That is
already a good scouting screen. Add, in this order:

| Layer | Add | For |
|---|---|---|
| glance | **the people's question** in one line under "Held by": the Pack: "They come from every side." The Risen: "Kill what raises them." The Lamplings: "Watch the ground." The Kerchiefs: "Get round the wall." | both |
| glance | **the reward**: the oaths' gear and ember as one line ("Gear ×1.5 · Ember ×1.4"), and its **Weight** (`RISK_REWARD.md` §4) | both |
| look | the people's kinds as small icons with a role glyph each (shield, bow, pot, ring, charge, burst) | sweaty |
| look | **your build against them**: a line computed from the survivor's own day skills and gear against the people's resistances ("Holy +50% against the Risen · your shadow −35%") | sweaty |
| study | the bestiary entry for each kind (§5.3), one click away | sweaty |

### 5.2 During: the arena

| What | How | For |
|---|---|---|
| Hostile telegraphs | reserved red, never faded, drawn over the survivor's effects (S-19 of the feel work) | both |
| A champion's Signs | named on its bar ("Swift, Bannered Barrow Knight") and worn on the creature in the Sign's colour | both; the sweaty read it |
| The priority target | a faint ring under an aura carrier, a mender or a raiser while it is working | both |
| Signature events | a sound and a shout before each ("A whistle in the dark: an ambush") | both |
| Off-screen threats | an edge pip for a charge or a lob aimed from beyond the frame (S-19) | both |
| The thief | a gold outline seen across the arena, a laugh, a countdown ring as it escapes | sweaty, ignorable |
| A guard turning a blow | the glance spark, and the number struck through (`Ev.Hit.Blocked` exists) | teaches the relaxed player that this is a wall |

Nothing in the arena should ever need reading text in the middle of a fight
apart from the champion's bar, which can be read when the fight allows.

### 5.3 After: the recap and the bestiary

| What | How | For |
|---|---|---|
| **A death that teaches** | the arena's end names what killed the survivor *and the tell they missed*: "Killed by a Swift Barrow Knight's lunge. Lunges mark a red lane first; a dash through it is a perfect dodge." One sentence, from the creature's role. | relaxed |
| **The night's hardest** | which creature hurt most this run (the balance lab already counts `hurt` by source) | both |
| **The bestiary grows answers** | the codex (`Book.Codex`) today shows a name, a count and a note. At 10 kills add the creature's **role** and **tell**; at 50, **what answers it** (the matrix's ●● cells, in words); at 200, its **resistances** in numbers. Knowledge earned by killing, in the voice of the notes already there. | both: it is the relaxed player's tutorial and the sweaty player's reference |

### 5.4 Settings

- **Clarity and spectacle** presets (S-19 of the feel work).
- **Show Signs as text over champions** (on by default at tiers 1–2).
- **Telegraph intensity**, for players who need more contrast.

No difficulty slider: the table is the difficulty selector (tier, oaths,
contested ground), which is how the genre's opt-in dials work best
(`RESEARCH.md`, opt-in difficulty).

## 6. Where the floor and ceiling could break

| Risk | Which player | Guard against it |
|---|---|---|
| A drafted build meets a people that hard-counters it (projectiles against a Kerchief wall) | relaxed | guards ≤ 80%, champions 60%, other kinds beside the guards, the table names the people |
| A sweaty trick removes a role's threat (Mirror Step against everything) | sweaty, and it bores them | shorten the reflections or let champions see through them (`COUNTERS.md` §5) |
| A Sign that only an art answers | relaxed | every Sign has two answers, one of them a build or movement |
| An oath far harder than it pays (the blight) or easier than unsworn (champions) | both | price it by measured difficulty, the Weight (`RISK_REWARD.md` §4) |
| The relaxed player never learns why they died | relaxed | the death that teaches (§5.3) |
| The sweaty player finds nothing to read in a people (wolves have no tell) | sweaty | the Pack's proposals (Ridge-Runner, Old Howler, the Ring event) |
