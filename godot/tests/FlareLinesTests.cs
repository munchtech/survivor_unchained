using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;
using static SurvivorUnchained.Tests.FlareStagedTests;

namespace SurvivorUnchained.Tests;

/// <summary>Phase 6a's line Flares (docs/design/CLASSES.md §3.6, §7's phase-6 plan; Sim/FlareLines.cs): the Long Cut and
/// One Arrow, on the shared line hit.</summary>
public class FlareLinesTests
{
    static List<Ev.Flare> Blows(List<Ev.Flare> ev, string part) => ev.Where(e => e.Phase == FlarePhase.Blow && e.Part == part).ToList();

    [Fact]
    public void The_long_cut_sweeps_its_reach_then_cleaves_a_24_m_line_along_her_aim_and_sunders_a_boss_in_it()
    {
        var b = Carrying("the_long_cut");
        b.Aim = (20, 0);
        var side = Foe(b, 0, 8);                 // in the sweep, off the line
        var far = Foe(b, 20, 0.5);               // beyond the sweep, on the line
        var off = Foe(b, 20, 6);                 // beyond both
        var boss = Foe(b, 10, 0, boss: true);
        var ev = Cast(b);
        var sweep = Blows(ev, "sweep");
        var cleave = Blows(ev, "cleave");
        Assert.Single(sweep);
        Assert.Single(cleave);
        Assert.Equal(3, sweep[0].Hitstop);
        Assert.Equal(8, cleave[0].Hitstop);
        Assert.True(cleave[0].Last);
        Assert.InRange(cleave[0].TX, 23.9, 24.1);
        Assert.Equal(boss.Id, cleave[0].Target);
        Assert.True(side.Hp < side.MaxHp && far.Hp < far.MaxHp);
        Assert.Equal(off.MaxHp, off.Hp);
        Assert.True(boss.SunderUntil > b.Time + 7 && boss.Sunder > 0.29);
        Assert.True(ev.FindIndex(e => e.Part == "sweep") < ev.FindIndex(e => e.Part == "cleave"));
    }

    [Fact]
    public void A_sundered_boss_takes_more_and_the_long_cut_with_nothing_near_still_cleaves_its_full_line()
    {
        var b = Carrying("the_long_cut");
        b.Aim = (0, 10);
        var ev = Cast(b);
        var cleave = Blows(ev, "cleave").Single();
        Assert.Equal(0, cleave.Target);
        Assert.InRange(cleave.TZ - b.Player.Z, 23.9, 24.1);
        Assert.True(cleave.Radius > 0);
        Assert.Single(Blows(ev, "sweep"));

        var b2 = Carrying("the_long_cut");
        var boss = Foe(b2, 3, 0, boss: true);
        double before = b2.HitEnemy(boss, 100, School.Physical, [], new HitOpts { NoCrit = true });
        boss.Sunder = 0.3;
        boss.SunderUntil = b2.Time + 8;
        double after = b2.HitEnemy(boss, 100, School.Physical, [], new HitOpts { NoCrit = true });
        Assert.InRange(after / before, 1.29, 1.31);
    }

    [Fact]
    public void Second_cut_sweeps_again_and_line_of_morning_leaves_the_line_burning_and_through_the_wall_runs_36_m()
    {
        var b = Carrying("the_long_cut", "long_cut.second_cut", "long_cut.line_of_morning", "long_cut.through_the_wall");
        b.Aim = (10, 0);
        var far = Foe(b, 30, 0);
        var ev = Cast(b, 1.2);
        Assert.Equal(2, Blows(ev, "sweep").Count);
        Assert.True(Blows(ev, "sweep")[1].Last);
        Assert.InRange(Blows(ev, "cleave").Single().TX, 35.9, 36.1);
        Assert.Single(Blows(ev, "burnline"));
        double hp = far.Hp;
        Run(b, 2);
        Assert.True(far.Hp < hp, "the burning line keeps hurting what stands in it");
    }

    static void NoCrits(Battle b) => b.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -b.Stats.Get(Stat.CritChance), "test"));

    [Fact]
    public void A_boss_takes_second_cuts_counter_sweep_and_the_burning_line_whole_as_the_crowd_does()
    {
        // Off the line, in the sweep's reach: only the two sweeps reach them.
        var b = Carrying("the_long_cut", "long_cut.second_cut");
        NoCrits(b);
        b.Aim = (20, 0);
        Foe(b, 0, 6, hp: 1e9, boss: true);
        Foe(b, 0, -6, hp: 1e9);
        b.FillFlare(100, "t");
        b.Events.Drain();
        Assert.True(b.UseFlare(1, 0));
        var took = new List<(double Boss, double Man)>();
        for (int i = 0; i < 90; i++)
        {
            b.Tick(1 / 60.0, 0, 0);
            if (!b.Events.Drain().OfType<Ev.Flare>().Any(e => e.Phase == FlarePhase.Blow && e.Part == "sweep")) continue;
            double onBoss = b.BossDamageBy.GetValueOrDefault("flare");
            took.Add((onBoss, b.DamageBy.GetValueOrDefault("flare") - onBoss));
        }
        Assert.Equal(2, took.Count);
        // No hidden boss measure (the owner, 13 October): a boss takes the counter-sweep whole, as the crowd does.
        Assert.InRange((took[1].Boss - took[0].Boss) / took[0].Boss, 0.99, 1.01);
        Assert.InRange((took[1].Man - took[0].Man) / took[0].Man, 0.99, 1.01);

        // The burning line's fires hit a boss as hard as anything else in them.
        var c = Carrying("the_long_cut", "long_cut.line_of_morning");
        NoCrits(c);
        c.Aim = (20, 0);
        Cast(c, 1.2);
        var fires = c.Zones.Items.Where(z => z.Alive && z.Credit == "flare").ToList();
        Assert.NotEmpty(fires);
        var fire = c.SpawnZone(Side.Player, -6, 6, 2, 2, 100, School.Holy)!;
        fire.Credit = "test";
        Foe(c, -6, 6, hp: 1e9, boss: true);
        Foe(c, -6.5, 6, hp: 1e9);
        Run(c, 1 / 60.0);
        double fb = c.BossDamageBy["test"];
        Assert.InRange(fb / (c.DamageBy["test"] - fb), 0.99, 1.01);
    }

    [Fact]
    public void One_arrow_pierces_a_30_m_line_kills_the_ordinary_it_leaves_low_and_splits_on_the_toughest()
    {
        var b = Carrying("one_arrow");
        b.Aim = (30, 0);
        var near = Foe(b, 5, 0, hp: 10);         // falls to the arrow (or dies below 30%)
        var tough = Foe(b, 12, 0, elite: true);  // the toughest it passes: a split leaves from it
        var past = Foe(b, 28, 0.5);
        var off = Foe(b, 10, 8);
        var ev = Cast(b);
        var arrow = Blows(ev, "arrow").Single();
        Assert.Equal(7, arrow.Hitstop);
        Assert.InRange(arrow.TX, 29.9, 30.1);
        Assert.False(near.Alive && near.State != EnemyState.Dying);
        Assert.True(tough.Hp < tough.MaxHp && past.Hp < past.MaxHp);
        Assert.Equal(off.MaxHp, off.Hp);
        var splits = Blows(ev, "split");
        Assert.Equal(3, splits.Count);
        Assert.True(splits[^1].Last);
        // The first split leaves from the toughest (the champion, where the arrow met it; it has walked on since).
        Assert.InRange(splits[0].X, 10.5, 12.5);
        Assert.True(ev.FindIndex(e => e.Part == "arrow") < ev.FindIndex(e => e.Part == "split"));
    }

    [Fact]
    public void One_arrow_with_nothing_near_flies_its_full_length_and_splits_at_its_end()
    {
        var b = Carrying("one_arrow");
        b.Aim = (0, -10);
        var ev = Cast(b);
        var arrow = Blows(ev, "arrow").Single();
        Assert.InRange(arrow.TZ - b.Player.Z, -30.1, -29.9);
        var splits = Blows(ev, "split");
        Assert.Equal(3, splits.Count);
        Assert.All(splits, s => { Assert.InRange(s.Z - b.Player.Z, -30.1, -29.9); Assert.True(s.Radius > 0); });
    }

    [Fact]
    public void One_arrow_strikes_a_boss_twice_as_hard_and_through_the_heart_stops_in_it_and_turns_its_splits_back()
    {
        double Took(params string[] mods)
        {
            var b = Carrying("one_arrow", mods);
            b.Aim = (30, 0);
            var boss = Foe(b, 10, 0, boss: true);
            var behind = Foe(b, 20, 0);
            var ev = Cast(b);
            if (mods.Length > 0)
            {
                Assert.Equal(behind.MaxHp, behind.Hp);
                Assert.InRange(Blows(ev, "arrow").Single().TX, 9, 10.01);
                Assert.All(Blows(ev, "split"), s => Assert.Equal(boss.Id, s.Target));
            }
            return boss.MaxHp - boss.Hp;
        }
        double plain = Took(), heart = Took("arrow.heart");
        Assert.True(heart > plain * 1.5, $"{heart:0} against {plain:0}");
    }

    [Fact]
    public void Pinned_to_the_earth_binds_what_it_strikes_and_split_thrice_more_splits_six_times()
    {
        var b = Carrying("one_arrow", "arrow.pinned", "arrow.split");
        b.Aim = (30, 0);
        var e = Foe(b, 8, 0);
        var ev = Cast(b);
        Assert.Equal(6, Blows(ev, "split").Count);
        Assert.True(e.Status.Has(StatusKind.Bound));
    }
}
