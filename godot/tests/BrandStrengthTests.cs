using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;
using static SurvivorUnchained.Tests.FlareStagedTests;

namespace SurvivorUnchained.Tests;

/// <summary>(L2, found fixing SU-054) A pending brand bursts with its own cast's power, and the marks preview a wave at
/// its own cast's reach: a Branding pressed before the last one's brands burst lends them neither.</summary>
public sealed class BrandStrengthTests
{
    static void Run(Battle b, double s, System.Action? each = null)
    {
        for (double t = 0; t < s - 1e-9; t += 1 / 60.0) { b.Tick(1 / 60.0, 0, 0); each?.Invoke(); }
    }

    /// <summary>The echo's first burst on a lone foe (Second Brand of a clutch cast): alone, or with a plain cast pressed
    /// once the echo has branded (before it bursts).</summary>
    static (double Took, bool Pressed) EchoBurst(bool second)
    {
        var b = Carrying("the_branding", "branding.second");
        var e = Foe(b, 3, 0);
        b.Player.Hp = b.MaxHp * 0.1;
        b.FillFlare(100, "t");
        b.Events.Drain();
        Assert.True(b.UseFlare(1, 0));
        int brandsSeen = 0;
        bool pressed = false;
        for (int i = 0; i < 600; i++)
        {
            double hp = e.Hp;
            b.Tick(1 / 60.0, 0, 0);
            var ev = b.Events.Drain().OfType<Ev.Flare>().ToList();
            if (brandsSeen >= 2 && ev.Any(x => x.Part == "burst")) return (hp - e.Hp, pressed);
            brandsSeen += ev.Count(x => x.Part == "brand");
            if (brandsSeen >= 2 && second && !pressed)
            {
                // a plain cast, and a stronger one (her level up: a bigger Flare power)
                b.Player.Hp = b.MaxHp;
                b.Level += 20; b.EmberLevel += 20;
                b.FillFlare(100, "t");
                pressed = b.UseFlare(1, 0);
            }
        }
        return (-1, pressed);
    }

    [Fact]
    public void A_pending_brand_bursts_with_its_own_casts_power()
    {
        var (alone, _) = EchoBurst(false);
        var (withPlain, pressed) = EchoBurst(true);
        Assert.True(alone > 0);
        Assert.True(pressed, "the plain cast was pressed before the echo burst");
        Assert.Equal(alone, withPlain, 6);
    }

    [Fact]
    public void An_owed_second_brand_is_previewed_at_its_own_casts_reach()
    {
        var b = Carrying("the_branding", "branding.second");
        Foe(b, 3, 0);
        b.Player.Hp = b.MaxHp * 0.1;
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        double clutchReach = 0;
        Run(b, 0.3, () => clutchReach = System.Math.Max(clutchReach, Ring(b)));
        Run(b, 0.95);
        b.Player.Hp = b.MaxHp;
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        double plainReach = double.MaxValue, owedMax = 0;
        Run(b, 0.15, () =>
        {
            var rings = Rings(b);
            if (rings.Count > 0) { plainReach = System.Math.Min(plainReach, rings.Min()); owedMax = System.Math.Max(owedMax, rings.Max()); }
        });
        Assert.True(clutchReach > plainReach + 1e-6, $"clutch {clutchReach} vs plain {plainReach}");
        Assert.Equal(clutchReach, owedMax, 6);
    }

    static List<double> Rings(Battle b) => b.FlareMarkShapes
        .Where(s => s.Kind == FlareMarkShapeKind.Circle && System.Math.Abs(s.X - b.Player.X) < 1e-6 && System.Math.Abs(s.Z - b.Player.Z) < 1e-6)
        .Select(s => s.Radius).ToList();

    static double Ring(Battle b) => Rings(b).DefaultIfEmpty(0).Max();
}
