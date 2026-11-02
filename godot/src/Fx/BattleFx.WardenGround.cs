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
    }

    sealed class WgRock
    {
        public required MeshInstance3D N;
        public bool On, Slab, Rested;
        public Vector3 P, V, Axis, Base, U;
        public Godot.Basis B;
        public float Age, Life, Spin, Scale, L, Hold, Delay;
        public int Bounces;
    }

    readonly List<WgDecal> wgDecals = new();
    readonly List<WgRock> wgRocks = new();
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

    const int WgDecalPool = 112, WgRockPool = 80;
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
            var n = new MeshInstance3D { Mesh = wgChunks![i % wgChunks.Length], Visible = false, CastShadow = GeometryInstance3D.ShadowCastingSetting.On };
            AddChild(n);
            wgRocks.Add(new WgRock { N = n });
        }
    }

    static void WgLoadChunks()
    {
        var list = new List<(Mesh M, float Len)>();
        const string path = WgDir + "chunks.glb";
        if (ResourceLoader.Exists(path) && GD.Load<PackedScene>(path) is { } ps)
        {
            var root = ps.Instantiate();
            foreach (var n in root.FindChildren("*", "MeshInstance3D", true, false))
                if (((MeshInstance3D)n).Mesh is { } m)
                {
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
        wgSlabs = big.Select(x => x.M).ToArray();
        wgSlabLen = big.Select(x => x.Len).ToArray();
    }

    /* ------------------------------------------------------------ hooks -- */

    /// <summary>Sunder's heavy line and Groundbreaker's crack (Lance's hook); false for any other beam.</summary>
    bool WgBeam(Ev.Beam e)
    {
        if (e.Art is not ("slash_heavy_line" or "slash_quake_crack")) return false;
        if (!wgWarm) WgWarmUp();
        bool quake = e.Art == "slash_quake_crack";
        var from = new Vector2((float)e.X0, (float)e.Z0);
        var to = new Vector2((float)e.X1, (float)e.Z1);
        float len = from.DistanceTo(to);
        if (len < 0.3f) return true;
        var dir = (to - from) / len;
        float travel = quake ? Mathf.Min((float)Math.Max(0.12, e.Duration), 0.06f + len * 0.028f) : 0.12f;
        bool night = Flare.Night;
        if (quake)
        {
            wgEnds.Add((e.X1, e.Z1, time, time + travel));
            wgCracks++;
            if (WgBeats && !wgGcShot && time > 4) { wgGcShot = true; wgGcAt = time; Shots.WantFrames("gc_f3", 3); Shots.WantFrames("gc_f12", 12); GD.Print($"[wg-beats] crack {wgCracks} len {len:F1} travel {travel:F2} t={time:F2}"); }
            // (twin: the second of a pair takes a different run of the strip)
            int t0 = wgEnds.Count(x => x.At == time) > 1 ? 1 : 0;
            int n = Math.Clamp((int)Mathf.Round(len / 1.7f), 2, 6);
            WgCrack(from, dir, len, t0, n, 1.05f, travel, 2.6f, night, true);
            Cam?.AddTrauma(0.05f);
        }
        else
        {
            wgLines++;
            if (WgBeats && !wgSlShot && time > 4) { wgSlShot = true; Shots.WantFrames("sl_f2", 2); Shots.WantFrames("sl_f8", 8); Shots.WantFrames("sl_f30", 30); GD.Print($"[wg-beats] line {wgLines} len {len:F1} t={time:F2}"); }
            bool sear = b0?.Lamps is { } lp && lp.Has("sunder.burning_edge");
            // Tiles 6-11 (the strip's narrowing half: 0.25 m at her end, closing to a hairline) over the line.
            WgCrack(from, dir, len, 6, 6, 1f, travel, 1.8f, night, false, sear);
            Cam?.AddTrauma(0.08f);
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
                WgLater(Mathf.Clamp(along / len, 0, 1) * travel, () => WgKit(id, awayDir, full));
            }
        }
        return true;
    }

    /// <summary>Groundbreaker's heave (the Explosion switch's own case): held until its crack's tip arrives.</summary>
    void WgHeave(Ev.Explosion e)
    {
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
                WgDecalOn(pos, theta, new Vector3(w, 1.6f, b), wgAlb![tile], wgNrm![tile], null, life, 1f, 0, 0);
                // The hot edge: this tile's first 4 frames, dull orange; by night held low (never clipping).
                WgDecalOn(pos, theta, new Vector3(w, 1.6f, b), null, null, wgEmi![tile], 4 / 60f + (sear ? 1.2f : 0), 1f, night ? 1.1f : 2.4f, sear ? 1 : 0);
            });
        }
        // Dust jets and chips as the tip passes: denser and taller where the force is (her end; the heave's end).
        float step = heavy ? 0.36f : 0.44f;
        int puffs = Math.Clamp((int)(len / step), 6, heavy ? 30 : 20);
        for (int i = 0; i < puffs; i++)
        {
            float along = (i + 0.3f + R() * 0.4f) * len / puffs;
            float force = heavy ? 0.75f + 0.35f * along / len : 1.1f - 0.45f * along / len;
            var p = WgCrackPoint(from, dir, side, along, len, t0, n, across);
            WgLater(travel * along / len, () => WgJet(p, force));
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
        var q = from + dir * along + side * off;
        return V(q.X, Y(q.X, q.Y), q.Y);
    }

    void WgDecalOn(Vector3 pos, float theta, Vector3 size, Texture2D? alb, Texture2D? nrm, Texture2D? emi, float life, float strength, float energy, float sear)
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
        d.Modulate = s.Glow ? new Color(WgHot.R, WgHot.G, WgHot.B, 0) : new Color(1, 1, 1, 0);
        d.EmissionEnergy = s.Glow ? energy : 0;
        d.Visible = true;
        s.On = true; s.Age = 0; s.Life = life; s.FadeFrom = s.Glow ? life : life * 0.45f; s.Strength = strength; s.Energy = energy; s.Sear = sear;
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
                float k = f < 1 ? 1 : f < 2 ? 0.7f : f < 3 ? 0.4f : f < 4 ? 0.15f : 0;
                if (s.Sear > 0 && f >= 4) k = 0.12f * (1 - (s.Age - 4 / 60f) / Mathf.Max(0.01f, s.Life - 4 / 60f));
                s.D.EmissionEnergy = s.Energy * k;
                s.D.Visible = k > 0.001f;
                continue;
            }
            float a = s.Strength * Mathf.Min(1, s.Age / 0.03f) * (s.Age < s.FadeFrom ? 1 : 1 - Mathf.SmoothStep(0, 1, (s.Age - s.FadeFrom) / (s.Life - s.FadeFrom)));
            s.D.Modulate = new Color(1, 1, 1, a);
        }
    }

    /* ------------------------------------------------------------ heave -- */

    void WgHeaveNow(double x, double z, float r, bool after)
    {
        wgHeaves++;
        if (after) wgAfters++;
        bool night = Flare.Night;
        float k = after ? 0.6f : 1f;
        if (WgBeats && !after && !wgGhShot && wgGcAt > 0) { wgGhShot = true; foreach (var f in new[] { 1, 6, 20, 60 }) Shots.WantFrames($"gh_f{f}", f); GD.Print($"[wg-beats] heave {wgHeaves} r {r:F2} t={time:F2}"); }
        if (WgBeats && after && !wgGaShot) { wgGaShot = true; Shots.WantFrames("ga_f6", 6); GD.Print($"[wg-beats] aftershock {wgAfters} t={time:F2}"); }
        var c = V(x, Y(x, z), z);
        Cam?.AddTrauma(after ? 0.08f : 0.18f);
        // The slabs: a ring of ground plates thrust up leaning out, and two or three at the heart, more upright.
        int ring = after ? 4 : 7;
        float a0 = R() * Mathf.Tau;
        for (int i = 0; i < ring; i++)
        {
            float a = a0 + (i + (R() - 0.5f) * 0.6f) / ring * Mathf.Tau, d = r * (0.48f + R() * 0.22f) * (after ? 0.8f : 1f);
            WgSlab(x + Mathf.Cos(a) * d, z + Mathf.Sin(a) * d, a, (1.0f + R() * 0.4f) * k, Mathf.DegToRad(55 + R() * 15), d / r * 0.06f);
        }
        int heart = after ? 1 : 3;
        for (int i = 0; i < heart; i++)
        {
            float a = a0 + 0.9f + i * Mathf.Tau / heart + (R() - 0.5f) * 0.8f, d = 0.15f + R() * 0.3f;
            WgSlab(x + Mathf.Cos(a) * d, z + Mathf.Sin(a) * d, a, (1.25f + R() * 0.3f) * k, Mathf.DegToRad(68 + R() * 12), 0);
        }
        // Radial crater cracks, the narrow end of the strip (tiles 8-11) out from the heart; a hot edge 4 frames.
        int cracks = after ? 3 : 7;
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
                WgDecalOn(pos, theta, size, null, null, wgEmi![t0 + j], 4 / 60f, 1f, night ? 1.0f : 2.2f, 0);
            }
        }
        // The dust ring: low, solid and lit, rolling out to ~1.3 r over ~1 s; a darker skirt under it.
        int puffs = after ? 12 : 26;
        for (int i = 0; i < puffs; i++)
        {
            float a = a0 + (i + R() * 0.7f) / puffs * Mathf.Tau, d0 = r * (0.35f + R() * 0.2f);
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            float reach = r * (1.2f + R() * 0.2f) * k - d0, drag = 2.6f;
            double px = x + o.X * d0, pz = z + o.Z * d0;
            float s = (0.7f + R() * 0.35f) * k;
            WgPuff(V(px, Y(px, pz) + 0.3 * k, pz), o * reach * drag * 1.05f + Vector3.Up * (0.25f + R() * 0.3f), s, 1.9f, 0.9f + R() * 0.3f, WgDust(1.05f + R() * 0.15f), 0.62f, drag);
            if (i % 2 == 0)
                WgPuff(V(px, Y(px, pz) + 0.15, pz), o * reach * drag * 0.8f, s * 0.8f, 1.7f, 0.8f + R() * 0.3f, WgDust(0.68f), 0.55f, drag);
        }
        // The heart's lift: a short column of dust shoved up among the slabs.
        for (int i = 0; i < (after ? 2 : 5); i++)
        {
            var o = new Vector3(R() - 0.5f, 0, R() - 0.5f) * 0.8f;
            WgPuff(c + o + Vector3.Up * 0.4f, Vector3.Up * (1.6f + R() * 1.0f) * k + o, (0.6f + R() * 0.25f) * k, 1.8f, 0.8f + R() * 0.25f, WgDust(1.1f), 0.58f, 2.4f);
        }
        // Chunks thrown up and falling back.
        int chunks = after ? 5 : 13;
        for (int i = 0; i < chunks; i++)
        {
            float a = R() * Mathf.Tau, d = r * 0.6f * Mathf.Sqrt(R());
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            double px = x + o.X * d, pz = z + o.Z * d;
            var v = o * (1.0f + R() * 2.4f) + Vector3.Up * (4.0f + R() * 3.5f) * (after ? 0.75f : 1f);
            WgThrow(V(px, Y(px, pz) + 0.2, pz), v, (0.9f + R() * 0.7f) * k, 2.0f + R() * 0.6f);
        }
    }

    /// <summary>A plate of ground stood up at (x, z), its top leaning out along `a` (`tilt` from the ground), `len` m
    /// long, a third of it buried; up in 0.09 s, held 0.4 s, sunk over 0.5 s.</summary>
    void WgSlab(double x, double z, float a, float len, float tilt, float delay)
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
        rk.Base = V(x, Y(x, z), z) + u * len * 0.2f;
        rk.N.Visible = false;
    }

    void WgThrow(Vector3 p, Vector3 v, float scale, float life)
    {
        var rk = WgRockNext();
        if (rk == null || wgChunks == null) return;
        int m = (int)(R() * wgChunks.Length * 0.999f);
        rk.N.Mesh = wgChunks[m];
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
                c.N.Transform = new Transform3D(c.B.Scaled(Vector3.One * c.Scale), at);
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
    Color WgDust(float lit)
    {
        var c = Flare.Night ? new Color(0.13f, 0.122f, 0.125f) : new Color(0.4f, 0.335f, 0.262f);
        return new Color(c.R * lit, c.G * lit, c.B * lit);
    }

    void WgPuff(Vector3 at, Vector3 v, float size, float grow, float life, Color col, float alpha, float drag)
    {
        Smoke.Spawn(new Sparks.P
        {
            At = at, V = v, Drag = drag, Life = life, Size = size, SizeEnd = size * grow,
            Color = col, ColorEnd = col * 0.94f, Alpha = alpha, Sprite = SolidPuff(), Core = true, Spin = R() * Mathf.Tau,
        });
    }

    /// <summary>A jet of dust lifting off the crack as the tip passes: a lit plume 0.3-0.7 m tall over a darker foot.</summary>
    void WgJet(Vector3 p, float force)
    {
        float s = (0.34f + R() * 0.16f) * force;
        WgPuff(p + Vector3.Up * 0.12f, Vector3.Up * (0.9f + R() * 0.7f) * force + new Vector3(R() - 0.5f, 0, R() - 0.5f) * 0.4f, s, 1.8f, 0.5f + R() * 0.3f, WgDust(1.08f + R() * 0.12f), 0.6f, 2.6f);
        WgPuff(p + Vector3.Up * 0.06f, new Vector3(R() - 0.5f, 0.2f, R() - 0.5f) * 0.6f, s * 0.85f, 1.6f, 0.55f + R() * 0.25f, WgDust(0.7f), 0.5f, 3f);
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
            b0.SetWickPath("groundbreaker", new[] { "groundbreaker.aftershock" });
            GD.Print("[wg-beats] aftershock lit");
        }
        if (wgOwned.Count > 64) { long f = Engine.GetFramesDrawn(); foreach (var k in wgOwned.Where(kv => kv.Value != f).Select(kv => kv.Key).ToList()) wgOwned.Remove(k); }
        WgStepDecals(dt);
        WgStepRocks(dt);
    }
}
