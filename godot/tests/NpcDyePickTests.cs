using System;
using System.Linq;
using SurvivorUnchained.Content;
using Xunit;

namespace SurvivorUnchained.Tests;

public class NpcDyePickTests
{
    [Fact]
    public void PicksRepeatAndSpread()
    {
        // the same seed and copy pick the same; across copies every entry of a palette turns up, none dominates
        Assert.Equal(NpcDyePick.Pick(10, 3, 0, 8), NpcDyePick.Pick(10, 3, 0, 8));
        var counts = new int[8];
        for (int copy = 0; copy < 800; copy++) counts[NpcDyePick.Pick(10, copy, 0, 8)]++;
        Assert.All(counts, c => Assert.InRange(c, 60, 140));
        // channels pick independently of each other
        int same = Enumerable.Range(0, 200).Count(c => NpcDyePick.Pick(1, c, 0, 8) == NpcDyePick.Pick(1, c, 1, 8));
        Assert.InRange(same, 5, 50);
        Assert.Equal(-1, NpcDyePick.Pick(1, 1, 0, 0));
    }

    [Fact]
    public void ScaleAndPhaseStayInRange()
    {
        for (int copy = 0; copy < 500; copy++)
        {
            Assert.InRange(NpcDyePick.Scale(7, copy, 0.04), 0.96, 1.04);
            Assert.InRange(NpcDyePick.Phase(7, copy), 0.0, 1.0);
        }
        Assert.Equal(1.0, NpcDyePick.Scale(7, 3, 0));
    }

    [Fact]
    public void ClampKeepsHueAndHoldsLightness()
    {
        var woad = NpcDyePick.Hex("#2f4466")!.Value;
        var o = NpcDyePick.ToOklab(woad);
        // inside the range: untouched
        Assert.Equal(woad, NpcDyePick.ClampL(woad, 0.1, 0.9));
        // a light shawl's range lifts a dark dye, keeping its hue
        var lifted = NpcDyePick.ClampL(woad, 0.645, 0.865);
        var lo = NpcDyePick.ToOklab(lifted);
        Assert.InRange(lo.L, 0.64, 0.65);
        Assert.InRange(Math.Atan2(lo.B, lo.A) - Math.Atan2(o.B, o.A), -0.05, 0.05);
        // round trip
        var back = NpcDyePick.FromOklab(o);
        Assert.InRange(Math.Abs(back.R - woad.R) + Math.Abs(back.G - woad.G) + Math.Abs(back.B - woad.B), 0, 1e-6);
    }

    [Fact]
    public void ChromaCapStopsCandyKeepsPeriodDyes()
    {
        // an acid chartreuse and a candy pink come down to the cap, lightness and hue kept
        foreach (var hex in new[] { "#9acd32", "#c8e830", "#ff5fa0", "#d0d020" })
        {
            var c = NpcDyePick.Hex(hex)!.Value;
            var o = NpcDyePick.ToOklab(c);
            var k = NpcDyePick.CapChroma(c);
            var ko = NpcDyePick.ToOklab(k);
            Assert.InRange(NpcDyePick.Chroma(k), 0, NpcDyePick.MaxChroma + 1e-6);
            Assert.InRange(ko.L - o.L, -0.01, 0.01);
            Assert.InRange(Math.Atan2(ko.B, ko.A) - Math.Atan2(o.B, o.A), -0.02, 0.02);
            // and in sRGB its saturation is muted (HSV S at most about 0.45 for a mid-to-light cloth)
            Assert.InRange(HsvS(k), 0, 0.5);
        }
        // a muted dye is untouched
        var drab = NpcDyePick.Hex("#5f513a")!.Value;
        Assert.Equal(drab, NpcDyePick.CapChroma(drab));
        // the gain eases: as is to 1.5, monotonic, never past 3
        Assert.Equal(1.2, NpcDyePick.Gain(1.2));
        double prev = 0;
        for (double g = 0; g < 60; g += 0.25) { double v = NpcDyePick.Gain(g); Assert.True(v >= prev && v < 3.0); prev = v; }
    }

    static double HsvS((double R, double G, double B) lin)
    {
        static double S(double c) => c <= 0.0031308 ? c * 12.92 : 1.055 * Math.Pow(c, 1 / 2.4) - 0.055;
        double r = S(lin.R), g = S(lin.G), b = S(lin.B), mx = Math.Max(r, Math.Max(g, b)), mn = Math.Min(r, Math.Min(g, b));
        return mx <= 0 ? 0 : 1 - mn / mx;
    }

    [Fact]
    public void RisenSkinTintVariesWithoutRed()
    {
        double[] hues = { 250, 145, 70 };
        Assert.Equal(NpcDyePick.SkinTint(4, 9, 0.7, 1.0, 0.03, hues), NpcDyePick.SkinTint(4, 9, 0.7, 1.0, 0.03, hues));
        double sum = 0; int n = 400; var seen = new System.Collections.Generic.HashSet<int>();
        for (int copy = 0; copy < n; copy++)
        {
            var t = NpcDyePick.SkinTint(4, copy, 0.7, 1.0, 0.03, hues);
            double lum = NpcDyePick.Lum(t);
            Assert.InRange(lum, 0.6, 1.0001);
            Assert.InRange(Math.Max(t.R, Math.Max(t.G, t.B)), 0, 1.0001);
            sum += lum;
            var o = NpcDyePick.ToOklab(t);
            double h = Math.Atan2(o.B, o.A) * 180 / Math.PI; h = (h + 360) % 360;
            // faint, and never red (Oklab red sits about 0..45 degrees)
            Assert.InRange(Math.Sqrt(o.A * o.A + o.B * o.B), 0.005, 0.04);
            Assert.InRange(h, 50, 290);
            seen.Add(h < 100 ? 0 : h < 200 ? 1 : 2);
        }
        Assert.InRange(sum / n, 0.80, 0.90);   // the mean comes down a little
        Assert.Equal(3, seen.Count);           // brown, green-gray and gray-blue all turn up
        // no chroma asked: a plain value multiplier
        var plain = NpcDyePick.SkinTint(4, 1, 0.7, 1.0, 0, hues);
        Assert.Equal(plain.R, plain.B);
    }

    [Fact]
    public void HexIsLinear()
    {
        var w = NpcDyePick.Hex("#ffffff")!.Value;
        Assert.InRange(w.R, 0.9999, 1.0001);
        Assert.InRange(NpcDyePick.Hex("#808080")!.Value.G, 0.2158, 0.2160);
        Assert.Null(NpcDyePick.Hex("red"));
        Assert.Null(NpcDyePick.Hex(null));
    }
}
