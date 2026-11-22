using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>(skills-five, 22 Nov; the owner: "it also pushes the mosnter outside the barrier idk if thats intended") Heroic
/// Leap's Henge (heroic_leap.quake.4: "where you land, standing stones rise in a 6 m ring for 4 s: lesser things inside
/// can't get out, and none outside get in") sits on Ninepins (quake.3: "what the landing throws flies 6 m"). The landing's
/// throw must stop at the stones: a lesser foe it throws stays inside the ring.</summary>
public sealed class HengeThrowTests
{
    const double Dt = 1 / 60.0;
    readonly ITestOutputHelper _out;
    public HengeThrowTests(ITestOutputHelper o) => _out = o;

    /// <summary>A campaign fight with Heroic Leap and its whole Quake strand lit (Crater, Second Quake, Ninepins, Henge), as
    /// --veteran lights it.</summary>
    static Battle Quake()
    {
        var b = new Battle(new BattleSetup
        {
            Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
            Weapons = [("heroic_leap", 5)], Ability = AbilityKind.ShieldBash,
        });
        b.Calling = "warden";
        b.Lamps = new LampLoadout();
        // (skill_lamps.json heroic_leap.quake.1-4's effects, as written there)
        void Rule(string rule, Dictionary<string, double> args) => b.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = rule, Args = args });
        Rule("heroic_leap.crater", new() { ["radius"] = 4.5, ["stun"] = 1.2 });
        Rule("heroic_leap.aftershock", new() { ["again"] = 1, ["againDamage"] = 0.4 });
        Rule("heroic_leap.ninepins", new() { ["cooldown"] = 11, ["throw"] = 6, ["damage"] = 0.5 });
        Rule("heroic_leap.henge", new() { ["radius"] = 6, ["seconds"] = 4 });
        foreach (var w in b.Weapons) w.Timer = 0;
        b.Resolve.Set(100);
        return b;
    }

    static Enemy Foe(Battle b, double x, double z, bool elite = false)
    {
        var e = b.SpawnEnemy("footpad", x, z)!;
        e.Hp = e.MaxHp = 1e9;
        e.AttackT = e.RangedT = 999;
        e.Elite = elite;
        return e;
    }

    /// <summary>Leap 8 m ahead into a ring of foes round the landing; returns the landing point and the foes' distances
    /// from it (with their radii) after `after` seconds.</summary>
    (double X, double Z, List<(Enemy E, double D)> At) LeapInto(Battle b, (double Dx, double Dz, bool Elite)[] ring, double after)
    {
        var p = b.Player;
        double lx = p.X + 8, lz = p.Z;
        var foes = ring.Select(r => Foe(b, lx + r.Dx, lz + r.Dz, r.Elite)).ToList();
        int slot = b.Weapons.Single(w => w.Id == "heroic_leap").Slot;
        Assert.True(b.PressSkill(slot, lx, lz));
        for (double t = 0; t < after; t += Dt) b.Tick(Dt, 0, 0);
        double cx = p.X, cz = p.Z;
        var at = foes.Select(e => (e, MathX.Dist(cx, cz, e.X, e.Z))).ToList();
        foreach (var (e, d) in at) _out.WriteLine($"foe {e.Id} elite={e.Elite} r={e.Radius:0.00}: {d:0.00} m from the landing (ring 6 m)");
        return (cx, cz, at);
    }

    static readonly (double, double, bool)[] Lesser =
        [(1.5, 0, false), (-1.5, 0.5, false), (0, 2.0, false), (0.5, -2.5, false), (2.2, 2.2, false), (-2.0, -2.0, false)];

    [Fact]
    public void A_lesser_foe_the_landing_throws_stops_at_the_stones_and_stays_inside()
    {
        var b = Quake();
        var (_, _, at) = LeapInto(b, Lesser, 1.5);
        foreach (var (e, d) in at) Assert.True(d <= 6 + 1e-6, $"foe {e.Id} thrown out to {d:0.00} m, past the 6 m stones");
    }

    [Fact]
    public void They_are_still_inside_when_the_stones_sink()
    {
        var b = Quake();
        var (_, _, at) = LeapInto(b, Lesser, 3.9);
        foreach (var (e, d) in at) Assert.True(d <= 6 + 1e-6, $"foe {e.Id} at {d:0.00} m, out of the ring before it sank");
    }

    [Fact]
    public void An_elite_inside_the_ring_at_the_landing_is_not_shoved_out_by_the_stones()
    {
        // The stones hold lesser things in and keep everything out; an elite already inside is neither, so they leave it be.
        var b = Quake();
        var (_, _, at) = LeapInto(b, [(2.0, 0.5, true)], 1.5);
        Assert.True(at[0].D < 6, $"the elite was moved to {at[0].D:0.00} m, out past the stones");
    }
}
