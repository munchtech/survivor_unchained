# How Survivor Unchained feels today, read from the code

An audit of the game's feel as the code makes it, set against the findings
in `RESEARCH.md`. Nothing here was seen running: this cloud session has no
GPU and no speakers. Everything is read from source, and where a judgement
depends on how a thing actually looks or sounds in motion it says so
(**inferred**). File references are to the `claude/vigilant-galileo-l6jqyx`
branch as of this audit.

Legend: **Strong** (keep, build on it), **Missing** (nothing does this yet),
**Off** (exists, but tuned or shaped against what the research suggests).

---

## The short version

The game already has more feel machinery than most survivors-likes ship
with: a trauma-model camera shake, gated hit-stop, a white-hot hit flash
with a squash and flinch, a perfect-dodge with slow motion, a pickup vacuum
with a "notice-hop", filmed flipbook blasts, decals, gibs, a layered
procedural sound set with variation and voice gating, and a score that
thickens with the fight. The foundations are sound and in places
thoughtful (the hit-stop cooldown so a crowd dying does not stutter; the
"small hot core in a faint halo" projectiles so bloom does not hide the
fight).

What is missing is mostly **the second layer: the moments, the ladder and
the budget.**

- **Moments.** The run's biggest rewards land flat. A chest opens
  instantly on pickup into a line of text. An evolution is a nova, a flash
  and a chord. The boss arrives with a shake and a title, and dies with a
  140 ms hit-stop. There is no reveal, no hold, no sequence anywhere a
  survivors-like puts its biggest dopamine.
- **Ladders.** Nothing escalates *within a burst*. Kill sounds do not climb
  with a multi-kill; the XP chime climbs, but in non-musical 50-cent steps
  and very quietly; the music's intensity reads only "how many enemies are
  near", not "how well it is going". The horde's size climbs in a straight
  line, with no swells and lulls.
- **Budget.** Every effect competes equally for a fixed pool of particles,
  sound voices and number labels. Late in a run, when the screen is
  fullest, the moments that matter most (a level, a kill streak, a crit)
  are the ones most likely to be dropped or drowned, and nothing ducks
  for them.
- **Touch** is the thinnest sense: no rumble at all, no input buffer for
  the dash, a HUD that updates at 12 Hz.

---

## 1. Impact

### What happens when a blow lands (from `BattleFx.Handle`, `Hits.cs`, `CrowdView.cs`, `vat.gdshaderinc`)

| Layer | Today | Verdict |
|---|---|---|
| Hit flash | `Enemy.Flash = 1` on every hit, decays at 11/s (`logic/Sim/Ai.cs:29`): ~90 ms. Shader squares it twice for a white-hot core (`hot⁴ × 2.2`, effectively the first ~30 ms), then a warm rim flare (`vat.gdshaderinc`). | **Strong.** Matches the 2–4 frame white flash of the research almost exactly. |
| Squash and flinch | Body scaled ±10% and pushed 0.14 m along the blow while the flash lasts (`src/Actors/CrowdView.cs:169-172`). | **Strong**, but small. At a 31 m camera, 0.14 m is a few pixels (**inferred**). |
| Knockback | `Knockback × stat × 7 / mass`, elites ×0.35, bosses none (`logic/Sim/Battle.cs:605-610`). Most weapons carry small values (0.25–0.5). | **Off (mild).** Horde games read mass through displacement of the crowd; small knockback keeps the crowd a wall (**inferred**). |
| Sparks | 4 sparks per hit, 10 on a crit, in the school's colours, 30% of them star "glints" (`BattleFx.Burst`). | **Strong.** |
| Blood | GPU spray scaled by damage share, splat decals that pool, dry and fade; gibs on a kill blow ≥3× remaining HP (≥2× on a crit), fire excepted (`Gore.cs`, `Battle.cs:670`). | **Strong.** "Overkill bursts the body" is exactly the right rule: it rewards power visibly. |
| Damage numbers | Every non-DoT hit gets a number; crits are larger (88 vs 60), gold, with "!" (`Hits.Number`). 48 labels in a ring, 0.75 s life, rise and fade, no scale pop. DoT ticks show a number 35% of the time. | **Off.** See §6. |
| Camera shake | Trauma model, shake = trauma², sum-of-sines noise, decay 1.4/s, max offset 0.7 m, roll 0.025 rad (`FollowCamera.cs`). Crit +0.04; player hurt +0.12–0.5; elite/boss kill +0.35; explosions up to +0.3; events +0.2; boss arrives +0.45. **Normal kills: 0.** | **Strong model, conservative tuning.** Shake almost never comes from *your* offence except crits and explosions. |
| Hit-stop | Gated (`WorldScene.Weigh`): boss kill 140 ms, elite kill 80 ms, a crit ≥35% of max HP 45 ms, a heavy hit on you (>12% max HP) 70 ms, shield bash 50 ms. Never twice within (stop + 0.3 s). The fight runs at 8% speed during the stop, camera and FX in real time. | **Strong design.** Values are in the research's range. Two gaps: no hit-stop for your *own* big landed arts (Crashing Leap, Bull Rush impact) beyond bash; and the boss kill (140 ms) is the same order as a single heavy blow, not a moment. |
| Slow motion | Perfect dodge: 0.38 s at 30% speed. | **Strong.** The only "bullet time" in the game; nothing else uses it (boss kill, last enemy of a swarm, evolution). |
| Anticipation | The swing animation and the damage are simultaneous with the arc (`Ev.Slash` emitted when damage is dealt). | **Fine for auto-weapons** (anticipation would delay damage); but the arc's 0.22 s sweep starts at full brightness, with no flash frame at contact (**inferred**). |

### Assessment

The per-hit layer is good. What is thin is **the scale of reaction between
small and big**: a crit adds 6 sparks, 28 px of font and 0.04 trauma; a
champion's death adds a flash, a blast and 0.35 trauma. There are only two
rungs. The research (and Vlambeer's list in particular) suggests three or
four: the tick, the hit, the *kill*, the *big kill*, the *chain*.

Normal kills are, as far as the code says, quiet to the camera and to the
time base: a burst of 10 sparks, 4 rising embers, a smoke puff and the kill
sound. In a survivors-like the kill, not the hit, is the unit of
satisfaction (see RESEARCH §1.6 and §8); hits are the means.

---

## 2. Power growth

### What the numbers say

- **Ember XP to next level** (`Battle.EmberNeed`): `12 + 9n + 1.6n²`, plus
  `6(L-20)²` past level 20. Level 10 needs 222, level 20 needs 760, level
  30 needs 2,218. Cumulative: 977 XP to level 10, 5,894 to 20, 20,261 to 30.
- **Weapon ranks** (`Content/Weapons.cs`): +20% damage, +4% area, +6%
  duration per rank, +1 projectile at ranks 4 and 7; max rank 8 (2.4× base
  damage). Six weapons, six passives. Evolutions at rank 8 with a
  catalyst passive: 19 weapons, two branches each.
- **Enemy level** (`ArenaRun.Level`): `2·tier − 1 + minute/2.5`. At tier 1
  a level-1 creature at the start, level 13 at the half hour.
- **Enemy health** (`Enemies.ScaleFor`): `1 + 0.38l + 0.035l²`. At level 13
  that is **10.6×** base health; damage `1 + 0.14l` = 2.7×.
- **Horde size** (`ArenaRun.Target`): `22 + 7.5 × minute`, capped at 320
  (380 after the win). 22 at the start, ~97 at 10 min, ~172 at 20, ~247 at 30.

### Assessment

- **Off: the treadmill may eat the power fantasy.** A rank-8 weapon is
  2.4× its rank-1 self; with passives, blessings and an evolution the real
  multiplier is larger, but the enemy at minute 30 has 10.6× the health.
  Whether the player *feels* stronger depends on whether **time-to-kill
  for an ordinary creature falls** across the run. In Vampire Survivors it
  plainly does (by mid-run the basic swarm evaporates on contact; the
  threat is volume, elites and the Reaper). Here, if ordinary creatures
  take as many hits at minute 25 as at minute 5, the run will feel like
  keeping pace, not ascending. **This is the single most important number
  to measure** (see SUGGESTIONS S-01). Inferred, not measured: the headless
  bot reports ember by the minute but not hits-to-kill.
- **Strong:** overkill gibs, evolutions with real behaviour changes
  ("Whirlwind", "Glacier Spear", "Tempest Coil" fork the web), rank pips on
  the HUD and on cards, "Fits your build" on draft cards, a draft that leans
  toward your tags and toward evolution catalysts (`LevelUp.cs`).
- **Missing:** a visible signal that a build has *come online*: an
  evolution is one event; there is no feedback for "you just crossed a
  threshold" (e.g. ordinary creatures now die in one hit, your clear rate
  just doubled). Players narrate this moment more than any other (RESEARCH
  §2, §8).
- **Missing:** big-number moments. Numbers are integers from the hit; no
  crit tiers, no "super-crit", no accumulation (the "number go up" of
  Balatro / Diablo / Brotato's end-of-wave tally).

---

## 3. Reward and anticipation

| Moment | Today | Verdict |
|---|---|---|
| Ember stones (XP) | Four tiers by value (≥4, ≥12, ≥40), sized 0.16–0.34 and coloured orange to white to pale blue (`BattleFx.EmberTiers`). Scatter, settle, bob and spin. | **Strong** (tiered gems are the genre's grammar). |
| The vacuum | Within pickup radius after 0.25 s: a hop *away* (3.5 m/s), then speed `1 + 80t²` capped at 36 m/s (`Battle.cs:1484-1499`). | **Strong.** The notice-hop is a known good trick. |
| Lodestone (magnet) | 0.4% × luck per kill. Pulls every ember and coin. Sound: the *dash* sound (`SoundBridge`: `PickupKind.Magnet: Sfx.Dash()`). | **Off.** The genre's single most cathartic pickup has a placeholder sound and no ceremony; the stream of gems arriving makes the XP chime run, but quietly. |
| Gold | 55% + luck on kills that carry gold; coin clip + two FM pings. | Fine. |
| Gear on the ground | Drawn as a **sack** (the "seed" item model) with a 3.2 m beam in the rarity colour; materials 1.4 m. Same beam for every rarity: only the colour changes. | **Off.** No rarity ladder in shape, height, sound or motion; a legendary looks like a common in a different tint. |
| Chests (champions, heralds) | On pickup, `OpenChest` runs instantly; the result is an `Announcement` ("A chest · Oathblade · Grave-Edge") and the loot sound. 1 item, 30% 2, 10% 3 (`ArenaRun.OnPickup`). | **Missing: the sequence.** This is the moment the genre is built round (RESEARCH §3.2). |
| Level-up | 0.35 s after the level the draft opens (`GameMenus.cs:153`); world FX: holy blast, a 7 m pillar, a flash, 30 rising sparks; sound: a **minor** arpeggio (0, 3, 7, 12, 15 semitones from D5) with a pad. HUD medal pops (scale 1.9 → 1 over 0.6 s). | **Strong body, off key.** A minor triad reads as melancholy, not gain (**inferred**; a deliberate dark choice, but the research favours a rising major-ish figure for reward and keeping minor for the score). |
| The draft | Scrim 72%, cards rise staggered 80 ms over 0.5 s, input armed at 0.38 s (guards against mis-picks), focus lifts the card 10 px, pick dims the others then closes 0.3 s later. Rarity shown as border colour and a word; evolution as gold "Legendary". Reroll, banish. 3 cards, 4 with luck ≥1.5. | **Strong UX.** **Missing:** no sound on card reveal or focus by rarity, no special entrance for a rare/legendary card, no hold-to-reveal; every draft is visually the same event. |
| Evolution | Arcane nova 9 m, 30-unit flash, trauma 0.3, an ascending major figure over 0.45 s with a low saw. | **Off.** The top of the reward ladder lands at roughly the weight of an elite kill. No slow motion, no name card, no first-volley showcase. |
| Discovery | Shares the evolution FX and plays a 3-note figure. | Fine. |
| Boss | Spawns with 14 escorts, shake 0.45, a "danger" announcement and stinger; boss bar. Dies: 140 ms hit-stop, a blast, flash, 0.35 trauma, the triumph stinger; a "Victory" announcement; a blue light where the way out opens. | **Off.** No intro camera, no music change before it, no slow-motion kill, no loot fountain (its 2–3 items and a manual drop as sacks). |

### Assessment

The game's reward *data* is rich (tiered ember, chests that can evolve,
rarity, manuals, tomes for the day) but its reward *presentation* is
uniform. The research is blunt that anticipation, not receipt, is where the
dopamine is (RESEARCH §4.1), and that the best games stage a delay with
escalating cues before the reveal (VS's chest, Diablo's drop sounds, PoE's
filter sounds, Hades' door icons). Survivor Unchained reveals everything
instantly.

---

## 4. Flow and escalation

- **Horde size climbs linearly** (`22 + 7.5·min`) with events every 60–85 s
  (ring, champion, stampede, swarm, in fixed rotation), heralds at 10 and
  20, the boss at 30. **Strong skeleton.**
- **Off: no breathing.** The curve has no designed valleys. The research's
  interest-curve and tension/release findings (RESEARCH §4) favour waves
  that swell and break (a crush, then a brief clearing in which to collect,
  then a bigger crush). Here the population target only rises; the events
  add on top. A clear-out does not happen unless the player's killing
  outpaces a respawn every 0.45 s.
- **Missing: the end-of-arc catharsis.** Vampire Survivors' late runs end in
  screen-clearing excess; Brotato's waves end in a tally; Hades' rooms end
  in a silence and a reward. The 30-minute mark here brings the boss, which
  is right, but the minutes 25–30 have no "run-up": no change of music, no
  rising danger cue, no visible countdown moment.
- **Strong:** the 15-minute great blessing (a mid-run spike of agency, the
  research's "second wind"), endless play after the win, the oath system
  (player-chosen difficulty).
- **Music** (`Music.cs`): D minor; mood switches to Combat when >4
  hostiles are within 20 m (smoothed); drum level follows
  `hostilesNear / 18`; Boss mood adds brass and a heavier drum. **Off:**
  intensity tracks *threat count only*. In an arena the count is nearly
  always high, so the score sits at one level for most of 30 minutes
  (**inferred**). Mood changes reset the step and chord at once (no
  crossfade, no transition on a bar line). Nothing in the music knows about
  the player's power, a kill streak, a level, the 15-minute blessing or
  the approaching boss.

---

## 5. Sound

The audio is synthesised at runtime (`Synth.cs`: tones, filtered noise, FM
bells, Kenney CC0 recordings for blows and bodies), four buses into a
shared reverb and a master compressor (−16 dB, 4:1, 4 ms attack, 250 ms
release).

### Strong

- **Layering is already there.** The physical hit is a recorded punch
  (heavy on crit) + a band-passed noise crack + a falling 130–160 Hz thump.
  Kills: a falling 95–115 Hz tone + filtered noise + a body or bone clip +
  a family-specific tail. Elite/boss kills add a 70→28 Hz sub drop and
  brown-noise rumble.
- **Variation:** random pitch on every layer (e.g. clip pitch 0.85–1.15,
  i.e. about ±2.5 semitones), random filter centres.
- **Voice gating** (`Synth.Gate`): hits max 7 per 70 ms, crit sweetener 3
  per 90 ms, kills 5 per 90 ms, XP 8 per 100 ms, explosions 3 per 150 ms.
  This is the right instrument against the "machine-gun" problem.
- **Spatialisation** of combat sounds by position: pan ±0.8 across 18 m,
  gain falls to zero at 32 m.
- **Perfect dodge** sound is the best in the set: a bright FM bell pair
  (E6, B6), a low whoomph, a high air layer.
- **Heartbeat** under 30% health, faster as it falls.

### Off

- **No priority or ducking for big moments.** The only duck is music
  under menus (`DuckMusic`). The master compressor will pump everything
  when booms land, which is an accidental, unshaped sidechain. A level-up,
  an evolution or a boss death plays at the same bus level as the
  hundred hits around it (**inferred**: whether it cuts through depends on
  how full the mix is).
- **The XP ladder is microtonal and faint.** `1150 Hz × 2^(streak × 0.5/12)`:
  the pitch climbs **half a semitone** per stone up to one octave (24
  stones), as a 50 ms sine chirp at gain 0.02 (the quietest sound in the
  game). Half-semitone steps sit between notes of any scale; the research
  on rising chains (Peggle, Mario coins, Balatro) uses scale steps that
  resolve. It resets after 0.7 s without a pickup.
- **Kills do not ladder.** A swarm dying is 5 kill sounds per 90 ms at
  random pitches. No multi-kill recognition, no rising sequence, no
  stinger at a streak.
- **Level-up is in a minor key**, see §3.
- **The magnet plays the dash sound.** The chest plays the generic loot
  sound. Gear on the ground makes **no sound when it drops**: the loot
  sound plays only when picked up or toasted.
- **Gating chooses by arrival, not importance.** The first 7 hits in a
  70 ms window play; a crit arriving eighth is silent apart from its own
  sweetener gate (**read**: `Hit` returns before the crit layer when its
  gate is full).
- **Music** as §4: one intensity axis, no transitions, no stingers on the
  beat.

### Missing

- A sub-bass "weight" layer on the *player's* biggest blows (arts, crits,
  evolution volleys).
- A loot-drop sound by rarity at the moment of the drop (Diablo's and PoE's
  most remembered feature).
- A sound for the build coming online, for a streak, for the last enemy of
  an event falling.

---

## 6. Sight

### Strong

- **One colour per school** (`Palette.cs`: fire orange, frost pale blue,
  storm blue-white, nature green, arcane violet, holy gold, shadow purple,
  physical warm white), with hot cores above 1 to bloom. Hostile is a
  separate red-orange (`HostileRim`, `HostileDanger`).
- **Telegraphs** on the ground in the hostile red: lanes for lunges, rings
  that fill for strikes, a flare at the end (`BattleFx.Ground/Ring/Lane`).
- **Projectiles drawn as the thing** (thrown axes whirl, daggers point,
  discs spin) with a small hot core in a faint halo so they never bloom
  into blobs.
- **Layered blasts** (flash, refracting shockwave ring, filmed flipbook
  burst, debris by school, thin smoke, a light, a scar decal), with an
  explicit rule that a "light" weapon pulse gets only burst and debris.
- **Corpses** lie 16 s then sink 3 s (160 max); blood pools dry; scars by
  school (scorch 9 s, frost 6 s, sigils 1.6 s). Permanence is there.

### Off

- **Damage numbers have no hierarchy beyond crit.** Every hit gets one.
  With 48 labels in a ring and a 0.75 s life, any more than ~64 hits per
  second recycles labels mid-flight (numbers vanish early) (**read**).
  Late in a run, hits per second will far exceed that (**inferred**). The
  research favours: aggregate per target, show crits and big hits louder,
  pop-scale on spawn (start ~1.5–2× and settle), and a setting to reduce or
  hide them.
- **The particle budget has no priority.** `Sparks` holds 6,000 and a full
  pool silently refuses new spawns (`Sparks.Spawn`: `if (count >=
  parts.Length) return`). Projectile trails spawn ~40 per second per
  projectile × trail factor, each living ~0.3–0.45 s: about 12–18 live
  sparks per projectile. A few hundred projectiles fill the pool, and
  then a level-up's 30 sparks, a crit's glints or an elite's death burst are
  what gets dropped (**inferred** from the arithmetic). The moments
  matter most exactly when the screen is fullest.
- **Loot beams have one shape.** See §3.
- **The HUD updates at 12 Hz** (`Game.cs:587`): the ember bar, the health
  bar and the kill count step in 83 ms jumps. A bar that *flows* and
  *flashes when nearly full* is a known anticipation cue (RESEARCH §4.3).
  The kill counter does not pop.
- **No screen-level response to your power**: no hue, bloom or vignette
  shift as the ember rises; the arena looks the same at level 3 and 40.

### Missing

- A "readability floor": nothing dims your own effects when the screen is
  dense, so enemy telegraphs compete with your own fire (the genre's most
  common complaint, RESEARCH §6.3). Today the defence is good restraint in
  each effect, not a system.
- A legendary/evolution "beam" visual language distinct from the gear beam.

---

## 7. Touch

### Input and the dash

- **Dash:** 5.5 m in 0.2 s (27.5 m/s), 0.3 s of i-frames, two charges
  recharging 2.6 s each; a perfect-dodge window of 0.18 s at the start of
  the dash; out of every dash a 0.8 s burst of +25% speed (`Abilities.Dash`).
  The perfect dodge refunds a charge, gives 1.5 s of sure crits and +30%
  damage, cracks the air for 12 × ability power with stun and knockback in
  3.2 m, and slows the world for 0.38 s. **Strong: this is the best piece
  of feel design in the game.** It turns the one input the player has into
  a skill expression with a payoff.
- **Off: no input buffer.** Presses are latched until a fixed step reads
  them (`Controls.Pressed` → `latched.Remove`), but `Battle.Dash` rejects
  the press while a dash, leap or rush is running or when out of charges,
  and the latch is already consumed: a dash pressed 50 ms before the
  current one ends is lost (**read**). The research's buffer windows are
  ~100–150 ms (RESEARCH §7.2).
- **Movement:** exponential approach to target velocity, `1 − e^(−14·dt)`
  (63% in ~70 ms, 95% in ~210 ms). Responsive, with a touch of weight.
  Facing turns instantly with velocity. **Strong.**

### Rumble

- **Missing entirely.** No call to `Input.StartJoyVibration` anywhere. The
  game supports a pad (`Controls.cs`). On a controller, the hit, the kill
  streak, the perfect dodge, the level-up and the boss would all be felt
  in the hands (RESEARCH §7.1).

### Camera

- Follow with velocity lead (2.2 × 0.2 × speed, damped at 3/s),
  damped look (7/s in XZ), steep three-quarter view; arenas at 64° pitch,
  31 m. **Strong.**
- **Missing:** no camera "kick" in the direction of your own blow (the
  research's directional shake/recoil), no zoom or framing for the boss
  arrival and death, no pull-back as the build's reach grows. `FocusOverride`
  exists and is used only for conversations.

---

## 8. The ineffable, read from the code

The research's synthesis (RESEARCH §8) is that "it just feels good" is
mostly **congruence** (every sense reporting the same event in the same
~100 ms), **contrast** (quiet before loud, small before big), **rhythm**
(events landing in a pattern the body can entrain to), **escalation**
(each instance of a thing a bit more than the last) and **attribution**
(the player knowing that *they* caused it).

How the code stands against each:

- **Congruence: mostly strong.** A hit is flash, squash, sparks, blood,
  number and sound on the same tick. The weak links are the HUD's 12 Hz
  updates and the gated sounds (the eighth hit in 70 ms is seen and not
  heard). Rumble, the third sense, is absent.
- **Contrast: weak.** Few quiet moments (the horde never thins by design);
  few ceremonies that stop the eye. The big moments lack the silence or
  hold before them that makes them big.
- **Rhythm: accidental.** Weapons fire on independent cooldowns (0.65–4.6 s),
  music on a 104 BPM grid; nothing aligns them. Peggle, Balatro and the
  survivors-likes players call "hypnotic" create rhythm out of repetition
  (RESEARCH §8.3); here, rhythm comes only from the swing cadence.
- **Escalation: missing at the small scale.** Nothing grows within a chain
  (sounds, numbers, shake). At the large scale the horde grows, but so does
  its health, so the player's experienced power may not.
- **Attribution: good for the dash, thin for the weapons.** In an
  auto-attack game, the player's choices are the draft and the movement.
  The draft's "Fits your build" line is the right instinct. What is missing
  is the payoff that names the choice: the first volley after an evolution
  framed, the first one-hit kill noticed, the multi-kill traced back to the
  weapon that made it.

---

## 9. Measured: the headless arena, minute by minute

The repo's own arena bot (`tests/ArenaPlay.cs`: go to the fight, give
ground when pressed, collect ember, dash out of a crush, take **the first
card offered**) was run with a probe that counted what feel depends on.
The probe was a scratch program outside the repo that compiled
`godot/logic` read-only; nothing in the game was changed. Four cases,
tier 1, no oaths, 36 minutes each (six minutes past the boss).

Caveat: the bot drafts blindly. A player choosing for synergy will do
better. But the *direction* of every trend below was the same for all
four callings, which is what matters here.

### Hits to kill an ordinary creature (direct blows, not DoT ticks)

| Minute | Warden / pack | Stalker / dead | Arcanist / kerchiefs | Reaver / lamplings |
|---|---|---|---|---|
| 2 | 1.7 (35% one-hit) | 1.4 (64%) | 3.0 (15%) | 1.5 (69%) |
| 5 | 1.6 (37%) | 1.4 (65%) | 2.9 (14%) | 1.4 (74%) |
| 10 | 2.1 (26%) | 2.1 (44%) | 3.4 (5%) | 1.4 (71%) |
| 15 | 3.0 (19%) | 2.6 (35%) | 3.6 (9%) | 1.7 (58%) |
| 20 | 3.4 (15%) | 3.6 (17%) | 5.1 (2%) | 1.9 (38%) |
| 25 | 3.2 (12%) | 3.9 (26%) | 4.6 (4%) | 2.2 (24%) |
| 30 | 3.9 (6%) | 4.4 (5%) | 4.6 (2%) | 3.5 (11%) |
| 35 (after the win) | 7.7 (0%) | 6.0 (1%) | (fell at 30.6) | 4.7 (3%) |

**This is the most important finding of the audit.** In every case the
ordinary creature gets *harder* to kill as the run goes on, even with six
weapons at rank 8 and several evolved. The share of creatures that die to a
single blow falls from between a quarter and three quarters of all kills
to about one in twenty. The genre's core promise (you start fragile and end
a god; the swarm that once threatened you now evaporates) is inverted in
the numbers. The player's power is expressed only as *volume* (kills per
minute roughly doubles, from ~550 to ~1,200), never as *ease*.

### Other numbers that set budgets

| Measure | Early (min 2–5) | Mid (min 15) | Late (min 30) | Peak in any 1 s |
|---|---|---|---|---|
| Direct hits per second | 5–16 | 30–48 | 75–87 | 170–260 (to 690 after the win) |
| Kills per second | 4–9 | 11–14 | 16–21 | 47–93 |
| Ember stones collected per second | 4–11 | 11–15 | 14–22 | 400–840 (lodestone sweeps) |
| Projectiles alive | 2–30 | 13–56 | 22–100 | 115 |
| Kills that burst the body (gibs) | 30–55% | 31–37% | 32–39% | |
| Crit rate (of hits) | 5–16% | 8–16% | 7–15% | |
| Ember level | 9–17 at min 2 | 32–41 | 47–57 | |
| Drafts per minute | 7–12 in minute 1, 3–9 in minute 2 | 1–3 | 1 | |

What these mean for feel:

- **Damage numbers:** at 75–90 hits/s late (and 250 in a burst), the 48
  labels with 0.75 s life (≈64/s) are saturated for the whole second half
  of every run. Numbers recycle mid-flight.
- **The XP chime:** lodestone sweeps deliver 400–800 stones in a second.
  The XP sound is gated to 80/s and its ladder tops out after 24 stones
  (0.3 s), then sits on one pitch. The best moment for a rising ladder
  plays as a flat buzz (**inferred** from the gate and the formula).
- **Kill sound:** gated to ~55/s; kills peak at 47–93/s. Fine on
  average, clipped at peaks.
- **Drafts:** 10–20 cards in the first two minutes, then one a minute
  from about minute 10. The early flood means many drafts are taken in
  quick succession, which the research links to choice fatigue and to
  each choice mattering less; the late trickle means the second half of
  the run has few reward beats other than chests (RESEARCH §3.4).
- **Gibs:** a third of all kills burst the body throughout. Good, but
  because it never rises, it cannot carry a sense of growth.
- **The boss minute** (31) is visible as a dip in kills: the horde is
  held at half while the boss lives.
