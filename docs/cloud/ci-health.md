# CI and code health

What the cloud session on `claude/cloud-ci-health` did: automatic testing,
a review of the commits since `2c9860c` for correctness bugs, and a
benchmark of the fight under a great horde. Everything here is on that
branch for the main session to take or leave.

## The workflow

`.github/workflows/godot.yml` ("Godot" in the Actions tab) runs on every
push and pull request, on every branch. It has one job of about a minute
and a quarter:

1. checks out only `godot/` and `tools/ci/`, because the web build's assets
   aren't needed;
2. sets up .NET 8 and restores both projects from nuget.org, with
   `~/.nuget/packages` cached by the hash of the project files (there are
   no lock files);
3. **Test the logic**: `dotnet test godot/tests/Tests.csproj`, which runs
   every test, StoryLint among them;
4. **Summarise the tests**: `tools/ci/trx_summary.py` turns the run's .trx
   into the run's summary page: the counts, each failure with its message
   and the top of its stack, and the ten slowest tests;
5. **Build the game**: `dotnet build godot/SurvivorUnchained.csproj`, the
   whole game's C#, view layer included;
6. on failure, uploads the .trx as an artifact (`test-results`).

How to read a run: open it, and the summary sits at the top of the page.
If it is red, a failed **Test the logic** step means a test broke (the
summary names it), and a failed **Build the game** step means the view
layer doesn't compile. If **Summarise the tests** says there were no
results, the tests themselves didn't compile: read the Test step's log.

The opt-in bots (`ARENA_PLAY`, `STORY_PLAY`) and the benchmark
(`HORDE_BENCH`) stay off, because the workflow never sets them. The old
`desktop.yml` is untouched and still runs only by hand. A newer push to
the same branch cancels a run already under way.

## Bugs found

Two reviews read every change under `godot/logic`, `godot/tests` and
`godot/src` in `2c9860c..` (76 commits). The suite is deterministic: no
shared mutable statics, no unseeded randomness, and no clock dependence
in the new tests. `Items.Load` and `MapGen.Catalog` now publish only once
complete.

### Fixed, with a test

**F1. Every creature's tick allocated, and so did every ground zone's.**
- `logic/Sim/Ai.cs`, in `Update`: `b.Graves.Exists(g => Dist(g.X, g.Z, e.X, e.Z) < raise.Range)`.
  The lambda captures the parameter `e`, so C# allocates its closure at
  the top of `Update`. That happens on every call, for every creature,
  whether or not the creature raises the dead. At 900 creatures it cost
  about 30 KB a tick.
- `logic/Sim/Battle.cs`, in `UpdateZones`: the lambdas capture the loop's
  zone, so two closures were made for every living zone on every tick,
  pulsing or not. That was another 10 KB a tick.
- Together they made about 2.4 MB/s of garbage in a full arena, and a
  gen-0 collection every second or so: hitches on the main thread.
- **The fix:** a plain loop (`GraveNear`), and the zone's pulse moved into
  its own method (`ZoneTick`). Behaviour is unchanged: the benchmark's
  fingerprints are identical before and after, in Debug and Release.
- **The tests** (`tests/HordeBench.cs`, always on):
  - `A_great_horde_allocates_little_a_tick` fails on the old code (20.1 KB
    a tick at 300) and passes on the new (0.4 KB).
  - `A_great_horde_plays_the_same_twice` checks the same seed gives the
    same fight.

No other logic bug outside story and quests turned up.

### Reported, not fixed (story and quest logic: the story session's lane)

**R1. Once the stream runs clear, an allied or exploited Pack still has
blighted wolves in the Hollow.**
- **Where:**
  - `logic/Play/Zones/Verge.cs:354`: `if (F("beasts.outcome").Str != "cured") SpawnGroup("wolf_blighted", 3, ...)`.
  - The same test sets `sick` at `Verge.cs:304`.
  - `data/content/rules.json`: `stream.clear` now excludes the allied
    outcome. The new `stream.clear_allied` sets `stream.clear` but leaves
    the outcome at `"allied"`, and `stream.clear_sold` sets it to
    `"exploited"`.
- **Scenario:** ally with Greymuzzle, break the pump and sleep two or
  three days. `stream.clear` is now true, and the morning report says the
  stream runs clear and your wolves were drinking from it. Walk to Wolf
  Hollow and three `wolf_blighted` spawn. Before these commits, the allied
  path ended at `"cured"` and they stopped. Selling the cure does the
  same.
- **Verified** by a failing test (the code is below).
- **Proposed fix:** sick means the poison is still running. At `:304` and
  `:354` use `!F("stream.clear").Truthy && F("beasts.outcome").Str != "cured"`.
  The cured, exploited and allied rules all set `stream.clear`.

**R2. After a slaughtered Pack, bitterroot can still be dug up once the
poison has stopped.**
- **Where:** `logic/Play/Zones/Verge.cs:506`, where the `When` is
  `... != "cured" && !F("stream.clear").Truthy`.
- **Why:** nothing sets `stream.clear` when the outcome is
  `"slaughtered"`, even with the pump broken and `blight.days_clean >= 2`.
  So the root stays up for good, though its comment says "while the
  poison lasts".
- **Verified** by a failing test.
- **Proposed fix:** test `blight.days_clean >= 2` in the `When`. Or add a
  rule that sets `stream.clear` whenever `blight.days_clean >= 2`, which
  would also make R1's fix cover every outcome. Low severity.

**R3. A promise to the Pack can break through self-defence.**
- **Where:** `logic/Play/Zones/Verge.cs:745`. Any wolf the survivor kills
  breaks `promise.pack`, hostile or not.
- **Scenario:** kneel to Greymuzzle (the promise), then wear the
  `wolfhide_cloak`. `Standing.HollowCalm` (`logic/World/Standing.cs:39`)
  turns the Hollow hostile, and a wolf attacks. Kill it and the
  `broke_promise` deed lands: Maeca's trust −30 and affection −20, and
  Vonnra reads it as betrayal.
- **Verified** by reasoning only.
- **Proposed fix**, if only deliberate kills should count: gate it on
  `e.Disposition == Disposition.Neutral || e.Provoked`, the same test
  `:752` uses for `TurnHostile`.

**R4. An allied player is never "who cleared the water".**
- **Where:** `logic/World/Chapter.cs:82-83` tests only for the `"cured"`
  outcome, which the allied path no longer reaches.
- **Note:** this may be intended, since "Ran with the Pack" has a verdict
  of its own. Flagged for the story session to decide.

The test that shows R1 and R2 failing goes in `godot/tests`, against the
branch as it stood:

```csharp
static (Journey J, FakeHost Host, Verge Zone, Battle B, ZoneMeta Meta) Make(System.Action<Journey> before)
{
    var a = Callings.Archetype("warden");
    var j = Journey.Begin(new CreationChoice { Name = "Ashe", Archetype = "warden", Background = "hunter",
        Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 42);
    j.World.Time = TimeOfDay.Day;
    before(j);
    var meta = ZoneMeta.Load("verge");
    var host = new FakeHost(j, meta);
    var zone = new Verge(host, meta);
    var at = zone.ArrivalFrom("waystation");
    var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 11);
    b.Hooks = zone.Hooks; host.Battle = b; zone.Begin(b);
    return (j, host, zone, b, meta);
}

[Fact]
public void An_allied_pack_by_a_clear_stream_is_not_sick()
{
    var s = Make(j =>
    {
        j.World.Facts["prologue.done"] = true; j.World.Facts["beasts.outcome"] = "allied"; j.World.Facts["pack.allied"] = true;
        j.World.Facts["greymuzzle"] = "ally"; j.World.Facts["dig.pump"] = "broken";
        var c = new Ctx(j.World, j.Ch);
        for (int d = 0; d < 3; d++) Simulation.AdvanceDay(c, () => 0.5);
        j.World.Time = TimeOfDay.Day;
    });
    Assert.True(s.J.World.Fact("stream.clear").Truthy);
    var hollow = s.Meta.Place("V", "hollow");
    s.B.Player.X = hollow.X + 20; s.B.Player.Z = hollow.Z;
    for (int i = 0; i < 30; i++) { s.Zone.Step(1 / 60.0); s.B.Tick(1 / 60.0, 0, 0); s.B.Events.Drain(); s.Host.Pass(1 / 60.0); }
    Assert.DoesNotContain(s.B.Enemies.Living(), e => e.Def.Id == "wolf_blighted" && e.Tag == "hollow");
}

[Fact]
public void Bitterroot_is_gone_once_the_poison_stops_even_after_a_slaughter()
{
    var s = Make(j =>
    {
        j.World.Facts["prologue.done"] = true; j.World.Facts["beasts.outcome"] = "slaughtered"; j.World.Facts["dig.pump"] = "broken";
        var c = new Ctx(j.World, j.Ch);
        for (int d = 0; d < 3; d++) Simulation.AdvanceDay(c, () => 0.5);
        j.World.Time = TimeOfDay.Day;
    });
    Assert.True(s.J.World.Fact("blight.days_clean").Number >= 2);
    Assert.False(s.Zone.Interactables.Single(i => i.Id == "root0").When!());
}
```

### Reported, not fixed (the view layer: the main session's lane)

The view layer compiles cleanly. The review found no crashes, null
paths, use after free, per-frame leaks or unbalanced subscriptions.

**V1. On the woman survivor, the "Colours of her suit" and "Figure"
controls do nothing.**
- **Where:**
  - `src/Ui/Front.cs:348` (the Figure slider) and `:357` (the palette,
    now labelled "Colours of her suit");
  - `src/Actors/People.cs:94-100`, where `Loadouts.HerBody` becomes
    `"heroine"` whenever `heroine.glb` exists and `--body woman` isn't
    given, which is the default.
- **Why:**
  - `Heroine`, `HerPart` and `HerOutfit` never read `look.Cloth`,
    `look.Under` or `look.Figure`.
  - `heroine.glb`'s body mesh has no shape keys, so there's no "Figure"
    key to drive.
- **Scenario:** at creation, pick another palette or drag Figure. The
  figure rebuilds (its LookKey changed) and looks exactly the same.
- **Fix:** either dye the outfit's materials from `look.Cloth` (and give
  the heroine a figure control), or hide the two controls while the
  heroine body is in use. It's a product decision, so it's left alone.

**V2. Her hairstyle choice is dead too.**
- **Where:** `logic/Play/Loadout.cs:79` sets `Hair = her || ... ? null`,
  so `People.cs:99` always gives her `HerHairs[0]`. Character creation
  still offers women hairstyle buttons.
- **Note:** the comment and a test say this is intended, but the
  buttons promise a choice that isn't there.

**V3. Teleports whip the spring sims.**
- **Where:**
  - `src/Actors/HerJiggle.cs:54`;
  - `src/Actors/HairSway.cs:100` (the chain) and `:140` (the single
    mass).
- **Why:** each re-seeds only when it isn't live yet. `PlayerView` snaps
  `Position` (`src/Actors/PlayerView.cs:165`), and Blink moves the
  survivor 6-9 m in one step (`logic/Sim/Arts.cs:195`). So do the
  time-slip echo and a respawn.
  - **HerJiggle:** clamps position but not velocity. In a 60 fps
    simulation of a 6 m jump, velocity reached about 190 m/s and the
    bones slammed between full stretch and squash for about 0.2 s.
  - **HairSway's Verlet chain:** keeps the pre-jump `xp`, so each point is
    flung about the jump's length, and the hair whips for several frames.
- **Fix:** keep the last target in each sim. If the target moved more
  than about 1 m since the last frame, set `Live`/`live` to false so it
  re-seeds. It's a few lines and visual only, but these files are under
  active work, so it's left for the main session.

## The horde benchmark

`tests/HordeBench.cs`. Run it with:

```
HORDE_BENCH=1 dotnet test godot/tests/Tests.csproj --filter HordeBench_Run --logger "console;verbosity=detailed"
```

`HORDE_TICKS` sets how many ticks are timed (600 by default).

The setup:
- a generated tier-3 arena (its clearing and cover);
- a mid-game build:

  | Weapon | Rank |
  |---|---|
  | oathblade | 6 |
  | seeking_motes | 5 |
  | cinderfall | 5 |
  | arcweb | 4 |
  | knifestorm | 4 |
  | hallowed_ring | 4 |

- a survivor who can't die, drifting the way a player holding ground
  does;
- a horde kept topped up to 300, 600 and 900, a mix of the dead, wolves,
  footpads and archers at level 5;
- ten seconds of warm-up (the horde closes in), then ten seconds timed.

It reports the mean and 95th-percentile milliseconds a tick, the bytes a
tick allocates, the gen-0 collections, the kills, and a fingerprint of the
fight's end: the stream's state, the kills, the survivor, and every
creature's and projectile's place and health. A change meant only to
make the fight faster must leave the fingerprint unchanged.

**900 is the ceiling.** `Battle.Enemies` is a pool of 900, and
`SpawnEnemy` returns null beyond it. A horde of 1500 isn't possible
without raising the pool, so the benchmark stops at 900.

### Numbers (this container: 4 cores; Debug is what `dotnet test` runs)

| horde | build | ms/tick before | after | p95 before | after | KB/tick before | after | gen-0 / 600 ticks before | after |
|---|---|---|---|---|---|---|---|---|---|
| 300 | Debug | 0.56 | 0.47 | 0.76 | 0.66 | 19.8 | 0.4 | 1 | 0 |
| 600 | Debug | 0.88 | 0.89 | 1.12 | 1.11 | 29.2 | 0.5 | 1 | 0 |
| 900 | Debug | 1.37 | 1.28 | 2.10 | 1.89 | 38.7 | 0.5 | 1 | 0 |
| 300 | Release | 0.59 | 0.59 | 0.83 | 1.01 | 20.3 | 0.4 | 2 / 1200 | 0 / 1200 |
| 600 | Release | 0.75 | 0.70 | 1.32 | 1.22 | 30.0 | 0.5 | 2 / 1200 | 0 / 1200 |
| 900 | Release | 0.82 | 0.72 | 1.65 | 1.55 | 39.6 | 0.5 | 2 / 1200 | 0 / 1200 |

The fingerprints are identical before and after: Debug, 600 ticks,
`f94aef52…`, `dfb9d0d4…`, `22fb3ddaa…`; Release, 1200 ticks,
`92a59c89…`, `b9b1e107…`, `3b904b08…`. Small differences in time are
within run-to-run noise. The real gain is that allocations dropped by
about 80 times and the collections went with them.

### Where the time goes, and what was left alone

From a `dotnet-trace` sample of 900 creatures, 3000 ticks, Release:

| Share of the tick | Where |
|---|---|
| 75% | the creatures' AI (`Ai.Update`) |
| 54% | moving apart from each other (`Ai.FinishMove`), of which about 18% is pushing out of walls (`CollisionWorld.Resolve`, 17% of it in `Near`) |
| 8% | choosing a target |
| 5% | projectiles |
| 4% | the flow field |
| 3% | statuses |
| 3% | the spatial hash's queries |

The whole tick is about 0.7 ms at 900 in Release, roughly 4% of a 60 Hz
frame, so CPU work isn't needed. Two things were tried and left alone:

- **Storing colliders directly in `CollisionWorld`'s buckets**, instead of
  looking each one up by id, with a stamp in place of the `HashSet` for
  de-duplication. The fingerprints were unchanged, but the time was
  within noise (0.63 ms against 0.64), so it was reverted: not worth the
  change.
- **The separation loop in `FinishMove`.** Its results depend on the
  order creatures are pushed and on positions read live during the AI
  pass. Batching or caching positions would change the fight, so it
  wasn't touched.

If the pool is ever raised past 900, look at `FinishMove` first. Its
query of a 3 m cell grid gathers whole crowded cells; a finer cell for
separation alone would cut the candidates. The push order would change
with it, so prove it with the fingerprints and take a new baseline.
