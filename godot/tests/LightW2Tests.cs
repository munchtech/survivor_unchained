using System;
using System.IO;
using System.Linq;
using SurvivorUnchained.Look;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(L1 W2, the light) The rigs' tone curve, warm-source term and the moon's giving way to her light as data, and the
/// material classes' albedo control (materials.json "albedo_ctl").</summary>
public class LightW2Tests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }
    static RigSet Real() => RigSet.Parse(File.ReadAllText(Path.Combine(Root(), "data", "look", "rigs.json")));

    [Fact]
    public void TheToneCurveRunsThroughItsPointsAndNeverTurnsBack()
    {
        Assert.Equal(0.37, Atmospheres.ToneCurve(null, 0.37), 9);
        var c = new[] { 0.0, 0.0, 0.3, 0.22, 0.6, 0.55, 0.8, 0.84, 1.0, 1.0 };
        Assert.Equal(0.22, Atmospheres.ToneCurve(c, 0.3), 6);
        Assert.Equal(0.84, Atmospheres.ToneCurve(c, 0.8), 6);
        double last = -1;
        for (int i = 0; i <= 200; i++) { double y = Atmospheres.ToneCurve(c, i / 200.0); Assert.True(y >= last - 1e-9); last = y; }
        // a blend of two curves at its ends is each
        var mix = Atmospheres.CurveMix(c, null, 0.5)!;
        Assert.Equal((0.22 + 0.3) / 2, Atmospheres.ToneCurve(mix, 0.3), 2);
    }

    [Fact]
    public void ARigsCurveWarmKeepAndGiveAreItsAndItsBasesUnlessNulled()
    {
        var s = RigSet.Parse("""
        { "rigs": {
          "a": { "from": "x", "grade": "day", "grade_curve": [[0, 0], [0.5, 0.4], [1, 1]], "warm_keep": 0.8, "ember_give": [0.7, 0.5, 0.2, 0.6] },
          "b": { "base": "a", "from": "y" },
          "c": { "base": "a", "from": "z", "grade_curve": null, "ember_give": null } } }
        """);
        Assert.Equal(new[] { 0, 0, 0.5, 0.4, 1, 1.0 }, s["b"]!.Curve);
        Assert.Equal(0.8, s["b"]!.WarmKeep);
        Assert.Null(s["c"]!.Curve);
        Assert.Null(s["c"]!.EmberGive);
        var lit = Rigs.Lit(Atmospheres.Day with { Rig = "b" }, s);
        Assert.Equal(new[] { 0, 0, 0.5, 0.4, 1, 1.0 }, lit.Grade.Curve);
        Assert.Equal(0.8, lit.Grade.WarmKeep);
        Assert.Equal(new[] { 0.7, 0.5, 0.2, 0.6 }, lit.EmberGive);
        Assert.Equal(Atmospheres.Day.Grade.Contrast, lit.Grade.Contrast);
    }

    [Fact]
    public void ARigsKeyAndSkyScaleKeepEachPlacesOwnLevelRelative()
    {
        // (L1 lead 8, S2b-N2) a rig over several places: the key's level times the place's own, and its sky recolored at
        // the place's own sky energy (hemi x the sky's luminance) times the sky's level
        var s = RigSet.Parse("""
        { "rigs": { "a": { "from": "x", "key": { "intensity": null, "scale": 0.5 }, "fill": { "sky": "#ffffff", "hemi": null, "sky_scale": 2 } } } }
        """);
        var p = Atmospheres.Night with { Rig = "a", KeyIntensity = 4, HemiSky = "#808080", HemiIntensity = 1.5 };
        var lit = Rigs.Lit(p, s);
        Assert.Equal(2, lit.KeyIntensity, 6);
        Assert.Equal(1.5 * 0.2158605 * 2, lit.HemiIntensity, 4);
        Assert.Equal("#ffffff", lit.HemiSky);
    }

    [Fact]
    public void TheRealRigsCurveTheDayAndGiveTheNightsMoonToHerPool()
    {
        var s = Real();
        foreach (var id in new[] { "day_town", "day_wild" }) Assert.True(s[id]!.Curve is { Length: >= 4 }, id);
        foreach (var id in new[] { "night_play", "arena_night" })
        {
            var g = s[id]!.EmberGive;
            Assert.True(g is { Length: 4 } && g[0] > 0 && g[0] <= 1 && g[2] < g[3], id);
            Assert.True(s[id]!.WarmKeep > 0, id);
        }
        // rule 3: the arena's pool is her ember's orange, not the old pale gold
        Assert.Equal("#ff8a3a", s["arena_night"]!.EmberColor);
    }

    [Fact]
    public void AClassesAlbedoControlIsReadAndAsPaintedWithoutOne()
    {
        string J(string ctl) => """{ "classes": { "k": { "cel": { "band": [0,0.06,0.2,0.05], "mid": [0.55,0.55,0.6,1], "form": 0.3, "spec": [9,1.5,1,0.85], "nmap": 0.35, "ink": 0, "rim_k": 1 } """
            + ctl + """ } }, "fallback": "k", "shaders": {}, "assign": [] }""";
        var a = MaterialLibrary.Parse(J(""", "albedo_ctl": { "target": 0.3, "pull": 0.7, "chroma": 0.8 }"""));
        Assert.Equal(new[] { 0.3f, 0.7f, 1f, 0.8f }, a.Classes["k"].AlbUniform);
        Assert.Equal(new[] { 0f, 0f, 1f, 1f }, MaterialLibrary.Parse(J("")).Classes["k"].AlbUniform);
        Assert.Throws<InvalidDataException>(() => MaterialLibrary.Parse(J(""", "albedo_ctl": { "pull": 2 }""")));
        // (L1 l9 PACK2) the hue: [h, C, pull] -> the target's Oklab a, b and the pull; none: its own hue
        var h = MaterialLibrary.Parse(J(""", "albedo_ctl": { "target": 0.3, "pull": 0.7, "hue": [266, 0.025, 0.8] }""")).Classes["k"].AlbHueUniform;
        Assert.Equal(-0.00174, (double)h[0], 4); Assert.Equal(-0.02494, (double)h[1], 4); Assert.Equal(0.8f, h[2]);
        Assert.Equal(new[] { 0f, 0f, 0f }, a.Classes["k"].AlbHueUniform);
        Assert.Throws<InvalidDataException>(() => MaterialLibrary.Parse(J(""", "albedo_ctl": { "hue": [266, 0.025, 1.5] }""")));
        // the pack's fur: cold neutral FROM target 09 (h 260-268), and no glossy band (rule 6: a clump band or none)
        var fur = MaterialLibrary.Parse(File.ReadAllText(Path.Combine(Root(), "data", "look", "materials.json"))).Classes["crowd_fur"];
        Assert.InRange(fur.AlbHue![0], 260f, 268f);
        Assert.Equal(0f, fur.Cel.Spec[2]);
    }
}
