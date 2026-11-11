using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The fight, headless: the web game's battle tests, ported.</summary>
public class BattleTests
{
    internal static StatBlock BaseStats()
    {
        var s = new StatBlock();
        s.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = 140, [Stat.Regen] = 0, [Stat.Armor] = 2, [Stat.MoveSpeed] = 5, [Stat.PickupRadius] = 2.4,
            [Stat.CritChance] = 0.05, [Stat.CritDamage] = 1.5, [Stat.Luck] = 1,
        });
        return s;
    }

    internal static Battle Arena(uint seed = 1, params (string Id, int Rank)[] weapons)
    {
        var col = new CollisionWorld(120);
        for (int i = 0; i < 20; i++)
            col.AddCircle(-30 + i % 5 * 12, -30 + i / 5 * 12, 0.6, new ColliderOpts(Tag: i == 0 ? "barrel" : null));
        return new Battle(new BattleSetup
        {
            Seed = seed, Collision = col, Combat = true, Stats = BaseStats(),
            Weapons = weapons.Length > 0 ? weapons.ToList() : [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
        });
    }

    static Battle ArenaWith(uint seed, List<(string, int)> weapons)
    {
        var col = new CollisionWorld(120);
        for (int i = 0; i < 20; i++) col.AddCircle(-30 + i % 5 * 12, -30 + i / 5 * 12, 0.6);
        return new Battle(new BattleSetup { Seed = seed, Collision = col, Combat = true, Stats = BaseStats(), Weapons = weapons, Ability = AbilityKind.ShieldBash });
    }

    /// <summary>Headless survivor: drifts, spawns a ring of the dead, takes every draft.</summary>
    internal static void Simulate(Battle b, double seconds, double spawnEvery = 1.2, string def = "risen", bool press = false)
    {
        const double dt = 1.0 / 60;
        double spawnT = 0;
        for (double t = 0; t < seconds; t += dt)
        {
            spawnT -= dt;
            if (spawnT <= 0)
            {
                spawnT = spawnEvery;
                for (int k = 0; k < 3; k++)
                {
                    double a = b.Rng.Next() * Math.PI * 2;
                    // The horde's level rises as an arena's does: every two and a half minutes.
                    b.SpawnEnemy(def, b.Player.X + Math.Cos(a) * 14, b.Player.Z + Math.Sin(a) * 14,
                        new Battle.SpawnOpts { Level = 1 + (int)Math.Floor(t / 150), Style = SpawnStyle.Rise });
                }
            }
            // Drift slowly, the way a player holding ground does, rather than fleeing.
            double mx = Math.Cos(t * 0.35) * 0.35, mz = Math.Sin(t * 0.35) * 0.35;
            if (press) PressAll(b);
            b.Tick(dt, mx, mz);
            while (b.DraftOwed) LevelUp.Choose(b, LevelUp.Draft(b, 3)[0]);
            b.Events.Drain();
            if (b.Over != null) break;
        }
    }

    /// <summary>A player's thumbs: every pressed or channel skill is pressed (and held) at the nearest foe.</summary>
    internal static void PressAll(Battle b)
    {
        foreach (var w in b.Weapons.ToArray())
        {
            if (!w.Pressed) continue;
            var foes = b.HostilesInRadius(b.Player.X, b.Player.Z, 20);
            if (foes.Count == 0) { b.HoldSkill(w.Slot, false); continue; }
            var near = foes.OrderBy(e => (e.X - b.Player.X) * (e.X - b.Player.X) + (e.Z - b.Player.Z) * (e.Z - b.Player.Z)).First();
            b.HoldSkill(w.Slot, true);
            b.PressSkill(w.Slot, near.X, near.Z);
        }
    }

    /// <summary>A late night's stones do not carpet the field: past the cap the rest of the ember is
    /// gathered into one hoard stone where the overflow began, which keeps every bit of it and does
    /// not cool.</summary>
    [Fact]
    public void Ember_past_the_cap_is_gathered_into_one_hoard_stone()
    {
        var b = Arena(1);
        b.Player.Iframes = 1e9;
        double dropped = 0;
        for (int i = 0; i < 500; i++)
        {
            var e = b.SpawnEnemy("risen", 40 + i % 25 * 0.6, 40 + i / 25 * 0.6)!;
            dropped += e.Def.Xp * Content.Enemies.ScaleFor(e.Level).Xp * b.Rules.EmberGain;
            b.KillEnemy(e, true, null);
            if (i % 25 == 0) b.Tick(1 / 60.0, 0, 0);
        }
        b.Tick(1 / 60.0, 0, 0);
        var stones = b.Pickups.Items.Where(p => p.Alive && p.Kind == PickupKind.Ember).ToList();
        Assert.InRange(stones.Count(p => p.Tier != Battle.HoardTier), Battle.EmberCap - 10, Battle.EmberCap + 10);
        var hoard = Assert.Single(stones, p => p.Tier == Battle.HoardTier);
        Assert.True(hoard.Persistent);
        Assert.Equal(dropped, stones.Sum(p => p.Value), 6);
    }

    /// <summary>(Codex audit SU-014) A kill's ember is kept whole however big: six stones at most, the last
    /// carrying the rest (a level-35 Pack-Mother is about 279; the night's split used to drop past 240).</summary>
    [Theory]
    [InlineData(39)]
    [InlineData(240)]
    [InlineData(279)]
    [InlineData(1000)]
    public void A_kills_ember_is_conserved_below_at_and_above_six_stones(double xp)
    {
        var b = Arena(1);
        b.Player.Iframes = 1e9;
        var e = b.SpawnEnemy("risen", 40, 40)!;
        b.Rules.EmberGain = xp / (e.Def.Xp * Content.Enemies.ScaleFor(e.Level).Xp * b.Rules.KillEmber);
        b.KillEnemy(e, true, null);
        var stones = b.Pickups.Items.Where(p => p.Alive && p.Kind == PickupKind.Ember).ToList();
        Assert.InRange(stones.Count, 1, Battle.StonesMost);
        Assert.Equal(xp, stones.Sum(p => p.Value), 6);
    }

    /// <summary>A battle whose survivor stands at the origin, untouched by anything else ("block": a Warding light
    /// rank; "dodge": the most dodge there is, three in four, on a seed whose first roll dodges).</summary>
    static Battle StatusArena(string how = "none")
    {
        var st = BaseStats();
        if (how is "block" or "dodge") st.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = 140, [Stat.Regen] = 0, [Stat.Armor] = 2, [Stat.MoveSpeed] = 5, [Stat.PickupRadius] = 2.4,
            [Stat.CritChance] = 0.05, [Stat.CritDamage] = 1.5, [Stat.Luck] = 1, [how == "block" ? Stat.Block : Stat.Dodge] = 1,
        });
        return new Battle(new BattleSetup { Seed = 3, Collision = new CollisionWorld(120), Combat = true, Stats = st, Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash });
    }

    /// <summary>How she is spared, for the status tests: "none" lets the hit land.</summary>
    static void Spare(Battle b, string how)
    {
        var p = b.Player;
        switch (how)
        {
            case "iframes": p.Iframes = 5; break;   // (a dash's or a dodge-roll's)
            case "leap": p.Leap = new Leap { Dur = 50, X0 = p.X, Z0 = p.Z, X1 = p.X, Z1 = p.Z }; break;
        }
    }

    /// <summary>(Codex audit SU-012) A frost missile chills only when it lands: never through i-frames, a leap or a block.</summary>
    [Theory]
    [InlineData("none", true)]
    [InlineData("iframes", false)]
    [InlineData("leap", false)]
    [InlineData("block", false)]
    [InlineData("dodge", false)]
    public void A_frost_missile_chills_only_a_landed_hit(string how, bool chilled)
    {
        var b = StatusArena(how);
        b.Tick(1 / 60.0, 0, 0);
        Spare(b, how);
        var p = b.Player;
        var pr = b.SpawnProjectile(Side.Enemy, p.X, p.Z, 5, School.Frost)!;
        pr.Radius = 0.28; pr.Life = 5; pr.Status = new StatusPayload(StatusKind.Chill, 1, 1, 2);
        b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(chilled, p.SlowT > 0);
    }

    /// <summary>(Codex audit SU-013) Burning and frozen ground set their burn and their cold only on a pulse that
    /// reached her; the burn is mitigated as the ground is.</summary>
    [Theory]
    [InlineData("none", School.Fire, true)]
    [InlineData("iframes", School.Fire, false)]
    [InlineData("leap", School.Fire, false)]
    [InlineData("none", School.Frost, true)]
    [InlineData("iframes", School.Frost, false)]
    [InlineData("leap", School.Frost, false)]
    public void A_ground_pulse_sets_its_status_only_when_it_reaches_her(string how, School school, bool reached)
    {
        var b = StatusArena();
        b.Tick(1 / 60.0, 0, 0);
        Spare(b, how);
        var p = b.Player;
        var z = b.SpawnZone(Side.Enemy, p.X, p.Z, 2, 10, 40, school)!;
        z.TickT = 0;
        b.Tick(1 / 60.0, 0, 0);
        if (school == School.Fire)
        {
            Assert.Equal(reached, p.BurnT > 0);
            if (reached) Assert.True(p.BurnDps < 40 * 0.25, $"the burn is mitigated as the ground is ({p.BurnDps})");
        }
        else Assert.Equal(reached, p.SlowT > 0);
    }

    /// <summary>(Codex audit SU-016) A blast finds every body it overlaps, whichever grid cell the body's centre is
    /// filed in: a small one just past a cell boundary, and a boss-sized one whose centre lies beyond the queried cells.</summary>
    [Theory]
    [InlineData(1.9, 1.0, 3.2, 0.45)]
    [InlineData(0.1, 1.0, 4.0, 3.5)]
    public void A_radius_hit_finds_bodies_across_cell_boundaries(double qx, double r, double ex, double radius)
    {
        var b = Arena(1);
        b.Player.Iframes = 1e9;
        var e = b.SpawnEnemy("risen", ex, 0.1)!;
        e.Radius = radius;
        b.Tick(1 / 60.0, 0, 0);
        Assert.True(Math.Abs(e.X - qx) <= r + radius, "the body overlaps the blast");
        Assert.Contains(e, b.HostilesInRadius(qx, 0.1, r));
    }

    [Fact]
    public void A_minute_of_fighting_kills_levels_and_stays_finite()
    {
        // The drifter (Oathblade rank 1, no presses) is a "fights at all" floor, not a strength bar. It read 133 kills
        // before bands round 8; grip damage x0.80 (d5d195064) put a whole cut (18.25) under a level-1 risen's 20 health,
        // so every risen takes two cuts: 39 kills. Passive play is meant to lose under the bands (docs/balance/m3_bands.md round 8).
        var b = Arena(1);
        Simulate(b, 60);
        Assert.True(b.KillCount > 35, $"kills {b.KillCount}");
        // (the same "fights at all" floor: level 2 with 39 kills under the bands)
        Assert.True(b.EmberLevel > 1, $"level {b.EmberLevel}");
        foreach (var e in b.Enemies.Items) if (e.Alive) { Assert.True(double.IsFinite(e.X)); Assert.True(double.IsFinite(e.Z)); }
        Assert.True(double.IsFinite(b.Player.X));
    }

    [Fact]
    public void Every_weapon_fires_and_kills()
    {
        var failed = new List<string>();
        foreach (var id in Content.Weapons.All.Keys)
        {
            var b = Arena(7, (id, 3));
            Simulate(b, 20, 0.5, press: true); // (pressed and channel skills never fire themselves)
            if (b.KillCount <= 3) failed.Add($"{id}: {b.KillCount}");
        }
        Assert.Empty(failed);
    }

    [Fact]
    public void Every_evolution_applies_and_still_fights()
    {
        var failed = new List<string>();
        foreach (var w in Content.Weapons.All.Values)
            foreach (var evo in w.Evolutions)
            {
                var b = Arena(11, (w.Id, 8));
                b.Evolve(w.Id, evo.Id);
                Simulate(b, 12, 0.4, press: true); // (pressed skills never fire themselves)
                if (b.KillCount <= 3) failed.Add($"{evo.Id}: {b.KillCount}");
            }
        Assert.Empty(failed);
    }

    [Fact]
    public void Synergies_chain()
    {
        var b = Arena(5, ("cinderfall", 5));
        b.AddBoon("kindling");
        b.AddBoon("pyre_burst");
        b.AddBoon("emberseekers");
        Simulate(b, 30, 0.3);
        var counts = b.Triggers.ToDictionary(t => t.Source, t => t.Count);
        Assert.True(counts["boon:kindling"] > 0);
        Assert.True(counts["boon:pyre_burst"] > 0);
        Assert.True(counts["boon:emberseekers"] > 0);
    }

    [Fact]
    public void A_frontal_shield_turns_projectiles_not_blades()
    {
        var b = ArenaWith(9, new());
        var e = b.SpawnEnemy("risen_warrior", 5, 0)!;
        e.Facing = Math.PI; // facing the survivor at the origin
        double front = b.HitEnemy(e, 20, School.Physical, [Tag.Projectile], new HitOpts { Projectile = true, FromX = 1, FromZ = 0, NoCrit = true });
        var e2 = b.SpawnEnemy("risen_warrior", 5, 3)!;
        e2.Facing = Math.PI;
        double melee = b.HitEnemy(e2, 20, School.Physical, [Tag.Melee], new HitOpts { NoCrit = true });
        Assert.True(front < melee * 0.5, $"{front} vs {melee}");
    }

    [Fact]
    public void The_horde_paths_around_a_wall()
    {
        var col = new CollisionWorld(60);
        col.AddBox(0, 5, 8, 0.5, 0);
        var flow = new FlowField(col, 20);
        flow.Update(0, 0);
        // From behind the wall, the path must be longer than the straight line.
        Assert.True(flow.DistanceAt(0, 10) > 12);
        Assert.True(flow.Dir(0, 10, out double dx, out _));
        Assert.True(Math.Abs(dx) > 0.3);
    }

    [Fact]
    public void Emits_hits_kills_and_pickups()
    {
        var b = Arena(2);
        int hits = 0, kills = 0, pickups = 0;
        const double dt = 1.0 / 60;
        for (int i = 0; i < 20; i++) b.SpawnEnemy("risen", 2 + i % 5, i / 5, new Battle.SpawnOpts { Style = SpawnStyle.Walk });
        for (double t = 0; t < 12; t += dt)
        {
            b.Tick(dt, 0.2, 0);
            foreach (var ev in b.Events.Drain())
            {
                if (ev is Ev.Hit) hits++;
                if (ev is Ev.Kill) kills++;
                if (ev is Ev.Pickup) pickups++;
            }
        }
        Assert.True(hits > 10);
        Assert.True(kills > 5);
        Assert.True(pickups > 3);
    }

    [Fact]
    public void Neutrals_are_never_hurt_by_accident()
    {
        var b = Arena(3, ("oathblade", 3));
        var wolf = b.SpawnEnemy("wolf", 1.2, 0)!;
        wolf.Disposition = Disposition.Neutral;
        var mate = b.SpawnEnemy("wolf", 2, 1)!;
        mate.Disposition = Disposition.Neutral;
        double hp = wolf.Hp;
        for (int i = 0; i < 600; i++) b.Tick(1.0 / 60, 0, 0);
        b.HitEnemy(wolf, 50, School.Fire, [Tag.Area, Tag.Fire]);
        Assert.Equal(hp, wolf.Hp);
        Assert.False(wolf.Provoked);
        // A deliberate blow starts it, and the pack answers.
        b.HitEnemy(wolf, 5, School.Physical, [Tag.Physical], new HitOpts { Provoke = true });
        Assert.True(wolf.Hp < hp);
        Assert.True(mate.Provoked);
    }
}

public class DraftTests
{
    [Fact]
    public void A_levels_own_draft_is_never_a_blessing_and_always_has_a_combat_skill()
    {
        var b = BattleTests.Arena(11);
        for (int i = 0; i < 20; i++)
        {
            b.GainEmber(b.EmberNext - b.EmberXp + 0.01);
            while (b.DraftOwed)
            {
                var offers = LevelUp.Draft(b, 3);
                Assert.Equal(3, offers.Count);
                if (LevelUp.BlessingNext(b))
                {
                    // A milestone's draft is blessings only.
                    Assert.All(offers, o => Assert.True(o.Blessing && Boons.All[o.Id].Kind == BoonKind.Blessing));
                    LevelUp.Choose(b, offers[0]);
                    continue;
                }
                Assert.DoesNotContain(offers, o => o.Kind == OfferKind.Boon && Boons.All[o.Id].Kind == BoonKind.Blessing);
                Assert.Contains(offers, o => o.Kind is OfferKind.Weapon or OfferKind.Rank or OfferKind.Evolve);
                LevelUp.Choose(b, offers[0]);
            }
        }
        Assert.Equal(21, b.EmberLevel);
    }

    [Fact]
    public void A_blessing_at_the_milestone_after_that_levels_skill()
    {
        var b = BattleTests.Arena(13);
        int milestone = Boons.Milestones[1];
        b.EmberLevel = milestone - 1;
        b.GainEmber(b.EmberNext - b.EmberXp + 0.01);
        Assert.Equal(milestone, b.EmberLevel);
        Assert.Equal(1, b.PendingLevels);
        Assert.Equal(new[] { milestone }, b.PendingBlessings);
        var skill = LevelUp.Draft(b, 3);
        Assert.All(skill, o => Assert.False(o.Blessing));
        LevelUp.Choose(b, skill[0]);
        Assert.True(b.DraftOwed);
        var blessing = LevelUp.Draft(b, 3);
        Assert.Equal(3, blessing.Count);
        Assert.All(blessing, o => Assert.True(o.Kind == OfferKind.Boon && o.Blessing && Boons.All[o.Id].Kind == BoonKind.Blessing));
        int before = b.Boons.Values.Sum();
        LevelUp.Choose(b, blessing[0]);
        Assert.Equal(before + 1, b.Boons.Values.Sum());
        Assert.False(b.DraftOwed);
    }

    [Fact]
    public void Fills_with_passives_and_honing_once_every_combat_skill_is_finished()
    {
        var b = BattleTests.Arena(12, Evolving().Take(Content.Weapons.MaxWeapons).Select(id => (id, Content.Weapons.MaxRank)).ToArray());
        b.EmberLevel = 3; b.PendingLevels = 1;
        foreach (var w in b.Weapons) b.Evolve(w.Id, w.Def.Evolutions[0].Id);
        var offers = LevelUp.Draft(b, 3);
        // Passives and honing; and a union where two of them belong together (it comes first).
        Assert.All(offers, o => Assert.True((o.Kind == OfferKind.Boon && !o.Blessing) || o.Kind is OfferKind.Hone or OfferKind.Union));
        Assert.Equal(3, offers.Count);
        // Honing a finished weapon: a little more each time, ten times at most.
        var w0 = b.Weapons[0];
        double before = w0.Damage;
        for (int i = 0; i < LevelUp.MaxHone + 3; i++) b.Hone(w0.Id);
        Assert.Equal(LevelUp.MaxHone, w0.Honed);
        Assert.Equal(before * System.Math.Pow(1 + LevelUp.HoneStep, LevelUp.MaxHone), w0.Damage, 6);
    }

    [Fact]
    public void Leans_toward_the_calling_and_locks_nothing_out()
    {
        var seen = new HashSet<string>();
        double SpellShare(bool lean)
        {
            int spell = 0, total = 0;
            for (uint seed = 1; seed <= 120; seed++)
            {
                var b = BattleTests.Arena(seed);
                if (lean) b.Favours.Add(Tag.Spell);
                b.EmberLevel = 2; b.PendingLevels = 1;
                foreach (var o in LevelUp.Draft(b, 3))
                    if (o.Kind == OfferKind.Weapon)
                    {
                        seen.Add(o.Id);
                        total++;
                        if (Content.Weapons.All[o.Id].Tags.Contains(Tag.Spell)) spell++;
                    }
            }
            return (double)spell / total;
        }
        Assert.True(SpellShare(true) > SpellShare(false));
        Assert.True(seen.Count > Content.Weapons.Pool.Length * 0.8);
    }

    [Fact]
    public void Evolutions_need_rank_eight_and_a_rank_of_their_passive()
    {
        var b = BattleTests.Arena(14, ("seeking_motes", Content.Weapons.MaxRank));
        Assert.Empty(LevelUp.EarnedBranches(b, "seeking_motes"));
        b.EmberLevel = 3; b.PendingLevels = 1;
        Assert.DoesNotContain(LevelUp.Draft(b, 3), o => o.Kind == OfferKind.Evolve);
        b.AddBoon("duplicity");
        Assert.Equal(new[] { "mote_cascade" }, LevelUp.EarnedBranches(b, "seeking_motes").Select(e => e.Id));
        Assert.Equal(new[] { "mote_cascade" }, LevelUp.Draft(b, 3).Where(o => o.Kind == OfferKind.Evolve).Select(o => o.Branch));
        b.AddBoon("precision");
        Assert.Equal(2, LevelUp.EarnedBranches(b, "seeking_motes").Count);
    }

    [Fact]
    public void Every_branch_names_a_draftable_passive()
    {
        foreach (var w in Content.Weapons.All.Values)
            foreach (var e in w.Evolutions)
            {
                Assert.NotEmpty(e.Catalysts);
                foreach (var c in e.Catalysts) Assert.Equal(BoonKind.Passive, Boons.Find(c)?.Kind);
            }
    }

    /// <summary>The findable skills that evolve, in the pool's order (the warden's calling skills have none yet:
    /// their evolutions are a later phase).</summary>
    static IEnumerable<string> Evolving() => Content.Weapons.Pool.Where(id => Content.Weapons.All[id].Evolutions.Length > 0);

    [Fact]
    public void Evolutions_come_one_weapon_at_a_time()
    {
        var b = BattleTests.Arena(15, Evolving().Take(Content.Weapons.MaxWeapons).Select(id => (id, Content.Weapons.MaxRank)).ToArray());
        foreach (var id in new[] { "duplicity", "precision", "expanse", "perennial", "haste", "velocity" }) b.AddBoon(id);
        b.EmberLevel = 3; b.PendingLevels = 1;
        var evos = LevelUp.Draft(b, 3).Where(o => o.Kind == OfferKind.Evolve).ToList();
        Assert.NotEmpty(evos);
        Assert.Single(evos.Select(o => o.Id).Distinct());
    }

    [Fact]
    public void Passives_are_ordinary_picks_up_to_six()
    {
        var b = BattleTests.Arena(16);
        int combat = 0, passive = 0;
        for (int i = 0; i < 40; i++)
        {
            b.GainEmber(b.EmberNext - b.EmberXp + 0.01);
            while (b.DraftOwed)
            {
                var offers = LevelUp.Draft(b, 3);
                if (LevelUp.BlessingNext(b)) { LevelUp.Choose(b, offers[0]); continue; }
                foreach (var o in offers)
                {
                    if (o.Kind is OfferKind.Weapon or OfferKind.Rank) combat++;
                    if (o.Kind == OfferKind.Boon) { passive++; Assert.Equal(BoonKind.Passive, Boons.All[o.Id].Kind); }
                }
                LevelUp.Choose(b, offers.FirstOrDefault(o => o.Kind == OfferKind.Boon) ?? offers[0]);
                Assert.True(LevelUp.PassivesHeld(b) <= Boons.MaxPassives);
            }
        }
        Assert.True(combat > 0);
        Assert.True(passive > 0);
        Assert.Equal(Boons.MaxPassives, LevelUp.PassivesHeld(b));
    }
}

/// <summary>The survival contract runs the zone harness (48 runs), so it sits in the Balance collection and runs alone.</summary>
[Collection("Balance")]
public class BattleBalanceTests(Xunit.Abstractions.ITestOutputHelper log)
{
    [Fact]
    public void A_crowd_is_dangerous_not_lethal()
    {
        // The old drifter contract (>= 12 of 16 survive) read 10 of 16 after 473daac72 ("M3 MR 3 clock: every wait exact
        // to the instant") and 5 of 16 after grip x0.80 (d5d195064); main ruled (10 Nov) it moves to the human bot at the
        // band's low edge: the bands' own measure, `zone --zone lowford --bots human --seeds 48 --tiers 1`
        // (human no-fall I 85+; 87.5% = 42/48 at round 8).
        var results = new System.Collections.Concurrent.ConcurrentBag<SurvivorUnchained.Balance.ZoneRunResult>();
        System.Threading.Tasks.Parallel.For(1, 49, seed =>
            results.Add(SurvivorUnchained.Balance.ZoneSim.Play(new SurvivorUnchained.Balance.ZoneRunSpec(seed, "lowford", "human", 1))));
        int noFall = results.Count(r => r.Falls == 0);
        string line = $"Low Ford, human bot, tier I: no fall in {noFall} of 48 runs; mean kills {results.Average(r => r.Kills):0.0}, mean minutes {results.Average(r => r.PlaySeconds / 60):0.0}";
        log.WriteLine(line);
        Assert.True(noFall >= 41, line + " (need >= 85%)");
    }
}
