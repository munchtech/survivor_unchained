using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;
using static SurvivorUnchained.Tests.FlareStagedTests;

namespace SurvivorUnchained.Tests;

/// <summary>Phase 6a's reaver Strikes (docs/design/CLASSES.md §3.6; Sim/FlareReaver.cs): Drag Them Under and the Butcher's Bill.</summary>
public class FlareReaverTests
{
    static List<Ev.Flare> Blows(List<Ev.Flare> ev, string part) => ev.Where(e => e.Phase == FlarePhase.Blow && e.Part == part).ToList();

    [Fact]
    public void Drag_them_under_hooks_the_far_hauls_them_to_a_knot_at_her_feet_and_slams_it()
    {
        var b = Carrying("drag_them_under");
        b.Aim = (10, 0);
        var far = Foe(b, 0, 12);
        var boss = Foe(b, -9, 0, boss: true);
        var ev = Cast(b);
        Assert.Equal(2, Blows(ev, "hook").Count);
        Assert.Single(Blows(ev, "knot"));
        var slam = Blows(ev, "slam").Single();
        Assert.True(slam.Last);
        Assert.Equal(8, slam.Hitstop);
        Assert.InRange(slam.TX, 1.4, 1.6);
        // Hauled into the knot; the boss only 3 m.
        Assert.True(Math.Sqrt(far.X * far.X + far.Z * far.Z) < 5, $"{far.X:0.0},{far.Z:0.0}");
        Assert.True(boss.X > -8.9, "dragged toward her (3 m; it walks on after)");
        Assert.True(far.Hp < far.MaxHp && boss.Hp < boss.MaxHp);
    }

    [Fact]
    public void Drag_them_under_with_nothing_near_bites_the_ground_round_her_reach_and_slams_the_knot()
    {
        var b = Carrying("drag_them_under", "drag.grinder");
        var ev = Cast(b);
        Assert.Equal(8, Blows(ev, "hook").Count);
        Assert.All(Blows(ev, "hook"), h => Assert.InRange(Math.Sqrt(h.TX * h.TX + h.TZ * h.TZ), 13.5, 14.5));
        Assert.Equal(3, Blows(ev, "grind").Count);
        Assert.Single(Blows(ev, "slam"));
    }

    [Fact]
    public void The_bill_leaps_on_the_strongest_and_chops_once_a_tenth_of_health_missing_each_mending()
    {
        int Chops(double hp, out double mended)
        {
            var b = Carrying("the_butchers_bill");
            Foe(b, 3, 0);
            var champ = Foe(b, 0, 7, elite: true);
            b.Player.Hp = b.MaxHp * hp;
            double before = b.Player.Hp;
            var ev = Cast(b);
            var leap = Blows(ev, "leap").Single();
            Assert.Equal(champ.Id, leap.Target);
            Assert.True(Math.Sqrt((b.Player.X - champ.X) * (b.Player.X - champ.X) + (b.Player.Z - champ.Z) * (b.Player.Z - champ.Z)) < 2.5);
            var chops = Blows(ev, "chop");
            Assert.All(chops, c => Assert.Equal(champ.Id, c.Target));
            Assert.True(chops[^1].Last && chops[^1].Hitstop == 7);
            mended = (b.Player.Hp - before) / b.MaxHp;
            return chops.Count;
        }
        Assert.Equal(4, Chops(0.7, out double m4));
        Assert.Equal(7, Chops(0.3, out double m8));
        Assert.True(m4 >= 0.079, $"{m4}");
        Assert.InRange(m8 - m4, 0.05, 0.07);
    }

    [Fact]
    public void The_bills_leftover_chops_vault_to_the_next_and_with_nothing_near_she_leaps_along_her_aim()
    {
        var b = Carrying("the_butchers_bill");
        var weak = Foe(b, 4, 0, hp: 1, elite: true);
        var next = Foe(b, 6, 2);
        var ev = Cast(b);
        Assert.Single(Blows(ev, "vault"));
        Assert.Contains(Blows(ev, "chop"), c => c.Target == next.Id);

        var e2 = Carrying("the_butchers_bill");
        e2.Aim = (0, 10);
        var ev2 = Cast(e2);
        var leap = Blows(ev2, "leap").Single();
        Assert.InRange(leap.TZ, 5.9, 6.1);
        Assert.Equal(4, Blows(ev2, "chop").Count);
        Assert.InRange(e2.Player.Z, 5.5, 6.5);
    }
}
