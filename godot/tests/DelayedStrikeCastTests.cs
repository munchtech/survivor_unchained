using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>CODEX_audit.md SU-050: a cast's strength is part of what it casts. A strike the cast leaves to land later
/// (Thunderhead's bolts, Battle.ScheduleStrike) carries the CastMul it was cast with, applied once when it lands; one
/// scheduled outside its weapon's cast lands at x1.</summary>
public class DelayedStrikeCastTests
{
    static LampEffect Rule(string id, params (string, double)[] args) =>
        new() { Do = LampDo.Rule, Rule = id, Args = args.ToDictionary(a => a.Item1, a => a.Item2) };

    /// <summary>Thunderhead with The Echo: every bolt of the first cast lands at x1, every bolt of its echo at the
    /// echo's share (by day 0.5, by night its night size). No crits; shock cleared before every tick. Before: the echo's
    /// bolts landed after the cast (castingW null) and took x1.</summary>
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void Thunderheads_echo_bolts_land_at_the_echos_share(bool night)
    {
        var b = BattleTests.Arena(3, ("thunderhead", 1));
        var w = b.Weapons.Single();
        b.Lamps = new LampLoadout { Night = night };
        b.Lamps.Add(Rule("the_echo", ("delay", 0.5), ("share", 0.5), ("longer", 0.25)));
        b.Stats.Add(new StatMod(Stat.CritChance, ModKind.More, -1));
        var e = b.SpawnEnemy("wolf", b.Player.X + 2, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e9;
        e.AttackT = e.RangedT = 999;
        double share = System.Math.Min(1, b.Lamps.Size("the_echo", "share", 0.5));
        Assert.True(share < 1);

        // the strike batches (each cast's bolts are emitted together) and every bolt's hit, by time
        var batches = new List<double>();
        var hits = new List<(double T, double Amount)>();
        double t = 0;
        for (int i = 0; i < 60 * 4 && batches.Count < 2; i++)
        {
            e.Status.Clear();
            e.X = b.Player.X + 2; e.Z = b.Player.Z;
            b.Tick(1 / 60.0, 0, 0);
            t += 1 / 60.0;
            foreach (var ev in b.Events.Drain())
            {
                if (ev is Ev.Strike s && s.Art == w.Art && (batches.Count == 0 || t - batches[^1] > 0.1)) batches.Add(t);
                if (ev is Ev.Hit h && h.Weapon == "thunderhead" && !h.Dot) hits.Add((t, h.Amount));
            }
        }
        Assert.Equal(2, batches.Count);
        // let the echo's bolts land
        for (int i = 0; i < 60; i++)
        {
            e.Status.Clear();
            e.X = b.Player.X + 2; e.Z = b.Player.Z;
            b.Tick(1 / 60.0, 0, 0);
            t += 1 / 60.0;
            foreach (var ev in b.Events.Drain()) if (ev is Ev.Hit h && h.Weapon == "thunderhead" && !h.Dot) hits.Add((t, h.Amount));
        }
        var first = hits.Where(h => h.T < batches[1]).Select(h => h.Amount).ToList();
        var echo = hits.Where(h => h.T > batches[1] && h.T < batches[1] + 0.9).Select(h => h.Amount).ToList();
        Assert.NotEmpty(first);
        Assert.NotEmpty(echo);
        Assert.All(first, a => Assert.Equal(first[0], a, 6));
        Assert.All(echo, a => Assert.Equal(first[0] * share, a, 6));
    }

    /// <summary>A strike scheduled outside its weapon's cast lands at x1, whatever the weapon's CastMul reads then.</summary>
    [Fact]
    public void A_strike_scheduled_outside_a_cast_lands_at_x1()
    {
        double Land(double castMul)
        {
            var b = BattleTests.Arena(3, ("thunderhead", 1));
            var w = b.Weapons.Single();
            w.DisabledT = 999;
            b.Lamps = new LampLoadout();
            b.Lamps.Add(Rule("the_echo", ("delay", 0.5), ("share", 0.5), ("longer", 0.25)));
            b.Stats.Add(new StatMod(Stat.CritChance, ModKind.More, -1));
            var e = b.SpawnEnemy("wolf", b.Player.X + 2, b.Player.Z)!;
            e.MaxHp = e.Hp = 1e9;
            e.AttackT = e.RangedT = 999;
            w.CastMul = castMul;
            b.ScheduleStrike(e.X, e.Z, 1.5, 100, w.School, w.Tags, 0.1, w);
            double got = 0;
            for (int i = 0; i < 30; i++)
            {
                e.Status.Clear();
                b.Tick(1 / 60.0, 0, 0);
                foreach (var ev in b.Events.Drain()) if (ev is Ev.Hit h && h.Weapon == "thunderhead" && !h.Dot) got += h.Amount;
            }
            return got;
        }
        double one = Land(1);
        Assert.True(one > 0);
        Assert.Equal(one, Land(0.3), 6);
    }
}
