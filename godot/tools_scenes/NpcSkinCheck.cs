using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Tools;

/// <summary>
/// People.NpcSkin on our base body (body_p1): a head and a body part, each by default and with a manifest "skin" block's
/// uniforms. One line per call, "npc_skin NAME {json}", also written to the report file given after "--".
///   Godot --headless --path godot -s res://tools_scenes/npc_skin_check.gd -- OUT.txt
/// tests/NpcSkinTests.cs runs it headless.
/// </summary>
public partial class NpcSkinCheck : Node
{
    const string Override = """{"uniforms": {"*": {"back_spec": 0.5}, "skin_head": {"zone_colour": 0.4, "cel_tone": [1,1,1]}, "brows": {"strength": 0.5}}}""";

    public override void _Ready()
    {
        var args = OS.GetCmdlineUserArgs();
        var outPath = args.Length > 0 ? args[0] : "npc_skin_check.txt";
        var scene = GD.Load<PackedScene>(P1Body.Dir + "body.glb");
        var root = scene.Instantiate();
        Mesh? headMesh = null, bodyMesh = null;
        var stack = new Stack<Node>();
        stack.Push(root);
        while (stack.Count > 0)
        {
            var n = stack.Pop();
            if (n is MeshInstance3D { Mesh: { } m })
                for (int s = 0; s < m.GetSurfaceCount(); s++)
                {
                    var name = m.SurfaceGetMaterial(s)?.ResourceName;
                    if (name == "skin_head") headMesh ??= m;
                    if (name == "skin") bodyMesh ??= m;
                }
            foreach (var c in n.GetChildren()) stack.Push(c);
        }
        var tex = ImageTexture.CreateFromImage(MakeImage("#d9a07a"));
        // (a darker paint: the x18 V3 smith's head mean, 0.65 of her paint's luminance; and one under the deep onset)
        var mid = ImageTexture.CreateFromImage(MakeImage("#80695e"));
        var deep = ImageTexture.CreateFromImage(MakeImage("#453024"));
        var warm1 = Json.ParseString("""{"cel_warm": 1}""").AsGodotDictionary();
        var over = Json.ParseString(Override).AsGodotDictionary();
        var lines = new List<string>
        {
            Line("head_default", "skin_head", headMesh, tex, null),
            Line("head_override", "skin_head", headMesh, tex, over),
            Line("body_default", "skin", bodyMesh ?? headMesh, tex, null),
            Line("head_mid", "skin_head", headMesh, mid, null),
            Line("body_deep", "skin", bodyMesh ?? headMesh, deep, null),
            Line("head_mid_warm1", "skin_head", headMesh, mid, warm1),
        };
        root.Free();
        foreach (var l in lines) GD.Print(l);
        File.WriteAllText(outPath, string.Join("\n", lines) + "\n");
        GetTree().Quit(headMesh == null ? 1 : 0);
    }

    static Image MakeImage(string colour)
    {
        var img = Image.CreateEmpty(4, 4, false, Image.Format.Rgba8);
        img.Fill(new Color(colour));
        return img;
    }

    static string Line(string name, string part, Mesh? mesh, Texture2D tex, Godot.Collections.Dictionary? skin)
    {
        var src = new StandardMaterial3D { ResourceName = part, AlbedoTexture = tex };
        var m = (ShaderMaterial)People.NpcSkin(src, mesh!, true, new Color("#7a3a1e"), skin);
        var d = new Dictionary<string, object?>();
        foreach (var k in new[] { "cel_tone", "cel_fill_tone", "back_spec", "back_neutral", "back_neutral_sky", "throat_terminator", "deep_spec", "shade_thin", "zone_colour", "zone_lids" })
            d[k] = Val(m.GetShaderParameter(k));
        d["skin_zones"] = m.GetShaderParameter("skin_zones").VariantType == Variant.Type.Object;
        d["features"] = m.GetShaderParameter("features").VariantType == Variant.Type.Object;
        d["ao_map"] = m.GetShaderParameter("ao_map").VariantType == Variant.Type.Object;
        var brows = m.NextPass as ShaderMaterial;
        d["next_pass_shader"] = brows != null;
        d["brow_dyed"] = brows != null ? Val(brows.GetShaderParameter("dyed")) : null;
        d["brow_strength"] = brows != null ? Val(brows.GetShaderParameter("strength")) : null;
        return $"npc_skin {name} " + JsonSerializer.Serialize(d);
    }

    static object? Val(Variant v) => v.VariantType switch
    {
        Variant.Type.Float or Variant.Type.Int => v.AsDouble(),
        Variant.Type.Bool => v.AsBool(),
        Variant.Type.Vector3 => new[] { v.AsVector3().X, v.AsVector3().Y, v.AsVector3().Z },
        Variant.Type.Nil => null,
        _ => v.ToString(),
    };
}
