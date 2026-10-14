using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;
using static SurvivorUnchained.Tests.FlareStagedTests;

namespace SurvivorUnchained.Tests;

/// <summary>Phase 6a's Branding (docs/design/CLASSES.md §3.6, §7's phase-6 plan; Sim/FlareBranding.cs).</summary>
public class FlareBrandingTests
{
    /// <summary>The press, then each Flare event with the seconds since the press.</summary>
    static List<(double T, Ev.Flare E)> Timed(Battle b, double seconds = 2.5)
    {
        b.FillFlare(100, "t");
        b.Events.Drain();
        double t0 = b.Time;
        Assert.True(b.UseFlare(1, 0));
        var got = b.Events.Drain().OfType<Ev.Flare>().Select(e => (0.0, e)).ToList();
        for (double t = 0; t < seconds - 1e-9; t += 1 / 60.0)
        {
            b.Tick(1 / 60.0, 0, 0);
            got.AddRange(b.Events.Drain().OfType<Ev.Flare>().Select(e => (b.Time - t0, e)));
        }
        return got;
    }

    [Fact]
    public void The_branding_brands_all_in_reach_then_bursts_them_outward_and_the_boss_last_and_hardest()
    {
        var b = Carrying("the_branding");
        var near = Foe(b, 2, 0);
        var far = Foe(b, 0, 11);
        var boss = Foe(b, -6, 0, boss: true);
        var ev = Timed(b);
        var brands = ev.Where(x => x.E.Part == "brand").ToList();
        Assert.Equal(3, brands.Count);
        Assert.All(brands, x => Assert.InRange(x.T, 0.43, 0.48));
        // One hitstop for the brand, on its first crescent.
        Assert.Equal(1, brands.Count(x => x.E.Hitstop > 0));
        Assert.True(near.Status.Has(StatusKind.Mark) && far.Status.Has(StatusKind.Mark));
        var bursts = ev.Where(x => x.E.Part == "burst").ToList();
        Assert.Equal(3, bursts.Count);
        double Tof(Enemy e) => bursts.Single(x => x.E.Target == e.Id).T;
        Assert.True(Tof(near) < Tof(far), "outward from her");
        Assert.True(Tof(far) < Tof(boss), "the boss last");
        Assert.InRange(Tof(near), 0.74, 0.85);
        var last = bursts.Single(x => x.E.Last);
        Assert.Equal(boss.Id, last.E.Target);
        Assert.Equal(6, last.E.Hitstop);
        Assert.True(near.Hp < near.MaxHp && boss.Hp < boss.MaxHp);
        // It all lands inside the Strike: the End comes after the boss's burst.
        Assert.True(ev.FindIndex(x => x.E.Phase == FlarePhase.End) > ev.FindIndex(x => x.E.Last));
    }

    [Fact]
    public void A_death_passes_its_mark_to_the_next_thing_standing_which_bursts_in_its_turn()
    {
        var b = Carrying("the_branding");
        // She stands 13 m from the weak one (in reach) and 17 m from the other (beyond it, 4 m past the weak one).
        b.Player.X = -7;
        var weak = Foe(b, 6, 0, hp: 1);
        var beyond = Foe(b, 10, 0, hp: 1e6);
        var ev = Timed(b);
        var pass = ev.Where(x => x.E.Part == "pass").ToList();
        Assert.Single(pass);
        Assert.Equal(beyond.Id, pass[0].E.Target);
        Assert.InRange(pass[0].E.X - weak.X, -0.3, 0.3);
        Assert.True(beyond.Hp < beyond.MaxHp, "the passed mark burst on it");
        Assert.True(beyond.Status.Has(StatusKind.Mark));
    }

    [Fact]
    public void The_branding_with_nothing_near_prints_its_brands_on_the_ground_and_bursts_them_there()
    {
        var b = Carrying("the_branding");
        var ev = Timed(b);
        var brands = ev.Where(x => x.E.Part == "brand").ToList();
        var bursts = ev.Where(x => x.E.Part == "burst").ToList();
        Assert.True(brands.Count >= 12, $"{brands.Count} brands");
        Assert.Equal(brands.Count, bursts.Count);
        Assert.All(bursts, x => { Assert.Equal(0, x.E.Target); Assert.True(x.E.Radius > 0); });
        Assert.Single(bursts, x => x.E.Last && x.E.Hitstop == 6);
        // A ripple: farther brands burst later.
        double D(Ev.Flare e) => Math.Sqrt((e.TX - b.Player.X) * (e.TX - b.Player.X) + (e.TZ - b.Player.Z) * (e.TZ - b.Player.Z));
        var byD = bursts.OrderBy(x => D(x.E)).ToList();
        Assert.True(byD[0].T < byD[^1].T);
        Assert.InRange(byD[^1].T, 0.9, 1.12);
    }

    [Fact]
    public void The_eye_keeps_the_boss_brand_open_and_bursts_it_whenever_a_marked_thing_falls_near()
    {
        double Took(bool eye)
        {
            var b = eye ? Carrying("the_branding", "branding.eye") : Carrying("the_branding");
            var boss = Foe(b, 4, 0, boss: true);
            var lesser = Enumerable.Range(0, 4).Select(i => Foe(b, 4 + Math.Cos(i * 1.6) * 3, Math.Sin(i * 1.6) * 3, hp: 1e6)).ToList();
            var ev = Timed(b, 2);
            // After the Flare, her own hand finishes the marked ones near the boss.
            foreach (var e in lesser) b.KillEnemy(e, true, null);
            ev.AddRange(Run(b, 0.2).Select(e => (2.2, e)));
            return boss.MaxHp - boss.Hp;
        }
        double plain = Took(false), eye = Took(true);
        Assert.True(eye > plain * 1.2, $"eye {eye:0} against {plain:0}");
    }

    [Fact]
    public void Second_brand_brands_again_a_second_later_and_branded_deep_bursts_wider()
    {
        var b = Carrying("the_branding", "branding.second", "branding.deep");
        Foe(b, 3, 0);
        var ev = Timed(b, 3);
        var brands = ev.Where(x => x.E.Part == "brand").ToList();
        Assert.Equal(2, brands.Count);
        Assert.InRange(brands[1].T - brands[0].T, 0.98, 1.02);
        var burst = ev.First(x => x.E.Part == "burst");
        Assert.InRange(burst.E.Radius, 2.99, 3.01);
    }
}
