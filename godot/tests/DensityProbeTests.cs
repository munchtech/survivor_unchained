using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Play.Pilots;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

[Collection("Balance")]
public class DensityProbeTests
{
    [Fact]
    public void Hits_keep_their_spawn_identity_when_a_pool_slot_is_reused_before_drain()
    {
        var b = BattleTests.Arena();
        b.Weapons.Clear();
        var first = b.SpawnEnemy("risen", 3, 0, new Battle.SpawnOpts { Style = SpawnStyle.Walk })!;
        int slot = first.Id; double seed = first.Seed;
        var groups = new List<DensityGroup> { new("a", new[] { (first, seed) }, false) };
        var probe = new DensityProbe(b, () => groups);
        probe.Observe(Array.Empty<CombatEvent>());
        b.Tick(1, 0, 0);
        b.HitEnemy(first, 1, School.Physical, [], new HitOpts { NoProcs = true });
        var hits = b.Events.Drain();
        var oldHit = Assert.Single(hits.OfType<Ev.Hit>());
        Assert.Equal(seed, oldHit.TargetSeed);
        Assert.Equal(1, oldHit.Time);
        b.Enemies.Release(first);
        var second = b.SpawnEnemy("risen", 4, 0, new Battle.SpawnOpts { Style = SpawnStyle.Walk })!;
        Assert.Equal(slot, second.Id); Assert.NotEqual(seed, second.Seed);
        groups.Clear(); groups.Add(new("b", new[] { (second, second.Seed) }, false));
        b.Tick(1, 0, 0);
        b.HitEnemy(second, 1, School.Physical, [], new HitOpts { NoProcs = true });
        hits.AddRange(b.Events.Drain());
        probe.Observe(hits);
        var d = probe.Finish(b.Time);
        Assert.Equal(1.0, d.Packs.Single(p => p.Id == "a").FirstHit);
        Assert.Equal(2.0, d.Packs.Single(p => p.Id == "b").FirstHit);
    }

    [Fact]
    public void Verge_walk_clears_the_field_and_returns_past_the_camp_wall()
    {
        var r = VergeZoneSim.Play(new VergeZoneSpec(2), maxWallTime: TimeSpan.FromSeconds(20), maxSeconds: 300);
        Assert.True(r.Reached, r.StopReason);
        Assert.Equal(0, r.Skipped);
        Assert.Equal(0, r.Falls);
        Assert.True(r.Density.Seconds < 300);
        Assert.All(r.Density.Packs.Where(p => p.Id.StartsWith("field:")), p => Assert.True(p.Cleared));
        Assert.Equal(r.Density.Kills, r.Density.Windows.Sum(w => w.Kills));
    }

    [Fact]
    public void Walk_wall_budget_stops_even_before_the_simulation_clock_advances()
    {
        var r = VergeZoneSim.Play(new VergeZoneSpec(2), maxWallTime: TimeSpan.FromTicks(1), maxSeconds: 300);
        Assert.False(r.Reached);
        Assert.StartsWith("wall-time limit", r.StopReason);
        Assert.Equal(0, r.Density.Seconds);
        Assert.All(r.Density.Packs, p => Assert.Null(p.FirstHit));
    }

    [Fact]
    public void Walk_simulation_budget_stops_without_waiting_for_the_wall_budget()
    {
        var r = VergeZoneSim.Play(new VergeZoneSpec(2), maxWallTime: TimeSpan.FromSeconds(20), maxSeconds: ArenaSim.Dt);
        Assert.False(r.Reached);
        Assert.StartsWith("simulation limit", r.StopReason);
        Assert.Equal(ArenaSim.Dt, r.Density.Seconds);
    }

    [Fact]
    public void Empty_range_observation_uses_the_pilots_current_engage_distance()
    {
        var b = BattleTests.Arena();
        var e = b.SpawnEnemy("risen", 0, 0, new Battle.SpawnOpts { Style = SpawnStyle.Walk })!;
        var probe = new DensityProbe(b, () => Array.Empty<DensityGroup>());
        double range = Pilot.EngageRange(b, e);
        e.X = b.Player.X + range + e.Radius + 0.01; e.Z = b.Player.Z;
        probe.Sample();
        b.Time = 4;
        e.X -= 0.02;
        probe.Sample();
        b.Time = 7;
        e.Disposition = Disposition.Ally;
        probe.Sample();
        var d = probe.Finish(12);
        Assert.Equal(new DensitySpan(7, 12), d.LongestNoEnemy);
    }
}
