using System;
using System.IO;
using System.Linq;
using SurvivorUnchained.Look;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(L1 B6) The FX language as data: godot/data/look/fx_language.json read whole, every school of Palette.Of there
/// with two or three rising bands and a FROM, fire's bands MB5's (white-gold core, amber, deep red edge).</summary>
public class FxLanguageTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }
    static FxLanguage Real() => FxLanguage.Parse(File.ReadAllText(Path.Combine(Root(), "data", "look", "fx_language.json")));

    [Fact]
    public void EverySchoolIsThereWithRisingBandsAndAFrom()
    {
        var l = Real();
        foreach (var s in new[] { "physical", "fire", "frost", "storm", "nature", "arcane", "holy", "shadow" })
        {
            var f = l[s];
            Assert.NotNull(f);
            Assert.False(string.IsNullOrWhiteSpace(f!.From));
            Assert.InRange(f.Bands.Count, 2, 3);
            Assert.Equal(0f, f.Edge.T);
            for (int i = 1; i < f.Bands.Count; i++) Assert.True(f.Bands[i].T > f.Bands[i - 1].T && f.Bands[i].L > f.Bands[i - 1].L);
        }
        Assert.Equal(2, l["physical"]!.Bands.Count);
        Assert.Same(l["physical"]!.Core, l["physical"]!.Mid);
    }

    [Fact]
    public void FireIsMb5sWhiteGoldAmberDeepRed()
    {
        var f = Real()["Fire"]!;
        Assert.InRange(f.Core.H, 80f, 100f);
        Assert.InRange(f.Mid.H, 45f, 65f);
        Assert.InRange(f.Edge.H, 25f, 45f);
        Assert.True(f.Core.L > 0.9f && f.Edge.L < 0.6f);
    }

    [Fact]
    public void LinearUndoesTheSrgbCurveAndAppliesTheGain()
    {
        var a = FxLanguage.Linear("#ffffff", new[] { 2f, 1f, 0f });
        Assert.Equal(new[] { 2f, 1f, 0f }, a);
        Assert.InRange(FxLanguage.Linear("#808080")[0], 0.215f, 0.217f);
    }

    [Fact]
    public void ABadFileSaysSo()
    {
        Assert.Throws<InvalidDataException>(() => FxLanguage.Parse("{\"schools\":{\"x\":{\"bands\":[]}}}"));
        Assert.Throws<InvalidDataException>(() => FxLanguage.Parse("{"));
    }

    [Fact]
    public void FrostAndHolyAreChartedTheDerivedSchoolsSaySo()
    {
        var l = Real();
        foreach (var s in new[] { "frost", "holy" })
            Assert.Contains(l[s]!.Bands, b => b.Emit.Any(e => Math.Abs(e - 1f) > 0.01f));
        using var doc = System.Text.Json.JsonDocument.Parse(File.ReadAllText(Path.Combine(Root(), "data", "look", "fx_language.json")));
        foreach (var s in new[] { "physical", "storm", "nature", "arcane", "shadow" })
            Assert.StartsWith("DERIVED AND UNCALIBRATED", doc.RootElement.GetProperty("schools").GetProperty(s).GetProperty("calibration").GetString());
    }

    [Fact]
    public void TheUiLanguageReadsWithItsBlocksTextAndPanel()
    {
        var u = UiLanguage.Parse(File.ReadAllText(Path.Combine(Root(), "data", "look", "ui_language.json")));
        foreach (var b in new[] { "bronze", "iron", "parchment", "statue_bronze" }) Assert.True(u.Blocks.ContainsKey(b));
        Assert.StartsWith("DERIVED", u.Blocks["parchment"].From);
        Assert.Equal("#e8dcc0", u.Text["cream"]);
        Assert.Equal("#d9b56a", u.Text["gold"]);
        foreach (var a in new[] { "skill", "level", "hostile" }) Assert.True(u.Accents.ContainsKey(a));
        // Stage B verdict B6 (bible rule 12): the frame is the targets' brown bronze, one lit bevel band plus the ink edge, 20-24 px at 1080 (was the measured 14-16 px, judged thin)
        Assert.InRange(u.Panel.FrameWidth, 20f, 24f);
        Assert.InRange(u.Line, 1.5f, 4f);
    }
}
