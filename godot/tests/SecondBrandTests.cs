using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;
using static SurvivorUnchained.Tests.FlareStagedTests;

namespace SurvivorUnchained.Tests;

/// <summary>(Codex audit SU-054) Second Brand is owed per cast: a Branding pressed before the last one's second brand
/// lands neither cancels it nor lends it its own strength (two casts, four waves; each echo at its cast's reach).</summary>
public sealed class SecondBrandTests
{
    [Fact]
    public void Two_brandings_give_four_waves_each_echo_at_its_own_casts_strength()
    {
        var b = Carrying("the_branding", "branding.second");
        Foe(b, 3, 0);
        var got = new List<(double T, Ev.Flare E)>();
        double t0 = b.Time;
        void Run(double s)
        {
            for (double t = 0; t < s - 1e-9; t += 1 / 60.0)
            {
                b.Tick(1 / 60.0, 0, 0);
                got.AddRange(b.Events.Drain().OfType<Ev.Flare>().Select(e => (b.Time - t0, e)));
            }
        }
        // The first at the clutch (her reach grown), the second at full health, pressed before the first's echo.
        b.Player.Hp = b.MaxHp * 0.1;
        b.FillFlare(100, "t");
        b.Events.Drain();
        Assert.True(b.UseFlare(1, 0));
        Run(1.25);
        Assert.Empty(got.Where(x => x.T > 0.9 && x.E.Part == "brand"));
        b.Player.Hp = b.MaxHp;
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        double t2 = b.Time - t0;
        Run(3);
        var brands = got.Where(x => x.E.Part == "brand").ToList();
        Assert.Equal(4, brands.Count);
        var bursts = got.Where(x => x.E.Part == "burst").ToList();
        Assert.Equal(4, bursts.Count);
        // Bursts in time order: cast 1, cast 1's echo (before cast 2's first lands), cast 2, cast 2's echo.
        var echo1 = bursts.Single(x => x.T > 1.3 && x.T < t2 + 0.6);
        var first1 = bursts.First();
        var last2 = bursts.Last();
        Assert.Equal(first1.E.Radius, echo1.E.Radius, 6);
        Assert.True(first1.E.Radius > last2.E.Radius + 1e-6, $"clutch {first1.E.Radius} vs plain {last2.E.Radius}");
    }
}
