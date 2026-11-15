using System.Linq;
using Xunit;

/// <summary>A package's fur casts its shadow from its hide through a shadow-only twin (NpcPackage.FurShadows): its 31
/// shell passes each cast, and their strand cut-outs drew a ragged, tufted shadow on the skin under them (x18 V3, 13 Nov).</summary>
public class FurShadowTests
{
    static string Src(params string[] path)
    {
        var d = new System.IO.DirectoryInfo(System.AppContext.BaseDirectory);
        while (d != null && !System.IO.File.Exists(System.IO.Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return System.IO.File.ReadAllText(System.IO.Path.Combine(new[] { d!.FullName }.Concat(path).ToArray()));
    }

    [Fact]
    public void PackageFurCastsThroughAPlainTwin_AfterTheLod()
    {
        var pkg = Src("src", "Actors", "NpcPackage.cs");
        int lod = pkg.IndexOf("if (m.Baked && m.LodFile != null) BakedLod(person, name, m);", System.StringComparison.Ordinal);
        int fur = pkg.IndexOf("FurShadows(person);", System.StringComparison.Ordinal);
        Assert.True(lod > 0 && fur > lod, "FurShadows runs after BakedLod, so the twin copies the 18 m range");
        // (the twin: shadow only, the fur as a plain two-sided caster, the mesh itself no longer casting)
        Assert.Contains("CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly,", pkg);
        Assert.Contains("CullMode = BaseMaterial3D.CullModeEnum.Disabled, ResourceName = \"fur_shadow\"", pkg);
        Assert.Contains("mi.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;", pkg);
        Assert.Contains("VisibilityRangeEnd = mi.VisibilityRangeEnd", pkg);
        // (the shells are what IsFurShell names: People.Fur's shader, with its next passes)
        Assert.Contains("furShader ??= GD.Load<Shader>(\"res://shaders/fur_shell.gdshader\");", Src("src", "Actors", "People.cs"));
        Assert.Contains("sm.Shader?.ResourcePath == \"res://shaders/fur_shell.gdshader\" && sm.NextPass != null", pkg);
    }
}
