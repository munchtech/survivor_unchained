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
        Assert.Contains("skin_hue_out(cel_fill, sky_skin)", shader);
        // (and the sky's own light past it, where the night sky alone lights her neck: navy under the grade at 0.5)
        Assert.InRange(SkinLight.SkyKeepAmbient, 2.0f, 2.4f);
        Assert.Contains("m.SetShaderParameter(\"sky_skin_amb\", SurvivorUnchained.Look.SkinLight.SkyKeepAmbient);", people);
        Assert.Contains("ALBEDO *= mix(vec3(1.0), skin_hue_out(cel_sky, sky_amb_k()), cel_on);", shader);
        Assert.Contains("un /= mix(vec3(1.0), skin_hue_out(cel_sky, sky_amb_k()), cel_on);", shader);
    }

    /// <summary>Fault 1 (the orange line): every part takes the head's cooler half-tone, unless --face-mid off.</summary>
    [Fact]
    public void HalfToneIsTheHeadsCoolLevel_OnEveryPart()
    {
        Assert.InRange(SkinLight.HalfTone.R / SkinLight.HalfTone.B, 1.0f, 1.2f);   // (near neutral: no orange line, no grey-mauve bruise)
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

    /// <summary>Fault 3 (the temple smudge): the head's half-tone reach narrower than the body's (CEL_BAND z 0.2), set by
    /// People.Skin on the head before the --skin-set switch.</summary>
    [Fact]
    public void HeadHalfToneReachIsNarrowerThanTheBodys()
    {
        Assert.InRange(SkinLight.HeadCelBand.Z, 0.05f, 0.15f);
        Assert.Equal(0.06f, SkinLight.HeadCelBand.Y);
        var people = Read("src", "Actors", "People.cs");
        int at = people.IndexOf("var hb = SurvivorUnchained.Look.SkinLight.HeadCelBand;", StringComparison.Ordinal);
        Assert.True(at > 0);
        Assert.Contains("m.SetShaderParameter(\"cel_band\", new Vector4(hb.X, hb.Y, hb.Z, hb.W));", people.Substring(at, 200));
        Assert.True(people.IndexOf("SkinSet(m, src.ResourceName);", at, StringComparison.Ordinal) > at);
        Assert.Contains("#define CEL_BAND vec4(0.0, 0.06, 0.2, 0.08)", Read("shaders", "heroine_skin.gdshader"));
    }

    /// <summary>Fault 1 (washed out): the day close-up's key is the rule's, in rigs.json.</summary>
    [Fact]
    public void CloseDayKeyInTheRigsIsTheRules()
    {
        var rigs = RigSet.Parse(Read("data", "look", "rigs.json"));
        Assert.Equal(SkinLight.CloseDayKey, rigs["close_day"]!.Key.Intensity!.Value, 9);
        Assert.Equal(SkinLight.CloseDayKeyColor, rigs["close_day"]!.Key.Color);
        Assert.InRange(SkinLight.CloseDayKey, 0.6, 1.0);
    }

    /// <summary>Fault 1 (her face near white over an orange body): her head's paint at her body's level outside the Look's
    /// rig, her own face trimmed to her chest at the Look, both in People's face tones.</summary>
    [Fact]
    public void HeadPaintAtTheBodysLevel_FaceTrimmedAtTheLook()
    {
        Assert.InRange(SkinLight.HeadPaintLevel, 0.6f, 0.75f);
        Assert.True(SkinLight.LookFaceTrim.R < SkinLight.LookFaceTrim.G && SkinLight.LookFaceTrim.G < SkinLight.LookFaceTrim.B && SkinLight.LookFaceTrim.B <= 1f);
        var people = Read("src", "Actors", "People.cs");
        Assert.Contains("* SurvivorUnchained.Look.SkinLight.HeadPaintLevel;", people);
        Assert.Contains("if (FaceId(look) == \"own\") f *= new Vector3(SurvivorUnchained.Look.SkinLight.LookFaceTrim.R", people);
    }

    /// <summary>Fault 1 (spray-tan orange): her cel warmth is the rule's, warm but less red than (1.39, 0.80, 0.54).</summary>
    [Fact]
    public void HerCelToneIsTheRules()
    {
        var t = SkinLight.CelTone;
        Assert.True(t.R > t.G && t.G > t.B, "warm");
        Assert.InRange(t.R / t.B, 1.15f, 1.9f);
        Assert.InRange(0.2126f * t.R + 0.7152f * t.G + 0.0722f * t.B, 0.85f, 0.97f);
        Assert.Contains("ArgVec(\"cel-tone\", new(SurvivorUnchained.Look.SkinLight.CelTone.R, SurvivorUnchained.Look.SkinLight.CelTone.G, SurvivorUnchained.Look.SkinLight.CelTone.B))", Read("src", "Actors", "People.cs"));
    }
}
