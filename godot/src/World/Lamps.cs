using System.Collections.Generic;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The world's lamp holders (tools/assets/env_lamps.py, art/world/lamps): the
/// keeper's lamp-iron on the Low Ford's pylons, the Watch's road post, a
/// standing lantern, a wall torch. Modeled iron, wood and glass, never a
/// glowing ball (look bible 10): the flame in each is the flame kit's, put
/// there by the zone (ZoneView), which drives the zone's own light with it.
/// Each casts no shadow; its LOD1 takes over past <see cref="Lod1From"/> metres.
/// </summary>
public static class Lamps
{
    public const string Dir = "res://art/world/lamps";
    public const float Lod1From = 24;

    public record Info(Vector3 Flame, float Height);

    static Dictionary<string, Info>? info;
    static ShaderMaterial? warm, cold;

    static Dictionary<string, Info> Infos
    {
        get
        {
            if (info != null) return info;
            info = new();
            var file = $"{Dir}/lamps.json";
            if (!FileAccess.FileExists(file)) return info;
            using var doc = JsonDocument.Parse(FileAccess.GetFileAsString(file));
            foreach (var p in doc.RootElement.EnumerateObject())
            {
                var f = p.Value.GetProperty("flame");
                info[p.Name] = new Info(new Vector3(f[0].GetSingle(), f[1].GetSingle(), f[2].GetSingle()), p.Value.GetProperty("height").GetSingle());
            }
            return info;
        }
    }

    /// <summary>Where a holder's flame stands (its base), in the holder's frame, and its height.</summary>
    public static Info? Of(string name) => Infos.TryGetValue(name, out var i) ? i : null;

    /// <summary>A holder, or null if it was never built. Tagged (meta "lamp") so the zone finds it.</summary>
    public static Node3D? Holder(string name, bool coldGlass = false)
    {
        var path = $"{Dir}/{name}.glb";
        if (!ResourceLoader.Exists(path) || Of(name) == null) return null;
        var root = GD.Load<PackedScene>(path).Instantiate<Node3D>();
        root.Name = "lamp_" + name;
        root.SetMeta("lamp", name);
        Dress(root, coldGlass);
        return root;
    }

    static void Dress(Node n, bool coldGlass)
    {
        foreach (var c in n.GetChildren())
        {
            if (c is MeshInstance3D m && m.Mesh != null)
            {
                m.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
                bool lod1 = m.Name.ToString().EndsWith("_LOD1");
                if (lod1) m.VisibilityRangeBegin = Lod1From;
                else m.VisibilityRangeEnd = Lod1From;
                for (int i = 0; i < m.Mesh.GetSurfaceCount(); i++)
                    if (m.Mesh.SurfaceGetMaterial(i) is Material mat && mat.ResourceName == "lamp_glass")
                        m.SetSurfaceOverrideMaterial(i, Glass(coldGlass));
            }
            Dress(c, coldGlass);
        }
    }

    /// <summary>The glass: unshaded, the flame's tint faint inside it, a fresnel edge (shaders/lamp_glass).</summary>
    /// <summary>--lamp-glass K, --lamp-glass-a A: the lit glass's brightness and cover, for pictures.</summary>
    static readonly float GlassK = SurvivorUnchained.Args.Num("lamp-glass", 1.0f), GlassA = SurvivorUnchained.Args.Num("lamp-glass-a", 0.3f);
    /// <summary>(Low Ford r1: 2.2 and 0.45 to 1.0 and 0.3: the post lantern's lit glass, seen through two panes from above, was a
    /// pale box round its flame. The town's wall glass keeps the old: ZoneView.Town's WallGlassOf.)</summary>
    public const float OldGlassK = 2.2f, OldGlassA = 0.45f;
    /// <summary>--lamp-glass-warm HEX, --lamp-glass-cold HEX: the lit glass's tint, for pictures (AgX greys a pale tint: saturated).</summary>
    static readonly string GlassWarm = SurvivorUnchained.Args.Get("lamp-glass-warm") ?? "#ff8a30", GlassCold = SurvivorUnchained.Args.Get("lamp-glass-cold") ?? "#3d70ff";
    /// <summary>(Low Ford r3, judge r2: the ford irons read unlit, cold white: 0.04 to 0.2, the glass lit blue round its flame)
    /// --ford-glass K, --ford-glass-a A, --ford-edge K, --ford-edge-a A: the ford irons' cold glass brightness and cover (its face under the flame), for pictures.</summary>
    static readonly float FordGlassK = SurvivorUnchained.Args.Num("ford-glass", 0.2f), FordGlassA = SurvivorUnchained.Args.Num("ford-glass-a", 0.3f),
        FordEdge = SurvivorUnchained.Args.Num("ford-edge", 0.2f), FordEdgeA = SurvivorUnchained.Args.Num("ford-edge-a", 0.3f);
    /// <summary>--lamp-edge K, --lamp-edge-a A: the warm glass's fresnel edge brightness and cover, for pictures.</summary>
    static readonly float WarmEdge = SurvivorUnchained.Args.Num("lamp-edge", 0.1f), WarmEdgeA = SurvivorUnchained.Args.Num("lamp-edge-a", 0.2f);
    /// <summary>The lit glass's material (warm or cold), for a lamp made in code (ZoneView.Town's wall lanterns).</summary>
    public static ShaderMaterial GlassOf(bool isCold) => Glass(isCold);
    static ShaderMaterial Glass(bool isCold)
    {
        ref var slot = ref isCold ? ref cold : ref warm;
        if (slot != null) return slot;
        var m = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/lamp_glass.gdshader") };
        m.SetShaderParameter("glow", new Color(isCold ? GlassCold : GlassWarm));
        m.SetShaderParameter("glow_strength", isCold ? FordGlassK : 0.24f * GlassK);
        m.SetShaderParameter("lit_alpha", isCold ? FordGlassA : GlassA);
        if (isCold) { m.SetShaderParameter("edge_k", FordEdge); m.SetShaderParameter("edge_alpha", FordEdgeA); }
        // (Low Ford r1) the warm glass's fresnel edge as the town's wall lanterns have it (ZoneView.Town's WallGlassOf): from the
        // play camera the post lantern shows two panes at a slant over its whole cage, and at the shader's 0.35/0.45 that edge
        // made the cage a pale box round a flame too small to find
        else { m.SetShaderParameter("edge_k", WarmEdge); m.SetShaderParameter("edge_alpha", WarmEdgeA); }
        // Drawn before the flames (theirs 1): the flame shows through its glass, not dimmed behind it.
        m.RenderPriority = -1;
        slot = m;
        return m;
    }

    /// <summary>--lamp-inner K: how strongly a lamp's flame lights its own iron from inside (shaders/lamp_inner), for pictures.</summary>
    static readonly float InnerK = SurvivorUnchained.Args.Num("lamp-inner", 2f);   // (Low Ford r1: 6 to 2, the cage's floor lit pale under the flame)
    /// <summary>--ford-inner K: the same for the ford irons' cold flame, for pictures.</summary>
    static readonly float FordInnerK = SurvivorUnchained.Args.Num("ford-inner", 2f);
    /// <summary>The holder's iron lit from inside by its flame at <paramref name="flame"/> (world, the flame's middle):
    /// a next pass on each of its non-glass surfaces, one material per holder (its flame's place).</summary>
    public static void Inner(Node3D holder, Vector3 flame, bool isCold, float radius)
    {
        var inner = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/lamp_inner.gdshader") };
        inner.SetShaderParameter("flame_at", flame);
        inner.SetShaderParameter("color", isCold ? new Color("#7aa8ff") : new Color("#ffa860"));
        inner.SetShaderParameter("strength", isCold ? FordInnerK : InnerK);
        inner.SetShaderParameter("radius", radius);
        holder.SetMeta("inner", inner);
        foreach (var c in holder.FindChildren("*", "MeshInstance3D", true, false))
            if (c is MeshInstance3D m && m.Mesh != null)
                for (int i = 0; i < m.Mesh.GetSurfaceCount(); i++)
                {
                    var mat = m.GetSurfaceOverrideMaterial(i) ?? m.Mesh.SurfaceGetMaterial(i);
                    if (mat == null || mat == warm || mat == cold) continue;
                    var own = (Material)mat.Duplicate();
                    own.NextPass = inner;
                    m.SetSurfaceOverrideMaterial(i, own);
                }
    }
    /// <summary>A holder's glass lit by its flame, or dark.</summary>
    public static void SetLit(Node3D holder, bool on)
    {
        if (holder.HasMeta("inner") && holder.GetMeta("inner").As<ShaderMaterial>() is ShaderMaterial im) im.SetShaderParameter("lit", on ? 1f : 0f);
        foreach (var c in holder.FindChildren("*", "MeshInstance3D", true, false))
            if (c is MeshInstance3D m && IsGlass(m)) m.SetInstanceShaderParameter("lit", on ? 1f : 0f);
    }

    static bool IsGlass(MeshInstance3D m)
    {
        for (int i = 0; m.Mesh != null && i < m.Mesh.GetSurfaceCount(); i++)
            if (m.GetSurfaceOverrideMaterial(i) is ShaderMaterial s && (s == warm || s == cold || s.Shader == warm?.Shader)) return true;   // (or a copy of it: ZoneView.Town's wall glass)
        return false;
    }
}
