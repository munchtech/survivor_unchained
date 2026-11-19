using System.Linq;
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
        var alts = new SurfaceTool(); alts.Begin(Mesh.PrimitiveType.Triangles);
        var stems = new SurfaceTool(); stems.Begin(Mesh.PrimitiveType.Triangles);
        // (lead 3, judge r1 fix 3) a halo a cluster, in its source's colour (glow_halo.gdshader; "halo" [radius m, strength])
        var halos = new SurfaceTool(); halos.Begin(Mesh.PrimitiveType.Triangles);
        var haloAlts = new SurfaceTool(); haloAlts.Begin(Mesh.PrimitiveType.Triangles);
        void Halo(SurfaceTool st, Vector3 c, float rad)
        {
            foreach (var (u, v) in new[] { (0f, 0f), (1f, 0f), (1f, 1f), (0f, 0f), (1f, 1f), (0f, 1f) })
            { st.SetUV(new Vector2(u, v)); st.SetUV2(new Vector2(rad, 0)); st.AddVertex(c); }
        }
        int clusters = 0, feet = 0, mush = 0, lit = 0, onPath = 0, nAlt = 0;
        // One cluster at (cx, cz), seeded by (sx, sz): its mushrooms, and a light on lightShare of them.
        void Cluster(float sx, float sz, float cx, float cz, double lightShare)
        {
            if (z.Meta.WaterAt(cx, cz)) return;
            bool alt = Hash(sx, sz, 8) < g.AltShare;
            var into = alt ? alts : caps;
            int n = g.CapsMin + (int)(Hash(sx, sz, 4) * (g.CapsMax - g.CapsMin + 1));
            float cy = (float)z.HeightAt(cx, cz);
            if (g.HaloRadius > 0) Halo(alt ? haloAlts : halos, new Vector3(cx, cy + 0.18f, cz), (float)(g.HaloRadius * (0.8 + 0.4 * Hash(sx, sz, 9))));
            for (int q = 0; q < n; q++)
            {
                float qa = Hash(sx, sz, 10 + q) * Mathf.Tau, qd = Mathf.Sqrt(Hash(sx, sz, 30 + q)) * 0.35f;
                float x = cx + Mathf.Cos(qa) * qd, zz = cz + Mathf.Sin(qa) * qd;
                float sh = 0.1f + 0.2f * Hash(sx, sz, 50 + q), sr = 0.02f + 0.02f * Hash(sx, sz, 70 + q);
                float cr = (float)(g.SizeMin + (g.SizeMax - g.SizeMin) * Hash(sx, sz, 90 + q));
                var tr = new Transform3D(Basis.Identity, new Vector3(x, (float)z.HeightAt(x, zz) - 0.02f, zz));
                stems.AppendFrom(new CylinderMesh { TopRadius = sr, BottomRadius = sr, Height = sh, RadialSegments = 6, Rings = 1 }, 0, tr * new Transform3D(Basis.Identity, new Vector3(0, sh / 2, 0)));
                into.AppendFrom(new SphereMesh { Radius = cr, Height = cr * (0.8f + 0.5f * Hash(sx, sz, 110 + q)), IsHemisphere = true, RadialSegments = 16, Rings = 6 }, 0, tr * new Transform3D(Basis.Identity, new Vector3(0, sh, 0)));
                mush++;
            }
            // (a light on a share of the clusters; the rest glow by their caps alone, so the lights in view stay few)
            if (Hash(sx, sz, 7) < lightShare)
            {
                // (lead 4, judge r2 fix 1: protected skin) the world's glow lights the world and the crowd, never people's layer (2,
                // her and the folk) nor her own layers: under the cyan her skin went from h 49-51 to 62, green)
                var light = new OmniLight3D { Name = "GlowLight", LightColor = Hex(alt ? g.AltLight : g.Light), LightEnergy = 0, OmniRange = (float)g.Range, ShadowEnabled = false, Position = new Vector3(cx, cy + 0.35f, cz),
                    LightCullMask = 0xFFFFFu & ~2u & ~PlayerView.HerLayers & ~PlayerView.CastLayer };
                root.AddChild(light); root.lights.Add((light, (float)g.Energy));
                lit++;
            }
            clusters++; if (alt) nAlt++;
        }
        // (lead 2, the glow bug: the woods alone put no cluster in the opening frame, one a 97 m2 spread over the whole zone,
        // most under a crown, so nothing showed; a test light beside her lit the ground at once. The clusters line the walked
        // paths first, where she and the camera are: one every step m, on a side by the hash, side m off the centre line, as
        // the reference's mushrooms flank its path.)
        if (g.Paths != null)
            foreach (var name in g.Paths)
            {
                if (!z.Meta.Paths.TryGetValue(name, out var pts) || pts.Length < 2) continue;
                double carry = 0;
                for (int i = 0; i + 1 < pts.Length; i++)
                {
                    double ax = pts[i][0], az = pts[i][1], bx = pts[i + 1][0], bz = pts[i + 1][1];
                    double len = System.Math.Sqrt((bx - ax) * (bx - ax) + (bz - az) * (bz - az));
                    if (len < 1e-6) continue;
                    double ux = (bx - ax) / len, uz = (bz - az) / len;
                    double t = carry;
                    for (; t < len; t += g.Step)
                    {
                        float sx = (float)(ax + ux * t), sz = (float)(az + uz * t);
                        float jit = (Hash(sx, sz, 5) - 0.5f) * (float)g.Step * 0.6f;
                        float side = Hash(sx, sz, 6) < 0.5f ? -1 : 1;
                        float off = (float)(g.SideMin + (g.SideMax - g.SideMin) * Hash(sx, sz, 3));
                        float cx = sx + (float)ux * jit - (float)uz * side * off, cz = sz + (float)uz * jit + (float)ux * side * off;
                        int before = clusters;
                        Cluster(sx, sz, cx, cz, g.PathLight);
                        onPath += clusters - before;
                    }
                    carry = t - len;
                }
            }
        // The woods: a share of tree and rock feet, spread over the whole zone (the hash's threshold is the smaller of the
        // share and the room left over every foot), each cluster just off its foot.
        int all = 0;
        foreach (var fg in z.Flora) if (System.Array.IndexOf(Feet, fg.Kind) >= 0) all += fg.At.Count();
        double share = System.Math.Min(g.Share, all > 0 ? (double)System.Math.Max(g.Max - clusters, 0) / all : 0);
        if (SurvivorUnchained.Args.Has("glow-rocks"))   // (lead 3: where the rocks stand, for framing stone in a shot)
            foreach (var fg in z.Flora) if (fg.Kind is "boulder" or "rock") GD.Print($"rocks {fg.Kind}: " + string.Join(" ", fg.At.Take(40).Select(t => $"{t.Origin.X:0},{t.Origin.Z:0}")));
        foreach (var fg in z.Flora)
        {
            if (System.Array.IndexOf(Feet, fg.Kind) < 0) continue;
            foreach (var t in fg.At)
            {
                feet++;
                if (clusters >= g.Max) break;
                var o = t.Origin;
                if (Hash(o.X, o.Z, 1) >= share) continue;
                float a = Hash(o.X, o.Z, 2) * Mathf.Tau, d = 0.6f + 0.8f * Hash(o.X, o.Z, 3);
                Cluster(o.X, o.Z, o.X + Mathf.Cos(a) * d, o.Z + Mathf.Sin(a) * d, g.WoodLight);
            }
        }
        if (clusters == 0) { root.QueueFree(); return null; }
        var mesh = new ArrayMesh();
        var shader = GD.Load<Shader>("res://shaders/glow_cap.gdshader");
        void Surface(SurfaceTool st, ShaderMaterial m) { int before = mesh.GetSurfaceCount(); st.Commit(mesh); if (mesh.GetSurfaceCount() > before) mesh.SurfaceSetMaterial(before, m); }
        var cm = new ShaderMaterial { Shader = shader }; cm.SetShaderParameter("cap_col", Hex(g.Cap));
        Surface(caps, cm);
        if (nAlt > 0) { var am = new ShaderMaterial { Shader = shader }; am.SetShaderParameter("cap_col", Hex(g.AltCap)); Surface(alts, am); }
        var sm = new ShaderMaterial { Shader = shader }; sm.SetShaderParameter("stem_col", Hex(g.Stem)); sm.SetShaderParameter("is_stem", 1f);
        Surface(stems, sm);
        root.AddChild(new MeshInstance3D { Name = "GlowCaps", Mesh = mesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        if (g.HaloRadius > 0)
        {
            var hmesh = new ArrayMesh();
            var hs = GD.Load<Shader>("res://shaders/glow_halo.gdshader");
            void HSurface(SurfaceTool st, string col) { int before = hmesh.GetSurfaceCount(); st.Commit(hmesh); if (hmesh.GetSurfaceCount() > before) { var m = new ShaderMaterial { Shader = hs }; m.SetShaderParameter("halo_col", Hex(col)); m.SetShaderParameter("halo_k", (float)g.HaloK); hmesh.SurfaceSetMaterial(before, m); } }
            HSurface(halos, g.Cap);
            if (nAlt > 0) HSurface(haloAlts, g.AltCap);
            // (the quads stand at the cluster's point; their reach is the vertex shader's: a box big enough that none is culled)
            root.AddChild(new MeshInstance3D { Name = "GlowHalos", Mesh = hmesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, ExtraCullMargin = 4f });
        }
        root.Visible = false;
        GD.Print($"NightGlow {z.Id}: {clusters} clusters ({onPath} on paths, {nAlt} alt), {lit} lights, {mush} mushrooms from {feet} feet");
        return root;
    }

    public override void _Process(double delta)
    {
        float k = Atmosphere.GlowK;
        if (Mathf.IsEqualApprox(k, last)) return;
        last = k;
        Visible = k >= 0.01f;
        foreach (var (l, e) in lights) l.LightEnergy = e * k;
        if (k >= 0.01f && GetViewport()?.GetCamera3D() is { } cam)
            GD.Print($"NightGlow k={k}: {lights.Count(x => cam.IsPositionInFrustum(x.L.GlobalPosition))} lights in view");
    }
}
