using SurvivorUnchained.Look;
using Xunit;

/// <summary>The skin's hard cel highlight stays off the body (pale, hard-edged patches over the sternum and breast tops,
/// 13 Nov) and on the head; People.Skin applies the rule to every skin it makes (hers, A or B, and every NPC's).</summary>
public class SkinHighlightTests
{
    [Fact]
    public void BodyPartsTakeNoHardHighlight_HeadKeepsTheShaders()
    {
        foreach (var part in new[] { "skin", "skin_graft", "skin_body", "Material_0.001", "" })
            Assert.Equal(0f, SkinHighlight.Strength(part));
        Assert.Null(SkinHighlight.Strength("skin_head"));
        // (and the head takes no stepped rim: inside the face it drew stripes down the nose and temple, 13 Nov r1)
        Assert.Equal(0f, SkinHighlight.RimShare("skin_head"));
        foreach (var part in new[] { "skin", "skin_graft", "skin_body" })
            Assert.Null(SkinHighlight.RimShare(part));
    }

    [Fact]
    public void PeopleSkinAppliesTheRule_AndTheShaderStillHasAHeadHighlight()
    {
        var d = new System.IO.DirectoryInfo(System.AppContext.BaseDirectory);
        while (d != null && !System.IO.File.Exists(System.IO.Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        var people = System.IO.File.ReadAllText(System.IO.Path.Combine(d!.FullName, "src", "Actors", "People.cs"));
        int rule = people.IndexOf("SkinHighlight.Strength(src.ResourceName) is float hs", System.StringComparison.Ordinal);
        Assert.True(rule > 0, "People.Skin sets cel_spec from Look.SkinHighlight");
        Assert.Contains("m.SetShaderParameter(\"cel_spec\", new Vector4(6f, 1f, hs, 0.85f));", people);
        Assert.Contains("if (SurvivorUnchained.Look.SkinHighlight.RimShare(src.ResourceName) is float rk)", people);
        Assert.Contains("m.SetShaderParameter(\"cel_rim_k\", rk);", people);
        // (the rule sits before the --skin-set switch, so a developer's switch still wins)
        Assert.True(people.IndexOf("SkinSet(m, src.ResourceName);", rule, System.StringComparison.Ordinal) > rule);
        var shader = System.IO.File.ReadAllText(System.IO.Path.Combine(d.FullName, "shaders", "heroine_skin.gdshader"));
        Assert.Contains("#define CEL_SPEC vec4(6.0, 1.0, 0.5, 0.85)", shader);
    }

    /// <summary>The head keeps the disc only where it is tightly curved: the spark map (tools/assets/heroine_spark.py)
    /// is black on her forehead, cheeks, temples and jaw (the patches of 13 Nov) and white at her nose's tip, and
    /// People.BaseHead hands it to the shader, which multiplies the disc by it.</summary>
    [Fact]
    public void HeadDiscKeptToItsSparks_NotOnForeheadCheeksTemplesJaw()
    {
        var d = new System.IO.DirectoryInfo(System.AppContext.BaseDirectory);
        while (d != null && !System.IO.File.Exists(System.IO.Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        var png = SurvivorUnchained.Tests.FxTests.Png.Read(System.IO.Path.Combine(d!.FullName, SkinHighlight.SparkMap.Replace("res://", "")));
        Assert.Equal(1024, png.Width);
        // (points on her base head, their UVs from heroine.glb's skin_head: a 13-texel window round each)
        int Max(double u, double v)
        {
            int m = 0, cx = (int)(u * png.Width), cy = (int)(v * png.Height);
            for (int y = cy - 6; y <= cy + 6; y++)
                for (int x = cx - 6; x <= cx + 6; x++) m = System.Math.Max(m, png.Light(x, y));
            return m;
        }
        foreach (var (name, u, v) in new[] { ("forehead", 0.5352, 0.5366), ("left cheek", 0.4197, 0.5062), ("right cheek", 0.5103, 0.4186),
                     ("left jaw", 0.3544, 0.4818), ("right jaw", 0.4774, 0.3484), ("left temple", 0.4634, 0.5848), ("right temple", 0.5864, 0.4663) })
            Assert.True(Max(u, v) < 16, $"the head's hard highlight is kept off her {name}");
        Assert.True(Max(0.4615, 0.4625) > 200, "her nose's tip keeps its spark");
        int lit = 0;
        for (int y = 0; y < png.Height; y++) for (int x = 0; x < png.Width; x++) if (png.Light(x, y) > 127) lit++;
        Assert.InRange(lit / (double)(png.Width * png.Height), 0.01, 0.10);
        var people = System.IO.File.ReadAllText(System.IO.Path.Combine(d.FullName, "src", "Actors", "People.cs"));
        int head = people.IndexOf("static void BaseHead(ShaderMaterial m)", System.StringComparison.Ordinal);
        Assert.True(head > 0);
        Assert.True(people.IndexOf("m.SetShaderParameter(\"spark_mask\", 1f);", head, System.StringComparison.Ordinal) > head, "BaseHead masks the head's disc");
        var shader = System.IO.File.ReadAllText(System.IO.Path.Combine(d.FullName, "shaders", "heroine_skin.gdshader"));
        Assert.Contains("* (spark_mask > 0.0 ? mix(1.0, textureLod(spark_map, UV, 0.0).r, spark_mask) : 1.0), cel_on);", shader);
    }
    [Fact]
    public void FoldMapTakesTheRimOnlyUnderTheBreast_AndNpcSkinSetsItOnBodyP1()
    {
        var d = new System.IO.DirectoryInfo(System.AppContext.BaseDirectory);
        while (d != null && !System.IO.File.Exists(System.IO.Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        var png = SurvivorUnchained.Tests.FxTests.Png.Read(System.IO.Path.Combine(d!.FullName, SkinHighlight.FoldMap.Replace("res://", "")));
        Assert.Equal(1024, png.Width);
        // (points on body_p1, their UVs from body.glb's body skin: a 13-texel window round each)
        int Max(double u, double v)
        {
            int m = 0, cx = (int)(u * png.Width), cy = (int)(v * png.Height);
            for (int y = System.Math.Max(cy - 6, 0); y <= System.Math.Min(cy + 6, png.Height - 1); y++)
                for (int x = System.Math.Max(cx - 6, 0); x <= System.Math.Min(cx + 6, png.Width - 1); x++) m = System.Math.Max(m, png.Light(x, y));
            return m;
        }
        Assert.True(Max(0.5801, 0.1362) > 200, "the breast's underside takes the rim off");
        foreach (var (name, u, v) in new[] { ("outer arm", 0.1674, 0.3301), ("shoulder", 0.3515, 0.0794), ("armpit", 0.1079, 0.4656),
                     ("buttock crease", 0.9895, 0.4821), ("inner thigh", 0.2467, 0.5739), ("elbow", 0.3148, 0.2929),
                     ("ribs' side under the breast", 0.6665, 0.0872), ("belly under the breast", 0.6919, 0.1672) })
            Assert.True(Max(u, v) < 16, $"the cream rim stays on her {name}");
        int lit = 0;
        for (int y = 0; y < png.Height; y++) for (int x = 0; x < png.Width; x++) if (png.Light(x, y) > 127) lit++;
        Assert.InRange(lit / (double)(png.Width * png.Height), 0.001, 0.02);
        var people = System.IO.File.ReadAllText(System.IO.Path.Combine(d.FullName, "src", "Actors", "People.cs"));
        int npc = people.IndexOf("public static Material NpcSkin(", System.StringComparison.Ordinal);
        Assert.True(npc > 0);
        Assert.True(people.IndexOf("SkinIndexCount(mesh, src.ResourceName) is int bi && bi > 0 && bi == BaseBodyIndices()", npc, System.StringComparison.Ordinal) > npc,
            "NpcSkin matches body_p1 by triangles (a run-time glTF load welds its vertices)");
        Assert.True(people.IndexOf("m.SetShaderParameter(\"rim_fold\", 1f);", npc, System.StringComparison.Ordinal) > npc, "NpcSkin sets rim_fold");
        var shader = System.IO.File.ReadAllText(System.IO.Path.Combine(d.FullName, "shaders", "heroine_skin.gdshader"));
        Assert.Contains("* (rim_fold > 0.0 ? 1.0 - rim_fold * textureLod(rim_fold_map, UV, 0.0).r : 1.0);", shader);
    }
}
