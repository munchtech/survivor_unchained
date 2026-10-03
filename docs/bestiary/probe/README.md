# The bestiary probe

A measuring program for `docs/bestiary`, not part of the game. It puts one
kind of creature (or one mix of kinds) round the survivor at a steady number,
gives the survivor one loadout, lets the balance lab's arena bot play for a
fixed time, and counts. It compiles `godot/logic` read-only, as
`docs/feel/probe` does.

## Running it

From the repo root, with the .NET 8 SDK:

    dotnet run --project docs/bestiary/probe -c Release -- OUT SEEDS SECONDS

`OUT` is where `runs.csv` and `summary.md` go (default `.lab/bestiary`),
`SEEDS` the seeds per cell (default 3), `SECONDS` each run's length (default
150). The committed results used 4 seeds and 150 s: 4,352 runs in about ten
minutes on four cores. `RESULTS.md` is that run's `summary.md`;
`runs.csv.gz` its every row.

## What one run is

- **The survivor:** a warden's body at character level 4 (170 health, 5
  armour, points in Might) for every loadout, so the loadout is the only
  difference. Their health is made enormous so every run lasts the full
  time and damage taken is a rate; it is reported as a percentage of 170
  health a minute. The ember is off: no levels, no drafts, the loadout is
  fixed.
- **The loadout:** one combat skill at rank 4 (fourteen of them), Volley with
  a grade III slayer (+32% against every family) or with +10 armour and +15%
  fire resistance, a Dawnpulse-and-Volley pair, and Volley with each of nine
  arts.
- **The creatures:** a group kept topped up every half second, arriving 15–19
  m away from out of sight, at creature level 5 (about minute ten of a tier
  2 arena). Rank and file in groups of 6–14; elites one at a time; champions
  (the arena's champion flag: ×3 health, a level up) two or three at a time;
  five mixes (`ROSTER.md`).
- **The bot:** the balance lab's arena bot (`godot/tests/ArenaPlay.cs` on
  `claude/cloud-balance-lab`), copied so the probe stands alone. **Plain:**
  gives ground when two or more press within 3.4 m, otherwise goes to the
  nearest creature and circles it, dashes out of a crush of three. **Deft:**
  also steps off a lunge's lane (dashing across it if late), out from under a
  pot and off burning ground, and closes on the nearest thrower when nothing
  presses. One change: with an all-melee loadout it closes to 2.2 m instead
  of 6 m, or a blade would never land.
- **The arts** are used on a simple rule: five or more creatures within 6 m,
  or a champion, a raiser or a caster mid-cast within 9 m; striking arts aim
  at that creature.
- **The oaths** are the map's rules (`MapOffers.Rules`) and pack size, on
  three groups and three loadouts.

## What it reports

Per run (`runs.csv`): kills, kills a minute, the median seconds from a
creature's first blow taken to its death (rank and file, and elites
apart), damage taken and as % of 170 health a minute, blows taken a minute,
the share of the survivor's blows that glanced off a guard, perfect dodges,
casts interrupted, the source that hurt most and its share.

## What it cannot tell you

- **It is not a run.** No draft, no blessings, no gear beyond the listed
  mods, no evolution, one skill. It measures matchups, not difficulty.
  Difficulty is the balance lab's job (`RISK_REWARD.md` uses it for the
  oaths).
- **A lone elite is fought standing.** The bot does not kite a single
  creature (its "give ground" needs two pressing), so elite damage is the
  cost of trading blows. The *ratios* between loadouts hold; the absolute
  hurt is a worst case.
- **Stalemates look safe.** A loadout that cannot kill slow guards takes
  little damage because nothing new arrives. `COUNTERS.md` brackets those
  cells.
- **The blight's poison on the survivor** ticks silently (no `PlayerHit`
  event), so the oath of the blight measures as nothing. Read its effect
  from the balance lab instead.
- **The raised dead** are counted with the director's risen (the director
  tops up only what is missing), so a raiser shows as fewer arrivals, not
  more creatures.
- **Level 5 only.** Ratios between loadouts drift as levels rise (crowds
  thicken, damage grows linearly and health quadratically); run it at other
  levels by changing `Level` in `Main`.
