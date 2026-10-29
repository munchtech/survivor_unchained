using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The Ford-Warden's look on his baked package (art/npc/ford_warden), for WardenView: soaked (shaders/warden_wet.gdshader
/// on his body and his hooded head, both the full meshes and the LOD), the base's bare fingers inside his gauntlets drawn
/// as their black iron, and the two cold eye-lights deep in the hood with the one tiny cold light they throw.
/// </summary>
public static class WardenLook
{
    static Shader? shader;

    /// <summary>His surfaces, by their source material's name, drawn soaked (the data maps: tools/assets/warden_wet_maps.py).</summary>
    public static void Wet(People.Person person, string dir)
    {
        shader ??= GD.Load<Shader>("res://shaders/warden_wet.gdshader");
        var body = ResourceLoader.Exists($"{dir}/wet_generated.png") ? GD.Load<Texture2D>($"{dir}/wet_generated.png") : null;
        var head = ResourceLoader.Exists($"{dir}/wet_head.png") ? GD.Load<Texture2D>($"{dir}/wet_head.png") : null;
        // the body's material ID map (tools/assets/warden_id_map.py): wool, tabard, quilting, leather, iron, badge, head
        var id = ResourceLoader.Exists($"{dir}/id_generated.png") ? GD.Load<Texture2D>($"{dir}/id_generated.png") : null;
        var made = new System.Collections.Generic.Dictionary<string, ShaderMaterial>();
        foreach (var mi in person.Skeleton.GetChildren())
        {
            if (mi is not MeshInstance3D m || m.Mesh == null || m.CastShadow == GeometryInstance3D.ShadowCastingSetting.ShadowsOnly) continue;
            for (int s = 0; s < m.Mesh.GetSurfaceCount(); s++)
            {
                if (m.Mesh.SurfaceGetMaterial(s) is not BaseMaterial3D src) continue;
                string key = src.ResourceName switch { "generated" => "generated", "warden_head" or "warden_head_lod" => "head", "skin" => "iron", _ => "" };
                if (key == "") continue;
                if (!made.TryGetValue(key, out var w))
                {
                    w = new ShaderMaterial { Shader = shader, ResourceName = "warden_wet_" + key };
                    if (key == "iron") w.SetShaderParameter("iron", 1.0f);
                    else
                    {
                        w.SetShaderParameter("albedo_tex", src.AlbedoTexture);
                        w.SetShaderParameter("normal_tex", src.NormalTexture);
                        w.SetShaderParameter("has_normal", src.NormalTexture != null);
                        w.SetShaderParameter("mr_tex", src.RoughnessTexture);
                        w.SetShaderParameter("has_mr", src.RoughnessTexture != null);
                        if ((key == "head" ? head : body) is { } d) w.SetShaderParameter("data_tex", d);
                        if (key == "generated" && id != null)
                        {
                            w.SetShaderParameter("id_near", id);
                            w.SetShaderParameter("id_lin", id);
                            w.SetShaderParameter("has_id", true);
                        }
                    }
                    made[key] = w;
                }
                m.SetSurfaceOverrideMaterial(s, w);
            }
        }
        // (a look test's overrides: WARDEN_WET="wet_dark=0.5;soak_dark=0.7", on every soaked surface but the iron; the
        //  judged r2 values are the shader's defaults)
        if (System.Environment.GetEnvironmentVariable("WARDEN_WET") is { Length: > 0 } ov)
            foreach (var kv in ov.Split(';', System.StringSplitOptions.RemoveEmptyEntries))
                if (kv.Split('=') is [var k, var v] && float.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var f))
                    foreach (var (key, w) in made) if (key != "iron") w.SetShaderParameter(k.Trim(), f);
        if (System.Environment.GetEnvironmentVariable("WARDEN_GLINT") is { Length: > 0 } gl && gl.Split(',') is [var ge, var gr])
        {
            GlintEnergy = float.Parse(ge, System.Globalization.CultureInfo.InvariantCulture);
            GlintReach = float.Parse(gr, System.Globalization.CultureInfo.InvariantCulture);
        }
    }

    static readonly Color Cyan = new(0.35f, 0.82f, 1f);

    /// <summary>The eye-lights: a white-hot core going to cyan, a soft glow round it (additive, depth-tested so the
    /// brow hides it from above), on the Head bone at the sockets; and one tiny cold light just in front of them that
    /// grazes brow, cheekbones and the beard's top. Returns the cores' and glows' materials and the light, for Light().</summary>
    public static (StandardMaterial3D Core, StandardMaterial3D Glow, OmniLight3D Glint) Eyes(Skeleton3D skel, Vector3 l, Vector3 r)
    {
        var at = new BoneAttachment3D { Name = "EyeLights", BoneName = skel.FindBone("Head") >= 0 ? "Head" : "head" };
        skel.AddChild(at);
        // (offsets in the package's frame, front +Z, turned into the bone's as the import has it)
        var toBone = skel.GetBoneGlobalRest(skel.FindBone(at.BoneName)).Basis.Inverse();
        var core = new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(2.2f, 3.0f, 3.4f),
            AlbedoTexture = Radial(new Color(1, 1, 1, 1), new Color(0.55f, 0.9f, 1f, 1), new Color(0.2f, 0.7f, 1f, 0)),
            Transparency = BaseMaterial3D.TransparencyEnum.Alpha, BlendMode = BaseMaterial3D.BlendModeEnum.Add,
            BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
        };
        var glow = new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(Cyan.R, Cyan.G, Cyan.B, 0.55f),
            AlbedoTexture = Radial(new Color(1, 1, 1, 1), new Color(1, 1, 1, 0.25f), new Color(1, 1, 1, 0)),
            Transparency = BaseMaterial3D.TransparencyEnum.Alpha, BlendMode = BaseMaterial3D.BlendModeEnum.Add,
            BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
        };
        foreach (var p in new[] { l, r })
        {
            // (a hair back in the socket, so the brow and the lids frame them)
            var q = p + toBone * new Vector3(0, 0, -0.004f);
            at.AddChild(new MeshInstance3D { Mesh = new QuadMesh { Size = Vector2.One * 0.011f, Material = core }, Position = q, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
            at.AddChild(new MeshInstance3D { Mesh = new QuadMesh { Size = Vector2.One * 0.045f, Material = glow }, Position = q + toBone * new Vector3(0, 0, 0.002f), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        }
        // the glint: between and in front of the eyes, a few centimetres' reach (scaled with him in Shine)
        var glint = new OmniLight3D
        {
            Name = "EyeGlint", LightColor = new Color("#8fd8ff"), ShadowEnabled = false, LightEnergy = 0,
            OmniRange = 0.16f, OmniAttenuation = 1.6f, Position = (l + r) / 2 + toBone * new Vector3(0, -0.006f, 0.035f), LightSpecular = 0.6f,
        };
        at.AddChild(glint);
        return (core, glow, glint);
    }

    /// <summary>The eye-lights at a glow (0 off, 1 as built), with a slow living flicker; the glint's reach in world
    /// metres (a light's range does not scale with the giant's body).</summary>
    public static void Glow((StandardMaterial3D Core, StandardMaterial3D Glow, OmniLight3D Glint) e, double g, double time)
    {
        float k = (float)(g <= 0.001 ? 0 : Mathf.Clamp(0.45 + 0.55 * g + Mathf.Sin((float)time * 5) * 0.06 * g, 0, 1.6));
        e.Core.AlbedoColor = new Color(2.2f * k, 3.0f * k, 3.4f * k, 1);
        e.Glow.AlbedoColor = new Color(Cyan.R, Cyan.G, Cyan.B, 0.55f * Mathf.Min(k, 1.2f));
        float s = e.Glint.GetParent<Node3D>().GlobalTransform.Basis.Scale.X;
        e.Glint.OmniRange = GlintReach * s;
        e.Glint.LightEnergy = GlintEnergy * k;
        e.Glint.Visible = k > 0;
    }

    public static float GlintReach = 0.12f, GlintEnergy = 0.12f;

    static GradientTexture2D Radial(Color a, Color b, Color c) => new()
    {
        Gradient = new Gradient { Colors = [a, b, c], Offsets = [0, 0.3f, 1] },
        Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f), Width = 64, Height = 64,
    };
}
