# Audit: our bosses today

What the game's bosses do now, read from the code and measured with the
probe, set against what the research (`RESEARCH.md`) and the catalogue
(`MECHANICS.md`) say a boss should do. File and line references are to the
branch this was written from; nothing in `godot/` was changed.

## 1. The short version

- **The prologue's Ford-Warden is a real boss**, and a good one: a ward fed
  by three lamps, a charge you can steer into a lamp, a channel you break or
  pay for, two phase thresholds, a bar that shows all of it, and a dead
  man's hint for the devout. It is the template the arenas should grow from.
- **The arena boss is not a boss.** At the half hour the arena spawns its
  people's champion (the same creature as the champion events and, for three
  of the four peoples, the same creature as the heralds at ten and twenty
  minutes) with its health multiplied, fourteen escorts and a title. It has
  one verb (a lunge, or for Grimtunnel a lobbed pot), no phases, no
  telegraph beyond the lunge's lane, and nothing that changes the arena.
- **The probe says the fight is a damage check, and only that**: from a
  quarter of a minute to never, depending on the build, with the boss
  rarely the thing that hurts (§4).
- **The story's four night fights** (Greymuzzle, Redcowl, Grimtunnel, the
  Barrow Lord) are the same four creatures with a name on the bar.
- **The building blocks for much better are already in the code**: a boss
  hook (`BattleHooks.BossTick`), delayed strikes that telegraph themselves,
  enemy ground, interrupts, the perfect dodge, a damage-taken multiplier, a
  bar with phase marks, a channel and a shield state, a boss view with poses.
  Most of the designs in `SURVIVORS_BOSSES.md` are new data and new tick
  functions on top of these, not new engines (`IMPLEMENTATION.md`).

## 2. The arena boss, step by step

Code: `godot/logic/Play/Zones/ArenaRun.cs`.

| Moment | What happens | Where |
|---|---|---|
| Before | The heralds come at 10 and 20 (`people.Champion`, health × (4 + tier), × 1.6 at 20, damage × 1.2, a chest). A herald later than 29:00 is skipped. Nothing announces the half hour coming. | `Step`, `Herald` |
| 30:00 | `Boss()`: the boss def (`Spec.Boss ?? people.Boss`) spawns 18 m away at a random bearing, walking in, elite, health × (6 + 2 × tier), damage × 1.3, with 14 of the horde in a ring 5 m round it. Shake 0.45, a "danger" announcement titled "The half hour". | `Boss` |
| The fight | Events stop. The horde is kept at half its target, in groups of 4 every 0.9 s. The boss runs its ordinary creature AI: no `BossTick` is installed in the arena. | `Step` |
| The bar | Name, title, health. No phase marks, no channel, never shielded (the bar supports all three). | `Frame` |
| The kill | Won at once: the story told (`Arenas.Won`), a blue light and the way out where it fell, shake 0.35, "Victory" announcement. Loot: 2 + tier/2 plain items at rarity 1 or better, and a movement art's manual. **No chest.** | `Victory`, `OnLoot` |
| After | Heralds every five minutes; creatures harden by the minute (health × (1 + 0.1m + 0.006m²), damage × (1 + 0.035m), a level per two minutes). No boss returns, no end, no dawn. | `Spawn`, `Step` |

### Who the bosses are

| People | Boss def | Its verbs | Herald def | Same creature? |
|---|---|---|---|---|
| The Pack | `wolf_alpha` (the Pack-Mother; Greymuzzle in the story) | pack flanking; lunge 9 m, 0.6 s wind-up, every 4.8 s | `wolf_alpha` | **yes** |
| The Risen | `barrow_knight` (the Barrow Lord) | chase; lunge 8 m, 0.75 s, every 5.5 s | `barrow_knight` | **yes** |
| The Lamplings | `grimtunnel_roused` | chase; a lobbed firepot (burning ground) every 4.5 s | `lampling_sapper` | no |
| The Kerchiefs | `enforcer` (the Red Hand; Redcowl in the story) | chase; lunge 8.5 m, 0.7 s, every 5 s | `enforcer` | **yes** |

At tier 1 the herald at twenty has health × 8 (5 × 1.6) of its level, and
the boss × 8 of a slightly higher level: **the half hour's boss is the
twentieth minute's herald again**, without the chest. At higher tiers the
boss pulls ahead (tier 4: × 14 against × 12.8), but it is still the herald's
body, verbs and bar. A player meets the boss three times before it comes.

### What a boss is exempt from

Bosses take no knockback (`Battle.cs:606`), shorter stuns (0.2–0.6 s for
1–1.5 s), no fear, no freeze, no execute, no marked-prey kill, no status
other than stun past five stacks (`Battle.cs:794`), and a weapon's
`BossDamage` multiplier applies to them and to elites alike (`Battle.cs:543`).
This is the right instinct (a boss must not be locked down), but every
exemption is a removal: nothing is *added* in its place, so crowd-control
builds simply lose their verbs at the climax. `MECHANICS.md` §6 and §7
suggest turning the exemptions into the boss's own currency (stagger,
breaks).

## 3. The Ford-Warden, the boss we already have

Code: `godot/logic/Play/Zones/Prologue.cs:187-385`, view
`godot/src/Actors/BossViews.cs`.

| Feature | How it works | In the catalogue |
|---|---|---|
| The ward | Three lamp pylons; damage taken × `Ward[LitCount]` (most blows absorbed while all burn). The bar greys (`Shielded`). | Shields and breakable parts (§6) |
| Breaking it | Hit a lamp (260 health) or **lure its charge into one**: the charge snuffs the lamp and stuns the Warden for 4 s. | Arena as a weapon (§4); the boss's own verb turned (§8) |
| Cleave | Circle 3.4 m, 1.05 s fill telegraph, then 1.5 × damage, shake. | Telegraph language (§2) |
| Charge | Line up to 24 m, 1.3 s telegraph, "It lowers its head...", 17 m/s; a wall stops it short and stuns it. | Telegraph language; movement check (§1) |
| Channel | At 70% and 40% (and every 34 s): "RISE, YOU WHO DROWNED HERE." Raises two risen every 0.9 s for 6 s; a 9% health burst or any interrupt breaks it (stunned, takes × 1.5); finished, it heals 6% and relights a lamp. The bar shows the channel's progress. | Phases (§3); adds (§5); damage check with a stake (§1) |
| Telling | The watchman's book; for the devout, the dead man's whisper: "It shatters its own lamps when it charges. Make it charge." Tips on the lamps and the channel. | Teaching (§2.6) |
| Its view | A skeleton with hand-picked clips per pose, a lamp in its fist, a light whose glow follows the lamps lit. | Readability (§2) |

It is a by-day-sized fight (one boss, a few adds) in the prologue's night,
and it teaches exactly the language the arena boss never uses. Its gaps are
small: the channel threshold is a fixed share of health, so a strong build
skips it; no hard enrage; the victory is the prologue's story beat rather
than a ceremony.

## 4. Measured: time to kill and what the boss costs

`probe/` plays the arena bot of `docs/feel/probe` through the half hour,
with the survivor's damage multiplied by a "power" factor from the first
second (a stand-in for builds from weak to absurd; the bot drafts the first
card offered and has no gear, so ×1 is a weak player at tier 1, not an
average one). Columns: the heralds' and the boss's lifetimes, the boss's
health, the fraction of the survivor's health lost (summed, so above 100%
means they healed through it) and the lowest point. Run with:

    dotnet run --project docs/bosses/probe -c Release -- 0.25,0.5,1,2,4,10 1,2,4

Seventy-two runs: four callings (each against one people), tiers 1, 2 and
4, power × 0.25 to × 10. Each cell is how long the boss lived, or what
happened instead ("fell 24.8": the survivor died at 24:48; "in the fight":
after the boss came; "alive at 40:00": the probe stopped with the boss
still up).

| Tier | Power | Warden / Pack | Stalker / Risen | Arcanist / Kerchiefs | Reaver / Lamplings |
|---|---|---|---|---|---|
| 1 | ×0.25 | fell 30.8 (in the fight) | fell 25.4 | fell 22.5 | fell 39.6 (in the fight) |
| 1 | ×0.5 | 243 s | 106 s | fell 34.1 (in the fight) | 276 s |
| 1 | ×1 | 30 s | 39 s | fell 30.6 (in the fight) | 23 s |
| 1 | ×2 | 22 s | 39 s | 16 s | 18 s |
| 1 | ×4 | 9 s | 13 s | fell 18.7 | 11 s |
| 1 | ×10 | 5 s | 8 s | fell 15.8 | 4 s |
| 2 | ×0.25 | fell 24.8 | fell 17.7 | fell 16.3 | alive at 40:00 |
| 2 | ×0.5 | 128 s | fell 24.5 | fell 11.3 | alive at 40:00 |
| 2 | ×1 | 17 s | fell 9.7 | fell 30.4 (in the fight) | 29 s |
| 2 | ×2 | 13 s | 35 s | 32 s | 34 s |
| 2 | ×4 | fell 30.2 (in the fight) | 7 s | fell 20.2 | 16 s |
| 2 | ×10 | 8 s | 7 s | fell 8.9 | 10 s |
| 4 | ×0.25 | fell 8.5 | fell 19.8 | fell 6.9 | alive at 40:00 |
| 4 | ×0.5 | fell 30.5 (in the fight) | fell 21.6 | fell 13.6 | alive at 40:00 |
| 4 | ×1 | 119 s | fell 29.3 | fell 7.1 | 41 s |
| 4 | ×2 | 20 s | 13 s | fell 21.3 | 44 s |
| 4 | ×4 | 16 s | 26 s | fell 10.2 | 27 s |
| 4 | ×10 | 10 s | fell 20.1 | 14 s | 7 s |

Boss health at the half hour: 40,000–49,000 at tier 1, 61,000–76,000 at
tier 2, 123,000–152,000 at tier 4 (the four peoples differ by their
champion's base health).

What it says:

- **The boss lives about twenty seconds.** In the 39 runs that killed it,
  the median was 16–20 s at every tier; 34 of the 39 were under 45 s. Only
  the weakest winning builds (× 0.5, or × 1 at tier 4) took two to four
  minutes. A fight a strong build ends in 4–10 s cannot show a phase, a
  telegraph or an arena change, so whatever the boss is given, its length
  has to be governed first (`MECHANICS.md` §3, §7; the gates and floors of
  `SURVIVORS_BOSSES.md` §0.5).
- **The boss is rarely what hurts.** In 20 of the 39 won fights the boss
  landed no blow at all, and the median was none. Its worst single blow was
  13–40% of the survivor's health (once 64%). The danger at the half hour is the
  escort and the horde: seven of the 29 deaths came after the boss arrived,
  and they were the weak and middling builds being crowded, not out-read.
- **The herald is a longer fight than the boss.** In 27 of the 39 wins the
  herald at twenty lived longer than the boss did (it comes alone into a
  full horde; the boss walks in beside the survivor and is mobbed). With the same body
  and verbs (§2), the climax is indistinguishable from the minute-20 event.
- **Nothing ends a stalemate.** Four runs, all Grimtunnel against a weak
  reaver, were still going at 40:00 with the boss alive: he lobs pots from
  range, the bot cannot close, and there is no enrage.
- **Power changes time, not experience.** From × 1 to × 10 the fight goes
  from about 30 s to about 7 s; nothing about it changes but its length.

Caveats: the bot is the feel probe's (it moves by simple rules, drafts the
first card and has no gear or day levels), so absolute survival is noisy
(some ×4 and ×10 runs died early to the horde, since power multiplies only
the survivor's damage). The boss rows are what matter, and their direction
held for all four callings.

## 5. Against the catalogue

Each row is a family of mechanics from `MECHANICS.md`, what the arena boss
does with it today, and what the Ford-Warden does.

| Mechanic | Arena boss today | Ford-Warden | Gap |
|---|---|---|---|
| Movement check (§1) | A lunge lane (Pack, Risen, Kerchiefs); a pot's ring (Lamplings) | Cleave circle, charge lane, walls | Only one, and the same as the herald's |
| Damage check (§1) | The whole fight is one | The channel (9% in 6 s) | No stake beyond "it takes longer" |
| Telegraph language (§2) | Line from the lunge; circle from a pot or a `ScheduleStrike` | Circle, line, bark, pose | One hostile colour for everything; `Cone` exists in the enum but draws as a circle and nothing uses it; no audio cue tied to a telegraph |
| Phases (§3) | None | Two thresholds (channel) | No phase marks on the arena bar; no change of behaviour, music or arena |
| Arena shaping (§4) | None | The lamps, the river, walls that stop a charge | An arena is one round clearing of radius 84 m, ringed at its edge by twelve standing stones and six fires (`MapGen.cs:112`, `:543-553`); the boss is spawned beside the survivor wherever they are, and nothing in the fight uses the stones, the fires or the people's cover |
| Adds and the horde (§5) | 14 escorts; the horde held at half | Raises the drowned | The boss neither commands, feeds on nor reshapes the horde |
| Shields and parts (§6) | None | Lamps, the shield bar | — |
| Enrage (§7) | None | None (the channel heals) | A strong build kills it in seconds; a weak one can be kited by it forever while the horde stays at half (the probe's "alive at 40:00" rows) |
| Stealing or turning the survivor's tools (§8) | None | Its own charge turned against its lamps | — |
| Pacing at 30 and after (§9) | No run-up; after the win, heralds and a steepening curve with no end | — | No 28-minute valley, no endless boss, no natural end |
| Reward and victory (§10) | Won at once; items and a manual as sacks; no chest | The heart, Grimtunnel's theft (a story beat) | `docs/feel` S-11 covers the ceremony; the boss should also drop the run's best chest |

## 6. Smaller things found on the way

- **Heralds play the boss music.** `SoundBridge` picks `Mood.Boss` whenever
  a boss bar is up (`src/Audio/SoundBridge.cs:152`), and the arena puts the
  herald on the bar. The half hour therefore sounds like the tenth minute.
- **The bar rebuilds its phase marks every frame** (`GameHud.Boss` frees and
  re-adds them on each `SetBoss`, which `ArenaRun.Frame` calls every frame).
  Harmless today (no arena phases), wasteful once there are some.
- **The boss walks in from a random bearing 18 m away**, usually off the
  high camera's picture (31 m away at 64°), so the first the player sees of
  it is the bar.
- **A boss's escorts are drawn from the horde at random**, so they are
  never the boss's own (a Pack-Mother's wolves may be boars).
- **The boss drops no chest.** Every herald and champion does; the run's
  climax is the one fight without the genre's signature reward, while the
  arena carries on afterwards and the build could still use it.
- **Story arenas name the boss but do not change it.** Redcowl is an
  `enforcer` titled "Redcowl"; the Barrow Lord of the sealed door is a
  `barrow_knight` "Of the Seventh Legion". The story's best-written people
  meet the survivor as stat blocks.
- **Grimtunnel cannot die by the story** (he carries the heart to the
  bottom in Act 3), but the arena kills him. The Dig's arena outcome text
  already says "drove Grimtunnel back down": the fight should end that way.
