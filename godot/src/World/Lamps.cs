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
    static ShaderMaterial Glass(bool isCold)
    {
        ref var slot = ref isCold ? ref cold : ref warm;
        if (slot != null) return slot;
        var m = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/lamp_glass.gdshader") };
        m.SetShaderParameter("glow", isCold ? new Color("#7aa8ff") : new Color("#ffa860"));
        m.SetShaderParameter("glow_strength", isCold ? 0.3f : 0.24f);
        slot = m;
        return m;
    }

    /// <summary>A holder's glass lit by its flame, or dark.</summary>
    public static void SetLit(Node3D holder, bool on)
    {
        foreach (var c in holder.FindChildren("*", "MeshInstance3D", true, false))
            if (c is MeshInstance3D m && IsGlass(m)) m.SetInstanceShaderParameter("lit", on ? 1f : 0f);
    }

    static bool IsGlass(MeshInstance3D m)
    {
        for (int i = 0; m.Mesh != null && i < m.Mesh.GetSurfaceCount(); i++)
            if (m.GetSurfaceOverrideMaterial(i) is ShaderMaterial s && (s == warm || s == cold)) return true;
        return false;
    }
}
