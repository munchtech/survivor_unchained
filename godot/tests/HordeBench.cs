using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>
/// The fight under a great horde, timed: a mid-game build holding ground in
/// a crowd kept topped up to 300, 600 and 900 (the enemy pool's whole size),
/// a mix of the dead, wolves and footpads with archers among them. Reports
/// milliseconds a tick (mean and the slowest twentieth), what a tick
/// allocates, and a fingerprint of where the fight ended, which must not
/// move when the fight is only made faster.
/// Only with HORDE_BENCH=1: dotnet test --filter HordeBench
/// --logger "console;verbosity=detailed" (HORDE_TICKS sets the ticks timed).
/// </summary>
public class HordeBench(ITestOutputHelper log)
{
    static readonly string[] Kinds = ["risen", "risen", "risen_warrior", "wolf", "footpad", "risen_archer"];

    /// <summary>Weapons at the ranks a survivor has twenty minutes in.</summary>
    static readonly (string, int)[] Build =
    [
        ("oathblade", 6), ("seeking_motes", 5), ("cinderfall", 5), ("arcweb", 4), ("knifestorm", 4), ("hallowed_ring", 4),
    ];

    internal sealed record Run(int Horde, double MeanMs, double P95Ms, double BytesPerTick, int Gen0, int Kills, string Fingerprint);

    internal static Run Play(int horde, int ticks, uint seed = 5, int warm = 600)
    {
        // A real arena's ground: a generated clearing with its cover.
        var map = MapGen.Generate(new ArenaSpec { Id = "table:bench", Name = "The Bench", Seed = (int)seed, Tier = 3, People = "dead" }.Map);
        var s = new StatBlock();
        s.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = 100000, [Stat.Regen] = 50, [Stat.Armor] = 8, [Stat.MoveSpeed] = 5, [Stat.PickupRadius] = 3,
            [Stat.CritChance] = 0.1, [Stat.CritDamage] = 1.6, [Stat.Luck] = 1,
        });
        var b = new Battle(new BattleSetup
        {
            Seed = seed, Collision = map.Meta.Collision(), HeightAt = map.Ground.HeightAt, Combat = true, Stats = s,
            StartX = map.Start.X, StartZ = map.Start.Z, Weapons = Build.ToList(), Ability = AbilityKind.ShieldBash,
        });
        b.Player.Hp = 100000;
        // The benchmark's own stream for where the horde comes from, so the
        // fight's stream is the fight's alone.
        var place = new Rng(seed * 7919);
        const double dt = 1.0 / 60;
        var times = new List<double>(ticks);
        long bytes = 0;
        int gen0 = 0;
        var sw = new Stopwatch();
        for (int i = 0; i < warm + ticks; i++)
        {
            for (int tries = 0; b.Enemies.Count < horde && tries < 4000; tries++)
            {
                double a = place.Next() * Math.PI * 2, r = 12 + place.Next() * 30;
                double x = b.Player.X + Math.Cos(a) * r, z = b.Player.Z + Math.Sin(a) * r;
                if (!map.CanStand(x, z)) continue;
                if (b.SpawnEnemy(Kinds[(int)(place.Next() * Kinds.Length)], x, z, new Battle.SpawnOpts { Level = 5 }) == null) break;
            }
            double t = i * dt, mx = Math.Cos(t * 0.35) * 0.35, mz = Math.Sin(t * 0.35) * 0.35;
            bool timed = i >= warm;
            long before = 0;
            int g = 0;
            if (timed)
            {
                g = GC.CollectionCount(0);
                before = GC.GetAllocatedBytesForCurrentThread();
                sw.Restart();
            }
            b.Tick(dt, mx, mz);
            if (timed)
            {
                sw.Stop();
                bytes += GC.GetAllocatedBytesForCurrentThread() - before;
                gen0 += GC.CollectionCount(0) - g;
                times.Add(sw.Elapsed.TotalMilliseconds);
            }
            while (b.DraftOwed) LevelUp.Choose(b, LevelUp.Draft(b, 3)[0]);
            b.Events.Drain();
            if (b.Over != null) break;
        }
        times.Sort();
        return new Run(horde, times.Average(), times[(int)(times.Count * 0.95)], (double)bytes / times.Count, gen0, b.KillCount, Fingerprint(b));
    }

    /// <summary>Where a fight stands, as one short string: the stream's state,
    /// the kills, the survivor, and every living creature's place and health.</summary>
    internal static string Fingerprint(Battle b)
    {
        unchecked
        {
            ulong h = 1469598103934665603UL;
            void Mix(double v) { h ^= (ulong)BitConverter.DoubleToInt64Bits(v); h *= 1099511628211UL; }
            Mix(b.Rng.State); Mix(b.KillCount); Mix(b.Player.X); Mix(b.Player.Z); Mix(b.Player.Hp); Mix(b.EmberLevel);
            foreach (var e in b.Enemies.Items)
                if (e.Alive) { Mix(e.Id); Mix(e.X); Mix(e.Z); Mix(e.Hp); }
            foreach (var p in b.Projectiles.Items)
                if (p.Alive) { Mix(p.Id); Mix(p.X); Mix(p.Z); }
            return $"{b.KillCount}k/{b.Enemies.Count}e/{b.Projectiles.Count}p/{h:x16}";
        }
    }

    /// <summary>Always on: the same seed makes the same fight, so a change
    /// meant only to make it faster can be shown to change nothing.</summary>
    [Fact]
    public void A_great_horde_plays_the_same_twice()
    {
        var a = Play(300, 120, warm: 60);
        var b = Play(300, 120, warm: 60);
        Assert.Equal(a.Fingerprint, b.Fingerprint);
        Assert.True(a.Kills > 0, a.Fingerprint);
    }

    /// <summary>Always on: a tick allocates for what happens (a blow, a
    /// death), not for every creature. A lambda capturing the creature in
    /// its Update once cost 30 KB a tick at 900, and a collection a second.</summary>
    [Fact]
    public void A_great_horde_allocates_little_a_tick()
    {
        var r = Play(300, 120, warm: 60);
        Assert.True(r.BytesPerTick < 8 * 1024, $"{r.BytesPerTick / 1024:F1} KB a tick");
    }

    [Fact]
    public void HordeBench_Run()
    {
        if (Environment.GetEnvironmentVariable("HORDE_BENCH") != "1") return;
        int ticks = int.TryParse(Environment.GetEnvironmentVariable("HORDE_TICKS"), out var n) ? n : 600;
        log.WriteLine($"{"horde",6} {"ms/tick",8} {"p95",7} {"KB/tick",8} {"gen0",5} {"kills",6}  fingerprint");
        foreach (var horde in new[] { 300, 600, 900 })
        {
            var r = Play(horde, ticks);
            log.WriteLine($"{r.Horde,6} {r.MeanMs,8:F3} {r.P95Ms,7:F3} {r.BytesPerTick / 1024,8:F1} {r.Gen0,5} {r.Kills,6}  {r.Fingerprint}");
        }
    }
}
