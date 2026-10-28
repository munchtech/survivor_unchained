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
        // Unkillable while they rise too (a carried Rebuke strikes back at any block).
        foreach (var e in es) e.MaxHp = e.Hp = 1e9;
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

    /* ------------------------------------------------------------- Rebuke -- */

    /// <summary>The blocker 2 m off; three near it (1, 1.5, 2.1 m from it); a fourth 3 m from it (not among the three
    /// nearest); one 7 m from it.</summary>
    static readonly (double, double)[] Blocker = [(2, 0), (3, 0), (2, 1.5), (1, -1.8), (2, -3), (9, 0)];

    /// <summary>A sure block (the Warding light) of a blow from `from`.</summary>
    static void Block(Battle b, Enemy? from)
    {
        if (!b.Boons.ContainsKey("warding")) b.AddBoon("warding");
        b.Player.Iframes = 0;
        b.Player.BlockT = 0;
        int blocks = b.Blocks;
        Assert.Equal(0, b.HurtPlayer(10, School.Physical, "test", from));
        Assert.Equal(blocks + 1, b.Blocks);
    }

    static double Taken(Enemy e) => e.MaxHp - e.Hp;

    [Fact]
    public void Rebuke_strikes_the_blocker_and_the_three_nearest_it_on_a_block_credited_rebuke_not_wall()
    {
        var b = Fight("rebuke");
        var es = Dummies(b, Blocker);
        // It never fires on its own.
        var w = b.Weapons[0];
        w.Timer = 0;
        int strikes = b.RebukeStrikes;
        Firing.Tick(b, w, 0.01);
        Assert.Equal(strikes, b.RebukeStrikes);
        foreach (var e in es) e.Hp = e.MaxHp;
        Pin(b, es, Blocker);
        Block(b, es[0]);
        Assert.Equal(strikes + 1, b.RebukeStrikes);
        Assert.All(es.Take(4), e => Assert.True(Hurt(e)));
        Assert.False(Hurt(es[4]));
        Assert.False(Hurt(es[5]));
        Assert.True(b.DamageBy.GetValueOrDefault("rebuke") > 0);
        Assert.Equal(0, b.DamageBy.GetValueOrDefault("wall"));
        // Thrown back, away from her.
        Assert.True(es[1].Kbx > 0);
        // A missile's block (no blocker near): the three nearest her.
        var c = Fight("rebuke");
        var cs = Dummies(c, Blocker);
        Block(c, null);
        Assert.Equal(3, cs.Count(Hurt));
        Assert.True(Hurt(cs[0]) && Hurt(cs[2]) && Hurt(cs[3]));
    }

    [Fact]
    public void Rebuke_carried_gives_a_block_chance_of_8_percent_and_1_more_a_rank()
    {
        static int Blocks(int rank)
        {
            var b = Fight("rebuke", rank);
            var es = Dummies(b, [(30, 0)]);
            for (int i = 0; i < 2000; i++) { b.Player.Iframes = 0; b.Player.Hp = b.MaxHp; b.HurtPlayer(1, School.Physical, "test", null); }
            return b.Blocks;
        }
        Assert.InRange(Blocks(1), 2000 * 0.065, 2000 * 0.095);
        Assert.InRange(Blocks(5), 2000 * 0.10, 2000 * 0.14);
    }

    [Fact]
    public void The_walls_answer_is_credited_wall_and_readier_answers_at_five()
    {
        var b = Fight("oathblade");
        var es = Dummies(b, [(2, 0)]);
        b.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "shield_arm", Args = new Dictionary<string, double> { ["block"] = 0, ["stones"] = 6, ["struck"] = 1, ["radius"] = 8, ["rebuke"] = 10, ["per_level"] = 0.08 } });
        b.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "rebuke.readier", Args = new Dictionary<string, double>() });
        for (int i = 0; i < 5; i++) { b.Player.Iframes = 0; b.HurtPlayer(1, School.Physical, "test", null); }
        Assert.Equal(1, b.Rebukes);
        Assert.True(b.DamageBy.GetValueOrDefault("wall") > 0);
        Assert.Equal(0, b.DamageBy.GetValueOrDefault("rebuke"));
    }

    [Fact]
    public void Rebuke_the_strong_doubles_on_an_elite_and_answering_light_mends_once_a_half_second()
    {
        double On(bool strong)
        {
            var b = Fight("rebuke", rules: strong ? ["rebuke.strong", "rebuke.answering"] : []);
            var es = Dummies(b, [(2, 0), (2, 1)]);
            es[1].Elite = true;
            b.Player.Hp = b.MaxHp * 0.5;
            Block(b, es[0]);
            if (strong)
            {
                Assert.Equal(b.MaxHp * 0.51, b.Player.Hp, 6);
                Block(b, es[0]);
                Assert.Equal(b.MaxHp * 0.51, b.Player.Hp, 6);
                b.Tick(0.6, 0, 0);
                double hp = b.Player.Hp;
                Block(b, es[0]);
                Assert.Equal(hp + b.MaxHp * 0.01, b.Player.Hp, 6);
                return Taken(es[1]) / Taken(es[0]);
            }
            return Taken(es[1]) / Taken(es[0]);
        }
        // Elites and the rest take the same blow, but the elite twice over with strong (crits aside: compared as ratios).
        Assert.InRange(On(true) / On(false), 1.6, 2.5);
    }

    [Fact]
    public void Rebuke_strikes_from_an_echo_s_corpse_and_on_kill_suits_it()
    {
        var b = Fight("rebuke");
        (double, double)[] at = [(6, 0), (7, 0), (6, 1), (6, -1.2), (8.5, 0)];
        var es = Dummies(b, at);
        Assert.True(Firing.OnKillEcho(b, b.Weapons[0], b.Player.X + 6, b.Player.Z));
        Assert.Equal(3, es.Count(Hurt));
        Assert.False(Hurt(es[4]));
        var rb = Weapons.Get("rebuke");
        Assert.True(Wicks.Suits(Wicks.Strand("rebuke", "onkill")!, WeaponBehavior.Reactive, rb.Tags, rb.School, false));
    }

    /* --------------------------------------------------------- Watch Bell -- */

    static readonly (double, double)[] Ring = [(6, 0), (0, 5), (-4, -4), (9, 0)];

    [Fact]
    public void The_bell_draws_what_is_near_to_her_strikes_it_and_wards_her()
    {
        var b = Fight("watch_bell");
        var w = b.Weapons[0];
        var es = Dummies(b, Ring);
        double shield = b.Player.Shield;
        FireOnce(b, w, es, Ring);
        Assert.Equal(1, b.Tolls);
        Assert.All(es.Take(3), e => Assert.True(Hurt(e)));
        Assert.False(Hurt(es[3]));
        Assert.Equal(b.MaxHp * 0.02 * 3, b.Player.Shield - shield, 6);
        Assert.Equal(b.MaxHp * 0.02 * 3, b.BellBarrier, 6);
        for (int i = 0; i < 10; i++) b.Tick(0.05, 0, 0);
        foreach (var e in es.Take(3))
            Assert.InRange(System.Math.Sqrt((e.X - b.Player.X) * (e.X - b.Player.X) + (e.Z - b.Player.Z) * (e.Z - b.Player.Z)), 0, 2.6);
        // A boss isn't drawn (nor gives a barrier), but is struck.
        var c = Fight("watch_bell");
        var bs = Dummies(c, [(5, 0)]);
        bs[0].Boss = true;
        FireOnce(c, c.Weapons[0], bs, [(5, 0)]);
        Assert.True(Hurt(bs[0]));
        Assert.Equal(0, c.BellBarrier);
        Assert.Equal(0, bs[0].Kbx);
    }

    [Fact]
    public void The_loud_bell_reaches_10_m_iron_slows_and_bell_and_barrier_gives_3_percent()
    {
        var b = Fight("watch_bell", rules: ["watch_bell.loud", "watch_bell.iron", "watch_bell.barrier"]);
        var es = Dummies(b, Ring);
        FireOnce(b, b.Weapons[0], es, Ring);
        Assert.All(es, e => Assert.True(Hurt(e)));
        Assert.Equal(b.MaxHp * 0.03 * 4, b.BellBarrier, 6);
        Assert.All(es, e => { Assert.True(e.SlowUntil > b.Time + 2); Assert.Equal(0.3, e.SlowBy, 6); });
    }

    [Fact]
    public void Oath_and_bell_tolls_on_a_stagger_at_most_every_3_s()
    {
        var b = Fight("watch_bell", rules: ["oath_and_bell"]);
        var w = b.Weapons[0];
        var es = Dummies(b, [(3, 0)]);
        b.HitEnemy(es[0], 1, School.Physical, [Tag.Physical], new HitOpts { Heavy = true });
        Firing.Tick(b, w, 0.01);
        Assert.Equal(1, b.Tolls);
        Assert.True(w.Timer > 100);
        b.HitEnemy(es[0], 1, School.Physical, [Tag.Physical], new HitOpts { Heavy = true });
        Firing.Tick(b, w, 0.01);
        Assert.Equal(1, b.Tolls);
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
        Assert.InRange(second / first, 0.25, 0.6);
    }

    [Fact]
    public void Shield_of_morning_leaves_a_barrier_for_each_creature_a_rebuke_strikes()
    {
        Assert.Equal(["fire", "onkill", "rebuke.morning"], Wicks.Of("rebuke")!.Strands);
        Assert.StartsWith("Shield of Morning:", Wicks.Text("rebuke", "rebuke.morning.4"));
        var b = Fight("rebuke", 4, plan: Strand("rebuke.morning"));
        Assert.Equal(["rebuke.morning"], b.Weapons[0].Wick!.Turns);
        var es = Dummies(b, Blocker);
        double shield = b.Player.Shield;
        Block(b, es[0]);
        Assert.Equal(b.MaxHp * 0.04, b.Player.Shield - shield, 6);
        // Two struck, 2%.
        var c = Fight("rebuke", 4, plan: Strand("rebuke.morning"));
        (double, double)[] two = [(2, 0), (2.5, 1)];
        var cs = Dummies(c, two);
        shield = c.Player.Shield;
        Block(c, cs[0]);
        Assert.Equal(c.MaxHp * 0.02, c.Player.Shield - shield, 6);
    }

    [Fact]
    public void Stone_bell_lays_a_stone_a_toll_and_one_more_a_champion_drawn()
    {
        Assert.Equal(["wide", "pulse", "watch_bell.stone"], Wicks.Of("watch_bell")!.Strands);
        Assert.StartsWith("Stone Bell:", Wicks.Text("watch_bell", "watch_bell.stone.4"));
        var wb = Weapons.Get("watch_bell");
        foreach (var s in new[] { "wide", "pulse" })
            Assert.True(Wicks.Suits(Wicks.Strand("watch_bell", s)!, WeaponBehavior.Toll, wb.Tags, wb.School, false));
        var b = Fight("watch_bell", 4, plan: Strand("watch_bell.stone"));
        b.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "shield_arm", Args = new Dictionary<string, double> { ["block"] = 0, ["stones"] = 10 } });
        var es = Dummies(b, Ring);
        es[0].Elite = true;
        FireOnce(b, b.Weapons[0], es, Ring);
        Assert.Equal(2, b.Stones);
    }
}
