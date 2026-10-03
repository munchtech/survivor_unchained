# Implementation: what the designs need from the code

How `SURVIVORS_BOSSES.md` and `ARPG_BOSSES.md` map onto the systems the game
already has, what is new, how big each piece is, and an order to build in
that buys the most for the least. Sizes: **S** a day or less, **M** two to
four days, **L** a week or two. References are to the branch this was
written from.

## 1. What already exists and carries most of it

| System | Where | Used by |
|---|---|---|
| A per-tick boss hook | `BattleHooks.BossTick`, called from `Ai.Update` for `e.Boss` (`Sim/Ai.cs:75`) | every boss script; today only the Prologue installs one |
| A worked boss script | `Prologue.WardenTick` (`Play/Zones/Prologue.cs:219-385`): modes, cooldowns, telegraphs, channel, stun, ward | the template; the Kiln Warden is nearly a port of it |
| Telegraphs | `Ev.Telegraph` (Circle, Line, Ring; Cone in the enum), drawn as ground decals with a fill (`Fx/BattleFx.cs:625`, `:910`) | every move |
| Delayed strikes that telegraph themselves | `Battle.ScheduleStrike(..., Side.Enemy)` (`Sim/Battle.cs:1146`); the enemy side is supported but nothing calls it with an enemy owner yet, so the first boss move to use it is its first test | slams, bursts, lobbed charges |
| Enemy ground | `Battle.SpawnZone(Side.Enemy, ...)` | slurry, bad air, burning ground, censers |
| Enemy missiles and lobs | `RangedSpec` (Lob, Zone, Count, Spread) | volleys, pots, pilum |
| Lunges with lanes | `LungeSpec`, `Ai.cs:104-180` | the Pack-Mother, the champions' lunges |
| A scripted charge | the Warden's charge is its own mode inside `WardenTick` (`Prologue.cs:269`, `:345`), not a `LungeSpec` | the Warden's echo, the Centurion's parting |
| Interrupts and the perfect dodge | `Battle.Interrupt`, `HurtPlayer(..., telegraphed)`, `PerfectDodge` | channels, the Toll, Duelist's Grace |
| A damage-taken multiplier | `Enemy.TakenMul` (`Battle.cs:550`) | wards, transitions (× 0), stagger windows |
| A boss bar with phases, a channel and a shield | `BossBar` (`Play/Zone.cs:40`), `GameHud.Boss` | every boss |
| Boss views with poses | `IBossView`, `WardenView` (`src/Actors/BossViews.cs`) | each boss's body |
| Walls at runtime | `CollisionWorld.AddCircle/AddBox/Remove/RemoveTagged`, which re-bake the flow field (`Sim/Collision.cs:80-118`) | cages, pits, pilum, beams, sliding rows |
| Light radius at runtime | `Battle.Rules.Light`, read every frame by `PlayerView` | the Pack-Mother's dark, Moonless |
| Burrowing | `EnemyState.Burrowed/Surfacing`, `Ai.Tunnel` | Grimtunnel's Under, the Thing in the Barn |
| Raising the dead | `RaiseSpec`, `Battle.Graves` | the Barrow Lord |
| Fleeing | `Behavior.Flee` | the Pack lying down, the Kerchiefs leaving, the thief |
| Breakable props | `BattleHooks.OnHitProp` (the Warden's lamps) | lamps, crates, standards |
| The great blessing draft | `Battle.GreatOwed`, `LevelUp.Draft(b, count)` | the Kindling's draft of four |
| Camera framing and slow motion | `FollowCamera.FocusOverride`, `WorldScene` slowmo | arrival and kill (with `docs/feel` S-11) |

## 2. New systems

### N1. The boss script and its contract (M) — the foundation

An `ArenaBoss` class per boss, chosen by the boss def's id and installed by
`ArenaRun.Boss()` as `Hooks.BossTick` (today the arena installs none).

- **Flag it as a boss first.** `ArenaRun.Boss()` spawns it with
  `elite: true` (`ArenaRun.cs:324`) and `Enemy.Boss` comes only from
  `def.Boss`, which only `ford_warden` sets; `BossTick` runs only for
  `e.Boss` (`Ai.cs:75`). Either add a `Boss` field to `SpawnOpts` and set
  it there, or set `boss.Boss = true` straight after the spawn; the
  champion defs stay unflagged, so a herald of the same def stays an
  elite. Without this no script runs, and the execute, fear, charm, full
  freeze and Mark Prey's kill below 20% (`Arts.cs:796`) keep cutting the
  fight short (`AUDIT.md` §2).

- **Phases**: a list of `(mark, floor, ceiling)`; the script holds health at
  the mark until the floor passes (overflow goes to `Break`), ends the phase
  at the mark or the ceiling, plays a 2.5 s stagger with `TakenMul = 0`, and
  calls the next phase's `Enter`. The bar gets the marks as `Phases` and a
  `Break` figure. This is `SURVIVORS_BOSSES.md` §0.5 and fixes the
  twenty-second boss on its own, before any new move exists.
- **Moves as data**: `Move(Name, Phase mask, Cooldown, Weight, Range, Telegraph
  (shape, size, wind-up), Effect)`, picked by a small scheduler; effects are
  calls into what exists (`ScheduleStrike`, `SpawnZone`, a lunge, a spawn).
  Keep the Warden's string modes for the odd ones.
- **Stagger** (§0.15): a meter on `Enemy`, filled in `Battle.ApplyStatus`
  where a boss's status is refused today (`Battle.cs:794`), shown under the
  health bar (`BossBar` gains `Stagger`); full, a 3 s hold with
  `TakenMul` × 1.25 and `Interrupt`, then 15 s of resistance.
- **Weakness** (§0.17): a hook from `Battle.HitEnemy` to the script when
  a boss is hit by its weakness's school during a named channel; the
  arena's opening card and the great blessing draft read the boss's
  weakness (one guaranteed answering card at 15:00).
- **Enrage**: timers from the bar going up (3:00 soft, 5:00 hard) that call
  the script's `Soft()` and `Hard()`.
- **The boss contract** in `ArenaRun`: the run-up at 28:00 (a sign at a
  bearing), arrival 12–14 m away on that bearing, its own escort, the
  horde's share during the fight (§0.4), its own chest (§0.11), oath effects
  on the boss (§0.12 as a switch per oath).
- Tests: a dummy survivor dealing × 10 damage cannot end a three-phase boss
  sooner than its floors; one dealing nothing sees every phase by its
  ceilings and meets both enrages. Extend `docs/bosses/probe` to report
  phase times.

### N2. Telegraph language (S–M)

- `Ev.Telegraph` gains a `Kind` (Blow, Ground, Safe, Wall), drawn in amber,
  violet, pale blue and grey with a distinct edge pattern each (filled,
  hatched, dashed, solid), so colour is never the only channel.
- Draw `Cone` (it falls through to a circle today, `BattleFx.cs:630`), and a
  moving ring (expanding or closing at a speed).
- An optional `Label` (a move's name over the boss for 1 s) and a `Sound` id
  played with the telegraph; boss telegraphs draw above the survivor's own
  effects.
- An accessibility setting that lengthens all wind-ups by 25%.

### N3. Breakable parts (S–M)

Parts as their own stationary `Enemy` (the lamps, valves, standard, cage
posts, the barn's segments) with an `Owner` id; their death calls the
script; the bar shows pips. Parts on a moving boss follow it each tick.
Today the Warden's lamps are props with health kept in the zone
(`pylonHp`); parts as creatures let every weapon, proc and tag work on them
without special cases.

### N4. Shaping the arena (M, in pieces)

- **Pits** (Grimtunnel, the barn): a collider plus an `InBounds` wrapper
  that refuses the cell; a decal. S.
- **Moving walls and cages**: exists in the collision world. The view has
  `AddProp` and `HideProps` (hide every prop of an id inside a circle,
  `ZoneView.cs:196`), which is enough to make a wall vanish; it needs a
  per-instance handle (`AddProp` returns nothing today; it would return a
  handle that can be removed or moved) and a slide for rows that move. S.
- **A rising band** (the Kiln flood): a zone of slow whose width grows; its
  creatures spawn only in it. S.
- **Dark and light**: `Rules.Light` changed over time by a script, and an
  `AtmosphereFor` lerp for the moon, the dawn and the boss's arrival. S–M.
- **The dawn line**: a straight front that crosses the arena, with the
  daylight side's rule (ember drain, creatures stilled). M.

### N5. Commanding the horde (M)

A small API on `ArenaRun` that boss scripts call: `Share(x)` (the horde's
target while the boss lives), `Line(def, n, from, facing, speed)` and
`Ring(def, n, centre, radius, closing)`, and `All(family, order)` with orders
Flee-to-point, Kneel (Stationary, then die), Charge. A new behaviour,
**March**: walk a heading in formation, keep station, `Guard` facing forward
(the Barrow Lord's lines, the Levy, the Legion). The Pack-Mother's crescent
is a `Ring` arc with a gap.

### N6. The survivor's own tools, turned (M–L)

- **Disable a weapon** for a time (the Toll): a flag on `WeaponInst`, skipped
  by `Weapons.Tick`, greyed with a kerchief in the HUD. S.
- **Take ember** (the Silver Ink, the dawn, the Centurion's toll):
  `Battle.LoseLevels(n)` that steps the bar and the level back without
  taking cards (decision 3 in `README.md`), and a spill of stones. M.
- **Enemy collects ember** (the Penitent): a pickup's target may be an enemy;
  a rival's "level" counter; its weapons fired from the survivor's own
  `WeaponDef`s with `Side.Enemy`. L: the riskiest piece in the set.
- **Hold a circle** (the lay-down): a player channel while inside a Safe
  telegraph, shown on the bar. S.
- **Allies change side** (the Barrow Lord's "Rise, and to me"): flip
  `Faction` for a time. S.

### N7. Ceremony, music and reward (S–M; mostly `docs/feel` S-11)

- The boss's own chest (`OnLoot`, one line) and its Named roll.
- `BossBar` gains `IsBoss`; `SoundBridge` plays `Mood.Boss` only for it, and a
  lighter herald mood for heralds (`AUDIT.md` §6). S.
- Per-boss deaths (lying down, sinking, the hole closing) as script `Die()`
  calls into the view and N5's orders. S each.
- Build the phase marks once per boss in `GameHud.Boss`, not every frame. S.

### N8. The Kindling at fifteen minutes (S–M)

Replace the announcement in `ArenaRun.Step` with: the S-12 breather, an
ember-core part (N3) and a lieutenant def per people with one move from its boss (N1),
and `LevelUp.Draft(b, 4)` when the core breaks in time.

### N9. The endless hour (M)

- **Echoes**: after the win, every five minutes spawn another people's boss
  script limited to its first two phases at 60% health, tinted
  (`view:echo`), and count links on the HUD. Needs N1 and at least two
  bosses.
- **The dawn**: the 50:00 atmosphere change, the 55:00 line (N4), the ember
  drain (N6) and `Finish()` as a win at 60:00 with its own result line.

### N10. Story hooks (S each)

New `ArenaSpec` fields or facts read by the scripts: Greymuzzle's "Let him
go" (`stream.clear`), Redcowl's crates (`be.crates`) and cage
(`caravan.survivors`), the Kiln Ford only if lit, the Centurion taking the
coin. Each needs a `StoryLint` check that its fact exists.

### N11. Day bosses (M each, after their zones exist)

The Slurry Engine fits the Verge today (`Verge.cs:596`). Keegan's duel and
the Keeper need Act 2's north gate and Silverstair, which are not built;
their scripts are the same N1 machinery run by a day zone, without the
horde, with `BossBar` and `SetBoss` as the Verge already uses them.

### N12. Measuring (S)

- The probe (`docs/bosses/probe`) reports phase times and Breaks once N1
  exists; run it after every boss lands.
- A day probe: the same bot in the Verge against the Slurry Engine at the
  zone's level with a day loadout, to set day bosses' health.

## 3. Each design's needs

| Design | Needs | Size |
|---|---|---|
| The contract for every boss (§0) | N1 (with stagger), N7, the multiplier (one line), the taught skill (a `Discovered` entry on the kill) | M |
| The Pack-Mother | N1, N5 (crescent), dark (N4), spectral lanes, Flee-to-point death | M |
| The Barrow Lord | N1, N5 (March, Ring), N3 (standard), lay-down (N6), allies stunned by his call | M–L |
| Grimtunnel | N1, N3 (three lamps), burrow (exists), pits (N4), the crate prop, an expanding ring (N2) | M |
| The Red Hand | N1, disable a weapon for 8 s (N6), cages (N4), N5 (Levy), a fleeing thief as the auto-aim priority | M |
| The Kiln Warden / Warden's echo | Port `WardenTick` to N1, lamps as N3, the flood (N4); a river map for the Kiln | S–M (echo), M (Kiln) |
| The Silver Penitent | N1, N6 in full (enemy ember, rival weapons, take ember), a return mechanic | L |
| The Thing in the Barn | N1, burrow, N3 (segments), sound-and-ring cues (N2), bad air (exists), pits | M–L |
| The Centurion | N1, N5 (a March that parts when the survivor stands still for 1 s), take ember (N6), a prompt | M |
| The Kindling | N3, N8, a lieutenant per people | S–M |
| Echoes | N9 and two or more bosses | S |
| The Dawn | N4 (line), N6 (take ember), N9 | M |
| The Slurry Engine | N1 in a day zone, N3 (valves), menders (adds with a task, one mend per valve), a master wheel to hold (an interaction), Snib's barks | M |
| Keegan | N1 in a day zone, labels as telegraphs (N2), a two-way prompt; Act 2's gate | M |
| The Keeper | N1 in a day zone, sliding rows (N4), hostages that targeting skips, stairs to the gallery, Act 2's Silverstair | M–L |

## 4. Build order

Most for least first. Each step is playable on its own.

1. **The cheap fixes (S, a day).** Flag the arena boss as a boss (N1's
   first bullet), which alone ends Mark Prey's execute of it and lets
   `BossTick` and the boss statistics see it; the boss's own chest; heralds
   off the boss music; the boss arriving on camera from a sounded bearing
   with its own escort; `Cone` drawn; the bar's marks built once. The
   climax stops being the herald again, and the reward stops being
   missing.
2. **The contract (N1, M).** Phases as gates with floors, ceilings and Break,
   enrages, the multiplier at × (12 + 2 × tier), applied to the four
   existing boss defs with no new moves. The probe should then show 45–60 s
   for strong builds and an end to the Grimtunnel stalemate. This is the
   biggest single gain.
3. **The Warden's echo (S–M).** Port `WardenTick` into N1 as the first real
   script, with its lamps as parts (N3). It proves the framework on code
   that already works and gives the table a boss everyone has met.
4. **Grimtunnel (M).** Burrowing exists; pits and three lamp parts are small;
   it ends the stalemate in the story's own words ("back down the hole").
5. **The telegraph language (N2, S–M)** before the bosses with many moves.
6. **The Kindling (S–M).** Puts a fight at the fifteenth minute and teaches
   each boss's first verse.
7. **The Barrow Lord and the Red Hand (M each).** Formations (N5) serve both,
   and the Legion later; the Toll is the first "your own tools" mechanic.
8. **The Pack-Mother (M).** Light and dark at runtime; the Greymuzzle exit.
9. **The Dawn (M).** The arena's natural end; needs "take ember" (N6).
10. **Echoes (S)** once four bosses exist.
11. **The Slurry Engine (M)**, the first day boss, in a zone that exists.
12. **Act 2 and 3** as their content lands: the Kiln Warden, the Thing in the
    Barn, Keegan, the Keeper, the Silver Penitent (the most expensive, last),
    the Centurion.

## 5. Risks

- **Clutter.** Boss telegraphs drawn under hundreds of creatures and the
  survivor's own effects. N2's draw order, the horde's share during the
  fight, and the particle budget of `docs/feel` S-07 are the mitigations;
  check in the running game, not headless.
- **The gate feeling like a cheat.** If the Break number and the stagger do
  not read, a floor looks like the boss refusing to die (Gungeon's lesson,
  `MECHANICS.md` §7). Make the Break loud.
- **Enemy ember (the Penitent)** touches pickups, levels and weapons at once;
  build it last and behind a flag.
- **Story facts.** Each story variant reads facts the lint must know about;
  add them to `StoryLint` as they are used.
