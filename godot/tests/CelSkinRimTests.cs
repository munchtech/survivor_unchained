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
        Assert.Equal(0.5, Atmospheres.Blend(Atmospheres.Day, Atmospheres.Night, 0.5).CelSkinRim, 6);
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
}
