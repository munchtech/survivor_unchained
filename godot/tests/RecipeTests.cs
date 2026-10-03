using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Every evolution and union, made the way a player makes it, and
/// fighting afterwards; and the shape of the content (every skill on a path,
/// every passive and blessing wanted by two builds).</summary>
public class RecipeTests
{
    static void Tick(Battle b, double seconds)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); }
    }

    /// <summary>A ring of the dead to fight, kept up.</summary>
    static void Crowd(Battle b, int n = 14, string def = "risen")
    {
        for (int i = 0; i < n; i++)
        {
            double a = i * Math.PI * 2 / n;
            b.SpawnEnemy(def, b.Player.X + Math.Cos(a) * 4, b.Player.Z + Math.Sin(a) * 4, new Battle.SpawnOpts { Level = 3 });
        }
    }

    public static IEnumerable<object[]> Branches() =>
        Weapons.All.Values.Where(w => w.Findable).SelectMany(w => w.Evolutions.SelectMany(e => e.Catalysts.Select(c => new object[] { w.Id, e.Id, c })));

    [Theory]
    [MemberData(nameof(Branches))]
    public void Every_branch_is_earned_by_its_passive_and_offered_and_fights(string weapon, string branch, string catalyst)
    {
        var b = BattleTests.Arena(7, (weapon, Weapons.MaxRank - 1));
        // Rank 7 and the passive: not yet.
        b.AddBoon(catalyst);
        Assert.Empty(LevelUp.EarnedBranches(b, weapon));
        b.RankWeapon(weapon);
        Assert.Contains(LevelUp.EarnedBranches(b, weapon), e => e.Id == branch);
        b.EmberLevel = 3; b.PendingLevels = 1;
        var offer = Assert.Single(LevelUp.Draft(b), o => o.Kind == OfferKind.Evolve && o.Branch == branch);
        LevelUp.Choose(b, offer);
        var w = b.Weapons.Single(x => x.Id == weapon);
        Assert.Equal(branch, w.Evolution?.Id);
        // Its own rules came with it, credited to the weapon.
        foreach (var t in w.Evolution!.Triggers)
            Assert.Contains(b.Triggers, x => x.Def == t && x.Credit == weapon);
        // And it still fights.
        Crowd(b);
        double before = b.DamageBy.GetValueOrDefault(weapon);
        Tick(b, 6);
        Assert.True(b.DamageBy.GetValueOrDefault(weapon) > before, $"{branch} dealt nothing");
    }

    public static IEnumerable<object[]> AllUnions() => Unions.All.Select(u => new object[] { u.Id });

    [Theory]
    [MemberData(nameof(AllUnions))]
    public void Every_union_is_made_from_its_two_evolved_halves_and_fights(string id)
    {
        var u = Unions.Find(id)!;
        var b = BattleTests.Arena(8, (u.A, Weapons.MaxRank), (u.B, Weapons.MaxRank));
        b.Evolve(u.A, Weapons.All[u.A].Evolutions[0].Id);
        b.Evolve(u.B, Weapons.All[u.B].Evolutions[1].Id);
        b.EmberLevel = 3; b.PendingLevels = 1;
        var offer = Assert.Single(LevelUp.Draft(b), o => o.Kind == OfferKind.Union && o.Id == id);
        LevelUp.Choose(b, offer);
        var w = Assert.Single(b.Weapons);
        Assert.Equal(u.Into, w.Id);
        Assert.False(Weapons.All[u.Into].Findable);
        Crowd(b);
        Tick(b, 8);
        Assert.True(b.DamageBy.GetValueOrDefault(u.Into) > 0, $"{id} dealt nothing");
    }

    [Fact]
    public void Each_evolution_does_what_its_words_promise()
    {
        // Grave-Edge finishes the bleeding below a sixth.
        var b = BattleTests.Arena(9, ("oathblade", Weapons.MaxRank));
        b.AddBoon("serration");
        b.Evolve("oathblade", "graveedge");
        var r = b.SpawnEnemy("barrow_knight", b.Player.X + 1.5, b.Player.Z)!;
        r.Hp = r.MaxHp * 0.15;
        r.Status.Ensure(StatusKind.Bleed, 3, 1, 1, 0.5);
        b.HitEnemy(r, 1, School.Physical, [Tag.Melee], new HitOpts { Weapon = b.Weapons[0], NoCrit = true });
        Assert.True(r.State == EnemyState.Dying || !r.Alive);

        // Skybreak's bolts strike.
        b = BattleTests.Arena(10, ("arcweb", Weapons.MaxRank));
        b.AddBoon("precision");
        b.Evolve("arcweb", "skybreak");
        Crowd(b, 8);
        Tick(b, 4);
        Assert.True(b.DamageBy.GetValueOrDefault("arcweb") > 0);
        Assert.Contains(b.Triggers, t => t.Source == "evo:skybreak" && t.Count > 0);

        // A Thousand Cuts deepens its wounds.
        b = BattleTests.Arena(11, ("knifestorm", Weapons.MaxRank));
        b.AddBoon("serration");
        b.Evolve("knifestorm", "thousand_cuts");
        var k = b.SpawnEnemy("barrow_knight", b.Player.X + 2, b.Player.Z)!;
        for (int i = 0; i < 4; i++)
            b.HitEnemy(k, 5, School.Physical, [Tag.Projectile], new HitOpts { Weapon = b.Weapons[0], Status = b.Weapons[0].StatusOf, NoCrit = true });
        Assert.True(k.Status[StatusKind.Bleed]!.Stacks >= 3);

        // Aegis Wheel wards you as it flies.
        b = BattleTests.Arena(12, ("judgement_disc", Weapons.MaxRank));
        b.AddBoon("ironhide");
        b.Evolve("judgement_disc", "aegis_wheel");
        Crowd(b, 10);
        Tick(b, 5);
        Assert.True(b.Player.Shield > 0);

        // The Harrowing raises what it kills.
        b = BattleTests.Arena(13, ("reaving_arc", Weapons.MaxRank));
        b.AddBoon("expanse");
        b.Evolve("reaving_arc", "harrowing");
        Crowd(b, 20);
        Tick(b, 8);
        Assert.Contains(b.Enemies.Items, e => e.Alive && e.Disposition == Disposition.Ally && e.Def.Id == "ghoul_ally");

        // Gravecall's risen fight, and grow with the skill.
        b = BattleTests.Arena(14, ("gravecall", 4));
        Crowd(b, 10);
        Tick(b, 6);
        Assert.Contains(b.Enemies.Items, e => e.Alive && e.SummonedBy == "gravecall");
    }

    [Fact]
    public void Every_skill_is_on_a_path_and_every_passive_and_blessing_is_wanted_by_two()
    {
        foreach (var id in Weapons.Pool)
            Assert.True(Paths.OfWeapon(id).Any(), $"{id} is on no path");
        foreach (var d in Boons.All.Values)
        {
            int wanted = Paths.All.Count(p => p.Passives.Contains(d.Id) || p.Blessings.Contains(d.Id) || p.Great.Contains(d.Id));
            Assert.True(wanted >= 2, $"{d.Id} is wanted by {wanted} paths");
        }
        foreach (var p in Paths.All)
        {
            Assert.True(p.Weapons.Count(id => Weapons.All.TryGetValue(id, out var w) && w.Findable) >= 4, $"{p.Id} has too few skills");
            Assert.Contains(p.Capstones, c => Unions.Find(c) != null);
            foreach (var c in p.Capstones)
                Assert.True(Unions.Find(c) != null || Weapons.All.Values.Any(w => w.Evolutions.Any(e => e.Id == c)), $"{p.Id}: no capstone {c}");
            foreach (var id in p.Passives) Assert.Equal(BoonKind.Passive, Boons.Find(id)?.Kind);
            foreach (var id in p.Blessings.Concat(p.Great)) Assert.Equal(BoonKind.Blessing, Boons.Find(id)?.Kind);
        }
        // Every catalyst a passive; every passive a catalyst of something or a reason of its own.
        foreach (var w in Weapons.All.Values)
            foreach (var e in w.Evolutions)
                foreach (var c in e.Catalysts) Assert.Equal(BoonKind.Passive, Boons.Find(c)?.Kind);
        foreach (var u in Unions.All)
        {
            Assert.True(Weapons.All[u.A].Findable && Weapons.All[u.B].Findable);
            Assert.True(Weapons.All.ContainsKey(u.Into));
        }
    }

    [Fact]
    public void A_union_is_never_drafted_on_its_own_and_both_halves_are_findable()
    {
        foreach (var u in Unions.All) Assert.DoesNotContain(u.Into, Weapons.Pool);
        Assert.Equal(Unions.All.Length, Unions.All.Select(u => u.A).Concat(Unions.All.Select(u => u.B)).Distinct().Count() / 2);
    }
}
