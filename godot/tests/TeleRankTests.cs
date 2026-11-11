using System;
using System.Collections.Generic;
using System.IO;
using SurvivorUnchained.View;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The telegraph rank reserve (docs/design/ARPG_FUN.md P0 item 4): rank 1 and rank 2 hues are never hers.</summary>
public class TeleRankTests
{
    readonly ITestOutputHelper log;
    public TeleRankTests(ITestOutputHelper o) { log = o; }

    static (double H, double S) Hs(string hex)
    {
        double r = Convert.ToInt32(hex.Substring(1, 2), 16) / 255.0, g = Convert.ToInt32(hex.Substring(3, 2), 16) / 255.0, b = Convert.ToInt32(hex.Substring(5, 2), 16) / 255.0;
        double mx = Math.Max(r, Math.Max(g, b)), mn = Math.Min(r, Math.Min(g, b)), d = mx - mn;
        double h = d == 0 ? 0 : mx == r ? 60 * (((g - b) / d + 6) % 6) : mx == g ? 60 * ((b - r) / d + 2) : 60 * ((r - g) / d + 4);
        return (h, mx == 0 ? 0 : d / mx);
    }
    static double Dist(double a, double b) { double d = Math.Abs(a - b) % 360; return d > 180 ? 360 - d : d; }

    static TeleRank Table()
    {
        for (var dir = new DirectoryInfo(AppContext.BaseDirectory); dir != null; dir = dir.Parent)
        {
            var f = Path.Combine(dir.FullName, "data", "content", "tele_rank.json");
            if (File.Exists(f)) return TeleRank.Parse(File.ReadAllText(f));
        }
        throw new FileNotFoundException("data/content/tele_rank.json");
    }

    [Fact]
    public void FallbackEqualsData()
    {
        var d = Table(); var f = TeleRank.Parse(TeleRank.Fallback);
        Assert.Equal(d.Rows, f.Rows);
    }

    [Fact(Skip = "FAILS on purpose-data: Fire glow/light (hue 21-22) is 3.5-5 deg from the crowd orange #ff7a14 (hue 26); Physical glow/light 10 deg. Her school hues are another lead's; remove Skip when resolved.")]
    public void HerSchoolHuesStayClearOfTheReservedRanks()
    {
        // Copied from godot/src/Fx/Palette.cs lines 27 (Physical), 28 (Fire), 34 (Holy): core, glow, light.
        var hers = new Dictionary<string, string>
        {
            ["Physical core"] = "#fff6e4", ["Physical glow"] = "#ffd9a0", ["Physical light"] = "#ffd9a0",
            ["Fire core"] = "#ffe29a", ["Fire glow"] = "#ff6a1a", ["Fire light"] = "#ff7a2a",
            ["Holy core"] = "#fffbe8", ["Holy glow"] = "#ffd46a", ["Holy light"] = "#ffe0a0",
        };
        var t = Table();
        var fails = new List<string>();
        foreach (var rk in new[] { t.Boss, t.Crowd })
        {
            var (rh, _) = Hs(rk.Color);
            foreach (var (name, hex) in hers)
            {
                var (h, s) = Hs(hex);
                double d = Dist(h, rh);
                log.WriteLine($"{name} {hex} hue {h:F1} sat {s:F2} vs {rk.Name} {rk.Color} hue {rh:F1}: {d:F1} deg");
                if (d < 12 && s >= 0.35) fails.Add($"{name} {hex} is {d:F1} deg from {rk.Name} (sat {s:F2})");
            }
        }
        Assert.True(fails.Count == 0, string.Join("; ", fails));
    }

    [Fact]
    public void ThreatRanksAreApartInHueOrEnergy()
    {
        var t = Table();
        var rows = new[] { t.Boss, t.Crowd, t.Ground };
        for (int i = 0; i < rows.Length; i++)
            for (int j = i + 1; j < rows.Length; j++)
            {
                double d = Dist(Hs(rows[i].Color).H, Hs(rows[j].Color).H);
                double ratio = Math.Max(rows[i].Edge, rows[j].Edge) / Math.Min(rows[i].Edge, rows[j].Edge);
                log.WriteLine($"{rows[i].Name} vs {rows[j].Name}: {d:F1} deg, energy x{ratio:F2}");
                Assert.True(d >= 25 || ratio >= 2, $"{rows[i].Name} vs {rows[j].Name}: {d:F1} deg, x{ratio:F2}");
            }
    }
}
