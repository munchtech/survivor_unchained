using System.IO;
using SurvivorUnchained.Maps;
using SurvivorUnchained.World;
using Xunit;

/// <summary>The stepped rim stays on skin by day and is off on skin at night (the moon's rim stepped into lilac specks,
/// 13 Nov): AtmospherePreset.CelSkinRim, global cel_skin_rim, heroine_skin's multiply.</summary>
public class CelSkinRimTests
{
    static string Root()
    {
        var d = new DirectoryInfo(System.AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d!.FullName;
    }

    static string Read(params string[] p) => File.ReadAllText(Path.Combine(Root(), Path.Combine(p)));

    [Fact]
    public void NightsTakeNoSkinRim_DaysKeepIt()
    {
        foreach (var n in new[] { Atmospheres.Night, Atmospheres.NightTown, Atmospheres.Front, Atmospheres.Title, Atmospheres.CineNight, Atmospheres.LowFordNight })
            Assert.Equal(0, n.CelSkinRim);
        foreach (var d in new[] { Atmospheres.Day, Atmospheres.Dawn, Atmospheres.Dusk })
            Assert.Equal(1, d.CelSkinRim);
        // (round 2: the share dips through the lower end at the middle, so the clock's night (a Dusk to Night blend past .5) is 0)
        Assert.Equal(0.5, Atmospheres.Blend(Atmospheres.Day, Atmospheres.Night, 0.25).CelSkinRim, 6);
        Assert.Equal(0, Atmospheres.Blend(Atmospheres.Dusk, Atmospheres.Night, 0.5).CelSkinRim, 6);
        Assert.Equal(0, Atmospheres.Blend(Atmospheres.Dusk, Atmospheres.NightTown, 0.7).CelSkinRim, 6);
        Assert.Equal(0, Atmospheres.Blend(Atmospheres.Night, Atmospheres.Dawn, 0.4).CelSkinRim, 6);
        Assert.Equal(0.5, Atmospheres.Blend(Atmospheres.Night, Atmospheres.Dawn, 0.75).CelSkinRim, 6);
        Assert.Equal(1, Atmospheres.Blend(Atmospheres.Day, Atmospheres.Dusk, 0.5).CelSkinRim, 6);
        Assert.Equal(0, ArenaPlaces.Light("barrow").Item1.CelSkinRim);
    }

    [Fact]
    public void ShaderGlobalAndRuleAreWired()
    {
        var shader = Read("shaders", "heroine_skin.gdshader");
        Assert.Contains("global uniform float cel_skin_rim", shader);
        Assert.Contains(": 1.0) * cel_skin_rim;", shader);
        Assert.Contains("cel_skin_rim={", Read("project.godot"));
        Assert.Contains("\"cel_skin_rim\", (float)p.CelSkinRim", Read("src", "World", "Atmosphere.cs"));
        var people = Read("src", "Actors", "People.cs");
        int skin = people.IndexOf("static Material Skin(", System.StringComparison.Ordinal);
        int fold = people.IndexOf("m.SetShaderParameter(\"rim_fold_map\"", skin, System.StringComparison.Ordinal);
        Assert.True(fold > skin, "People.Skin cuts the fold line under her breast");
        Assert.True(people.IndexOf("SkinSet(m, src.ResourceName);", fold, System.StringComparison.Ordinal) > fold);
    }

    /// <summary>(round 3) The rim only on her outline's near side: RimMask's depth mask at PreOpaque, made between frames,
    /// sampled by the skin under its gate (no Ink node: the rim everywhere, as before).</summary>
    [Fact]
    public void RimMaskIsWired()
    {
        var shader = Read("shaders", "heroine_skin.gdshader");
        Assert.Contains("global uniform sampler2D cel_rim_mask;", shader);
        Assert.Contains("rim_edge = cel_rim_mask_on > 0.5 ? textureLod(cel_rim_mask, SCREEN_UV, 0.0).r : 1.0;", shader);
        Assert.Contains(") * rim_edge", shader);
        Assert.DoesNotContain("rim_edge_px", shader);
        Assert.DoesNotContain("rim_geo", shader);
        var proj = Read("project.godot");
        Assert.Contains("cel_rim_mask={", proj);
        Assert.Matches("cel_rim_mask_on=\\{\\s*\"type\": \"float\",\\s*\"value\": 0\\.0", proj);
        var mask = Read("src", "World", "RimMask.cs");
        Assert.Contains("EffectCallbackTypeEnum.PreOpaque", mask);
        Assert.Contains("AccessResolvedDepth = !show", mask);
        var ink = Read("src", "World", "InkPass.cs");
        Assert.Contains("RenderingServer.CallOnRenderThread(Callable.From(RimMask.Make))", ink);
        Assert.Contains("RimMask.GlobalOn, ready ? 1f : 0f", ink);
    }
}
