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
        // (the rule sits before the --skin-set switch, so a developer's switch still wins)
        Assert.True(people.IndexOf("SkinSet(m, src.ResourceName);", rule, System.StringComparison.Ordinal) > rule);
        var shader = System.IO.File.ReadAllText(System.IO.Path.Combine(d.FullName, "shaders", "heroine_skin.gdshader"));
        Assert.Contains("#define CEL_SPEC vec4(6.0, 1.0, 0.5, 0.85)", shader);
    }
}
