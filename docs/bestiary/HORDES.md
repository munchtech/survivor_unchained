# Hordes: mixing, composition and the readability budget

One kind of creature asks one question. Two kinds together can ask a third
that neither asks alone, and that third question is where an arena's
character comes from, and where its unfairness comes from too. This file is
about what happens when the roles of `ROLES.md` share the field: which
pairings make emergent problems, how many distinct threats a screen can
hold, how the thirty minutes should be composed, and how mixing should grow
from tier 1 to the top.

## 1. What the mixes measured

The probe ran five mixes against fourteen loadouts (`probe/RESULTS.md`).
"Expected" is what the kinds cost alone, weighted by how many of each were
in the mix; "synergy" is the mix's damage taken over the expected.

| Mix | Kinds (at once) | Hurt alone (each) | Expected | Mix | Synergy | What happened |
|---|---|---|---|---|---|---|
| **Shield wall** | 4 bruisers + 4 pillagers | 43, 73 | 58 | 163 | **2.8×** | the guards hold the survivor at the throwers' range; the pots land on a survivor who cannot get through to them and will not walk round |
| **Ford** | 4 shieldmen + 4 bowmen | 14, 93 | 54 | 84 | **1.6×** | the same, softer: bowmen's bolts are smaller than pots |
| Hunt | 10 wolves + 3 tuskers | 42, 44 | 52 | 63 | 1.2× | the ring of wolves blocks the side-step out of a charge's lane |
| Raised ranks | 2 callers + 8 risen + 3 shieldmen | 44, 14 | 42 | 44 | 1.0× | the shieldmen add nothing the risen did not |
| Dig | 10 tunnelers + 4 sappers | 10, 66 | 40 | 37 | 0.9× | tunnelers surfacing round the survivor pull them off the pots' landing points |

**Guards in front of throwers are the strongest emergent problem in the
game today**, by a distance, and both peoples that have guards field it.
That is the right problem to have (it is the Kerchiefs' whole identity),
but it should be *composed* (an event with a tell) rather than the steady
state of every Kerchief arena after minute nine. §4 does that.

## 2. Pairings: the emergent problems

Each pairing below is two roles that change each other's question. "Keep"
means it is a good problem (readable, answerable two ways, worth composing);
"cap" means it is good in small doses and must be limited; "never" means
the director must not make it.

| Pairing | The third question | Answers | Verdict |
|---|---|---|---|
| **guard + ranged / lobber** | "Can you get round the wall before the fire finds you?" | flank, area that ignores the guard, chains, a stun or freeze to open the wall, Bulwark | **keep, compose** (measured 1.6–2.8×) |
| **guard + raiser** | "The wall protects the one making more of them" | non-projectile reach, interrupts that reach (Grapple, Time Slip) | keep, cap (one caller behind a wall) |
| **raiser + splitter** | "Every corpse is three corpses, and every corpse gets up" | area, burning ground, moving the fight off the bodies | **cap**: callers raise only rank and file, never splitters' young (the young give no grave) |
| **charger + area denial** | "Step off the lane... into the fire?" | reading the lane early, a dash, fire resistance | keep (it is the Pack's Slurry Sow's purpose) |
| **charger + swarmer** | "The ring blocks the side-step" | knockback, fear, a dash through the lane (perfect dodge) | keep (measured 1.2×) |
| **swarmer + buffer** | "The pack is faster while the howler lives" | kill the howler; Hunter's Mark finds it | keep |
| **buffer / healer + guard** | "The wall heals" | none good: healing walls are the genre's tedium | **never**: a healer's mend never targets a guarding creature, and a Mending champion is never a guard |
| **exploder + swarmer** | "The pack dies into a field of bursts" | ranged kills, a dash out | cap: a blight-sick wolf's burst never sets off another's (no chain) |
| **exploder + exploder** | a cascade | – | **never**: bursts never trigger bursts |
| **burrower + lobber** | "Moving is how you avoid the pots, and moving is when they surface" | standing still with a nova when the rings show | keep (measured 0.9×: easier than it sounds) |
| **orbiter + ranged** | a ring that shoots | – | **never**: orbiters never shoot (that is a kiter) |
| **thief + any** | "Do you leave the fight to chase it?" | ignore it, or chase it | keep: opt-in by nature |
| **two peoples at war** | "Can you set them on each other?" | pulling one into the other | keep, as its own offer (`ROSTER.md`, contested ground) |

### Forbidden in one arena, whatever the tier

- A healer or Mending Sign on, or healing, anything with a guard.
- More than one aura source on screen at once (Bannered, Mending, Old Howler,
  Ford-Lamp, Levy Drummer, Bell-Ringer).
- A Swift champion under the oath of the hunt (both stack to +62% speed).
- Rimed on a swarmer champion under the oath of winter.
- Bursts that trigger bursts.

## 3. The readability budget

A threat is anything that asks for a read: a telegraph that will hurt, a
priority target, a special the player must answer. Fodder is not a threat
(it is the crowd); the crowd's density is budgeted by `ArenaRun.Target`
already. Telegraphs are the scarce resource: the feel research's rule
("hostile red is reserved and never faded", `docs/feel/SUGGESTIONS.md`
S-19) only works if there are few enough of them to read.

### 3.1 Distinct threats a screen can hold

"Kinds" are distinct threatening kinds on screen (fodder excluded);
"telegraphs" are hostile telegraphs alive at once; "priority" is creatures
that should be killed first (raisers, buffers, healers, Sign-bearers).

| Tier | Kinds of threat | Telegraphs at once | Priority targets | Signs on one champion | Champions at once |
|---|---|---|---|---|---|
| 1 | 2 | 6 | 1 | 0, then 1 from minute 10 | 1 |
| 2 | 3 | 8 | 1 | 1 | 1 |
| 3 | 4 | 10 | 2 | 1, then 2 from minute 15 | 2 |
| 4 | 5 | 12 | 2 | 2 | 2 |
| 5+ | 6 | 14 | 3 | 2 (heralds 3) | 3 |
| past the half hour | +1 every 10 minutes | +2 every 10 minutes | +1 | as the tier | +1 every 10 minutes |

Why these numbers: research on visual attention puts the number of moving
objects a person can track at about four, rising to eight or so when they
move slowly (Pylyshyn and Storm 1988; Alvarez and Franconeri 2007: see
`RESEARCH.md` §4);
the tier-1 player is learning, so two kinds and one priority leave room;
the tier-5 player is reading, so six kinds and three priorities is the
ceiling at which a sweaty player is challenged and a relaxed one is not
killed by what they did not see (their auto-play still clears fodder, and
no single threat is lethal through the grace window).

### 3.2 Caps the code should hold

`ArenaRun.RangedCap` is the model: one counter, one rule, a substitute when
it is full. The same for the other telegraphing roles:

| Cap | Value | How |
|---|---|---|
| shooters and throwers (exists) | `5 + minute / 3`, ≤ 16 | as today |
| creatures winding up a charge or lunge at once | 2 + tier / 2, ≤ 4 | `Ai`: a creature that would start a wind-up while the count is full waits 0.5 s |
| underground at once | 8 | `Ai.Tunnel`: a tunneler that would burrow while 8 are under walks instead |
| death bursts fusing at once | 6 | `Battle.KillEnemy`: the oath of ruin's bursts skip while 6 fuse |
| aura sources | 1 | the spawner swaps a second aura creature for its people's fodder |
| ground fire from enemies | 12 zones | `SpawnZone(Side.Enemy, ...)`: the oldest goes out first |

These are cheap (a counter each) and they are what keeps a minute-25 screen
fair without dimming anything.

## 4. Composing the thirty minutes

### 4.1 What the arena does today

The horde is kept at a number that climbs with the minute; a people's kinds
join at set minutes and weigh more the longer they have been in; every 60–85
s an event comes in a fixed rotation (a closing ring, a champion with escort
and a chest, a stampede of the fastest, a swarm from one quarter); heralds
at 10 and 20; the boss at 30 (`ArenaRun`). The kinds' shares drift: for the
Kerchiefs at minute 25, footpads ~58%, pillagers ~26% (until the ranged cap
holds them), bruisers ~17%.

It works, and it is flat in one way: the events are the same four in every
arena, and a people's kinds always arrive mixed, so the people's signature
problem (the shield wall, the raised ranks) is a texture rather than a
moment.

### 4.2 A shape for the half hour

| Minutes | Phase | What the horde does | What it teaches |
|---|---|---|---|
| 0–3 | **arrival** | the people's fodder only; one event | the people's look, the ember's rhythm |
| 3–9 | **the question** | the people's first special joins; its first *signature event* at about 6 | the people's question, alone, in a moment with a tell |
| 9–10 | **breath** | the target holds for 30 s (S-12's "breathing") | – |
| 10 | **herald** | the herald, with one Sign at tier 2+ | the champion's read |
| 10–15 | **mixing** | the second special; events alternate signature and generic | the third question (§2) |
| 15 | **great blessing** | as today | – |
| 15–20 | **pressure** | the full roster; champions bear Signs; the composed problem at full strength | everything at once, within the budget |
| 20 | **herald** | ×1.6 as today, one Sign more | – |
| 20–28 | **the long push** | the densest field; the third signature event | stamina, the build's peak |
| 28–30 | **the hush** | spawning slows, the field thins; the boss's tell begins (with `claude/cloud-bosses`) | the calm before it |

### 4.3 Signature events, a people each

Each people gets two events of its own, mixed into the rotation in place of
two generic ones (the closing ring and the swarm stay for all).

| People | Signature event | What it is | Its tell |
|---|---|---|---|
| the Pack | **The Hunt** (today's stampede, kept) | the fastest kind in a column across the arena | a howl from one quarter, then the column |
| the Pack | **The Ring** | wolves fan to slots on a 7 m ring and hold for 2 s, then close at once | the ring forms visibly, grey eyes all round; the answer is a nova or a dash out before it closes |
| the Risen | **The Ford Rises** | the graves round the survivor (the arena's grave props and the fallen) all rise at once, 10–20 risen in a 10 m ring, helpless for their 1.1 s | the ground cracks in a ring; a sweaty player stands in the middle with a nova |
| the Risen | **The Shield Line** | a line of shieldmen walks in from one side with bowmen behind | the line in the open, shields up; the answer is round its end |
| the Lamplings | **The Dig Opens** | every tunneler on the field surfaces at once in a ring | the surfacing rings all appear together, 0.8 s |
| the Lamplings | **The Cart** | a Blasting-Cart and an escort from one side | the fuse's hiss before it appears |
| the Kerchiefs | **The Ambush** | footpads from two opposite sides at once | a whistle; red cloth at the edge of the light |
| the Kerchiefs | **The Wall** | bruisers walk in a line with pillagers behind it: the shield-wall mix as an event, not a steady state | the drum (if the Drummer exists) and the line in the open |

Composing the shield wall as an event lets the steady Kerchief horde keep
fewer bruisers (lower their weight from 2 to 1.2 and their join from minute
9 to 12) while the wall still comes, three times a run, as a moment with a
beginning and an end.

### 4.4 A threat budget for the spawner (optional, later)

When the roster grows past eight kinds a fixed weight table stops being
enough. A small director in the manner of Left 4 Dead's (`RESEARCH.md`,
Left 4 Dead) can hold the budget of §3 directly: every kind has a **threat
cost** (fodder 0, a swarmer 0.5, a ranged or lobber 1, a guard 1, a charger
1.5, a raiser, healer or buffer 2, a champion 3 plus 1 a Sign); the spawner
keeps the threat on screen under `budget(tier, minute)` and, when it is full,
spawns fodder. The rotation of events stays as it is and spends the budget
in a burst. This is `IMPLEMENTATION.md` item 14: worth doing once the roster
is twice today's.

## 5. Mixing from tier 1 to the top

| | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5+ |
|---|---|---|---|---|---|
| Peoples | one | one | one; contested ground offered | one or contested | one or contested |
| Kinds in the field by minute 20 | 3 | 4 | 5 | 6 | all |
| Signature events | 1 | 2 | 2 | 2, at full strength | 2, plus a third from the other people when contested |
| Champion Signs | none, then 1 from minute 10 | 1 | 1–2 | 2 | 2; heralds 3 |
| New kinds join | minutes as listed ×1.3 (later) | as listed | ×0.85 (sooner) | ×0.7 | ×0.6 |
| Oaths on the table | 0–1 | 1–2 | 2 | 2–3 | 3 |
| What makes it harder | numbers | the first Signs | Signs and mixing | stacked oaths | the people's whole question, stacked |

Brotato's lesson (`RESEARCH.md`, lesson 2) runs through the table: each tier
first adds *kinds and verbs*, and only then numbers. Health and damage
already rise by tier through the level (`tier × 2 − 1`); nothing here adds
another stat multiplier.

## 6. Past the half hour

The endless play after the boss is the place the research says should be
openly unbeatable (Last Epoch; `RESEARCH.md`, lesson 12). Mixing there should
keep growing by kinds and Signs, not only by the health curve the code
applies (`1 + 0.1 m + 0.006 m²` health, `1 + 0.035 m` damage per minute past):

- a herald every five minutes (today) bearing one more Sign each time, to
  the cap of three;
- every ten minutes, one more kind of threat allowed on screen and two more
  telegraphs (§3.1), so the late field is denser in *questions*;
- from minute 45, a second people joins for contested ground if the arena
  was not already contested ("the night draws others to the light").

The glory of a long stay is the reward (`RISK_REWARD.md` §6); the field
should become a spectacle the sweaty player reads at its limit, while the
relaxed player, who has already won, may simply take the way out.
