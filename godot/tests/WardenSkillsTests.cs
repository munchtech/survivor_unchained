using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The warden's calling skills (docs/design/CLASS_IDENTITY_AND_TALENTS.md 1, 3.3; Sim/WardenSkills.cs): one
/// test a mechanic, its lamps (rule ids "skill.rule") and its bespoke Turn. Fights with no calling, so the Hand's own
/// heavy count stays out of it. Sections: Sunder, Groundbreaker, (Rebuke, Watch Bell), the bespoke strands.</summary>
public sealed class WardenSkillsTests
{
    /* ------------------------------------------------------------ helpers -- */

    /// <summary>One skill, its lamps' rules lit (fixed numbers: the rule's own fallbacks), its wick's plan lit to its rank.</summary>
    static Battle Fight(string skill, int rank = 1, string[]? rules = null, string[]? plan = null)
    {
        var b = BattleTests.Arena(3, (skill, rank));
        b.Lamps = new LampLoadout();
        foreach (var r in rules ?? []) b.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = r, Args = new Dictionary<string, double>() });
        b.Calling = null;
        if (plan != null) b.SetWickPath(skill, WickBook.Path(plan, skill));
        return b;
    }

    static string[] Strand(string id) => Enumerable.Range(1, 4).Select(n => $"{id}.{n}").ToArray();

    /// <summary>Creatures that stand and take it, risen at these offsets from her; the rest of the field sent far off.</summary>
    static Enemy[] Dummies(Battle b, params (double X, double Z)[] at)
    {
        foreach (var w in b.Weapons) w.Timer = 1e9;
        var es = at.Select(o => b.SpawnEnemy("risen", b.Player.X + o.X, b.Player.Z + o.Z)!).ToArray();
        for (int i = 0; i < 30; i++) b.Tick(0.1, 0, 0);
        b.Events.Drain();
        foreach (var e in b.Enemies.Items) if (e.Alive && !es.Contains(e)) e.X += 500;
        for (int i = 0; i < es.Length; i++)
        {
            var e = es[i];
            e.MaxHp = e.Hp = 1e9;
            e.AttackT = e.RangedT = 99;
            e.Status.Remove(StatusKind.Stun);
        }
        Pin(b, es, at);
        return es;
    }

    static void Pin(Battle b, Enemy[] es, (double X, double Z)[] at)
    {
        for (int i = 0; i < es.Length; i++) { es[i].X = b.Player.X + at[i].X; es[i].Z = b.Player.Z + at[i].Z; }
        b.Spatial.Clear();
        foreach (var e in b.Enemies.Items) if (e.Alive && e.State != EnemyState.Dying) b.Spatial.Insert(e.Id, e.X, e.Z);
    }

    /// <summary>The skill fires once (the creatures pinned where they were put).</summary>
    static void FireOnce(Battle b, WeaponInst w, Enemy[] es, (double X, double Z)[] at)
    {
        Pin(b, es, at);
        w.Timer = 0;
        int casts = w.Casts;
        Firing.Tick(b, w, 0.01);
        Assert.Equal(casts + 1, w.Casts);
    }

    static bool Hurt(Enemy e) => e.Hp < e.MaxHp;

    /* ------------------------------------------------------------- Sunder -- */

    static readonly (double, double)[] NearAndFar = [(1.5, 0), (6, 0)];

    [Fact]
    public void Sunders_fourth_swing_is_heavy_and_splits_the_ground_ahead()
    {
        var b = Fight("sunder");
        var w = b.Weapons[0];
        var es = Dummies(b, NearAndFar);
        for (int i = 0; i < 3; i++) FireOnce(b, w, es, NearAndFar);
        Assert.False(Hurt(es[1]));
        Assert.Equal(0, b.LinesStruck);
        Assert.Equal(0, b.HandHeavies);
        FireOnce(b, w, es, NearAndFar);
        // The line reaches what the swing can't, once; the swing is heavy (the Hand's heavy: a stun, with no Hand).
        Assert.True(Hurt(es[1]));
        Assert.Equal(1, b.LinesStruck);
        Assert.True(b.HandHeavies >= 2);
        Assert.True(es[0].Status.Has(StatusKind.Stun));
        Assert.True(b.DamageBy.GetValueOrDefault("sunder") > 0);
        Assert.Contains(b.Events.Drain(), x => x is Ev.Beam { Art: "slash_heavy_line" });
    }

    [Fact]
    public void Third_blow_makes_every_third_swing_heavy_and_burning_edge_sears_the_line()
    {
        var b = Fight("sunder", rules: ["sunder.third_blow", "sunder.burning_edge"]);
        var w = b.Weapons[0];
        var es = Dummies(b, NearAndFar);
        for (int i = 0; i < 2; i++) FireOnce(b, w, es, NearAndFar);
        Assert.Equal(0, b.LinesStruck);
        FireOnce(b, w, es, NearAndFar);
        Assert.Equal(1, b.LinesStruck);
        Assert.True(es[1].Status.Has(StatusKind.Sear));
    }

    [Fact]
    public void Wide_swing_turns_the_arc_to_300_degrees()
    {
        // Nearest ahead, and one 130° round from it: outside 220°, inside 300°.
        (double, double)[] at = [(1.5, 0), (2 * System.Math.Cos(2.27), 2 * System.Math.Sin(2.27))];
        foreach (var lit in new[] { false, true })
        {
            var b = Fight("sunder", rules: lit ? ["sunder.wide_swing"] : []);
            var es = Dummies(b, at);
            FireOnce(b, b.Weapons[0], es, at);
            Assert.True(Hurt(es[0]));
            Assert.Equal(lit, Hurt(es[1]));
        }
    }

    [Fact]
    public void Still_reach_reaches_further_only_standing_still()
    {
        // Just past her rank-1 reach (3 m, and its body's breadth): struck only standing still with the lamp.
        foreach (var (lit, still) in new[] { (false, true), (true, false), (true, true) })
        {
            var b = Fight("sunder", rules: lit ? ["sunder.still_reach"] : []);
            var es = Dummies(b, (3.1, 0));
            (double, double)[] at = [(3.15 + es[0].Radius, 0)];
            b.Player.StillT = still ? 1 : 0;
            FireOnce(b, b.Weapons[0], es, at);
            Assert.Equal(lit && still, Hurt(es[0]));
        }
    }

    /* ------------------------------------------------------- Groundbreaker -- */

    static readonly (double, double)[] PackAndPath = [(6, 0), (6, 0.8), (6.4, -0.6), (3, 0)];

    [Fact]
    public void Groundbreakers_crack_runs_to_the_pack_and_the_heave_stuns_it_but_not_a_boss()
    {
        var b = Fight("groundbreaker");
        var w = b.Weapons[0];
        var es = Dummies(b, PackAndPath);
        es[2].Boss = es[2].Elite = true;
        FireOnce(b, w, es, PackAndPath);
        Assert.Equal(1, b.Heaves);
        Assert.All(es, e => Assert.True(Hurt(e)));
        Assert.True(es[0].Status.Has(StatusKind.Stun) && es[1].Status.Has(StatusKind.Stun));
        Assert.False(es[2].Status.Has(StatusKind.Stun));
        Assert.True(es[2].Stagger > 0);
        // Along the crack: half the damage, no heave.
        Assert.False(es[3].Status.Has(StatusKind.Stun));
        Assert.InRange((es[3].MaxHp - es[3].Hp) / (es[0].MaxHp - es[0].Hp), 0.3, 0.8);
        Assert.True(b.DamageBy.GetValueOrDefault("groundbreaker") > 0);
        // Nothing within its range: it doesn't go off.
        var far = Fight("groundbreaker");
        var fs = Dummies(far, (12, 0));
        far.Weapons[0].Timer = 0;
        Firing.Tick(far, far.Weapons[0], 0.01);
        Assert.Equal(0, far.Heaves);
        // Fault line: the crack runs 14 m.
        var fl = Fight("groundbreaker", rules: ["groundbreaker.fault_line"]);
        var ls = Dummies(fl, (12, 0));
        FireOnce(fl, fl.Weapons[0], ls, [(12, 0)]);
        Assert.Equal(1, fl.Heaves);
        Assert.True(Hurt(ls[0]));
    }

    [Fact]
    public void Twin_cracks_heave_twice_and_upheaval_throws_up_the_lesser()
    {
        var b = Fight("groundbreaker", rules: ["groundbreaker.twin", "groundbreaker.upheaval"]);
        // A pair straight ahead (the pack, its center 6.25 m off) and one where each crack, splayed 30° either side of
        // the line to it, heaves.
        double a = System.Math.PI / 6;
        (double, double)[] at = [(6.25 * System.Math.Cos(a), 6.25 * System.Math.Sin(a)), (6.25 * System.Math.Cos(-a), 6.25 * System.Math.Sin(-a)), (6, 0), (6.5, 0)];
        var es = Dummies(b, at);
        es[1].Elite = true;
        FireOnce(b, b.Weapons[0], es, at);
        Assert.Equal(2, b.Heaves);
        Assert.All(es.Take(2), e => Assert.True(Hurt(e)));
        Assert.True(es[0].AirUntil > b.Time);
        Assert.Equal(0, es[1].AirUntil);
        // Airborne, it takes 30% more.
        double before = es[0].Hp;
        b.HitEnemy(es[0], 100, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        double airborne = before - es[0].Hp;
        es[0].AirUntil = 0;
        before = es[0].Hp;
        b.HitEnemy(es[0], 100, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        Assert.Equal(1.3, airborne / (before - es[0].Hp), 3);
    }

    /* ------------------------------------------------------ bespoke strands -- */

    [Fact]
    public void The_calling_strands_are_bespoke_and_suit_their_skills()
    {
        Assert.Equal(["wide", "holy", "sunder.stroke"], Wicks.Of("sunder")!.Strands);
        Assert.Equal(["wide", "linger", "groundbreaker.aftershock"], Wicks.Of("groundbreaker")!.Strands);
        Assert.Equal(StrandKind.Calling, Wicks.Strand("sunder", "sunder.stroke")!.Kind);
        Assert.Equal(StrandKind.Calling, Wicks.Strand("groundbreaker", "groundbreaker.aftershock")!.Kind);
        Assert.Null(Wicks.Strand("oathblade", "sunder.stroke"));
        Assert.StartsWith("Splitting Stroke:", Wicks.Text("sunder", "sunder.stroke.4"));
        Assert.StartsWith("Aftershock:", Wicks.Text("groundbreaker", "groundbreaker.aftershock.4"));
        Assert.Equal("+10% damage", Wicks.Text("sunder", "sunder.stroke.1"));
        var gb = Weapons.Get("groundbreaker");
        foreach (var s in new[] { "wide", "linger" })
            Assert.True(Wicks.Suits(Wicks.Strand("groundbreaker", s)!, WeaponBehavior.Crack, gb.Tags, gb.School, false));
        Assert.False(Wicks.Suits(Wicks.Strand("groundbreaker", "pulse")!, WeaponBehavior.Crack, gb.Tags, gb.School, false));
    }

    [Fact]
    public void Splitting_stroke_makes_every_second_swing_heavy_and_swings_slower()
    {
        var b = Fight("sunder", 4, plan: Strand("sunder.stroke"));
        var w = b.Weapons[0];
        Assert.Equal(["sunder.stroke"], w.Wick!.Turns);
        var es = Dummies(b, NearAndFar);
        FireOnce(b, w, es, NearAndFar);
        Assert.Equal(0, b.LinesStruck);
        FireOnce(b, w, es, NearAndFar);
        Assert.Equal(1, b.LinesStruck);
        FireOnce(b, w, es, NearAndFar);
        FireOnce(b, w, es, NearAndFar);
        Assert.Equal(2, b.LinesStruck);
        var bare = Fight("sunder", 4);
        Assert.Equal(1.15 * 0.92, Firing.CooldownOf(b, w) / Firing.CooldownOf(bare, bare.Weapons[0]), 6);
    }

    [Fact]
    public void Aftershock_heaves_the_same_spot_again_and_stuns_again()
    {
        var b = Fight("groundbreaker", 4, plan: Strand("groundbreaker.aftershock"));
        var w = b.Weapons[0];
        Assert.Equal(["groundbreaker.aftershock"], w.Wick!.Turns);
        (double, double)[] at = [(6, 0)];
        var es = Dummies(b, at);
        FireOnce(b, w, es, at);
        Assert.Equal(1, b.Heaves);
        double first = es[0].MaxHp - es[0].Hp;
        es[0].Status.Remove(StatusKind.Stun);
        for (int i = 0; i < 9 && b.Heaves < 2; i++) { Pin(b, es, at); b.Tick(0.1, 0, 0); }
        Assert.Equal(2, b.Heaves);
        Assert.True(es[0].Status.Has(StatusKind.Stun));
        double second = es[0].MaxHp - es[0].Hp - first;
        Assert.InRange(second / first, 0.4, 0.9);
    }
}
