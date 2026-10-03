# Suggestions: what to build, in order

Concrete changes for the main agent, ordered by **return for the work**:
the cheapest changes that move the most feeling come first. Each says the
feeling it targets, exactly what to build, the numbers to start tuning
from, where in the code it goes, what it costs, and how to tell in play
whether it worked.

Costs:
- **Tweak**: numbers or a few lines in one place; under an hour.
- **Small**: one file or two, an afternoon.
- **Medium**: a few files and a new piece of UI or state; a day or two.
- **Large**: a new system; several days.

Starting numbers are starting points, not answers: where they come from a
source it is cited (`RESEARCH §n`); otherwise they are estimates to tune.
Every visual or audible change needs checking in the running game, which
this research session could not do. The arena changes can also be
checked headless with the probe in `probe/` (see the end of this file).

---

## At a glance

| # | Suggestion | Feeling | Cost |
|---|---|---|---|
| S-01 | Ordinary creatures get easier as the run goes on | Power fantasy, the inversion | Tweak + measure |
| S-02 | A musical XP crescendo; the lodestone as a jackpot | The hum, the vacuum | Small |
| S-03 | Big moments duck the small ones; crits never go unheard | Congruence, contrast | Small |
| S-04 | A level-up that sounds like a gain | Reward | Tweak |
| S-05 | A 120 ms dash buffer | Responsive, fair | Tweak |
| S-06 | Bars that flow; a bar about to fill that glows | Anticipation | Small |
| S-07 | A particle budget with priority | The big moments survive the chaos | Small |
| S-08 | The kill, not the hit: a multi-kill swell | "Melting", the hum | Small |
| S-09 | The chest as a sequence | The jackpot | Medium |
| S-10 | The evolution as a ceremony, mid-run | "It clicked" | Medium |
| S-11 | The boss as the run's peak and its end | Peak-end, catharsis | Medium |
| S-12 | An arena that swells and breathes | Flow, escalation and release | Medium |
| S-13 | Damage numbers that merge, rank and cap | Number go up, readability | Medium |
| S-14 | Rumble | Touch, weight | Small–Medium |
| S-15 | Loot that announces itself, by rarity | Anticipation, rarity | Medium |
| S-16 | An end screen that tells the run's story | Peak-end, one more run | Small–Medium |
| S-17 | Your own blows kick the camera; arts land with hit-stop | Weight, attribution | Small |
| S-18 | A score that follows success, not only threat | Escalation, the hum | Large |
| S-19 | A readability layer | Fairness, signal in the noise | Medium–Large |
| S-20 | Calm the first two minutes' draft flood | Brain-off, choices that matter | Tweak |
| S-21 | Name the night's phases | Escalation as a story | Small |
| S-22 | Experiment: weapons that fire on the beat | Rhythm, trance | Medium (experimental) |

The **top ten**, by return for the work, are S-01 to S-10. S-01 is the one
that matters most: it decides whether the rest have a power fantasy to
celebrate.

---

## Tier 1: quick, high return

### S-01. Ordinary creatures get easier as the run goes on

**Feeling.** The power fantasy: "it starts with you throwing a single whip
at a bat and ends with you becoming a literal god of death". Players
describe a *slope*, an inversion from fleeing the horde to wading into it
(RESEARCH §2.2, §8.2).

**The problem, measured** (AUDIT §9). An ordinary creature takes ~1.5
direct blows to kill at minute 5 and ~4 at minute 30, in every case run.
One-blow kills fall from 25–75% of kills to about 5%, even with six evolved
rank-8 weapons. Enemy health grows ×10.6 by minute 30 (`Enemies.ScaleFor`
at level 13); weapon damage grows ×2.4 by rank 8. The run currently says
what players said of Deep Rock Galactic: Survivor: "You're rarely ahead of
the power curve".

**What to build.** Split the arena's health curve in two:
- **Ordinary creatures** (not elite, not herald, not boss) get softer
  relative to the level curve as the minutes pass, so that time-to-kill
  falls.
- **Elites, heralds and the boss** keep the steep curve. They are the
  "witness" that keeps power meaningful (RESEARCH §2.2: "power needs a
  witness").
- Keep ordinary creatures' **damage** on its curve, so contact still
  matters (residual threat, RESEARCH §8.2).
- Threat comes back through **count and surges** (S-12) and elites, which
  is how the genre does it.

**Start from.** In `ArenaRun.Spawn`, after the creature is made, for
ordinary creatures:

    e.MaxHp = e.Hp = e.MaxHp / (1 + k * Minute);

with **k = 0.12**, tuning between 0.10 and 0.15 (see "What the experiment showed" below). Targets to tune
toward with the probe:

| Minute | Median blows per ordinary kill | One-blow kills |
|---|---|---|
| 5 | ≤ 2 | ≥ 35% |
| 15 | ≤ 1.5 | ≥ 50% |
| 25 | ≤ 1.3 | ≥ 65% |

Past the half hour, keep the existing hardening (`Beyond`): the endless
part is meant to rise until something gives.

**What the experiment showed.** This was tried on a scratch copy of
the logic (the repo untouched), two cases (warden against the pack, and
the arcanist against the kerchiefs, the hardest case), 31 minutes each:

| k | Minute | Warden: blows / one-blow kills | Arcanist: blows / one-blow kills |
|---|---|---|---|
| 0 (today) | 5 → 15 → 30 | 1.6 / 37% → 3.0 / 19% → 3.9 / 6% | 2.9 / 14% → 3.6 / 9% → 4.6 / 2% |
| 0.06 | 5 → 15 → 30 | 1.3 / 72% → 1.9 / 33% → 2.1 / 41% | 2.6 / 22% → 2.6 / 30% → 2.5 / 20% |
| **0.12** | 5 → 15 → 30 | **1.2 / 80% → 1.4 / 70% → 1.8 / 54%** | **2.0 / 41% → 2.2 / 59% → 1.9 / 64%** |
| 0.20 | 5 → 15 → 30 | 1.4 / 64% → 1.5 / 64% → 1.4 / 72% | (fell at 10.4 minutes) |

At k = 0.12 the slope turns the right way for the arcanist (from rising to
falling) and holds the warden near one or two blows all run. It did not
make the arena safe: one of these bots still fell at 30.4 minutes, and the
k = 0.20 arcanist fell at 10. (Each variant's bot drafts differently, so
read the trend, not single cells.)

**A second finding from the same runs:** kills per minute barely changed
(~1,200 a minute at minute 30 in every variant), but the number alive
fell from ~130 to ~75–125. **The kill rate is capped by the spawner**
(groups of 3–6 + minute/5 every 0.45 s): a stronger survivor thins the
field rather than killing more. So S-01 needs S-12's spawning (bigger
groups when the field is thin) to turn ease into the screen-clearing
volume the genre is known for.

**Side effects to expect.** A thinner field unless the spawner keeps
up (above, and S-12); with it, more kills per minute (more ember, more
levels; the late XP curve absorbs it); more bodies bursting (overkill gibs
rise, which is *good*: it makes growth visible, AUDIT §1); more sound and
particles (S-03, S-07 and S-08 become more urgent); possibly an easier run
(raise the horde in surges, S-12, rather than restoring health).

**Where.** `godot/logic/Play/Zones/ArenaRun.cs` (`Spawn`, next to the
existing `Beyond` hardening). Run the probe and `ARENA_PLAY=1` before and
after.

**Cost.** Tweak, plus an hour of measuring.

**You'll know it works when** the probe's blows-per-kill column falls
across the run instead of rising; in play, by minute 15 the swarm
evaporates on contact with your weapons and you start walking *into* it
(RESEARCH §8.3 #4: the sign of your movement relative to the horde's
centre flips between minutes 10 and 20).

---

### S-02. A musical XP crescendo; the lodestone as a jackpot

**Feeling.** "the lil ding-sounds from getting XP crystals are satisfying,
especially when u run through an entire field of them"; "a certifiable
symphony of sounds as you suck up these gems like an industrial grade
vacuum cleaner" (RESEARCH §3.5, §8.2). The gem stream is a crescendo the
player conducts by walking.

**The problem** (AUDIT §5, §9). The XP chime rises in **half-semitone**
steps (`Sfx.Xp`: `streak × 0.5` semitones), which sit between the notes of
any scale; it is the quietest sound in the game (gain 0.02, a 50 ms
chirp); it is gated to 80 a second and tops out after 24 stones. A
lodestone sweep collects 400–800 stones in a second, so the best moment
for the ladder plays as a flat buzz. The lodestone itself plays the
*dash* sound.

**What to build.**
1. **A pentatonic ladder in the score's key.** The score is in D minor
   (`Music.cs`); use D minor pentatonic (D F G A C): semitone offsets
   `0, 3, 5, 7, 10, 12, 15, 17, 19, 22, 24` from **D6 (1174.7 Hz)**,
   close to today's 1150 Hz. One step per stone (RESEARCH §5.3: one step
   per chain link; Peggle tunes the steps to the music).
2. **Merge, don't drop.** Stones collected within **33 ms** become one
   voice at **+3 dB × log2(n)**, capped at +9 dB, and advance the ladder by
   `min(n, 3)` steps (RESEARCH §5.2). Replace `Gate("xp", 8, 100)` with this.
3. **Louder and rounder.** Gain 0.035–0.045 (about +6 dB on today's);
   attack 2 ms, decay 90 ms; two sines detuned +7 cents, or a sine plus its
   3rd harmonic at 0.3 (RESEARCH §5 implications 19).
4. **Clamp and resolve.** After the top step (two octaves), hold the top
   note and add an octave-up shimmer. Reset after **0.8 s** without a stone.
5. **The bar near full is a cue** (RESEARCH §3.1): above 85% of the ember
   bar, each ladder note gets a soft fifth above it.
6. **The lodestone is a jackpot.** Its own sound: a rising "inhale" (brown
   noise through a low-pass swept 300 → 3,500 Hz over 0.6 s) under a fast
   run of the ladder; it is the *only* time the ladder may climb past its
   clamp (to three octaves). Raise its rarity only if it starts to feel
   ordinary (0.4% × luck per kill today).

**Where.** `godot/src/Audio/Sfx.cs` (`Xp`, a new `Lodestone`),
`godot/src/Audio/SoundBridge.cs` (the `Ev.Pickup` case and `xpStreak`),
`godot/src/Audio/Synth.cs` (a small merge helper beside `Gate`).

**Cost.** Small.

**You'll know it works when** a sound-only recording (`--wav`) of a
lodestone sweep at minute 15 sounds like a rising run that resolves, not a
buzz; testers rate the pickup sound as highly at minute 25 as at minute 5
("constant and absurd" is the failure, RESEARCH §8.2).

---

### S-03. Big moments duck the small ones; crits never go unheard

**Feeling.** Congruence and contrast: "every sound is important, but not
at the same time" (DICE, RESEARCH §5.5).

**The problem** (AUDIT §5). Nothing ducks for a level, an evolution, a
boss's death; the only duck is music under menus. The master compressor
pumps everything at once. The crit sweetener is skipped when the hit gate
is full (`Sfx.Hit` returns before reaching it).

**What to build.**
1. **A duck envelope on the SFX bus**, like the music's `duckNow`:
   `Synth.Duck(Bus bus, float dB, float attackMs, float releaseMs)`.
2. **Who ducks whom** (RESEARCH §5.5 starting values):

   | Event | SFX bus | Music | Attack / release |
   |---|---|---|---|
   | Level-up, evolution, chest, boss arrives or dies, legendary drop | −8 dB | −4 dB | 10 / 400 ms |
   | Perfect dodge | −6 dB | −3 dB | 5 / 300 ms |
   | A blow on you > 12% of health | −6 dB | — | 5 / 250 ms |

   The ducking sound itself plays on a bus that is not ducked (`Ui` today,
   or a new `Stinger` bus).
3. **A hurt filter**: on a blow > 12% of health (the same threshold as
   the hit-stop), a one-pole low-pass on the SFX bus from 18 kHz to 1.2 kHz
   in 20 ms, recovering over 350 ms.
4. **Crits are not gated by ordinary hits.** Move the crit layer above the
   `Gate("hit", ...)` early return in `Sfx.Hit`, with its own gate.

**Where.** `godot/src/Audio/Synth.cs` (the mix loop, around the `duckNow`
line), `godot/src/Audio/SoundBridge.cs` (call `Duck` per event),
`godot/src/Audio/Sfx.cs` (`Hit`).

**Cost.** Small.

**You'll know it works when** a level-up at minute 20 in a thick fight is
clearly heard over the battle in a `--wav` recording, and crits are audible
as a separate layer in a dense crowd.

---

### S-04. A level-up that sounds like a gain

**Feeling.** Reward. The level-up is the most repeated reward in the run.

**The problem.** `Sfx.LevelUp` is a **minor** arpeggio (0, 3, 7, 12, 15
semitones from D5), which reads as melancholy (inferred; AUDIT §3). The
dark tone is right for the score, but the reward stinger should resolve
upward (RESEARCH §5.3: Mario's coin is a rising fourth; the genre's level
sounds rise and resolve).

**What to build.** Keep the darkness, then let the light in: play the
minor figure quickly (0, 3, 7 at 50 ms apart), then land on a **held major
third and fifth an octave up (16, 19)**, the Picardy third, the old
"dark, then light" cadence. Keep the low triangle and the air layer. For
milestone levels (the blessing levels) add the evolution's low saw under it.

**Where.** `godot/src/Audio/Sfx.cs`, `LevelUp` (one array and a timing
change).

**Cost.** Tweak.

**You'll know it works when** testers asked "what does this sound mean?"
say "level up" or "reward", not "loss" or "danger".

---

### S-05. A 120 ms dash buffer

**Feeling.** Responsive and fair: "everything is fudged a tiny bit in the
player's favor" (Celeste, RESEARCH §7.2).

**The problem** (AUDIT §7). A dash pressed while a dash, leap or rush is
still running, or while the charge is coming back, is consumed by
`Controls.Pressed` and dropped by `Battle.Dash`. Pressing a little early
does nothing. The dash is the game's skill expression (the perfect dodge),
so a dropped press costs most exactly when it matters.

**What to build.** In `WorldScene.Update`'s fixed step:

    if (Pressed(Act.Dash)) dashBuffer = 0.12;
    if (dashBuffer > 0) { if (b.Dash(mx, mz)) dashBuffer = 0; else dashBuffer -= Step; }

Do the same for the art in hand (`Act.Ability`). Read the direction at the
moment the dash fires, not when it was pressed. Clear the buffers when a
draft or overlay opens (`Controls.ClearLatches` is already called there).

**Start from.** 120 ms (RESEARCH §7.2: 100–150 ms is standard; over ~200
ms buffered actions misfire).

**Where.** `godot/src/Game/WorldScene.cs` (`Update`).

**Cost.** Tweak.

**You'll know it works when** mashing dash at the end of a dash never
"eats" a press, and the perfect-dodge rate rises a little for the same
player.

---

### S-06. Bars that flow; a bar about to fill that glows

**Feeling.** Anticipation. The bar nearing full is the cue that carries the
reward's dopamine (RESEARCH §3.1).

**The problem** (AUDIT §6). `Game.cs` refreshes the HUD at 12 Hz
(`hudT = 1.0 / 12`): the ember and health bars step in 83 ms jumps. The
kill count changes without a pop.

**What to build.**
- Move the bar fills to `GameHud._Process` (every frame), easing the shown
  value toward the true one (`1 − e^(−18·dt)`). Text can stay at 12 Hz.
- At **≥ 85%** full, the ember bar's leading edge brightens and the bar
  pulses (alpha 0.25 + 0.25·sin(8t)).
- On a level: the bar flashes white for 80 ms and the overflow carries into
  the new level visibly (it drains to the carried value over 150 ms).
- The kill counter pops (scale 1.15, back over 150 ms) at most ten times a
  second.

**Where.** `godot/src/Ui/GameHud.cs` (`Frame` around the ember fill,
`_Process`).

**Cost.** Small.

**You'll know it works when** the bar visibly *flows* during a lodestone
sweep, and testers can tell a level is coming without reading it.

---

### S-07. A particle budget with priority

**Feeling.** That the big moments survive the chaos.

**The problem** (AUDIT §6). `Sparks` holds 6,000 and refuses new spawns
when full. Projectile trails spawn about 12–18 live sparks each; the probe
measured up to 100–115 projectiles alive late in a run, plus burning
ground and gore. Late in a run, the moments that matter (a level-up's 30
sparks, a crit's glints, an elite's death) are what get dropped.

**What to build.**
- `Sparks.Spawn(..., bool important = false)`.
- **Ordinary spawns** (trails, burning ground, ambient) stop at **60%** of
  capacity.
- **Important spawns** (level-up, evolution, crits, elite and boss deaths,
  the perfect dodge, the chest) may use the rest, and when it is full they
  overwrite the oldest ordinary particle.
- Trails thin with numbers: with more than 150 projectiles alive, scale
  each trail's rate by `150 / n`.
- Count dropped important spawns in the `--log` line; it should stay 0.

**Where.** `godot/src/Fx/Sparks.cs` (`Spawn`), `godot/src/Fx/BattleFx.cs`
(`Projectiles`, `Zones`, the event cases that should be important).

**Cost.** Small.

**You'll know it works when** at minute 30 with a full build a level-up
still throws its full fountain, and the dropped-important counter is 0.

---

### S-08. The kill, not the hit: a multi-kill swell

**Feeling.** "Melting", "evaporating", the hum (RESEARCH §1.6, §8.2). In a
horde game the kill is the unit of satisfaction, and a crowd dying is
heard as one texture.

**The problem** (AUDIT §1, §5). Ordinary kills give no camera response
(right) and a kill sound gated to 5 per 90 ms at random pitches; a swarm
event dying is a scatter of identical thuds. Nothing marks the moment a
crowd goes down. Kills run 16–21 a second late in a run, 47–93 in a
burst (AUDIT §9).

**What to build.**
1. **Merge kill sounds** like S-02: kills within 33 ms become one voice,
   louder by log2(n), with a "crowd falling" layer (a short brown-noise
   burst, low-passed at 800 Hz, gain rising with n).
2. **A multi-kill swell.** Count kills credited to the player in a rolling
   **1.5 s** window. At thresholds (start at **15, 40, 80, 150**, and
   re-tune after S-01 raises kill rates) play a swell stinger, each a step
   up the same pentatonic ladder as S-02, with a sub thump (60 → 35 Hz,
   120 ms), trauma +0.08 / 0.12 / 0.16 / 0.2, and a rumble tick (S-14).
   Never more than one swell per 1.5 s.
3. **A bone layer** for the dead and the beasts: a dry, transient-rich
   crack (band-passed noise at 2.6–3.4 kHz, Q 4, two hits 45 ms apart:
   it is already there for the undead in `Sfx.Kill`), randomised ±3
   semitones. Halls of Torment players call this "skeleton bone crunch
   ASMR" (RESEARCH §8.2).

**Where.** `godot/src/Audio/SoundBridge.cs` (the streak state),
`godot/src/Audio/Sfx.cs` (`Kill`, a new `Swell`),
`godot/src/Fx/BattleFx.cs` (trauma on the swell).

**Cost.** Small.

**You'll know it works when** a sound-only recording of a swarm event
being cleared has an audible rise and a peak; players use words like
"melting" and "mowing".

---

### S-09. The chest as a sequence

**Feeling.** The jackpot. "My dopamine levels spike as soon as the
treasure chests start rolling and the music starts playing"; "Why would I
skip the animation? That's the best part of this game!" (RESEARCH §3.2).

**The problem** (AUDIT §3). A chest opens instantly on pickup:
`ArenaRun.OnPickup` runs `LevelUp.OpenChest` and shows an announcement
("A chest · Oathblade · Grave-Edge") with the generic loot sound. It also
comes rarely: a champion every fourth event (every 4–6 minutes) and the
heralds at 10 and 20.

**What to build.** A chest panel, built like `DraftPanel`:
1. **Pause** the fight (as the draft does) and dim the world.
2. **Anticipation** (0.4 s): the chest shakes, light leaks from the seam,
   a low swell rises.
3. **The reel**: for each item, icons cycle at ~12 a second, easing out
   over 0.9 s, landing with a clunk and a bell one step up the ladder
   (S-02). Each later item takes 0.35 s. Gold ticks up beside it with a
   coin ladder.
4. **An evolution** is held for an extra 0.4 s with a gold flare and the
   choir chord (S-10).
5. **Three jingles by tier**: 1 item, a 0.6 s bell figure; 3 items, 1.6 s
   with a drum and a pad; 5 items, 2.8 s with a choir pad and a gong.
   Music ducked 12 dB (RESEARCH §5 implications 10).
6. **Tiers**: Vampire Survivors' **1 / 3 / 5 items at 50 / 10 / 3%**
   before luck (RESEARCH §3.2), instead of today's 1 + 30% + 10%.
7. **Skippable** after 0.5 s (any key jumps to the result); from the
   third chest of a run, the sequence plays at double speed. Ceremony
   scales with contents, so the 20th chest is not "annoying as hell".
8. **The cue before it**: a champion carrying a chest wears a visible
   glint over it, so the chase starts when it walks in (RESEARCH §3.1).

**Where.** A `ChestPanel` in `godot/src/Ui/Panels.cs`; open it from
`godot/src/Game/GameMenus.cs` as the draft is opened (`hudMode = "chest"`);
`godot/logic/Play/Zones/ArenaRun.cs` (`OnPickup` hands the result to the
host instead of announcing it); `godot/logic/Sim/LevelUp.cs`
(`OpenChest`, the count); `godot/src/Audio/Sfx.cs` (the three jingles).

**Cost.** Medium.

**You'll know it works when** testers do not skip it for the first several
chests, and rate the last chest of a run as highly as the first.

---

### S-10. The evolution as a ceremony, mid-run

**Feeling.** "It clicked", "the build came online": a phase change the
player predicted and the game exceeded (RESEARCH §2.4, §8.2).

**The problem** (AUDIT §3). An evolution is a nova, a flash, trauma 0.3
and a chord, about the weight of an elite's death. Nothing frames the first
volley of the new weapon.

**What to build.**
1. **The moment (about 1.5 s):** on `Ev.Evolve`, slow the world to 0.25×
   for 0.6 s (`WorldScene` already has `slowmo`); duck the music −10 dB
   for 0.5 s; the weapon's HUD slot flares gold and its old glyph shatters
   into the new one; a name card ("Grave-Edge — the edge drinks") for 1.6 s.
2. **The showcase:** reset the evolved weapon's cooldown so it fires the
   moment time returns, with its effects at 1.5× scale, a sub thump, and
   trauma 0.3 on *that volley* (not on the card).
3. **The timing:** in arenas, offer evolutions from **minute 10**, as
   Vampire Survivors does (its first big spike comes at 11). If the build
   is ready earlier, the card says "ready at the tenth minute". Measure
   the minute of the first evolution with the probe and aim for a median
   between 11 and 16 (RESEARCH §8.3 #6: centred mid-run, with variance).

**Where.** `godot/src/Game/WorldScene.cs` (slow motion on `Ev.Evolve`),
`godot/src/Fx/BattleFx.cs` (the `Ev.Evolve` case),
`godot/logic/Sim/Battle.cs` (`Evolve`: reset the weapon's cooldown),
`godot/logic/Sim/LevelUp.cs` (`EarnedBranches`: the minute gate in
arenas), `godot/src/Ui/GameHud.cs` (the name card).

**Cost.** Medium.

**You'll know it works when** players asked for their best moment of a
run name an evolution.

---

## Tier 2: the moments and the rhythm

### S-11. The boss as the run's peak and its end

**Feeling.** Peak-end: a run is remembered by its most intense moment and
how it ended (RESEARCH §4.5). VS clears the screen to silence before the
Reaper; Halls of Torment players "remember your first boss kill way longer
than your first Reaper kill in VS" because they did something for it.

**The problem** (AUDIT §3, §4). The boss arrives with a shake, a title and
a stinger; dies with a 140 ms hit-stop, a blast and an announcement. The
minutes before it have no run-up.

**What to build.**
1. **The run-up (28:00):** an announcement ("The dark gathers"); the music
   drops to drums and drone; spawns ease off by 20% for 90 s: a valley
   before the peak.
2. **The arrival (30:00):** the camera turns to the boss (`FocusOverride`,
   blending as for conversations) for 1.2 s while the fight runs at 0.5×,
   then pulls back to 36 m for the fight.
3. **The kill:** the existing 140 ms hit-stop, then **0.8 s at 0.25×**;
   music cut to silence for 0.6 s, then a bell and choir chord; every
   ordinary creature within 20 m dies in rings outward from the boss, 30 ms
   per ring (the release); the boss's spoils thrown out in an arc and
   landing one by one 0.25 s apart, each with its rarity sound and beam
   (S-15); trauma 0.6; rumble at full for 400 ms.
4. Ration all of this to the boss: nothing else in the run gets silence.

**Where.** `godot/logic/Play/Zones/ArenaRun.cs` (`Step`, `Boss`,
`Victory`), `godot/src/Game/WorldScene.cs` (slow motion for any event, not
only the perfect dodge), `godot/src/Game/FollowCamera.cs`
(`FocusOverride`, `TargetDistance`), `godot/src/Audio/Music.cs` (a `Drop`
call: silence, then return).

**Cost.** Medium.

**You'll know it works when** players describing their last run mention
the boss and the build together; a video of the kill holds a viewer's
attention to the end.

---

### S-12. An arena that swells and breathes

**Feeling.** Flow, and escalation with release: rising peaks separated by
valleys, so each peak registers (RESEARCH §4.2, §4.3).

**The problem** (AUDIT §4). The horde's target count is a straight line
(`22 + 7.5 × minute`); events come every 60–85 s; chests only from
champions (every 4–6 minutes) and heralds. Vampire Survivors swings its
kept-alive count from 10 to 300 within the same few minutes and has a
boss or chest every 1–2 minutes (almost every minute after 10). Halls of
Torment, the other 30-minute run, is the one players call "torture".

**What to build.**
1. **Breathers.** After each event, 20–25 s with the target at 40% and
   the spawn tick doubled: time to collect, to see the board, to breathe.
2. **Floods.** At minutes 11 and 21 (after the heralds, as VS does after
   its Arcana bosses), 45 s at 1.8× the target with a spawn tick of
   0.15 s. Precede each by a quiet minute (minute 10 and 20 at 50%).
3. **More chests.** After minute 10, make every second event a champion
   with a chest (about every 2–3 minutes), and add a "lantern-bearer" every
   5–7 minutes: a fleeing creature, heard before it is seen, carrying a
   chest, gone after 12 s (Diablo III's treasure goblin, RESEARCH §3.3).
4. **A spawner that keeps up.** Today a group of 3–6 (+1 per 5 minutes)
   comes every 0.45 s while the field is under target; after S-01 the
   survivor kills faster than that and the field thins (S-01's
   experiment). When fewer than 60% of the target are alive, halve the
   spawn interval and double the group size, so a strong build *mows*
   rather than *waits*.
5. Keep the curve's average where it is; this reshapes it, it does not make
   it harder.

**Start from.** Target over time:
`base(m) × (breather ? 0.4 : flood ? 1.8 : 1)`, with `base` today's line.

**Where.** `godot/logic/Play/Zones/ArenaRun.cs` (`Target`, `Step`, `Event`).
Re-run `ARENA_PLAY=1` and the probe.

**Cost.** Medium (mostly tuning).

**You'll know it works when** the probe's "alive" column swings by 3× or
more within two-minute windows; testers stop calling the middle of the run
"samey"; no reward-free gap longer than about 20 s mid-run (RESEARCH §8.3 #9).

---

### S-13. Damage numbers that merge, rank and cap

**Feeling.** "Number go up", legibly; and seeing the fight through them
(RESEARCH §6.2).

**The problem** (AUDIT §6, §9). Every hit gets a number, from a ring of 48
labels living 0.75 s (≈ 64 a second). The probe measured 75–87 hits a
second at minute 30, up to 260 in a burst: numbers recycle mid-flight for
the whole second half of a run. DoT ticks show numbers 35% of the time. Only
crits stand out.

**What to build.**
- **Merge per target within 200 ms** into one number that rolls up as it
  grows and pops (scale 1.0 → 1.25 → 1.0 over 120 ms) each time.
- **Punch in**: each number spawns at 1.6× and settles to 1× in 60 ms.
- **Rank**: plain hits white (60 px); hits over 3× the run's median hit
  warm (72 px); crits gold (88 px) with a 2 px shake for 150 ms; a killing
  blow of 3× or more what was left (the gib threshold) red-gold (96 px).
- **Cap at 32 live numbers**; when full, drop the smallest non-crit.
- **DoT**: no per-tick numbers; a faint summed number per target every 0.5 s.
- **A setting**: numbers All / Big hits / Off (Vampire Survivors ships a
  toggle).
- Abbreviate past 10,000 (12.3k).

**Where.** `godot/src/Fx/Hits.cs` (`Number`, `Text`, `_Process`),
`godot/src/Fx/BattleFx.cs` (the `Ev.Hit` case), `godot/src/Game/Settings.cs`
and the settings menu.

**Cost.** Medium.

**You'll know it works when** a minute-25 frame shows ≤ 32 numbers, all
readable, and testers can tell their crit chance from the screen.

---

### S-14. Rumble

**Feeling.** Touch, weight; the third sense that makes congruence complete
(RESEARCH §7.1).

**The problem** (AUDIT §7). There is no rumble at all, though the game
supports a pad.

**What to build.** A small `Haptics` that sums requests into a per-motor
envelope each frame, clamps, rate-limits, and calls
`Input.StartJoyVibration(device, weak, strong, duration)` (in Godot `weak`
is the high-frequency motor, `strong` the low). Only when
`Controls.UsingPad`. A setting: Rumble Off / Low / Full.

**Start from** (RESEARCH §7.1):

| Event | Low (strong) | High (weak) | Duration |
|---|---|---|---|
| Your crit (not every one: ≤ 4 a second) | — | 0.2 | 30 ms |
| A multi-kill swell (S-08) | 0.2 per tier | 0.2 | 40 ms |
| Perfect dodge | 0.3 | 0.5 | 60 ms |
| A blow on you | 0.6 | 0.3 | 120 ms, decaying |
| Level-up | 0.4, gap 60 ms, 0.5 | — | 80 + 80 ms |
| Elite or herald killed | 0.7 | — | 150 ms |
| Boss killed, your death | 1.0 | — | 400 ms |

Ceiling 0.8 except the last row; at most one non-damage rumble per 250 ms;
never per ordinary kill.

**Where.** A new `godot/src/Game/Haptics.cs`, fed from
`WorldScene.OnEvents`; the setting in `godot/src/Game/Settings.cs`.

**Cost.** Small–Medium.

**You'll know it works when** pad players notice it and none call it a
buzz; the boss kill and the perfect dodge are the two they mention.

---

### S-15. Loot that announces itself, by rarity

**Feeling.** Anticipation, rarity: "you'd hear it. So the sound became
kinda emblematic of 'Something cool has dropped'" (Diablo, RESEARCH §3.3).

**The problem** (AUDIT §3). Gear lies on the ground as a sack (the "seed"
model) with the same 3.2 m beam for every rarity; only the colour changes.
It makes no sound when it drops. The level-up uses a 7 m vertical pillar,
the same shape as a loot beam, which dilutes the loot language.

**What to build.**
- **A drop sound by rarity, at the drop**: common none; uncommon a short
  glass tick; rare two notes; epic three notes; legendary a reserved bell
  with a sub (plays nowhere else). Positional.
- **A beam ladder**: heights 1.4 / 2.2 / 3.2 / 5 / 8 m by tier; the beam
  shoots up over 0.25 s when the item lands; legendary pulses at 1 Hz and
  casts a light; an edge-of-screen pip for epic and above.
- **Show the item**, not a sack: `ItemModels.Make` already builds a model
  per item icon (`helm`, `ring` …) for the pack's photographs; `BattleFx`
  already merges such models into batches (`Pickup(...)`).
- **Keep vertical beams for loot only**: give the level-up a ring or a
  rising spiral instead of `Pillar`.

**Where.** `godot/src/Fx/BattleFx.cs` (`Pickups`, `Ev.LevelUp`), a drop
event from `godot/logic/Sim/Battle.cs` (`SpawnPickup` for items and
chests), `godot/src/Audio/Sfx.cs` (a `Drop(rarity)`).

**Cost.** Medium.

**You'll know it works when** testers turn toward a legendary before they
see it.

---

### S-16. An end screen that tells the run's story

**Feeling.** Peak-end and one more run: a readable end, a framed near miss,
the run's best moment (RESEARCH §4.5, §4.6, §8.5).

**The problem.** `ArenaResultScreen` shows the time held, the kills, the
ember level, what you take out and what stays. It does not say what killed
you, how close you came, or what the run's peak was.

**What to build.**
- **The cause**: "Slain by a Kerchief cutthroat at 24:13"
  (`Ev.PlayerDeath.Killer` exists).
- **The near miss**: "6 minutes from Redcowl", or "Redcowl at 22%".
- **The peak**: your biggest blow and what dealt it; most slain in ten
  seconds; the evolution and the minute it came.
- **One more**: on a loss, "Again" (the rematch) as the first button.

**Where.** `godot/src/Ui/ArenaResult.cs`; `ArenaResult` in
`godot/logic/Arena/Arena.cs`; the peaks tracked in `Battle` (beside
`Profile`).

**Cost.** Small–Medium.

**You'll know it works when** players restart within ten seconds of a loss
more often (RESEARCH §8.3 #11).

---

### S-17. Your own blows kick the camera; arts land with hit-stop

**Feeling.** Weight, and attribution: the player knows *they* did that
(RESEARCH §1.3, §8.3).

**What to build.**
- **A directional camera kick** toward the player's own heavy blows: 0.25
  m toward the blow over 90 ms, back over 160 ms; for arts landing (the
  Crashing Leap, the Bull Rush's stop, the Shield Bash), crits of ≥ 35% of
  a target's health, explosions of power > 1. (Nijman's camera kick;
  rotational rather than translational shake is better in 3D, RESEARCH §1.3,
  so lean the kick into a 0.5° pitch nudge as well.)
- **Hit-stop on arts' impacts**: 60 ms on the leap's landing, 50 ms on the
  rush's stop (they already shake, `Arts.cs`; route them through
  `WorldScene.Weigh`).
- **More visible flinch**: `CrowdView` pushes a struck body 0.14 m; at a
  31 m camera that is a few pixels. Try 0.25 m, and 0.5 m on crits.
- **Knockback on crits ×2** (`Battle.HitEnemy`), capped per enemy per
  second so the crowd does not jitter.

**Where.** `godot/src/Game/FollowCamera.cs` (a `Kick(direction, amount)`),
`godot/src/Game/WorldScene.cs` (`Weigh`), `godot/src/Actors/CrowdView.cs`,
`godot/logic/Sim/Battle.cs`.

**Cost.** Small.

**You'll know it works when** testers say the arts "land".

---

## Tier 3: bigger systems

### S-18. A score that follows success, not only threat

**Feeling.** Escalation, "scoring your playthrough" (Darren Korb,
RESEARCH §5.6); the hum.

**The problem** (AUDIT §4). Music intensity is `hostilesNear / 18`; in an
arena that is high nearly all the time, so the score sits at one level for
most of 30 minutes (inferred). Mood changes jump at once; nothing in the
music knows about a level, a streak, the 15th minute or the boss's
approach.

**What to build.**
- **Intensity** = 0.4 × threat (today's measure) + 0.4 × success (kill
  rate against the minute's expected rate, rising over 2 s, falling over
  6 s) + 0.2 × the minute (m/30).
- **Stems**: pad always; bass from 0.15; drums from 0.4; ostinato and lead
  from 0.75; the boss's brass. Bring stems in and out **on the bar**, and
  crossfade the pad when the mood changes rather than restarting it.
  Hades picks stems semi-randomly per chamber to stay fresh; do the same
  per event.
- **Drops**: `Music.Drop(seconds)` for executions (S-10, S-11).
- **One key**: the XP ladder (S-02), the swells (S-08), the chest jingles
  (S-09) all in D minor pentatonic, so everything rewarding is in tune with
  the score.

**Where.** `godot/src/Audio/Music.cs`, `godot/src/Audio/SoundBridge.cs`
(`Update`).

**Cost.** Large.

**You'll know it works when** a recording of a whole run has an audible
arc: quieter valleys, louder floods, a run-up to the boss.

---

### S-19. A readability layer

**Feeling.** Fairness and signal in the noise: "LET US TURN DOWN OR TURN
OFF WEAPON EFFECTS I CANT SEE A DAMN THING" (RESEARCH §6.3, §8.2).

**What exists.** Good per-effect restraint, a reserved hostile red, ground
telegraphs.

**What to build.**
- **Friendly effects fade with density**: when the spark pool is above half
  full or there are more than 150 hostiles, scale the player's own additive
  effects to 60–70% alpha. Hostile projectiles and telegraphs are never
  faded and draw above the player's effects.
- **A silhouette for the survivor**, visible through effects and props (a
  second pass, low alpha, no depth test).
- **Settings**: Spectacle / Clarity presets that change particle *count and
  layering*, not only alpha.
- **Off-screen warnings**: an edge pip for a charge or a missile aimed at
  you from beyond the frame.
- **Never let death effects hurt** (Diablo IV's lesson): check the oath of
  bursting dead (`Rules.DeathBurst`) telegraphs clearly in a crowd.

**Where.** `godot/src/Fx/BattleFx.cs`, `godot/src/Fx/Sparks.cs`, the
survivor's materials, `godot/src/Game/Settings.cs`, `godot/src/Ui/GameHud.cs`.

**Cost.** Medium–Large.

**You'll know it works when** on a minute-25 screenshot a stranger finds
the survivor, the nearest threat and the nearest pickup within 300 ms
(RESEARCH §8.3 #8).

---

### S-20. Calm the first two minutes' draft flood

**Feeling.** Brain-off, and choices that matter. Deliberation spikes break
the trance ("until I realized I had to actually think about making a
coherent build", RESEARCH §8.2).

**The problem** (AUDIT §9). The probe counted 7–12 cards in the first
minute and 3–9 in the second, on top of the great blessing at the start.
That is a card every 5–8 s before the fight has any shape.

**What to build.** Raise the first few levels' cost a little so the first
minute gives about 5 drafts and the second about 4: start from
`EmberNeed = 12 + 12n + 1.6n²` for the first ten levels (today `12 + 9n`),
re-measured with the probe. Keep the fast start; it is the hook. Vampire
Survivors floods early too, so treat this as a tuning question, not a flaw.

**Where.** `godot/logic/Sim/Battle.cs` (`EmberNeed`).

**Cost.** Tweak.

**You'll know it works when** the probe's cards column reads about 5, 4,
3, 2 for minutes 1–4, and testers don't skim the first cards.

---

### S-21. Name the night's phases

**Feeling.** Escalation as a story (Risk of Rain 2 shows its difficulty
as a named ladder, RESEARCH §2.3).

**What to build.** The arena clock shows a phase name with a short sting
and a colour shift at each change: **Dusk** (0–5), **Gloaming** (5–10),
**the Witching** (10–20), **Ashfall** (20–28), **the Coming** (28–30),
then **Beyond**. Tie S-12's floods and S-11's run-up to the names, and
let the story name them per people where it wants to.

**Where.** `godot/logic/Play/Zones/ArenaRun.cs` (`Objectives`),
`godot/src/Ui/GameHud.cs` (the clock).

**Cost.** Small.

---

### S-22. Experiment: weapons that fire on the beat

**Feeling.** Rhythm and the trance (RESEARCH §8.3 #3: periodic events
invite entrainment; Tetris Effect makes the player "both player and
conductor").

**What to try.** Hold each weapon's fire until the next 16th of the score
(at 104 BPM a 144 ms grid; an auto-weapon's delay is not felt as lag).
Measure session length and an absorption question against free-running
cooldowns. Keep it only if testers prefer it blind.

**Where.** `godot/logic/Sim/Weapons.cs` (`Tick`), with the beat clock from
`Music`.

**Cost.** Medium; experimental.

---

## What not to do

- **No global hit-stop or shake on ordinary kills or hits.** At 20 kills a
  second, 33 ms each is two-thirds of real time frozen (RESEARCH §1.2).
  Keep the existing gating.
- **Don't celebrate trivial events like real wins.** It is the slot
  machine's "loss disguised as a win", and it devalues the real ones
  (RESEARCH §3.6, §5.7). Scale ceremony to value.
- **Don't add beams or bells to anything but loot of rank.** Reserved
  signals must stay rare (Diablo III removed the beam from rift keys,
  RESEARCH §3.3).
- **Don't rumble per kill**, or at full strength for anything but the boss
  and death (RESEARCH §7.1).
- **Don't answer "it doesn't feel powerful" with more particles.**
  Brightness is not weight: "Everything explodes but nothing has serious
  oomph" (RESEARCH §8.2). Fix the curve (S-01), the reaction and the sound.
- **Don't move juice to extreme.** Medium to high beats none and extreme,
  even on performance (Kao 2020, RESEARCH §0).
- **No real-money randomness, no rigged near misses** (RESEARCH §3.7).

---

## Measuring: the probe and the targets

`probe/` holds the program that produced AUDIT §9: the arena bot of
`godot/tests/ArenaPlay.cs`, counting per minute what feel depends on. From
the repo root, with the .NET 8 SDK:

    dotnet run --project docs/feel/probe -c Release -- 36

(The argument is minutes per case; four cases; about two minutes each on
a fast machine.)

Targets worth holding the arena to:

| Measure | Target | Today (AUDIT §9) |
|---|---|---|
| Blows per ordinary kill, minute 15 / 25 | ≤ 1.5 / ≤ 1.3 | 1.7–3.6 / 2.2–4.6 |
| One-blow kills, minute 25 | ≥ 65% | 4–26% |
| Hostiles alive, swing within a 2-minute window | ≥ 3× | ≈ 1.5× |
| Longest gap between reward events, mid-run | ≤ 20 s | not measured |
| Minute of the first evolution, median | 11–16 | not measured |
| Damage numbers alive at once | ≤ 32 | 48 (saturated) |
| Important particles dropped | 0 | not counted |
