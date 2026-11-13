using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-075, SU-076, SU-077) The Hand's grounds are held by lifetime and kept to the cap the Hand
/// has now (the newest stay); a dynamic stat a lamp held goes when a build without that lamp replaces it.</summary>
public sealed class BuildReconcileTests
{
    static Battle Fight(string calling)
    {
        var b = BattleTests.Arena(3, ("cinderfall", 1));
        b.Lamps = new LampLoadout();
        b.Calling = calling;
        return b;
    }

    static LampEffect Rule(string rule, Dictionary<string, double>? args = null) =>
        new() { Do = LampDo.Rule, Rule = rule, Args = args ?? new() };

    static Enemy Foe(Battle b)
    {
        var e = b.SpawnEnemy("risen", b.Player.X + 30, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e9; e.Speed = 0; e.AttackT = e.RangedT = 99;
        return e;
    }

    static int HandZones(Battle b) => b.Zones.Living().Count(z => z.Credit == "hand");

    static void Lay(Battle b, Enemy e, int n, double x0)
    {
        for (int i = 0; i < n; i++) { e.X = x0 + i * 0.1; b.LayHandGround(e, b.Weapons[0], School.Fire); }
    }

    [Fact]
    public void Grounds_laid_after_the_first_ones_ran_out_all_stay()
    {
        // old: the ring kept refs to released pooled zones; reused, they read Alive and "hand", so laying released fresh ones (6 of 12 stayed)
        var b = Fight("arcanist");
        var e = Foe(b);
        int cap = SurvivorUnchained.Content.Hands.Arcanist.Cap;
        Lay(b, e, cap, 30);
        Assert.Equal(cap, HandZones(b));
        for (int i = 0; i < 600 && HandZones(b) > 0; i++) b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(0, HandZones(b));
        Lay(b, e, cap, 30);
        Assert.Equal(cap, HandZones(b));
    }

    [Fact]
    public void The_cap_follows_more_hearths_both_ways_and_the_newest_stay()
    {
        // old: the ring was sized once (12) on the first ground, so More Hearths never made room, and putting it out never trimmed
        var b = Fight("arcanist");
        var e = Foe(b);
        int cap = SurvivorUnchained.Content.Hands.Arcanist.Cap;
        Lay(b, e, 1, 20);
        var more = new LampLoadout();
        more.Add(Rule("hand", new() { ["cap"] = 4 }));
        b.ReplaceLamps(more);
        Lay(b, e, cap + 4, 30);
        Assert.Equal(cap + 4, HandZones(b));
        b.ReplaceLamps(new LampLoadout());
        Assert.Equal(cap, HandZones(b));
        double newestFirst = 30 + 4 * 0.1;
        Assert.All(b.Zones.Living().Where(z => z.Credit == "hand"), z => Assert.True(z.X >= newestFirst - 1e-9));
    }

    [Fact]
    public void Chainbounds_armor_goes_with_its_lamp()
    {
        // old: the tick skipped bound.armor's block once it was not lit, so its armor stayed for the fight
        var b = Fight("reaver");
        double bare = b.Stats.Get(Stat.Armor);
        var l = new LampLoadout();
        l.Add(Rule("bound.armor", new() { ["radius"] = 50, ["cap"] = 10, ["per"] = 2 }));
        b.ReplaceLamps(l);
        var e = b.SpawnEnemy("risen", b.Player.X + 3, b.Player.Z)!;
        e.MaxHp = e.Hp = 1e9; e.AttackT = e.RangedT = 99;
        b.ApplyStatus(e, new StatusPayload(StatusKind.Bound, 1, 1, 30), 0);
        for (int i = 0; i < 30; i++) b.Tick(1 / 60.0, 0, 0);
        Assert.True(b.Stats.Get(Stat.Armor) > bare);
        b.ReplaceLamps(new LampLoadout());
        for (int i = 0; i < 30; i++) b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(bare, b.Stats.Get(Stat.Armor), 9);
    }

    [Fact]
    public void Standing_in_fires_armor_goes_with_its_lamp()
    {
        // (L3) old: an empty loadout returned before the stand check, so the armor stayed
        var b = Fight("arcanist");
        double bare = b.Stats.Get(Stat.Armor);
        var l = new LampLoadout();
        l.Add(Rule("stand_in_fire", new() { ["armor"] = 0.5 }));
        b.ReplaceLamps(l);
        b.SpawnZone(Side.Player, b.Player.X, b.Player.Z, 3, 30, 0, School.Fire);
        for (int i = 0; i < 30; i++) b.Tick(1 / 60.0, 0, 0);
        Assert.True(b.Stats.Get(Stat.Armor) > bare);
        b.ReplaceLamps(new LampLoadout());
        for (int i = 0; i < 30; i++) b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(bare, b.Stats.Get(Stat.Armor), 9);
    }
}
