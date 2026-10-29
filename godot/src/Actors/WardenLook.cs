using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The Ford-Warden's look on his baked package (art/npc/ford_warden), for WardenView: soaked (shaders/warden_wet.gdshader
/// on his body and his hooded head, both the full meshes and the LOD), the base's bare fingers inside his gauntlets drawn
/// as their black iron, and the two cold eye-lights deep in the hood with the one tiny cold light they throw.
/// </summary>
public static class WardenLook
{
    static Shader? shader, faceShader;

    /// <summary>His surfaces, by their source material's name, drawn soaked (the data maps: tools/assets/warden_wet_maps.py).</summary>
    public static void Wet(People.Person person, string dir)
    {
        shader ??= GD.Load<Shader>("res://shaders/warden_wet.gdshader");
        var body = ResourceLoader.Exists($"{dir}/wet_generated.png") ? GD.Load<Texture2D>($"{dir}/wet_generated.png") : null;
        var head = ResourceLoader.Exists($"{dir}/wet_head.png") ? GD.Load<Texture2D>($"{dir}/wet_head.png") : null;
        // the body's material ID map (tools/assets/warden_id_map.py): wool, tabard, quilting, leather, iron, badge, head
        var id = ResourceLoader.Exists($"{dir}/id_generated.png") ? GD.Load<Texture2D>($"{dir}/id_generated.png") : null;
        // his Face Forge head's data map (tools/assets/warden_face_maps.py: de-light, wet, creases, hair zones)
        var faceData = ResourceLoader.Exists($"{dir}/face_data.png") ? GD.Load<Texture2D>($"{dir}/face_data.png") : null;
        faceShader ??= GD.Load<Shader>("res://shaders/warden_face.gdshader");
        // his hood and capelet (armor/hood.glb, tools/assets/warden_hood.py): the wool on this shader as the body's wool
        // (class 0) by its own ID map (all wool, its bind height for the soak), so it matches the body's wool under the
        // same light; laid as a piece it was a plain StandardMaterial3D (specular 0.5, the import's defaults): pale glossy
        // blue-grey in the moonlight beside the body's dark wet wool (Warden 6 hood r2)
        var hoodId = ResourceLoader.Exists($"{dir}/armor/hood_id.png") ? GD.Load<Texture2D>($"{dir}/armor/hood_id.png") : null;
        var made = new System.Collections.Generic.Dictionary<string, ShaderMaterial>();
        foreach (var mi in person.Skeleton.GetChildren())
        {
            if (mi is not MeshInstance3D m || m.Mesh == null || m.CastShadow == GeometryInstance3D.ShadowCastingSetting.ShadowsOnly) continue;
            for (int s = 0; s < m.Mesh.GetSurfaceCount(); s++)
            {
                if (m.Mesh.SurfaceGetMaterial(s) is not BaseMaterial3D src) continue;
                if (src.ResourceName is "warden_hood_inner" or "warden_hood_fringe") { HoodTrim(src); continue; }
                string key = src.ResourceName switch { "generated" => "generated", "warden_head" or "warden_head_lod" => "head", "skin" => "iron",
                    "warden_face" => "face", "warden_face_lod" => "face_lod", "warden_hood_wool" => "hood", _ => "" };
                if (key == "") continue;
                if (key.StartsWith("face") && !made.ContainsKey(key))
                {
                    // the face: its own shader (shaders/warden_face.gdshader); the LOD's own texture has no data map
                    var f = new ShaderMaterial { Shader = faceShader, ResourceName = "warden_" + key };
                    f.SetShaderParameter("albedo_tex", src.AlbedoTexture);
                    f.SetShaderParameter("normal_tex", src.NormalTexture);
                    f.SetShaderParameter("has_normal", src.NormalTexture != null);
                    if (key == "face" && faceData != null) { f.SetShaderParameter("face_data", faceData); f.SetShaderParameter("has_data", true); }
                    made[key] = f;
                }
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
                        // (the hood: no data map, the body's is not in its UVs)
                        if ((key == "head" ? head : key == "hood" ? null : body) is { } d) w.SetShaderParameter("data_tex", d);
                        if ((key == "hood" ? hoodId : key == "generated" ? id : null) is { } idm)
                        {
                            w.SetShaderParameter("id_near", idm);
                            w.SetShaderParameter("id_lin", idm);
                            w.SetShaderParameter("has_id", true);
                        }
                        if (key == "hood")
                        {
                            if (System.Environment.GetEnvironmentVariable("WARDEN_HOODCHECK") == "1")
                                GD.Print($"hoodlook: src {src.GetType().Name} albedo={src.AlbedoTexture?.GetWidth() ?? 0} normal={src.NormalTexture?.GetWidth() ?? 0} " +
                                    $"rough_tex={src.RoughnessTexture?.GetWidth() ?? 0} rough={src.Roughness} spec={src.MetallicSpecular} metal={src.Metallic} id={hoodId != null}");
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
                    foreach (var (key, w) in made) if (key != "iron" && !key.StartsWith("face")) w.SetShaderParameter(k.Trim(), f);
        // (and the face's: WARDEN_FACE="face_value=0.5;delight=1")
        if (System.Environment.GetEnvironmentVariable("WARDEN_FACE") is { Length: > 0 } fo)
            foreach (var kv in fo.Split(';', System.StringSplitOptions.RemoveEmptyEntries))
                if (kv.Split('=') is [var k, var v] && float.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var f))
                    foreach (var (key, w) in made) if (key.StartsWith("face")) w.SetShaderParameter(k.Trim(), f);
        if (System.Environment.GetEnvironmentVariable("WARDEN_LIGHTS") is { Length: > 0 } lq) LightProbe(person, lq);
        if (System.Environment.GetEnvironmentVariable("WARDEN_GLINT") is { Length: > 0 } gl && gl.Split(',') is [var ge, var gr])
        {
            GlintEnergy = float.Parse(ge, System.Globalization.CultureInfo.InvariantCulture);
            GlintReach = float.Parse(gr, System.Globalization.CultureInfo.InvariantCulture);
        }
    }

    /// <summary>The hood's dark inner shell and its frayed fringe (plain materials): the wet wool's low specular and
    /// rough sheen, the fringe's strands alpha-to-coverage (fine fibres at a distance, not square stubs).</summary>
    static void HoodTrim(BaseMaterial3D m)
    {
        if (m.HasMeta("hood_trim")) return;
        m.SetMeta("hood_trim", true);
        m.MetallicSpecular = 0.15f;
        m.Roughness = 0.9f;
        if (m.ResourceName == "warden_hood_fringe")
        {
            m.Transparency = BaseMaterial3D.TransparencyEnum.AlphaScissor;
            m.AlphaScissorThreshold = 0.4f;
            m.AlphaAntialiasingMode = BaseMaterial3D.AlphaAntiAliasing.AlphaToCoverage;
            m.AlphaAntialiasingEdge = 0.3f;
            m.CullMode = BaseMaterial3D.CullModeEnum.Disabled;
        }
    }

    /// <summary>A lighting probe (WARDEN_LIGHTS="dump" and/or "off=a,b"): every half second, every light that reaches his
    /// head (directional; omni within range; spot within range and cone), its path, type, colour, energy, range, cull mask
    /// and the script that owns it, printed as "wlight" lines when the set changes; "off=": lights whose path contains
    /// any of the words have his layers taken out of their cull mask (an A/B of one light on him; others keep it).</summary>
    static void LightProbe(People.Person person, string q)
    {
        bool dump = q.Contains("dump");
        var off = q.Split(';').Where(x => x.StartsWith("off=")).SelectMany(x => x[4..].Split(',', System.StringSplitOptions.RemoveEmptyEntries)).ToArray();
        var tree = (SceneTree)Engine.GetMainLoop();
        var skel = person.Skeleton;
        ulong next = 0; string last = "";
        tree.ProcessFrame += () =>
        {
            if (!GodotObject.IsInstanceValid(skel) || !skel.IsInsideTree()) return;
            int hb = skel.FindBone("Head") >= 0 ? skel.FindBone("Head") : skel.FindBone("head");
            var head = skel.GlobalTransform * skel.GetBoneGlobalPose(hb).Origin;
            uint layers = 0;
            foreach (var c in skel.GetChildren()) if (c is VisualInstance3D vi && vi.IsVisibleInTree()) layers |= vi.Layers;
            var lines = new System.Collections.Generic.List<string>();
            foreach (var n in tree.Root.FindChildren("*", "Light3D", true, false))
            {
                var l = (Light3D)n;
                string path = l.GetPath();
                if (off.Length > 0 && off.Any(o => path.Contains(o)) && layers != 0) l.LightCullMask &= ~layers;   // (off him only)
                if (!dump || !l.IsVisibleInTree() || l.LightEnergy <= 0) continue;
                float dist = l.GlobalPosition.DistanceTo(head);
                string kind, reach;
                if (l is DirectionalLight3D) { kind = "dir"; reach = "-"; }
                else if (l is OmniLight3D o)
                {
                    if (dist > o.OmniRange) continue;
                    kind = "omni"; reach = $"range={o.OmniRange:0.##} att={o.OmniAttenuation:0.##} dist={dist:0.00}";
                }
                else if (l is SpotLight3D sp)
                {
                    float ang = Mathf.RadToDeg((-sp.GlobalTransform.Basis.Z).Normalized().AngleTo((head - sp.GlobalPosition).Normalized()));
                    if (dist > sp.SpotRange || ang > sp.SpotAngle) continue;
                    kind = "spot"; reach = $"range={sp.SpotRange:0.##} att={sp.SpotAttenuation:0.##} cone={sp.SpotAngle:0.#} off_axis={ang:0.#} dist={dist:0.00}";
                }
                else continue;
                // the owner: the nearest node up the tree with a C# class of its own
                Node? ow = l; while (ow != null && ow.GetType().Namespace == "Godot") ow = ow.GetParent();
                var c = l.LightColor;
                lines.Add($"{kind} {path} col=({c.R:0.00},{c.G:0.00},{c.B:0.00}) energy={l.LightEnergy:0.###} spec={l.LightSpecular:0.##} {reach} " +
                    $"cull={l.LightCullMask:X} hits_him={(l.LightCullMask & layers) != 0} shadow={l.ShadowEnabled} owner={ow?.GetType().Name ?? "-"}");
            }
            if (!dump) return;
            ulong now = Time.GetTicksMsec();
            if (now < next) return;
            next = now + 500;
            string sig = string.Join("|", lines.Select(x => System.Text.RegularExpressions.Regex.Replace(x, @"energy=\S+|dist=\S+|off_axis=\S+", "")));
            if (sig == last) return;
            last = sig;
            GD.Print($"wlight t={now} head=({head.X:0.00},{head.Y:0.00},{head.Z:0.00}) layers={layers:X} n={lines.Count}");
            foreach (var x in lines) GD.Print("wlight   " + x);
        };
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
