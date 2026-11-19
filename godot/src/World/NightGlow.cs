using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Look;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>(lane J art-color, night glow; the owner's night reference) The world's own light by night: clusters of glowing
/// mushrooms at the feet of trees and rocks, each with a light that tints the ground and stones round it. The clusters are the
/// palette's "glow" (rigs.json palettes.wild_night.glow: colours, energy, range, share of tree feet, most clusters, mushrooms a
/// cluster, cap sizes), laid once per zone by a hash of each foot; all caps in one mesh (glow_cap.gdshader, times the global
/// glow_k), one light a cluster (no shadow; energy times Atmosphere.GlowK, 0 by day: the node hides).</summary>
public partial class NightGlow : Node3D
{
    static readonly string[] Feet = ["pine", "broadleaf", "autumn", "dead", "boulder", "rock"];
    readonly List<(OmniLight3D L, float E)> lights = new();
    float last = -1;

    static float Hash(float x, float z, int k)
    {
        float h = Mathf.Sin(x * 12.9898f + z * 78.233f + k * 37.719f) * 43758.5453f;
        return h - Mathf.Floor(h);
    }

    /// <summary>The glow root for a zone, or null (a dungeon, or its night air's palette has no glow).</summary>
    public static NightGlow? Build(ZoneData z)
    {
        if (z.DungeonTheme != "") return null;
        Atmosphere.RigsLoad();
        var night = Rigs.Lit(z.Place?.Night ?? Atmospheres.Night);
        if (night.GlowName == "" || !Rigs.Current.Glows.TryGetValue(night.GlowName, out var g)) return null;
        Color Hex(string s) => new Color(s);
        var root = new NightGlow { Name = "NightGlow" };
        var caps = new SurfaceTool(); caps.Begin(Mesh.PrimitiveType.Triangles);
        var stems = new SurfaceTool(); stems.Begin(Mesh.PrimitiveType.Triangles);
        int clusters = 0, feet = 0, mush = 0;
        foreach (var fg in z.Flora)
        {
            if (System.Array.IndexOf(Feet, fg.Kind) < 0) continue;
            foreach (var t in fg.At)
            {
                feet++;
                if (clusters >= g.Max) break;
                var o = t.Origin;
                if (Hash(o.X, o.Z, 1) >= g.Share) continue;
                float a = Hash(o.X, o.Z, 2) * Mathf.Tau, d = 0.6f + 0.8f * Hash(o.X, o.Z, 3);
                float cx = o.X + Mathf.Cos(a) * d, cz = o.Z + Mathf.Sin(a) * d;
                int n = g.CapsMin + (int)(Hash(o.X, o.Z, 4) * (g.CapsMax - g.CapsMin + 1));
                float cy = (float)z.HeightAt(cx, cz);
                for (int q = 0; q < n; q++)
                {
                    float qa = Hash(o.X, o.Z, 10 + q) * Mathf.Tau, qd = Mathf.Sqrt(Hash(o.X, o.Z, 30 + q)) * 0.35f;
                    float x = cx + Mathf.Cos(qa) * qd, zz = cz + Mathf.Sin(qa) * qd;
                    float sh = 0.1f + 0.2f * Hash(o.X, o.Z, 50 + q), sr = 0.02f + 0.02f * Hash(o.X, o.Z, 70 + q);
                    float cr = (float)(g.SizeMin + (g.SizeMax - g.SizeMin) * Hash(o.X, o.Z, 90 + q));
                    var tr = new Transform3D(Basis.Identity, new Vector3(x, (float)z.HeightAt(x, zz) - 0.02f, zz));
                    stems.AppendFrom(new CylinderMesh { TopRadius = sr, BottomRadius = sr, Height = sh, RadialSegments = 6, Rings = 1 }, 0, tr * new Transform3D(Basis.Identity, new Vector3(0, sh / 2, 0)));
                    caps.AppendFrom(new SphereMesh { Radius = cr, Height = cr * (0.8f + 0.5f * Hash(o.X, o.Z, 110 + q)), IsHemisphere = true, RadialSegments = 16, Rings = 6 }, 0, tr * new Transform3D(Basis.Identity, new Vector3(0, sh, 0)));
                    mush++;
                }
                var light = new OmniLight3D { Name = "GlowLight", LightColor = Hex(g.Light), LightEnergy = 0, OmniRange = (float)g.Range, ShadowEnabled = false, Position = new Vector3(cx, cy + 0.35f, cz) };
                root.AddChild(light); root.lights.Add((light, (float)g.Energy));
                clusters++;
            }
        }
        if (clusters == 0) { root.QueueFree(); return null; }
        var mesh = new ArrayMesh();
        caps.Commit(mesh);
        var cm = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/glow_cap.gdshader") };
        cm.SetShaderParameter("cap_col", Hex(g.Cap));
        mesh.SurfaceSetMaterial(0, cm);
        stems.Commit(mesh);
        var sm = new ShaderMaterial { Shader = cm.Shader };
        sm.SetShaderParameter("stem_col", Hex(g.Stem)); sm.SetShaderParameter("is_stem", 1f);
        mesh.SurfaceSetMaterial(1, sm);
        root.AddChild(new MeshInstance3D { Name = "GlowCaps", Mesh = mesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        root.Visible = false;
        GD.Print($"NightGlow {z.Id}: {clusters} clusters, {clusters} lights, {mush} mushrooms from {feet} feet");
        return root;
    }

    public override void _Process(double delta)
    {
        float k = Atmosphere.GlowK;
        if (Mathf.IsEqualApprox(k, last)) return;
        last = k;
        Visible = k >= 0.01f;
        foreach (var (l, e) in lights) l.LightEnergy = e * k;
    }
}
