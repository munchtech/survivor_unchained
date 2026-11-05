using System;
using System.IO;
using System.Linq;
using SurvivorUnchained.Look;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(L1 B4) The lighting rigs as data: godot/data/look/rigs.json read whole, every rig named FROM something, the
/// presets lit by their rig under cel and left as they are without one.</summary>
public class RigsTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }
    static RigSet Real() => RigSet.Parse(File.ReadAllText(Path.Combine(Root(), "data", "look", "rigs.json")));

    [Fact]
    public void EveryRigTheBriefNamesIsThereAndSaysWhatItIsFrom()
    {
        var s = Real();
        foreach (var id in new[] { "night_play", "night_town", "day_town", "day_wild", "dawn", "arena_night", "close_night", "close_day", "look" })
            Assert.NotNull(s[id]);
        Assert.All(s.Rigs.Values, r => Assert.False(string.IsNullOrWhiteSpace(r.From)));
        Assert.True(s["close_day"]!.Camera && !s["night_play"]!.Camera);
        // rule 8's ink rig: night (0.42, 0.45, 0.85), day (0.85, 0.6, 0.5)
        Assert.Equal(new[] { 0.42, 0.45, 0.85 }, s["night_town"]!.Ink);
        Assert.Equal(new[] { 0.85, 0.6, 0.5 }, s["day_wild"]!.Ink);
    }

    [Fact]
    public void ABaseIsInheritedAndANullLeavesThePresetItsOwn()
    {
        var s = Real();
        Assert.Equal(s["night_play"]!.Fill.Color, s["night_town"]!.Fill.Color);
        Assert.Null(s["arena_night"]!.Key.Az);
        var place = Atmospheres.Night with { KeyAzimuth = 200, KeyIntensity = 4.7, Rig = "arena_night" };
        var lit = Rigs.Lit(place, s);
        Assert.Equal(200, lit.KeyAzimuth);
        Assert.Equal(4.7, lit.KeyIntensity);
        Assert.Equal(s["night_play"]!.Rim.Strength, lit.CelRim);
    }

    [Fact]
    public void TheDaysFiresAreAGlowAndTheNightsBurnWhole()
    {
        var s = Real();
        Assert.True(s["day_town"]!.FireShare < 0.5);
        Assert.Equal(s["day_town"]!.FireShare, s["day_wild"]!.FireShare);
        Assert.Equal(1, s["night_play"]!.FireShare);
        Assert.Equal(s["day_town"]!.Fill.Sky, s["day_wild"]!.Fill.Sky);   // (one day fill: the sky's hue too)
    }

    [Fact]
    public void LitTakesTheRigsNumbersOnceAndLeavesAnUnriggedPreset()
    {
        var s = Real();
        var lit = Rigs.Lit(Atmospheres.WaystationDay, s);
        Assert.True(lit.IsLit);
        Assert.Same(Atmospheres.WaystationDay, lit.Source);
        Assert.Equal(s["day_town"]!.Key.Color, lit.KeyColor);
        Assert.Equal(s["day_town"]!.Fill.Strength, lit.CelFill);
        Assert.Equal(lit, Rigs.Lit(lit, s));
        Assert.Same(Atmospheres.Front, Rigs.Lit(Atmospheres.Front, s));
        Assert.Same(Atmospheres.Dusk, Rigs.Lit(Atmospheres.Dusk, s));
    }

    [Fact]
    public void ABlendIsLitAsTheBlendOfItsRigs()
    {
        var s = Real(); var was = Rigs.Current; Rigs.Current = s;
        try
        {
            var b = Atmospheres.Blend(Atmospheres.LowFordNight, Atmospheres.LowFordDawn, 0.25);
            Assert.NotNull(b.CelTwin);
            var lit = Rigs.Lit(b);
            var want = Atmospheres.Blend(Rigs.Lit(Atmospheres.LowFordNight), Rigs.Lit(Atmospheres.LowFordDawn), 0.25);
            Assert.Equal(want.CelFill, lit.CelFill, 9);
            Assert.Equal(want.KeyColor, lit.KeyColor);
            // the dawning keeps its own key fade on the lit side
            var d = Atmospheres.Dawning(0.5);
            Assert.Equal(0, Rigs.Lit(d).KeyIntensity, 9);
            Assert.True(Rigs.Lit(Atmospheres.Morning(0.5)).IsLit);
        }
        finally { Rigs.Current = was; }
    }

    [Fact]
    public void TheCanopyMaskStandsWhereTheTreesAre()
    {
        var s = Real();
        var m = Rigs.CanopyMask(new[] { (0.0, 0.0, "broadleaf", 1.0), (20.0, 20.0, "fern", 1.0) }, s, 64, 128);
        int At(double x, double z) => m[(int)((z + 32) / 0.5) * 128 + (int)((x + 32) / 0.5)];
        Assert.True(At(0, 0) > 200);
        Assert.Equal(0, At(20, 20));
        Assert.Equal(0, At(-20, 10));
        var (r, u, b) = Rigs.CameraKey(35, 40);
        Assert.True(r > 0 && u > 0 && b > 0);
        Assert.Equal(1, r * r + u * u + b * b, 9);
    }

    /// <summary>(B4r3) By day and at dawn the zones' fires and lamps take the rig's share (rule 3); the night rigs keep
    /// theirs whole; the Look by day has a fill of its own; every grade a rig names exists.</summary>
    [Fact]
    public void FiresShareByDayAndDawnOnly()
    {
        var s = Real();
        Assert.Equal(0.2, s["day_town"]!.FireShare, 6);
        Assert.Equal(0.2, s["day_wild"]!.FireShare, 6);
        Assert.Equal(0.5, s["dawn_waystation"]!.FireShare, 6);
        foreach (var id in new[] { "night_play", "night_town", "night_wild", "arena_night" }) Assert.Equal(1, s[id]!.FireShare, 6);
        Assert.NotNull(s["look_day"]!.Fill.Color);
        foreach (var r in s.Rigs.Values) if (r.Grade is string g) Assert.NotNull(SurvivorUnchained.World.Atmospheres.GradeNamed(g));
    }
}
