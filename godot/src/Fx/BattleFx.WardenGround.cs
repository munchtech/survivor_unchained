using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The Warden's ground skills (Combat VFX 10 item 3; WARDEN_SKILLS_VFX_HOOKS §1-2): Sunder's heavy line and
/// Groundbreaker's crack, heave and Aftershock. Weight and earth, not light: a dark split in the ground running out
/// from her (the Long Cut's baked crack strip, art/fx/longcut/crack_*_NN, laid as lit decals tile by tile as the tip
/// passes), a dull-orange hot edge on each tile's first frames only, solid lit dust jets lifting along it, stone chips
/// (chunks.glb) kicked up; the heave a ring of ground plates thrust up leaning out (chunks.glb's slabs, lit, shadowed),
/// a low rolling dust ring, chunks thrown and falling back, radial crater cracks. No rings of light, no flash.
/// r2 (VFX 11): the heave's own warm omni (#FF9A4A, 3.5 m, 2-frame rise, 18-frame decay), crater cracks glowing #C8551E
/// over 20 frames, slabs 0.9-1.4 m standing and 1.3x wide with fresh-earth tops, a tan dust wall to 3.25 m in 0.5 s,
/// 12-20 faceted lit stones; Sunder's line 0.6 m past her shield, 1.6x across and darkened, a #FF8A3A core held 10
/// frames, 6-8 tall jets, raised lips; the crack's tip a hot core and glow with stones popping; ground dust #8C7558;
/// the struck bodies' numbers and flinch wait for the tip or the heave (view only: wgHitAt, CrowdView.FlashHeld).
///
/// The sim fires the heave in the same tick as the crack; the view holds the heave (and the struck bodies' kits) until
/// the crack's tip arrives (0.06 s + 0.028 s a metre, at most the event's 0.35 s). The bodies the line and the heave
/// strike get the shared HitKit as the tip or the heave reaches them, and the plain school impact is skipped for them.
/// Dev: --wg-beats (frames: sl_*, gc_*, gh_*, ga_*), --wg-aftershock (lights Groundbreaker's Aftershock Turn).
/// </summary>
public partial class BattleFx
{
    const string WgDir = "res://art/fx/longcut/";
    static readonly bool WgBeats = Args.Has("wg-beats");
    static readonly Color WgHot = new Color("#ff7026").SrgbToLinear();

    static Texture2D?[]? wgAlb, wgNrm, wgEmi;
    /// <summary>The crack's centre across the strip (m) in 256 steps along its 24 m (crack.json centre_m).</summary>
    static float[]? wgOff;
    static Mesh[]? wgChunks, wgSlabs;
    static float[]? wgChunkLen, wgSlabLen;

    sealed class WgDecal
    {
        public required Decal D;
        public bool On, Glow;
        public float Age, Life, FadeFrom, Strength = 1, Energy, Sear;
        /// <summary>A held glow (Hold s at full, then cooling over Life - Hold), in its own colour; 0 the 4-frame edge.</summary>
        public float Hold;
        public Color Col;
    }

    /// <summary>A raised lip of earth along a crack's edge: up as the tip passes, sunk at the end.</summary>
    sealed class WgLip
    {
        public required MeshInstance3D N;
        public bool On;
        public float Age, Life, H, Delay;
        public Transform3D T;
    }

    /// <summary>A crack's travelling tip.</summary>
    sealed class WgTip
    {
        public Vector2 From, Dir, Side;
        public float Len, Across, Travel, Age;
        public int T0, N;
    }

    /// <summary>The heave's own warm light (2-frame rise, 18-frame decay).</summary>
    sealed class WgGlow
    {
        public required OmniLight3D L;
        public bool On;
        public float Age, Peak;
    }

    sealed class WgRock
    {
        public required MeshInstance3D N;
        public bool On, Slab, Rested;
        public Vector3 P, V, Axis, Base, U;
        public Godot.Basis B;
        public float Age, Life, Spin, Scale, L, Hold, Delay;
        public Vector3 Local = Vector3.One;
        public int Bounces;
    }

    readonly List<WgDecal> wgDecals = new();
    readonly List<WgRock> wgRocks = new();
    readonly List<WgLip> wgLips = new();
    readonly List<WgTip> wgTips = new();
    readonly List<WgGlow> wgGlows = new();
    /// <summary>Bodies the line or the heave strike: when the blow lands in the view (their numbers and flinch wait).</summary>
    readonly Dictionary<int, double> wgHitAt = new();
    static Mesh? wgLipMesh;
    static Mesh[]? wgStones;
    static readonly Color WgCore = new Color("#ff8a3a").SrgbToLinear(), WgTipCol = new Color("#ff7a2e").SrgbToLinear(),
        WgCrater = new Color("#c8551e").SrgbToLinear(), WgHeaveLight = new Color("#ff9a4a");
    int wgLipNext;
    int wgDecalNext, wgRockNext;
    bool wgWarm, wgWickSet;
    /// <summary>Crack ends this tick (where its heave will be) and when its tip arrives.</summary>
    readonly List<(double X, double Z, double At, double Arrive)> wgEnds = new();
    /// <summary>Aftershocks owed: (x, z, due).</summary>
    readonly List<(double X, double Z, double Due)> wgAfter = new();
    (double X, double Z, double At) wgLastHeave = (0, 0, -1);
    /// <summary>Bodies whose plain impact this tick is the line's or the heave's (their kit comes with the tip).</summary>
    readonly Dictionary<int, long> wgOwned = new();
    int wgLines, wgCracks, wgHeaves, wgAfters;
    bool wgSlShot, wgGcShot, wgGhShot, wgGaShot;
    double wgGcAt = -1;

    const int WgDecalPool = 112, WgRockPool = 96;
    const uint WgLayer = 1u << 17;
    static readonly Color WgLineTint = new Color(1, 1, 1) * (float)Args.Num("wg-line-tint", 0.45f);
    static readonly bool WgNoDust = Args.Has("wg-no-dust");
    /// <summary>Dev (--wg-sl-after T): the Sunder line pictured is the first after T s.</summary>
    static readonly double WgSlAfter = Args.Num("wg-sl-after", 2.5f);
    const float WgTile = 2f, WgBand = 2.4f;

    /* ------------------------------------------------------------ set-up -- */

    void WgWarmUp()
    {
        wgWarm = true;
        if (wgAlb == null)
        {
            wgAlb = new Texture2D?[12]; wgNrm = new Texture2D?[12]; wgEmi = new Texture2D?[12];
            for (int i = 0; i < 12; i++)
            {
                string n = i.ToString("00");
                wgAlb[i] = Load($"crack_albedo_{n}.png");
                wgNrm[i] = Load($"crack_normal_{n}.png");
                wgEmi[i] = Load($"crack_emis_{n}.png");
            }
            static Texture2D? Load(string f) => ResourceLoader.Exists(WgDir + f) ? GD.Load<Texture2D>(WgDir + f) : null;
            wgOff = new float[256];
            try
            {
                using var fa = FileAccess.Open(WgDir + "crack.json", FileAccess.ModeFlags.Read);
                if (fa != null)
                {
                    using var doc = System.Text.Json.JsonDocument.Parse(fa.GetAsText());
                    if (doc.RootElement.TryGetProperty("centre_m", out var c) && c.GetArrayLength() == 256)
                    {
                        int k = 0;
                        foreach (var v in c.EnumerateArray()) wgOff[k++] = v.GetSingle();
                    }
                }
            }
            catch (Exception ex) { GD.PrintErr($"warden ground: crack.json {ex.Message}"); }
            WgLoadChunks();
        }
        for (int i = 0; i < WgDecalPool; i++)
        {
            var d = new Decal { UpperFade = 0.3f, LowerFade = 0.3f, CullMask = 1, NormalFade = 0.3f, Visible = false };
            AddChild(d);
            wgDecals.Add(new WgDecal { D = d });
        }
        for (int i = 0; i < WgRockPool; i++)
        {
            // (on a layer of their own, out of the crack decals' reach: the strip's paint and its hot edge on a stone or
            // a lip read as a pale plank, a white speck)
            var n = new MeshInstance3D { Mesh = wgChunks![i % wgChunks.Length], Visible = false, CastShadow = GeometryInstance3D.ShadowCastingSetting.On, Layers = WgLayer };
            AddChild(n);
            wgRocks.Add(new WgRock { N = n });
        }
        wgLipMesh ??= WgBuildLip();
        for (int i = 0; i < 48; i++)
        {
            var n = new MeshInstance3D { Mesh = wgLipMesh, Visible = false, CastShadow = GeometryInstance3D.ShadowCastingSetting.On, Layers = WgLayer };
            AddChild(n);
            wgLips.Add(new WgLip { N = n });
        }
        for (int i = 0; i < 2; i++)
        {
            // (its own light, in the heave's colour; shadowed, so the slabs throw theirs away from the heart)
            var l = new OmniLight3D { LightColor = WgHeaveLight, OmniRange = 3.5f, OmniAttenuation = 1.2f, ShadowEnabled = true, LightEnergy = 0, Visible = false };
            AddChild(l);
            wgGlows.Add(new WgGlow { L = l });
        }
    }

    /// <summary>A lip of earth, 1 m long (+X) and 1 high (scaled per use): a steep inner face at the crack (-Z), a
    /// longer outer slope, its ridge fresh and pale (the lit top edge), its feet the ground's own.</summary>
    static Mesh WgBuildLip()
    {
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        var foot = new Color(0.045f, 0.036f, 0.026f);
        var ridge = new Color(0.1f, 0.078f, 0.054f);
        // cross-section (z, y): inner foot, ridge, outer foot
        var cs = new[] { new Vector2(-0.01f, -0.15f), new Vector2(0.02f, 1f), new Vector2(0.14f, -0.15f) };
        var cc = new[] { foot, ridge, foot };
        void Tri(Vector3 a, Color ca, Vector3 b, Color cb, Vector3 c, Color ccol)
        {
            var nrm = (c - a).Cross(b - a).Normalized();
            if (nrm.Y < 0) { nrm = -nrm; (b, c) = (c, b); (cb, ccol) = (ccol, cb); }
            st.SetNormal(nrm); st.SetColor(ca); st.AddVertex(a);
            st.SetNormal(nrm); st.SetColor(cb); st.AddVertex(b);
            st.SetNormal(nrm); st.SetColor(ccol); st.AddVertex(c);
        }
        // tapered ends: the ridge drops to the feet over the first and last 15%
        float[] xs = { 0, 0.15f, 0.85f, 1 };
        float[] hk = { 0.05f, 1, 1, 0.05f };
        for (int k = 0; k < 3; k++)
            for (int j = 0; j < 2; j++)
            {
                Vector3 P(int x, int c) => new(xs[x], c == 1 ? cs[1].Y * hk[x] : cs[c].Y, cs[c].X);
                var a0 = P(k, j); var a1 = P(k, j + 1); var b0 = P(k + 1, j); var b1 = P(k + 1, j + 1);
                Tri(a0, cc[j], b0, cc[j], a1, cc[j + 1]);
                Tri(a1, cc[j + 1], b0, cc[j], b1, cc[j + 1]);
            }
        st.SetMaterial(new StandardMaterial3D { VertexColorUseAsAlbedo = true, Roughness = 0.95f, CullMode = BaseMaterial3D.CullModeEnum.Disabled });
        return st.Commit();
    }

    /// <summary>A mesh with flat normals (each face its own): the chunks as faceted stones, each surface its own lit
    /// stone (the weathered face dark, the broken face paler), never bright enough to read as a white speck.</summary>
    static Mesh WgFacet(Mesh src)
    {
        var outm = new ArrayMesh();
        for (int si = 0; si < src.GetSurfaceCount(); si++)
        {
            var st = new SurfaceTool();
            st.Begin(Mesh.PrimitiveType.Triangles);
            var arr = src.SurfaceGetArrays(si);
            var vs = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            var idx = arr[(int)Mesh.ArrayType.Index].AsInt32Array();
            int n = idx.Length > 0 ? idx.Length : vs.Length;
            for (int i = 0; i + 2 < n; i += 3)
            {
                Vector3 a = vs[idx.Length > 0 ? idx[i] : i], b = vs[idx.Length > 0 ? idx[i + 1] : i + 1], c = vs[idx.Length > 0 ? idx[i + 2] : i + 2];
                var nrm = (c - a).Cross(b - a).Normalized();
                st.SetNormal(nrm); st.AddVertex(a);
                st.SetNormal(nrm); st.AddVertex(b);
                st.SetNormal(nrm); st.AddVertex(c);
            }
            bool broken = src.SurfaceGetMaterial(si) is BaseMaterial3D bm && bm.AlbedoColor.R > 0.07f;
            st.SetMaterial(new StandardMaterial3D
            {
                AlbedoColor = broken ? new Color(0.27f, 0.22f, 0.165f) : new Color(0.12f, 0.1f, 0.085f),
                Roughness = 0.9f, MetallicSpecular = 0.25f,
            });
            st.Commit(outm);
        }
        return outm;
    }

    static void WgLoadChunks()
    {
        var list = new List<(Mesh M, float Len)>();
        const string path = WgDir + "chunks.glb";
        if (ResourceLoader.Exists(path) && GD.Load<PackedScene>(path) is { } ps)
        {
            var root = ps.Instantiate();
            foreach (var n in root.FindChildren("*", "MeshInstance3D", true, false))
                if (((MeshInstance3D)n).Mesh is ArrayMesh src)
                {
                    // Earth, not pale stone: the chunks' own paint taken down to the ground's brown.
                    var m = (ArrayMesh)src.Duplicate();
                    for (int si = 0; si < m.GetSurfaceCount(); si++)
                        if (m.SurfaceGetMaterial(si) is BaseMaterial3D bm)
                        {
                            var t = (BaseMaterial3D)bm.Duplicate();
                            t.AlbedoColor = bm.AlbedoColor * new Color(0.52f, 0.46f, 0.4f);
                            t.Roughness = 0.95f;
                            m.SurfaceSetMaterial(si, t);
                        }
                    var s = m.GetAabb().Size;
                    list.Add((m, Mathf.Max(s.X, s.Z)));
                }
            root.Free();
        }
        if (list.Count == 0)
        {
            var mat = new StandardMaterial3D { AlbedoColor = new Color(0.09f, 0.075f, 0.06f), Roughness = 0.95f };
            for (int i = 0; i < 4; i++) list.Add((new BoxMesh { Size = new Vector3(0.3f + 0.08f * i, 0.1f, 0.24f), Material = mat }, 0.3f + 0.08f * i));
        }
        wgChunks = list.Select(x => x.M).ToArray();
        wgChunkLen = list.Select(x => x.Len).ToArray();
        // The slabs: the biggest pieces (a plate of ground stood up), scaled to 1.0-1.5 m.
        var big = list.OrderByDescending(x => x.Len).Take(Math.Max(1, list.Count / 2)).ToList();
        // Their own copies, paler (fresh earth turned up: 1.6-2x the ground's value where the light takes their tops).
        wgSlabs = big.Select(x =>
        {
            var m = (Mesh)x.M.Duplicate();
            for (int si = 0; si < m.GetSurfaceCount(); si++)
                if (m.SurfaceGetMaterial(si) is BaseMaterial3D bm)
                {
                    var t = (BaseMaterial3D)bm.Duplicate();
                    t.AlbedoColor = bm.AlbedoColor * new Color(1.75f, 1.62f, 1.45f);
                    m.SurfaceSetMaterial(si, t);
                }
            return m;
        }).ToArray();
        wgSlabLen = big.Select(x => x.Len).ToArray();
        // The thrown stones: the chunks faceted (flat normals), lit, a weathered grey-brown stone.
        try { wgStones = list.Select(x => WgFacet(x.M)).ToArray(); }
        catch (Exception ex) { GD.PrintErr($"warden ground: facet {ex.Message}"); wgStones = wgChunks; }
        if (WgBeats) GD.Print($"[wg-beats] chunks {list.Count}: {string.Join(",", list.Select(x => x.Len.ToString("F2")))}");
    }

    /* ------------------------------------------------------------ hooks -- */

    /// <summary>Sunder's heavy line and Groundbreaker's crack (Lance's hook); false for any other beam.</summary>
    bool WgBeam(Ev.Beam e)
    {
        if (e.Art is not ("slash_heavy_line" or "slash_quake_crack")) return false;
        if (WfxOff) return true;
        if (!wgWarm) WgWarmUp();
        bool quake = e.Art == "slash_quake_crack";
        var from = new Vector2((float)e.X0, (float)e.Z0);
        var to = new Vector2((float)e.X1, (float)e.Z1);
        float len = from.DistanceTo(to);
        if (len < 0.3f) return true;
        var dir = (to - from) / len;
        if (!quake && b0 != null)
        {
            // The line starts 0.6 m past her shield (0.45 m before her), not under the swing.
            var pl = new Vector2((float)b0.Player.X, (float)b0.Player.Z);
            float a0 = (from - pl).Dot(dir);
            if (a0 < 1.05f && len - (1.05f - a0) > 1.5f) { from += dir * (1.05f - a0); len -= 1.05f - a0; }
        }
        float travel = quake ? Mathf.Min((float)Math.Max(0.12, e.Duration), 0.06f + len * 0.028f) : 0.12f;
        bool night = Flare.Night;
        if (quake)
        {
            wgEnds.Add((e.X1, e.Z1, time, time + travel));
            wgCracks++;
            if (WgBeats && !wgGcShot && (len >= 4 || time > 12)) { wgGcShot = true; wgGcAt = time; Shots.WantFrames("gc_f3", 3); Shots.WantFrames("gc_f12", 12); GD.Print($"[wg-beats] crack {wgCracks} len {len:F1} travel {travel:F2} t={time:F2}"); }
            // (twin: the second of a pair takes a different run of the strip)
            int t0 = wgEnds.Count(x => x.At == time) > 1 ? 1 : 0;
            int n = Math.Clamp((int)Mathf.Round(len / 1.7f), 2, 6);
            WgCrack(from, dir, len, t0, n, 1.05f, travel, 2.6f, night, true);
            wgTips.Add(new WgTip { From = from, Dir = dir, Side = new Vector2(-dir.Y, dir.X), Len = len, Across = 1.05f, Travel = travel, T0 = t0, N = n });
            Cam?.AddTrauma(0.05f);
        }
        else
        {
            wgLines++;
            if (WgBeats && !wgSlShot && time > WgSlAfter) { wgSlShot = true; foreach (var f in new[] { 3, 5, 10, 30 }) Shots.WantFrames($"sl_f{f}", f); GD.Print($"[wg-beats] line {wgLines} len {len:F1} from {from.X:F2},{from.Y:F2} dir {dir.X:F2},{dir.Y:F2} scr {WgScr(from.X, from.Y)} -> {WgScr(to.X, to.Y)} her {b0?.Player.X:F2},{b0?.Player.Z:F2} t={time:F2}"); }
            bool sear = b0?.Lamps is { } lp && lp.Has("sunder.burning_edge");
            // Tiles 4-9 (1.6x across: its dark gap 25-32 px at her end, ~10 px at the tip) over the line.
            WgCrack(from, dir, len, 4, 6, (float)Args.Num("wg-line-across", 1.6f), travel, 1.8f, night, false, sear);
            Cam?.AddTrauma(0.125f); // (shake goes as trauma squared: ~40% of Groundbreaker's ~0.2)
        }
        // The struck: what stands on it, kitted as the tip reaches it.
        if (b0 != null)
        {
            float half = (float)e.Width * 0.5f;
            var items = b0.Enemies.Items;
            int kits = 0;
            for (int i = 0; i < items.Length; i++)
            {
                var en = items[i];
                if (en == null || !en.Alive) continue;
                var p = new Vector2((float)en.X, (float)en.Z) - from;
                float along = p.Dot(dir), off = Mathf.Abs(p.X * dir.Y - p.Y * dir.X);
                if (along < -0.3f || along > len + 0.3f || off > half + (float)en.Radius) continue;
                // (the crack's own trail hits stop short of the heave: the heave kits those)
                if (quake && along > len - 2.5f) continue;
                wgOwned[i] = Engine.GetFramesDrawn();
                int id = i; bool full = kits++ < 6;
                var awayDir = new Vector3(dir.X, 0, dir.Y);
                float kd = Mathf.Clamp(along / len, 0, 1) * travel;
                wgHitAt[id] = time + kd;
                WgLater(kd, () => WgKit(id, awayDir, full));
            }
        }
        return true;
    }

    /// <summary>Groundbreaker's heave (the Explosion switch's own case): held until its crack's tip arrives.</summary>
    void WgHeave(Ev.Explosion e)
    {
        if (WfxOff) return;
        if (!wgWarm) WgWarmUp();
        double delay = 0;
        foreach (var c in wgEnds)
            if (c.At == time && Math.Abs(c.X - e.X) < 0.05 && Math.Abs(c.Z - e.Z) < 0.05) { delay = Math.Max(0, c.Arrive - time); break; }
        wgEnds.RemoveAll(c => time - c.At > 1);
        bool after = false;
        for (int i = 0; i < wgAfter.Count; i++)
            if (Math.Abs(wgAfter[i].X - e.X) < 0.05 && Math.Abs(wgAfter[i].Z - e.Z) < 0.05 && Math.Abs(wgAfter[i].Due - time) < 0.3) { after = true; wgAfter.RemoveAt(i); break; }
        wgAfter.RemoveAll(a => time - a.Due > 1);
        if (!after) wgLastHeave = (e.X, e.Z, time);
        // The struck: their plain impact skipped; their kit at the heave.
        var ids = new List<int>();
        if (b0 != null)
        {
            var items = b0.Enemies.Items;
            for (int i = 0; i < items.Length; i++)
            {
                var en = items[i];
                if (en == null || !en.Alive) continue;
                double dx = en.X - e.X, dz = en.Z - e.Z;
                if (dx * dx + dz * dz > (e.Radius + en.Radius) * (e.Radius + en.Radius)) continue;
                wgOwned[i] = Engine.GetFramesDrawn();
                wgHitAt[i] = time + delay;
                ids.Add(i);
            }
        }
        float r = (float)e.Radius, k = after ? 0.35f : 1f;
        double x = e.X, z = e.Z;
        WgLater((float)delay, () =>
        {
            WgHeaveNow(x, z, r, after);
            var c = new Vector2((float)x, (float)z);
            int kits = 0;
            foreach (var id in ids)
            {
                var en = b0?.Enemies.Items[id];
                var p = en != null ? new Vector2((float)en.X, (float)en.Z) : c;
                var away = p - c;
                away = away.LengthSquared() > 0.01f ? away.Normalized() : Vector2.Right;
                WgKit(id, new Vector3(away.X, 0, away.Y), kits++ < (after ? 3 : 6));
            }
        });
    }

    /// <summary>Fall's hook: an Aftershock's strike (emitted with its heave, same tick, same spot) owes a heave the
    /// sim will fire itself; it draws nothing now and stops Fall's own slash_quake mark (Landing's crack, stones,
    /// blast) doubling the heave.</summary>
    bool WgStrike(Ev.Strike e)
    {
        if (WgBeats && e.Art == "slash_quake") GD.Print($"[wg-beats] strike slash_quake delay {e.Delay:F2} lastHeave {wgLastHeave.At:F2} t={time:F2}");
        if (e.Art != "slash_quake" || wgLastHeave.At != time) return false;
        if (Math.Abs(wgLastHeave.X - e.X) > 0.05 || Math.Abs(wgLastHeave.Z - e.Z) > 0.05) return false;
        wgAfter.Add((e.X, e.Z, time + e.Delay));
        // (a grumble while it comes: a little grit off the crater's lip)
        double x = e.X, z = e.Z;
        WgLater((float)Math.Max(0, e.Delay - 0.25), () =>
        {
            for (int i = 0; i < 3; i++)
            {
                float a = R() * Mathf.Tau, d = 0.4f + R() * 0.8f;
                var at = V(x + Mathf.Cos(a) * d, Y(x + Mathf.Cos(a) * d, z + Mathf.Sin(a) * d) + 0.1, z + Mathf.Sin(a) * d);
                WgPuff(at, Vector3.Up * 0.4f, 0.3f, 1.5f, 0.6f, WgDust(0.8f), 0.4f, 2f);
            }
        });
        return true;
    }

    /// <summary>Impact's hook: a body the line or the heave kits itself.</summary>
    bool WgOwns(Ev.Hit e) =>
        e.Art is "slash_heavy" or "slash_quake" && wgOwned.TryGetValue(e.Target, out var f) && f == Engine.GetFramesDrawn();

    /// <summary>How long this blow's number waits for the view's blow (0: now).</summary>
    float WgHitWait(Ev.Hit e) =>
        e.Art is "slash_heavy" or "slash_quake" && !e.Dot && wgHitAt.TryGetValue(e.Target, out var at) && at > time + 0.001
            && wgOwned.TryGetValue(e.Target, out var f) && f == Engine.GetFramesDrawn() ? (float)(at - time) : 0;

    int wgNumLogged;
    void WgNumberLog(int id)
    {
        if (WgBeats && wgNumLogged++ < 40) GD.Print($"[wg-beats] number lands on {id} frame {Engine.GetFramesDrawn()} t={time:F3}");
    }

    /// <summary>CrowdView's flash for a body the line or the heave strikes: none until the blow lands, then the sim's
    /// own (1, down at 11 a second) from that moment.</summary>
    float? WgFlash(int id)
    {
        if (wgHitAt.Count == 0 || !wgHitAt.TryGetValue(id, out var at)) return null;
        double since = time - at;
        if (since < 0) return 0;
        if (since > 0.1) return null;
        return (float)Math.Max(0, 1 - since * 11);
    }

    string WgScr(double x, double z) => GetViewport()?.GetCamera3D() is { } cam ? $"{cam.UnprojectPosition(V(x, Y(x, z), z)).X:F0},{cam.UnprojectPosition(V(x, Y(x, z), z)).Y:F0}" : "-";

    void WgLater(float dt, Action fn)
    {
        if (dt <= 0.0001f) fn();
        else pending.Add((time + dt, fn));
    }

    /* ------------------------------------------------------------ crack -- */

    /// <summary>A crack from `from` along `dir`: tiles t0..t0+n-1 of the strip laid over `len`, each as the tip
    /// reaches it (`travel` s for the whole), `across` times the strip's width, with a hot edge on each tile's first
    /// frames, dust jets and chips along it; `life` s to its fade.</summary>
    void WgCrack(Vector2 from, Vector2 dir, float len, int t0, int n, float across, float travel, float life, bool night, bool heavy, bool sear = false)
    {
        float seg = len / n;
        // Along: tile metres to world metres; the tile's own crack centre (crack.json) scaled across.
        float alongK = seg / WgTile;
        float theta = Mathf.Atan2(-dir.Y, dir.X);
        var side = new Vector2(-dir.Y, dir.X); // the decal's local +Z (texture V increasing) turned by theta
        for (int i = 0; i < n; i++)
        {
            int tile = Math.Clamp(t0 + i, 0, 11);
            var c = from + dir * (seg * (i + 0.5f));
            float at = travel * i / n;
            float w = seg * 1.03f, b = WgBand * across;
            WgLater(at, () =>
            {
                var pos = V(c.X, Y(c.X, c.Y), c.Y);
                // (Sunder's strip darkened: its gap read 6-7 px on the verge's dark earth; 25-32 px at her end wanted)
                WgDecalOn(pos, theta, new Vector3(w, 1.6f, b), wgAlb![tile], wgNrm![tile], null, life, 1f, 0, 0, 0, heavy ? null : WgLineTint);
                // The hot edge: this tile's first 4 frames, dull orange; by night held low (never clipping).
                // Sunder's: a #FF8A3A core held 10 frames, then cooling over 12 (burning_edge: over 1.2 s).
                if (heavy) WgDecalOn(pos, theta, new Vector3(w, 1.6f, b), null, null, wgEmi![tile], 4 / 60f, 1f, night ? 0.7f : 1.3f, 0);
                else WgDecalOn(pos, theta, new Vector3(w, 1.6f, b), null, null, wgEmi![tile], 10 / 60f + (sear ? 1.2f : 12 / 60f), 1f, night ? 1.1f : 2.2f, 0, 10 / 60f, WgCore);
            });
        }
        // Dust jets and chips as the tip passes: denser and taller where the force is (her end; the heave's end).
        // (not evenly spaced: an even chain of like puffs read as a caterpillar; random places, some in pairs)
        int puffs = heavy ? Math.Clamp((int)(len * 2.0f), 6, 22) : 6 + (int)(R() * 2.99f);
        for (int i = 0; i < puffs; i++)
        {
            // (Sunder's 6-8 jets: spread along the line, one in each stretch, 1.0-1.5 m tall)
            float along = heavy ? Mathf.Pow(R(), 0.8f) * len : (i + 0.2f + R() * 0.6f) / puffs * len;
            float force = heavy ? 0.75f + 0.35f * along / len : 1.1f - 0.3f * along / len;
            var p = WgCrackPoint(from, dir, side, along, len, t0, n, across);
            if (heavy) WgLater(travel * along / len, () => WgJet(p, force));
            else WgLater(travel * along / len, () => WgTallJet(p, force));
        }
        if (!heavy && !Args.Has("wg-no-lips")) WgLipsAlong(from, dir, side, len, t0, n, across, travel, life);
        else
        {
            // Small stones popping off the path just behind the tip.
            int pops = 3 + (int)(R() * 2.99f);
            for (int i = 0; i < pops; i++)
            {
                float along = (0.15f + 0.8f * (i + R()) / pops) * len;
                var p = WgCrackPoint(from, dir, side, along, len, t0, n, across);
                WgLater(travel * along / len + 0.02f, () =>
                {
                    var v = new Vector3(R() - 0.5f, 0, R() - 0.5f) * 1.6f + Vector3.Up * (2.6f + R() * 1.4f);
                    WgThrow(p + Vector3.Up * 0.05f, v, 0.45f + R() * 0.25f, 1.1f + R() * 0.4f);
                });
            }
        }
        int chips = heavy ? Math.Clamp((int)(len * 1.3f), 8, 14) : 6 + (int)(R() * 4.99f);
        for (int i = 0; i < chips; i++)
        {
            float along = (0.08f + R() * 0.9f) * len;
            float force = heavy ? 1f : 1.05f - 0.4f * along / len;
            var p = WgCrackPoint(from, dir, side, along, len, t0, n, across);
            var s = side * (R() < 0.5f ? -1 : 1);
            WgLater(travel * along / len + R() * 0.03f, () =>
            {
                float h = (0.3f + R() * 0.5f) * force * (heavy ? 1.15f : 1f);
                var v = new Vector3(s.X, 0, s.Y) * (0.8f + R() * 1.6f) + new Vector3(dir.X, 0, dir.Y) * (R() - 0.3f) * 1.2f + Vector3.Up * Mathf.Sqrt(2 * 16 * h);
                WgThrow(p + Vector3.Up * 0.05f, v, (heavy ? 0.75f : 0.6f) + R() * 0.45f, 1.5f + R() * 0.5f);
            });
        }
    }

    /// <summary>The crack's own centre at `along` (m) on a crack laid from tiles t0..t0+n-1.</summary>
    Vector3 WgCrackPoint(Vector2 from, Vector2 dir, Vector2 side, float along, float len, int t0, int n, float across)
    {
        float u = (t0 + Mathf.Clamp(along / len, 0, 1) * n) / 12f;
        float off = 0;
        if (wgOff != null)
        {
            float k = Mathf.Clamp(u, 0, 1) * 255;
            int i = (int)k;
            off = Mathf.Lerp(wgOff[i], wgOff[Math.Min(255, i + 1)], k - i) * across;
        }
        var q = from + dir * along - side * off; // (centre_m runs toward V=0: the decal's -Z)
        return V(q.X, Y(q.X, q.Y), q.Y);
    }

    void WgDecalOn(Vector3 pos, float theta, Vector3 size, Texture2D? alb, Texture2D? nrm, Texture2D? emi, float life, float strength, float energy, float sear, float hold = 0, Color? col = null)
    {
        if (wgDecals.Count == 0) return;
        WgDecal? s = null;
        for (int k = 0; k < wgDecals.Count && s == null; k++)
        {
            var c = wgDecals[(wgDecalNext + k) % wgDecals.Count];
            if (!c.On) { s = c; wgDecalNext = (wgDecalNext + k + 1) % wgDecals.Count; }
        }
        s ??= wgDecals[wgDecalNext++ % wgDecals.Count];
        var d = s.D;
        d.TextureAlbedo = alb;
        d.TextureNormal = nrm;
        d.TextureEmission = emi;
        d.AlbedoMix = alb != null ? 0.92f : 0f;
        d.Position = pos;
        d.Rotation = new Vector3(0, theta, 0);
        d.Size = size;
        s.Glow = emi != null;
        var hc = col ?? (emi != null ? WgHot : Colors.White);
        d.Modulate = new Color(hc.R, hc.G, hc.B, 0);
        d.EmissionEnergy = s.Glow ? energy : 0;
        d.Visible = true;
        s.On = true; s.Age = 0; s.Life = life; s.FadeFrom = s.Glow ? life : life * 0.45f; s.Strength = strength; s.Energy = energy; s.Sear = sear;
        s.Hold = hold; s.Col = hc;
    }

    void WgStepDecals(float dt)
    {
        foreach (var s in wgDecals)
        {
            if (!s.On) continue;
            s.Age += dt;
            if (s.Age >= s.Life) { s.On = false; s.D.Visible = false; continue; }
            if (s.Glow)
            {
                // Hot for 4 frames (1, 0.7, 0.4, 0.15), then dark; burning_edge: a faint warm sear after, cooling.
                float f = s.Age * 60;
                if (s.Hold > 0)
                {
                    // Held, then cooling: its energy down and its colour toward a deep red as it goes.
                    float u = s.Age < s.Hold ? 0 : Mathf.Clamp((s.Age - s.Hold) / Mathf.Max(0.01f, s.Life - s.Hold), 0, 1);
                    float kh = (1 - u) * (1 - u);
                    s.D.EmissionEnergy = s.Energy * kh;
                    s.D.Modulate = new Color(s.Col.R, s.Col.G * (1 - 0.55f * u), s.Col.B * (1 - 0.8f * u), 0);
                    s.D.Visible = kh > 0.001f;
                    continue;
                }
                float k = f < 1 ? 1 : f < 2 ? 0.7f : f < 3 ? 0.4f : f < 4 ? 0.15f : 0;
                if (s.Sear > 0 && f >= 4) k = 0.12f * (1 - (s.Age - 4 / 60f) / Mathf.Max(0.01f, s.Life - 4 / 60f));
                s.D.EmissionEnergy = s.Energy * k;
                s.D.Visible = k > 0.001f;
                continue;
            }
            float a = s.Strength * Mathf.Min(1, s.Age / 0.03f) * (s.Age < s.FadeFrom ? 1 : 1 - Mathf.SmoothStep(0, 1, (s.Age - s.FadeFrom) / (s.Life - s.FadeFrom)));
            s.D.Modulate = new Color(s.Col.R, s.Col.G, s.Col.B, a);
        }
    }

    /* ------------------------------------------------------------ heave -- */

    void WgHeaveNow(double x, double z, float r, bool after)
    {
        wgHeaves++;
        if (after) wgAfters++;
        bool night = Flare.Night;
        float k = after ? 0.72f : 1f;
        if (WgBeats && !after && !wgGhShot && wgGcAt > 0) { wgGhShot = true; foreach (var f in new[] { 1, 6, 20, 60 }) Shots.WantFrames($"gh_f{f}", f); GD.Print($"[wg-beats] heave {wgHeaves} frame {Engine.GetFramesDrawn()} r {r:F2} at {x:F2},{z:F2} scr {WgScr(x, z)} her {b0?.Player.X:F2},{b0?.Player.Z:F2} t={time:F2}"); }
        if (WgBeats && after && !wgGaShot) { wgGaShot = true; foreach (var f in new[] { 1, 6, 20 }) Shots.WantFrames($"ga_f{f}", f); GD.Print($"[wg-beats] aftershock {wgAfters} t={time:F2}"); }
        var c = V(x, Y(x, z), z);
        Cam?.AddTrauma(after ? 0.08f : 0.18f);
        // Its own warm light from the heart: up in 2 frames, gone over 18; at its peak the ground within 2.5 m as
        // bright as her lamp's pool (shadowed: the slabs throw theirs outward).
        WgGlowOn(c + Vector3.Up * 1.3f, (float)Args.Num("wg-heave-light", 3.8f) * (after ? 0.6f : 1f));
        // The slabs: a ring of ground plates thrust up leaning out, and two or three at the heart, more upright;
        // 0.9-1.4 m standing (the aftershock's 0.65-1.0), 1.3x wider than the pieces, their tops fresh earth.
        int ring = after ? 5 : 7;
        float a0 = R() * Mathf.Tau;
        for (int i = 0; i < ring; i++)
        {
            float a = a0 + (i + (R() - 0.5f) * 0.6f) / ring * Mathf.Tau, d = r * (0.48f + R() * 0.22f) * (after ? 0.8f : 1f);
            float tilt = Mathf.DegToRad(55 + R() * 15), h = (0.9f + R() * 0.5f) * k;
            WgSlab(x + Mathf.Cos(a) * d, z + Mathf.Sin(a) * d, a, h / (0.7f * Mathf.Sin(tilt)), tilt, d / r * 0.06f);
        }
        int heart = after ? 2 : 3;
        for (int i = 0; i < heart; i++)
        {
            float a = a0 + 0.9f + i * Mathf.Tau / heart + (R() - 0.5f) * 0.8f, d = 0.15f + R() * 0.3f;
            float tilt = Mathf.DegToRad(68 + R() * 12), h = (1.1f + R() * 0.3f) * k;
            WgSlab(x + Mathf.Cos(a) * d, z + Mathf.Sin(a) * d, a, h / (0.7f * Mathf.Sin(tilt)), tilt, 0);
        }
        // Radial crater cracks, the narrow end of the strip (tiles 8-11) out from the heart, glowing #C8551E and
        // fading over 20 frames.
        int cracks = after ? 4 : 7;
        for (int i = 0; i < cracks; i++)
        {
            float a = a0 + 0.4f + (i + (R() - 0.5f) * 0.5f) / cracks * Mathf.Tau;
            var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
            float len = r * (0.75f + R() * 0.45f) * k;
            int t0 = 8 + (int)(R() * 1.99f);
            var from = new Vector2((float)x, (float)z) + dir * 0.1f;
            float theta = Mathf.Atan2(-dir.Y, dir.X), seg = len / 2;
            for (int j = 0; j < 2; j++)
            {
                var cc = from + dir * seg * (j + 0.5f);
                var pos = V(cc.X, Y(cc.X, cc.Y), cc.Y);
                var size = new Vector3(seg * 1.03f, 1.6f, WgBand * 1.15f * k);
                WgDecalOn(pos, theta, size, wgAlb![t0 + j], wgNrm![t0 + j], null, after ? 1.6f : 2.5f, 1f, 0, 0);
                WgDecalOn(pos, theta, size, null, null, wgEmi![t0 + j], 20 / 60f, 1f, (night ? 1.6f : 2.6f) * (after ? 0.75f : 1f), 0, 1 / 60f, WgCrater);
            }
        }
        // The dust wall: 24-32 puffs (the aftershock's 16-20) rolling out from the heart to 3.25 m (2.3 m) in 0.5 s,
        // 0.4-0.6 m tall, ground tan; a darker skirt under every other one.
        int puffs = after ? 16 + (int)(R() * 4.99f) : 26 + (int)(R() * 6.99f);
        float reachTo = after ? 2.3f : 3.25f;
        const float drag = 4f;
        for (int i = 0; i < puffs; i++)
        {
            // (gaps, clumps, sizes and reaches varied: an even ring of like puffs read as a donut)
            float a = a0 + (i + R() * 0.9f) / puffs * Mathf.Tau, d0 = 0.5f + R() * 0.4f;
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            float reach = reachTo * (0.88f + R() * 0.2f) - d0;
            // x(t) = v/D (1 - e^-Dt): there at 0.5 s (86% of the way), rolling on to rest a little past
            float v0 = reach * drag / (1 - Mathf.Exp(-drag * 0.5f)) * 0.93f;
            double px = x + o.X * d0, pz = z + o.Z * d0;
            float s = (0.36f + R() * 0.14f) * (after ? 0.85f : 1f);
            WgPuff(V(px, Y(px, pz) + 0.27, pz), o * v0 + Vector3.Up * (0.1f + R() * 0.15f), s, 1.3f, 0.95f + R() * 0.35f, WgDust(1.0f + R() * 0.15f), 0.76f, drag);
            if (i % 2 == 0)
                WgPuff(V(px, Y(px, pz) + 0.14, pz), o * v0 * 0.9f, s * 0.85f, 1.3f, 0.85f + R() * 0.3f, WgDust(0.78f), 0.72f, drag);
        }
        // The heart's lift: a short column of dust shoved up among the slabs.
        for (int i = 0; i < (after ? 2 : 4); i++)
        {
            var o = new Vector3(R() - 0.5f, 0, R() - 0.5f) * 0.8f;
            WgPuff(c + o + Vector3.Up * 0.4f, Vector3.Up * (1.4f + R() * 0.8f) * k + o, (0.5f + R() * 0.2f) * k, 1.7f, 0.8f + R() * 0.25f, WgDust(1.05f), 0.74f, 2.4f);
        }
        // 12-20 faceted, lit rocks (the aftershock's 6-9) thrown up and falling back, 0.2-0.45 m.
        int chunks = after ? 6 + (int)(R() * 3.99f) : 12 + (int)(R() * 8.99f);
        for (int i = 0; i < chunks; i++)
        {
            float a = R() * Mathf.Tau, d = r * 0.6f * Mathf.Sqrt(R());
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            double px = x + o.X * d, pz = z + o.Z * d;
            var v = o * (1.0f + R() * 2.4f) + Vector3.Up * (4.0f + R() * 3.5f) * (after ? 0.75f : 1f);
            WgThrow(V(px, Y(px, pz) + 0.2, pz), v, (1.0f + R() * 0.35f) * (after ? 0.85f : 1f), 2.0f + R() * 0.6f, 5);
        }
    }

    /// <summary>A plate of ground stood up at (x, z), its top leaning out along `a` (`tilt` from the ground), `len` m
    /// long, a third of it buried; up in 0.09 s, held 0.4 s, sunk over 0.5 s.</summary>
    void WgSlab(double x, double z, float a, float len, float tilt, float delay, float wide = 1.3f)
    {
        var rk = WgRockNext();
        if (rk == null || wgSlabs == null) return;
        int m = (int)(R() * wgSlabs.Length * 0.999f);
        rk.N.Mesh = wgSlabs[m];
        var outw = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
        var u = (outw * Mathf.Cos(tilt) + Vector3.Up * Mathf.Sin(tilt)).Normalized();
        var nrm = (-outw * Mathf.Sin(tilt) + Vector3.Up * Mathf.Cos(tilt)).Normalized();
        var third = u.Cross(nrm).Normalized();
        // The mesh's longest flat axis (X or Z) along u, its thin Y as the plate's face.
        var aabb = wgSlabs[m].GetAabb().Size;
        bool xLong = aabb.X >= aabb.Z;
        float sc = len / Mathf.Max(0.05f, wgSlabLen![m]);
        var basis = xLong ? new Godot.Basis(u, nrm, third) : new Godot.Basis(-third, nrm, u);
        basis = basis * new Godot.Basis(Vector3.Up, (R() - 0.5f) * 0.3f);
        rk.On = true; rk.Slab = true; rk.Age = -delay; rk.Life = 0.09f + 0.4f + 0.5f;
        rk.B = basis; rk.Scale = sc; rk.U = u; rk.L = len;
        // (1.3x wider than the piece's own across its face)
        rk.Local = xLong ? new Vector3(1, 1, wide) : new Vector3(wide, 1, 1);
        rk.Base = V(x, Y(x, z), z) + u * len * 0.2f;
        rk.N.Visible = false;
    }

    void WgThrow(Vector3 p, Vector3 v, float scale, float life, int minIdx = 0)
    {
        var rk = WgRockNext();
        var set = wgStones ?? wgChunks;
        if (rk == null || set == null) return;
        int m = minIdx + (int)(R() * (set.Length - minIdx) * 0.999f);
        m = Math.Clamp(m, 0, set.Length - 1);
        rk.N.Mesh = set[m];
        rk.On = true; rk.Slab = false; rk.Rested = false; rk.Age = 0; rk.Life = life; rk.Bounces = 0;
        rk.P = p; rk.V = v; rk.Scale = scale;
        rk.Axis = new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f).Normalized();
        rk.Spin = 6 + R() * 10;
        rk.B = new Godot.Basis(rk.Axis, R() * Mathf.Tau);
        rk.N.Visible = true;
        rk.N.Transform = new Transform3D(rk.B.Scaled(Vector3.One * scale), p);
    }

    WgRock? WgRockNext()
    {
        if (wgRocks.Count == 0) return null;
        for (int k = 0; k < wgRocks.Count; k++)
        {
            var c = wgRocks[(wgRockNext + k) % wgRocks.Count];
            if (!c.On) { wgRockNext = (wgRockNext + k + 1) % wgRocks.Count; return c; }
        }
        return wgRocks[wgRockNext++ % wgRocks.Count];
    }

    void WgStepRocks(float dt)
    {
        foreach (var c in wgRocks)
        {
            if (!c.On) continue;
            c.Age += dt;
            if (c.Age >= c.Life) { c.On = false; c.N.Visible = false; continue; }
            if (c.Slab)
            {
                if (c.Age < 0) continue;
                // Up (an overshoot of 6%), held, then sunk back along itself and a little more.
                float up = Mathf.Min(1, c.Age / 0.09f);
                float rise = up < 1 ? 1 - (1 - up) * (1 - up) * (1 - up) : 1 + 0.06f * Mathf.Sin(Mathf.Min(1, (c.Age - 0.09f) / 0.12f) * Mathf.Pi);
                float sink = Mathf.Clamp((c.Age - 0.49f) / 0.5f, 0, 1);
                sink *= sink;
                var at = c.Base - c.U * c.L * 0.85f * (1 - rise) - c.U * c.L * 0.9f * sink - Vector3.Up * 0.1f * sink;
                c.N.Visible = true;
                c.N.Transform = new Transform3D(c.B * Godot.Basis.FromScale(c.Local * c.Scale), at);
                continue;
            }
            float g = Y(c.P.X, c.P.Z);
            if (c.Bounces < 3)
            {
                c.V.Y -= 16 * dt;
                c.P += c.V * dt;
                if (c.P.Y < g + 0.04f && c.V.Y < 0)
                {
                    c.P.Y = g + 0.04f;
                    c.Bounces++;
                    c.V = new Vector3(c.V.X * 0.4f, -c.V.Y * 0.28f, c.V.Z * 0.4f);
                    c.Spin *= 0.35f;
                    if (c.V.Y < 0.6f) c.Bounces = 3;
                }
                if (c.Spin > 0.01f) c.B = new Godot.Basis(c.Axis, c.Spin * dt) * c.B;
            }
            float s = Mathf.SmoothStep(c.Life - 0.45f, c.Life, c.Age);
            c.N.Transform = new Transform3D(c.B.Orthonormalized().Scaled(Vector3.One * c.Scale), c.P - Vector3.Up * s * 0.25f);
        }
    }

    /* ------------------------------------------------------------- dust -- */

    /// <summary>Ground dust, lit by hand (the smoke batch is unshaded): brown-grey matched to the verge by day,
    /// dark by night; `lit` above 1 the sunlit top, below 1 the shadowed skirt.</summary>
    static readonly Color WgDustDay = new Color("#8c7558").SrgbToLinear() * new Color(0.95f, 0.95f, 0.75f) * (float)Args.Num("wg-dust-day", 1f),
        WgDustNight = new Color("#8c7558").SrgbToLinear() * (float)Args.Num("wg-dust-night", 0.7f);

    Color WgDust(float lit)
    {
        // (#8C7558 by day; by night the same tan held low but at least twice the dark ground's value)
        var c = Flare.Night ? WgDustNight : WgDustDay;
        return new Color(c.R * lit, c.G * lit, c.B * lit);
    }

    void WgPuff(Vector3 at, Vector3 v, float size, float grow, float life, Color col, float alpha, float drag)
    {
        if (WgNoDust) return;
        Smoke.Spawn(new Sparks.P
        {
            At = at, V = v, Drag = drag, Life = life, Size = size, SizeEnd = size * grow,
            Color = col, ColorEnd = col * 0.94f, Alpha = alpha, Sprite = SolidPuff(), Core = true, Spin = R() * Mathf.Tau,
        });
    }

    /// <summary>A jet of dust lifting off the crack as the tip passes: a lit plume 0.3-0.7 m tall over a darker foot.</summary>
    void WgJet(Vector3 p, float force)
    {
        // Sizes and lifts varied widely (a few tall spurts, more low bursts), thrown off either lip.
        bool spurt = R() < 0.3f;
        float s = (spurt ? 0.26f + R() * 0.12f : 0.3f + R() * 0.3f) * force;
        var lip = new Vector3(R() - 0.5f, 0, R() - 0.5f) * (spurt ? 0.4f : 1.2f);
        WgPuff(p + Vector3.Up * 0.1f + lip * 0.15f, Vector3.Up * (spurt ? 1.9f + R() * 0.9f : 0.6f + R() * 0.7f) * force + lip, s, spurt ? 2.2f : 1.8f, 0.5f + R() * 0.3f, WgDust(1.0f + R() * 0.2f), 0.78f, 2.6f);
        if (!spurt || R() < 0.5f)
            WgPuff(p + Vector3.Up * 0.05f, lip * 0.8f + Vector3.Up * 0.15f, s * (0.7f + R() * 0.3f), 1.6f, 0.55f + R() * 0.25f, WgDust(0.62f), 0.7f, 3f);
    }

    /// <summary>Sunder's jet: a column of tan dust 1.0-1.5 m tall off the line, a lit head over a darker foot.</summary>
    void WgTallJet(Vector3 p, float force)
    {
        float s = (0.34f + R() * 0.1f) * force;
        var lip = new Vector3(R() - 0.5f, 0, R() - 0.5f) * 0.5f;
        float up = (2.1f + R() * 0.9f) * force;
        WgPuff(p + Vector3.Up * 0.15f, Vector3.Up * up + lip, s, 1.9f, 0.3f, WgDust(1.0f + R() * 0.15f), 0.76f*0.7f, 2.4f);
        WgPuff(p + Vector3.Up * 0.1f, Vector3.Up * up * 0.55f + lip * 0.5f, s * 1.1f, 1.7f, 0.3f, WgDust(0.9f), 0.74f*0.7f, 2.6f);
        WgPuff(p + Vector3.Up * 0.05f, lip * 0.8f + Vector3.Up * 0.15f, s * 0.9f, 1.6f, 0.3f, WgDust(0.72f), 0.72f*0.7f, 3f);
    }

    static float WgGap(float u)
    {
        // crack.json gap_width_m_at_u
        float[] us = { 0, 0.05f, 0.25f, 0.5f, 0.75f, 0.93f, 0.98f, 1 };
        float[] ws = { 0.002f, 0.386f, 0.35f, 0.253f, 0.156f, 0.093f, 0.019f, 0.002f };
        for (int i = 1; i < us.Length; i++)
            if (u <= us[i]) return Mathf.Lerp(ws[i - 1], ws[i], (u - us[i - 1]) / (us[i] - us[i - 1]));
        return 0.002f;
    }

    /// <summary>Raised lips of earth (0.08-0.12 m) along both edges of a crack, up as the tip passes.</summary>
    void WgLipsAlong(Vector2 from, Vector2 dir, Vector2 side, float len, int t0, int n, float across, float travel, float life)
    {
        if (wgLips.Count == 0) return;
        int segs = Math.Clamp((int)(len / 0.55f), 3, 14);
        float seg = len / segs;
        for (int sd = -1; sd <= 1; sd += 2)
            for (int i = 0; i < segs; i++)
            {
                if (R() < 0.12f) continue; // (a few gaps: torn, not piped)
                float a0 = Mathf.Max(0, seg * (i + (R() - 0.5f) * 0.15f)), a1 = Mathf.Min(len, a0 + seg * (1.05f + R() * 0.25f));
                float u0 = (t0 + a0 / len * n) / 12f, u1 = (t0 + a1 / len * n) / 12f;
                var p0 = WgCrackPoint(from, dir, side, a0, len, t0, n, across);
                var p1 = WgCrackPoint(from, dir, side, a1, len, t0, n, across);
                var sd3 = new Vector3(side.X, 0, side.Y) * sd;
                p0 += sd3 * (WgGap(u0) * across * 0.5f + 0.01f);
                p1 += sd3 * (WgGap(u1) * across * 0.5f + 0.01f);
                var along = p1 - p0;
                along.Y = 0;
                float l = along.Length();
                if (l < 0.05f) continue;
                var x = along / l;
                var z = x.Cross(Vector3.Up);
                if (z.Dot(sd3) < 0) { (p0, p1) = (p1, p0); x = -x; z = x.Cross(Vector3.Up); }
                float h = 0.08f + R() * 0.04f, wide = 0.8f + R() * 0.4f;
                var lip = wgLips[wgLipNext++ % wgLips.Count];
                lip.On = true; lip.Age = -travel * a0 / len; lip.Life = life; lip.H = h;
                lip.T = new Transform3D(new Godot.Basis(x * l, Vector3.Up, z * wide), p0);
                lip.N.Visible = false;
            }
    }

    void WgStepLips(float dt)
    {
        foreach (var c in wgLips)
        {
            if (!c.On) continue;
            c.Age += dt;
            if (c.Age < 0) continue;
            if (c.Age >= c.Life) { c.On = false; c.N.Visible = false; continue; }
            // Up in 3 frames (a 10% overshoot), held; settled back down over the last 0.4 s.
            float up = Mathf.Min(1, c.Age / 0.05f);
            float k = up < 1 ? up * 1.1f : 1 + 0.1f * Mathf.Max(0, 1 - (c.Age - 0.05f) / 0.08f);
            k *= 1 - Mathf.SmoothStep(c.Life - 0.4f, c.Life, c.Age);
            var t = c.T;
            t.Basis = new Godot.Basis(t.Basis.X, Vector3.Up * Mathf.Max(0.002f, c.H * k), t.Basis.Z);
            c.N.Transform = t;
            c.N.Visible = true;
        }
    }

    /// <summary>The crack's tip as it runs: a small hot core with a glow behind it.</summary>
    void WgStepTips(float dt)
    {
        for (int i = wgTips.Count - 1; i >= 0; i--)
        {
            var tp = wgTips[i];
            tp.Age += dt;
            float u = tp.Age / Mathf.Max(0.02f, tp.Travel);
            if (u > 1.02f) { wgTips.RemoveAt(i); continue; }
            var p = WgCrackPoint(tp.From, tp.Dir, tp.Side, Mathf.Min(1, u) * tp.Len, tp.Len, tp.T0, tp.N, tp.Across) + Vector3.Up * 0.06f;
            var back = new Vector3(tp.Dir.X, 0, tp.Dir.Y) * -0.22f;
            bool night = Flare.Night;
            // the glow (30-40 px across) a touch behind, then the core (5-7 px)
            Sparks.Spawn(p + back, Vector3.Zero, 1.5f / 60f, 0.5f, new Color(WgTipCol.R * 1.6f, WgTipCol.G * 1.6f, WgTipCol.B * 1.6f), alpha: night ? 0.55f : 0.8f, sprite: -1);
            Sparks.Spawn(p, Vector3.Zero, 1.5f / 60f, 0.09f, new Color(WgTipCol.R * 2f, WgTipCol.G * 2f, WgTipCol.B * 2f), alpha: 1, sprite: -1);
        }
    }

    void WgGlowOn(Vector3 at, float peak)
    {
        var g = wgGlows.FirstOrDefault(x => !x.On) ?? wgGlows.FirstOrDefault();
        if (g == null) return;
        g.On = true; g.Age = 0; g.Peak = peak;
        g.L.Position = at;
        g.L.LightEnergy = 0;
        g.L.Visible = true;
    }

    /// <summary>The heave's light: up over 2 frames, held at peak to frame 12, decaying to zero by frame 30 (judge r2).</summary>
    void WgStepGlows(float dt)
    {
        foreach (var g in wgGlows)
        {
            if (!g.On) continue;
            g.Age += dt;
            float f = g.Age * 60;
            if (f >= 30) { g.On = false; g.L.Visible = false; g.L.LightEnergy = 0; continue; }
            float k = f < 2 ? (f + 1) / 3f : f < 12 ? 1f : Mathf.Pow(1 - (f - 12) / 18f, 1.6f);
            g.L.LightEnergy = g.Peak * k;
        }
    }

    /* ------------------------------------------------------------ bodies -- */

    void WgKit(int id, Vector3 away, bool full)
    {
        if (b0 == null || id < 0 || id >= b0.Enemies.Capacity) return;
        var en = b0.Enemies.Items[id];
        if (en == null) return;
        var (gx, gz) = CrowdView.Placed?.Invoke(en) ?? (en.X, en.Z);
        var at = V(gx, Y(gx, gz) + 1.0, gz);
        HitKit(at, away, BashSpark, 1f, false, full, away + Vector3.Up * 0.3f, id);
        if (full) ChipPuff(at + Vector3.Down * 0.6f, away, 1);
    }

    /* ------------------------------------------------------------- step -- */

    void StepWardenGround(float dt)
    {
        if (b0 == null) return;
        if (!wgWarm) WgWarmUp();
        if (Args.Has("wg-aftershock") && !wgWickSet && b0.Weapons.Exists(w => w.Id == "groundbreaker"))
        {
            wgWickSet = true;
            b0.SetWickPath("groundbreaker", new[] { "groundbreaker.aftershock.4" });
            GD.Print("[wg-beats] aftershock lit");
        }
        if (wgOwned.Count > 64) { long f = Engine.GetFramesDrawn(); foreach (var k in wgOwned.Where(kv => kv.Value != f).Select(kv => kv.Key).ToList()) wgOwned.Remove(k); }
        WgStepDecals(dt);
        WgStepRocks(dt);
        WgStepLips(dt);
        WgStepTips(dt);
        WgStepGlows(dt);
        if (wgHitAt.Count > 0 && Engine.GetFramesDrawn() % 30 == 0) foreach (var k in wgHitAt.Where(kv => time - kv.Value > 1).Select(kv => kv.Key).ToList()) wgHitAt.Remove(k);
    }
}
