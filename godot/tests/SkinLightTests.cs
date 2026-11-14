using System;
using System.IO;
using SurvivorUnchained.Look;
using Xunit;

/// <summary>The skin-lighting rules of 13 Nov (Look.SkinLight), each with where it is applied: People.Skin (hers, A or B,
/// and every NPC's), heroine_skin.gdshader, GameCloseUp's camera key and rigs.json's day close-up.</summary>
public class SkinLightTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d!.FullName;
    }
    static string Read(params string[] p) => File.ReadAllText(Path.Combine(Root(), Path.Combine(p)));

    /// <summary>Fault 2 and 4: the sky's and the fill's hue half given back (not the night's navy, not the day's grey-olive),
    /// applied on every part before the --skin-set switch; the shader takes it out of her albedo and the fill and puts the
    /// lamps back.</summary>
    [Fact]
    public void SkyKeepIsHalf_PeopleSetsIt_TheShaderUsesIt()
    {
        Assert.Equal(0.5f, SkinLight.SkyKeep);
        var people = Read("src", "Actors", "People.cs");
        int at = people.IndexOf("m.SetShaderParameter(\"sky_skin\", SurvivorUnchained.Look.SkinLight.SkyKeep);", StringComparison.Ordinal);
        Assert.True(at > 0, "People.Skin sets sky_skin from Look.SkinLight.SkyKeep");
        Assert.True(people.IndexOf("SkinSet(m, src.ResourceName);", at, StringComparison.Ordinal) > at, "before the --skin-set switch");
        var shader = Read("shaders", "heroine_skin.gdshader");
        Assert.Contains("uniform float sky_skin : hint_range(0.0, 1.0) = 0.0;", shader);
        Assert.Contains("ALBEDO *= mix(vec3(1.0), skin_hue_out(cel_sky, sky_skin), cel_on);", shader);
        Assert.Contains("un /= mix(vec3(1.0), skin_hue_out(cel_sky, sky_skin), cel_on);", shader);
        Assert.Contains("skin_hue_out(cel_fill, sky_skin)", shader);
    }

    /// <summary>Fault 1 (the orange line): every part takes the head's cooler half-tone, unless --face-mid off.</summary>
    [Fact]
    public void HalfToneIsTheHeadsCoolLevel_OnEveryPart()
    {
        Assert.True(SkinLight.HalfTone.B > SkinLight.HalfTone.G && SkinLight.HalfTone.G > SkinLight.HalfTone.R);
        Assert.True(SkinLight.HalfTone.R < 0.85f, "darker and cooler than the skin's CEL_MID (0.85, 0.45, 0.38)");
        var people = Read("src", "Actors", "People.cs");
        Assert.Contains("static readonly Vector3 HeadMid = new(SurvivorUnchained.Look.SkinLight.HalfTone.R, SurvivorUnchained.Look.SkinLight.HalfTone.G, SurvivorUnchained.Look.SkinLight.HalfTone.B);", people);
        int sky = people.IndexOf("SkinLight.SkyKeep);", StringComparison.Ordinal);
        int mid = people.IndexOf("m.SetShaderParameter(\"face_mid\", HeadMid);", sky, StringComparison.Ordinal);
        Assert.True(mid > sky, "People.Skin (every part) sets face_mid from HalfTone");
        Assert.Contains("m.SetShaderParameter(\"face_mid_mask\", 0f);", people.Substring(mid, 300));
        Assert.True(people.IndexOf("SkinSet(m, src.ResourceName);", mid, StringComparison.Ordinal) > mid);
    }

    /// <summary>Fault 5: no soft rim on body parts (specks on her shoulders at night); the head keeps its own.</summary>
    [Fact]
    public void BodyPartsTakeNoSoftRim_HeadKeepsIt()
    {
        foreach (var part in new[] { "skin", "skin_graft", "skin_body", "Material_0.001", "" })
            Assert.Equal(0f, SkinLight.SoftRim(part));
        Assert.Null(SkinLight.SoftRim("skin_head"));
        var people = Read("src", "Actors", "People.cs");
        Assert.Contains("if (SurvivorUnchained.Look.SkinLight.SoftRim(src.ResourceName) is float sr)", people);
        Assert.Contains("m.SetShaderParameter(\"rim\", sr);", people);
    }

    /// <summary>Fault 3 (the jaw wedge): the camera key's shadow bias low enough that her jaw's shadow meets her jaw.</summary>
    [Fact]
    public void CameraKeyShadowBiasIsTheRules()
    {
        Assert.InRange(SkinLight.KeyShadowBias, 0.008f, 0.015f);
        var close = Read("src", "Game", "GameCloseUp.cs");
        Assert.Contains("ShadowBias = SurvivorUnchained.Look.SkinLight.KeyShadowBias", close);
        Assert.DoesNotContain("ShadowBias = 0.03f", close);
    }

    /// <summary>Fault 3 (the temple smudge): edge_tone on the head only below edge_head_y, whatever the seam map's green.</summary>
    [Fact]
    public void EdgeToneOnTheHeadIsHeldBelowItsHeight()
    {
        var shader = Read("shaders", "heroine_skin.gdshader");
        Assert.Contains("edge_w = (seam_ease ? max(1.0 - aot.g, edge_head) * (1.0 - smoothstep(edge_head_y.x, edge_head_y.y, model_y)) : mix(1.0, fk.b, edge_neck))", shader);
    }

    /// <summary>Fault 1 (washed out): the day close-up's key is the rule's, in rigs.json.</summary>
    [Fact]
    public void CloseDayKeyInTheRigsIsTheRules()
    {
        var rigs = RigSet.Parse(Read("data", "look", "rigs.json"));
        Assert.Equal(SkinLight.CloseDayKey, rigs["close_day"]!.Key.Intensity!.Value, 9);
        Assert.InRange(SkinLight.CloseDayKey, 0.6, 1.0);
    }
}
