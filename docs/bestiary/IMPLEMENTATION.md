# Implementation: what each proposal needs, in build order

Every proposal in this folder mapped onto the code as it stands, sized, and
ordered by value for the work. Nothing here has been built; the main session
decides. Sizes: **XS** under an hour, **S** half a day, **M** one to three
days, **L** a week or more. "Data" means a change to `Content/Enemies.cs`,
`Maps/MapOffers.cs` or JSON only; "view" means a creature also needs a look
in `godot/src/Actors` (`Visuals.Tint`, `Beasts`, `CrowdView`), which for most
proposals is an existing model with a tint, a scale and a prop.

## The order

| # | What | Why first | Where | Size |
|---|---|---|---|---|
| 1 | **Tuning the measured problems** | four numbers, each fixing a finding | see below | XS |
| 2 | **Telegraph caps** | keeps every later addition fair | `Ai`, `Battle` | S |
| 3 | **Seven creatures from verbs already written** | doubles the Lamplings, widens every people, nearly free | data + view | S each |
| 4 | **Champion Signs, phase A** (from existing specs) | the biggest gap in the horde, mostly made of parts that exist | `Enemy`, `Ai`, `Battle`, `ArenaRun` | M |
| 5 | **The table tells more** | the scouting step that makes counters fair | `MapTable`, `MapOffers` | S |
| 6 | **Signature events** | gives each people its moment | `ArenaRun.Event` | M |
| 7 | **The death that teaches, the bestiary that grows** | the relaxed player's tutorial | `ArenaResult`, `Book.Codex` | M |
| 8 | **Auras and mending** (new verbs) | buffers and healers, and three Signs | `EnemyDef`, `Ai` | M |
| 9 | **Enemy hazards that hurt the horde** (a decision) | turns exploders and lobbers into tools | `Battle.SpawnZone`, strikes | S |
| 10 | **Thieves** (`Flee`, `Steal`) | the purest opt-in risk | `Ai`, `Battle` | M |
| 11 | **Oaths repriced and the Weight** | rewards that match risk | `MapOffers`, `MapTable` | S |
| 12 | **Contested ground** | the sweatiest offer, mostly data | `MapOffers`, `ArenaRun` | M |
| 13 | **Flyers** | the crows | `Ai`, `Collision` use | S–M |
| 14 | **A threat-budget spawner** | once the roster is twice today's | `ArenaRun` | L |
| 15 | **Gear answers** (`flanking`, of the Cinder-Walker) | with `docs/items` phase 2–3 | `Items`, Marks | S |

## 1. Tuning the measured problems (XS)

| Change | Where | From → to | Finding |
|---|---|---|---|
| The Lamplings' champion and herald | `MapOffers.Peoples`, the `lamplings` entry, `Champion` | `lampling_sapper` → `lampling` until the Blasting-Cart exists, then `blast_cart` | a thrower herald with ×6 health is a chase (`ROSTER.md`) |
| A champion's guard | `Battle.HitEnemy`, the guard block | `guard.Reduction` → `e.Elite && !e.Def.Elite ? Math.Min(guard.Reduction, 0.6) : guard.Reduction` | champion bruiser: 56–99 s kills for projectile builds |
| The oaths of the blight and of champions | `MapOffers.Oaths`, `blight`, `champions` | blight Gear 1 → 1.6; champions Gear 1.6 → 1.3 (or keep 1.6 once its champions bear Signs); per `RISK_REWARD.md` §4 | blight: lowest health and most falls; champions: easier than unsworn |
| Mirror Step's reflections | `Arts` (mirror step), `Ai.ChooseTarget` | champions and heralds skip decoys, or reflections live half as long | halves or thirds the damage of every role |
| Raised dead give no ember | `Battle.KillEnemy`: skip `DropEmber` for an enemy spawned by `Raise` (a flag set in `Ai`'s raise) | – | raising is never a farm |
| Frost lock | `Battle.ApplyStatus`, `StatusKind.Chill` | chill on the frozen extends the freeze → it does not; a creature just thawed cannot freeze again for 3 s (elites 5 s) | anything chilled twice a second stays frozen for good (`DEPTH.md` §7) |
| Poison on the survivor | `Battle.Tick` (`p.PoisonT`) | silent → a quiet `PlayerHit` each second with `Source = "poison"` | a death by poison is named after the last creature to hit |
| Sapper burst | `Enemies`, `lampling_sapper` | `Burst` 1.2× → 1.0×; `Ranged.Cooldown` 4.4 → 5 | melee's worst rank-and-file matchup |

## 2. Telegraph caps (S)

`HORDES.md` §3.2. Each is a counter on `Battle` filled in the same pass that
counts `rangedAlive` (`ArenaRun.Step`) or kept live, and one condition:

- **Wind-ups at once** (`Ai.Update`, the `lunge != null` branch): before
  `e.State = EnemyState.Windup`, if `b.WindupsAlive >= cap`, set
  `e.RangedT = 0.5` and carry on. Cap `2 + tier / 2`, at most 4 (`Battle`
  needs the tier: put it on `MapRules`).
- **Underground at once** (`Behavior.Tunneler`): if `b.Burrowed >= 8`, walk.
- **Bursts fusing** (`KillEnemy`, the oath of ruin's burst): skip while 6
  `strikes` of `Side.Enemy` are pending.
- **Enemy ground** (`SpawnZone(Side.Enemy, ...)`): at 12, release the oldest.
- **Aura sources**: in `ArenaRun.Spawn`, a kind with an aura when one is
  alive becomes the people's first kind.

A unit test per cap in `godot/tests/BattleTests.cs` (spawn ten tuskers in
range, tick, count wind-ups).

## 3. Creatures from verbs already written (S each)

All of these are `EnemyDef` entries whose verbs exist and are unused or used
by one creature. Each needs its numbers (`ROSTER.md`), a line in its
people's `Arena` list in `MapOffers.Peoples` and a look.

| Creature | Spec(s) | Look (reuse) | Notes |
|---|---|---|---|
| Ridge-Runner | `Orbit` + `Lunge` | `wolf`, paler tint, 0.9 scale | the lunge code runs for any behaviour; check that `Orbit`'s slot steering and the lunge's state machine do not fight (a test: it lunges within 10 s of reaching its ring) |
| Slurry Sow | `Chase` + `Trail` (nature) | `boar`, green glow tint (`Visuals.Tint` already glows) | `TrailSpec` is wired in `Ai` (`def.Trail`); it shares `RaiseT` as its clock, harmless for a creature that does not raise |
| Bone-Heap | `Chase` + `Split` into `risen` | `skeleton_warrior`, ×1.5 scale, a bone pile prop | `SplitSpec` is wired in `KillEnemy`; `CrowdVisuals` already follows `Split.Into` |
| Wick | `Pack` | `lampling`, ×0.75, a candle prop | – |
| Lamp-Pole | `Stationary` + `Ranged` with `Count = 3`, `Spread = 0.3` | a lamp-post prop as a creature (new visual, simple) | `Count` and `Spread` are wired in `Ai.Shoot`; family Construct; knockback already skips stationary |
| Levy Crossbow | `Ranged` with `Count = 3`, `Spread = 0.22` | `kerchief_hooded` with a crossbow | – |
| Blasting-Cart | `Charge` + `Burst` | two lamplings and a cart (new visual, the only real art cost here) | a cart that hits a tree is stunned as a tusker; consider bursting on the tree too (small code) |

## 4. Champion Signs, phase A (M)

`COUNTERS.md` §4. Today `EnemyDef` holds every verb and `Enemy` holds none,
so a Sign needs a way to give one creature a verb its kind does not have.

- **Data.** `Content/Signs.cs`: `SignDef { Id, Name, Colour, Tags, Apply(Enemy) }`
  and the forbidden pairs. Phase A, the Signs built from existing parts:
  Swift (speed, lunge cooldown), Ironbound (a per-creature `IronSkin`),
  Kindled (a trail), Rimed (a per-creature `HitChill`), Brood (a split),
  Volatile (a burst), Shielded (a guard), Gravebound (a raise).
- **The creature.** `Enemy` gains nullable instance verbs (`Trail`, `Burst`,
  `Split`, `Raise`, `Guard`, `IronSkin`, `HitChill`) and a `Signs` list. Every
  read of `e.Def.Trail` and the rest becomes `e.Trail ?? e.Def.Trail` (about
  ten sites in `Ai` and `Battle.HitEnemy`, `KillEnemy`, `HurtPlayerRaw`).
  `SpawnEnemy` clears them.
- **Who bears them.** `ArenaRun.Event` (case 1, the champion) and `Herald`
  roll Signs by `COUNTERS.md`'s count table, skipping forbidden pairs; the
  1.2% random champions of `Group` bear one from tier 2.
- **Telling the player.** The champion's name on `BossBar` and on the
  champion bar, "Swift, Kindled Barrow Knight"; a tint and an outline per
  Sign in `CrowdView` (the Sign's colour on the champion's rim light).
- **Tests.** No forbidden pair is ever rolled (a thousand seeds); a Brood
  champion's young are not champions; a Shielded Sign never lands on a
  guard.

Phase B (after item 8): Bannered, Mending, Leader, Warded.

## 5. The table tells more (S)

`DEPTH.md` §5.1.

- `Denizens` gains `Question` (one line) and role glyphs come from each
  kind's `Behavior` and verbs (a function, no data).
- `MapTable` adds the question under "Held by", a reward line from the
  oaths' multipliers and the Weight (item 11), and on hover the kinds'
  icons and **your build against them**: for each school the survivor's
  day skills and gear carry, the people's average resistance
  (`Enemies.Get(kind).Resists`), shown as "+50%" or "−35%".

## 6. Signature events (M)

`HORDES.md` §4.3. `ArenaRun.Event` has four cases in a fixed rotation;
make the rotation `[ring, people's first, champion, people's second, swarm,
...]` and give `Denizens` two event ids. The Pack's Hunt is today's stampede.
The rest are short functions in the style of the existing cases:

- **The Ring** (Pack): spawn wolves at slots on a 7 m ring with a `Hold`
  timer (a new 2 s state, or reuse `Stunned` with no stun effect), then
  release.
- **The Ford Rises** (Risen): `SpawnEnemy(... Style = Rise)` on a 10 m ring;
  the rising state already makes them helpless for 1.1 s.
- **The Shield Line** and **The Wall**: a row of guards across one bearing,
  throwers 4 m behind; lower the guards' steady weight.
- **The Dig Opens**: set every burrowed tunneler to `Surfacing` with a
  shared 0.8 s ring.
- **The Ambush**: two groups at opposite bearings.

## 7. The death that teaches, the bestiary that grows (M)

- **Death.** `Battle.PlayerDeath` already carries the killer's id; record
  the killing blow's kind (contact, lunge, missile, ground, burst) in
  `HurtPlayer` (the `telegraphed` flag and the source name are there) and
  map it to one sentence per kind of blow, shown on `ArenaResult`.
- **Bestiary.** `World.Bestiary` already counts kills by creature. In
  `Book.Codex`, add a creature's role and tell at 10, what answers it at 50,
  its resistances at 200. The text lives on `EnemyDef` (`Tell`, `Answer`)
  in the voice of `Note`.

## 8. Auras and mending (M)

Two small specs and their tick, written once:

```
public sealed record AuraSpec(double Radius, string Stat, double Value, double Every = 0, double For = 0);
public sealed record MendSpec(double Every, double Cast, double Radius, int Count, double Pct);
```

- `AuraSpec` with `Every = 0` is constant (the Ford-Lamp's ward: allies
  inside take `Value` less, via `Enemy.TakenMul` set each tick); with
  `Every > 0` it is a pulse (the Old Howler's 4 s haste). Applied in `Ai`
  for the creature that carries it, to its own faction within the radius.
- `MendSpec` reuses the raise's cast state (`EnemyState.Casting`, the ring
  telegraph, `Interrupt` already stops it).
- Creatures: Old Howler, Ford-Lamp, Bell-Ringer, Levy Drummer, Goodwife.
  Signs: Bannered, Mending, Leader (Leader's rout is `StatusKind.Fear` on
  its escort, which `ArenaRun` already groups).
- Hunter's Mark and `Seek.Strongest` should rank aura and mend carriers
  first (`Battle` line ~1283: add them to the `1e6` bonus that elites get).

## 9. Enemy hazards that hurt the horde (S, and a decision)

Today enemy ground, pots and death bursts hurt only the survivor
(`Side.Enemy`). Letting them hurt the horde too (at half, with no credit)
turns every lobber and exploder into a tool the sweaty player can aim, and
costs the relaxed player nothing. It also makes the oaths of embers and ruin
double-edged in the player's favour, so their rewards would need a look.
**Decision for the owner** (README).

## 10. Thieves (M)

`Behavior.Flee` and `EnemyState.Fleeing` exist and do nothing. Write the
branch: run from the survivor along the flow field's reverse, toward the
nearest ember stones (`b.Pickups`, kind `Ember`); on touching one, take it
(count it on the creature); after 20 s, burrow or leave the field and
release. On death, drop what it took ×1.5 and gold through `OnLoot`.
The Cutpurse's blow-steals-gold is a hook in `HurtPlayerRaw` when `from` is
a thief. Visual: a gold outline seen across the arena.

## 11. Oaths repriced and the Weight (S)

`RISK_REWARD.md` §4: change the multipliers in `MapOffers.Oaths`, add a
`Weight` to `OathDef`, sum it on the card and in the reward line. A test
that the table never offers a total Weight above the tier's ceiling.

## 12. Contested ground (M)

A `Denizens` made from two (`MapOffers.Contested(a, b)`), its `Arena` list
both peoples' kinds; `ArenaRun.Pick` draws one people's kind per group and
spawns the two peoples from opposite halves of the ring. `Battle.DefaultWar`
already sets them at war. The boss is the stronger people's; the Lean is
both banes. Offered by `MapOffers.Today` from tier 3, one card in three.

## 13. Flyers (S–M)

A `Flies` flag on `EnemyDef`: `Ai` skips `b.Flow` and `FinishMove` skips
`Collision.Resolve` for it; `CrowdView` lifts it 1.5 m. Orbit behaviour as
today. Check that the survivor's ground-targeted skills (fields, novas) still
hit it: they test distance in the plane, so they will.

## 14. A threat-budget spawner (L)

`HORDES.md` §4.4: threat costs per kind, a budget by tier and minute, and
the spawner filling with fodder when it is full. Only worth it when the
roster is twice today's; until then, the weights in `Denizens.Arena` and the
caps of item 2 do the job.

## 15. Gear answers (S, with `docs/items`)

- `flanking` (prefix, weapon and off-hand): "Your projectiles strike guarded
  creatures as if from the side, one time in four" (a chance to skip the
  guard block in `HitEnemy`).
- **of the Cinder-Walker** (Mark, body and cloak): standing in burning
  ground, Steel skills strike 30% faster and the survivor takes 50% less
  from it (`ModWhen.InBurning` already exists in `Stats`).

## The probe as a tool

`probe/` builds against `godot/logic` read-only and runs a full sweep in about
ten minutes. Re-run it after items 1, 3 and 4 and compare `RESULTS.md`: the
guard row, the lobber row and the elite rows are the ones these changes
should move. Its creature list and loadouts are arrays at the top of
`BestiaryProbe.cs`; adding a new creature is one line.
