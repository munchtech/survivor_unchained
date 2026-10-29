using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// What the ground shader and the grass read besides the zone's own paint,
/// made once per zone at load (look bible 1f, "The trick" 4 and 5):
///
/// <para>The paint, reconciled: thin mud strokes (the web game's ruts, a texel
/// or two wide, which read as black slashes) are opened away, and along each
/// road the dirt is repainted as the road's own soft verge.</para>
///
/// <para>A mask over the zone, as the paint is laid: R the road's made
/// surface (0.8; its centre strip above that, to 1, where sparse grass shows), G the wheel
/// ruts (depth, 0-1), B wetness (concave ground from the heights' curvature,
/// the ruts, the gutters at wall bases), A where puddles may stand.</para>
/// </summary>
public sealed class GroundPaint
{
    public readonly Image Splat;
    public readonly Image Mask;
    /// <summary>The frost's exposure (look bible 1f, "The trick" 5) and the meadow's lows, RGBA8 over the zone at a
    /// quarter metre: R the open sky (0 under a crown, by a wall and under its eaves; 1 in the open; blurred about a
    /// metre), G the sun on the ground for the thaw (0 in the shade of a crown or a wall at the key's angle; baked by
    /// SunAt), B the lie of the land over 10-40 m (0.5 level; up to 1 in a damp low, down to 0 on a dry rise).</summary>
    public ImageTexture Exposure => exposure ??= ImageTexture.CreateFromImage(Image.CreateFromData(er, er, false, Image.Format.Rgba8, exposurePx));
    ImageTexture? exposure;
    byte[] exposurePx;
    /// <summary>The sun the exposure was baked for (SunAt; null: none yet).</summary>
    Vector3? baked;

    static readonly ConditionalWeakTable<ZoneData, GroundPaint> Made = new();
    static GroundPaint? latest;
    static Vector3? sun;

    public static GroundPaint Of(ZoneData z)
    {
        var p = latest = Made.GetValue(z, k => new GroundPaint(k));
        // Made ahead (Ready), the sun may have moved since: baked again for it, as it would have been made now.
        if (sun is Vector3 s && p.baked != s) { Perf.Lap("ground paint: (before)"); p.BakeSun(s); Perf.Lap("ground paint: baked again for the sun"); }
        return p;
    }

    /// <summary>The paint worked out ahead of its place being built, on a worker thread (Game.Prepare): it is the
    /// latest only once its place is built (Of). Its textures are made on the main thread as they are first asked for.</summary>
    public static void Ready(ZoneData z) => Made.GetValue(z, k => new GroundPaint(k));

    /// <summary>The zone's paint, without making it the latest (a place built ahead: Of makes it so once it is added).</summary>
    public static GroundPaint Ahead(ZoneData z) => Made.GetValue(z, k => new GroundPaint(k));

    /// <summary>The thaw's sun (toward the light): the latest zone's sun on the ground is baked for it.</summary>
    public static void SunAt(Vector3 dir)
    {
        if (dir.Y < 0.05f || sun is Vector3 was && was.AngleTo(dir) < 0.02f) return;
        sun = dir;
        if (latest == null) return;
        // Baked ahead for this sun (SunAhead): taken (waited for, if it is not done: no longer than baking it here).
        int k = latest.sunsAhead.FindIndex(a => a.Dir.AngleTo(dir) < 1e-4f);
        if (k >= 0)
        {
            var px = latest.sunsAhead[k].Px.Result;
            latest.sunsAhead.RemoveAt(k);
            latest.TakeSun(dir, px);
            return;
        }
        latest.BakeSun(dir);
    }

    /// <summary>The thaw's sun baked ahead for the latest zone on a worker thread (a cinematic about to bring up a
    /// dawn: Game.Cine.SunAhead), so SunAt only takes it. Its result is the same as SunAt baking it then.</summary>
    public static void SunAhead(Vector3 dir)
    {
        if (latest is not { } p || dir.Y < 0.05f || p.baked is Vector3 b && b.AngleTo(dir) < 1e-4f
            || p.sunsAhead.Exists(a => a.Dir.AngleTo(dir) < 1e-4f)) return;
        // (a few at most: a cinematic's suns; the oldest let go)
        if (p.sunsAhead.Count >= 4) p.sunsAhead.RemoveAt(0);
        p.sunsAhead.Add((dir, System.Threading.Tasks.Task.Run(() => p.SunPx(dir))));
    }

    readonly List<(Vector3 Dir, System.Threading.Tasks.Task<byte[]> Px)> sunsAhead = new();

    // Tunable from the command line for sweeps (SurvivorUnchained.Args).
    internal static readonly float RoadHalf = Args.Num("road-half", 1.55f);      // the made surface, half its width
    internal static readonly float VergeW = Args.Num("road-verge", 1.5f);        // trodden earth beyond it
    internal static readonly float RutOff = Args.Num("road-rut-off", 0.75f);     // each rut from the centre
    // A rut (judge 1, E3 fix 1): a core 0.25-0.4 m wide, then a 0.15 m feathered shoulder; the gauge 1.4-1.5 m.
    internal static readonly float RutCore = Args.Num("road-rut-core", 0.16f);    // half the core's width
    internal static readonly float RutFeather = Args.Num("road-rut-feather", 0.15f);
    internal static readonly float ClearingSoft = Args.Num("clearing-soft", 2.2f);  // a clearing's dirt edge blurred over this (m)
    internal static readonly float PoolEvery = Args.Num("pool-every", 0f);   // open setts: one puddle in this many square metres (0: none)
    internal static readonly bool PoolsOn = !Args.Has("no-pools");
    internal static float RutW => RutCore + RutFeather * 0.5f;                       // a rut's half width, to its shoulder's middle

    /// <summary>The zone's roads as point lists with their base half width (the scatter walks the same ones).</summary>
    internal static List<(Vector2[] P, float Half)> RoadPaths(ZoneData z)
    {
        var paths = new List<(Vector2[] P, float Half)>();
        foreach (var (key, pts) in z.Meta.Paths)
        {
            // The roads; their keys and the streams are not, nor a generated map's WAY (its ways
            // run together into one list) or an arena's RIM.
            if (key.EndsWith("_KEYS") || key.Contains("STREAM") || key is "WAY" or "RIM" || pts.Length < 2) continue;
            var p = new Vector2[pts.Length];
            for (int i = 0; i < pts.Length; i++) p[i] = new Vector2((float)pts[i][0], (float)pts[i][1]);
            paths.Add((p, key.Contains("RUT") ? RoadHalf * 0.75f : RoadHalf));
        }
        return paths;
    }

    /// <summary>The width wanders, as a road worn by use does.</summary>
    internal static float HalfWidth(float hw0, float s) =>
        hw0 * (1f + 0.16f * Mathf.Sin(s * 0.093f + 1.3f) + 0.08f * Mathf.Sin(s * 0.41f));

    /// <summary>How far the ruts wander off the centre line, the left and right together.</summary>
    internal static float RutShift(float s) => 0.18f * Mathf.Sin(s * 0.057f + 0.4f);

    /// <summary>Each rut's distance from the centre line, for a road of this (wandered) half width.</summary>
    internal static float RutHalf(float hw) => RutOff * (hw / RoadHalf > 0.9f ? 1f : 0.8f);

    /// <summary>A hash of (i, seed) in 0-1.</summary>
    static float Hash(int i, int seed)
    {
        uint h = (uint)i * 0x9E3779B1u ^ (uint)seed * 0x85EBCA77u;
        h ^= h >> 15; h *= 0x2C1B3C6Du; h ^= h >> 12; h *= 0x297A2D39u; h ^= h >> 15;
        return (h & 0xFFFFFF) / (float)0x1000000;
    }

    /// <summary>Smooth value noise along a line, -1 to 1, one knot a unit.</summary>
    static float Wander(float x, int seed)
    {
        int i = (int)Math.Floor(x);
        float f = x - i;
        f = f * f * (3 - 2 * f);
        return Mathf.Lerp(Hash(i, seed), Hash(i + 1, seed), f) * 2 - 1;
    }

    /// <summary>A rut along s on one side (0, 1): its depth (0.42-1: plus or minus 40% over 3-6 m), with a gap of a
    /// metre or two every 20 m or so (a firm patch); `spot` 1 where water stands in it (one stretch in most 20 m).</summary>
    internal static float RutAlong(float s, int sd, out float spot)
    {
        float depth = 0.71f + 0.29f * (0.65f * Wander(s / 4.5f, 11 + sd) + 0.35f * Wander(s / 2.7f, 31 + sd)) / 1.0f;
        int k = (int)Math.Floor(s / 20f);
        float gap = 1;
        for (int q = k - 1; q <= k + 1; q++)
        {
            float gc = (q + 0.2f + 0.6f * Hash(q, 21 + sd)) * 20f, gl = 0.5f + 0.5f * Hash(q, 23 + sd);
            gap = Math.Min(gap, Mathf.SmoothStep(gl * 0.5f, gl * 0.5f + 0.9f, Math.Abs(s - gc)));
        }
        spot = 0;
        for (int q = k - 1; q <= k + 1; q++)
        {
            if (Hash(q, 41 + sd) > 0.7f) continue;
            float wc = (q + 0.1f + 0.8f * Hash(q, 43 + sd)) * 20f, wl = 0.6f + 0.9f * Hash(q, 47 + sd);
            spot = Math.Max(spot, 1f - Mathf.SmoothStep(wl * 0.5f, wl * 0.5f + 0.35f, Math.Abs(s - wc)));
        }
        return Math.Clamp(depth, 0.3f, 1f) * gap;
    }

    GroundPaint(ZoneData z)
    {
        float size = z.Size, half = z.Half;
        var paths = RoadPaths(z);

        int mr = paths.Count > 0 ? 2048 : 1024;
        float mt = size / mr;
        // Distance to the nearest road's centre line (signed: left negative),
        // the distance along it, and that road's half width.
        var dist = new float[mr * mr];
        var side = new float[mr * mr];
        var along = new float[mr * mr];
        var hwOf = new float[mr * mr];
        Array.Fill(dist, 1e9f);
        float reach = RoadHalf + VergeW + 3f;
        foreach (var (p, hw0) in paths)
        {
            float s0 = 0;
            for (int k = 0; k < p.Length - 1; k++)
            {
                Vector2 a = p[k], b = p[k + 1], ab = b - a;
                float len = ab.Length();
                if (len < 1e-4f) continue;
                Vector2 dir = ab / len;
                int i0 = Math.Max(0, (int)((Math.Min(a.X, b.X) - reach + half) / mt)), i1 = Math.Min(mr - 1, (int)((Math.Max(a.X, b.X) + reach + half) / mt));
                int j0 = Math.Max(0, (int)((Math.Min(a.Y, b.Y) - reach + half) / mt)), j1 = Math.Min(mr - 1, (int)((Math.Max(a.Y, b.Y) + reach + half) / mt));
                for (int j = j0; j <= j1; j++)
                    for (int i = i0; i <= i1; i++)
                    {
                        var w = new Vector2(-half + (i + 0.5f) * mt, -half + (j + 0.5f) * mt);
                        Vector2 ap = w - a;
                        float t = Math.Clamp(ap.Dot(dir), 0, len);
                        Vector2 q = ap - dir * t;
                        float d = q.Length();
                        int at = j * mr + i;
                        if (d >= dist[at]) continue;
                        dist[at] = d;
                        side[at] = dir.X * ap.Y - dir.Y * ap.X;
                        along[at] = s0 + t;
                        hwOf[at] = hw0;
                    }
                s0 += len;
            }
        }

        // Concave ground from the heights (one sample a metre), blurred.
        int n = z.Res;
        float st = z.Step;
        var lap = new float[n * n];
        var h = z.Heights;
        for (int j = 1; j < n - 1; j++)
            for (int i = 1; i < n - 1; i++)
            {
                int c = j * n + i;
                lap[c] = (h[c - 1] + h[c + 1] + h[c - n] + h[c + n] - 4 * h[c]) / (st * st);
            }
        var lap0 = lap;
        lap = Blur(Blur(lap, n, 2), n, 2);

        // The gutters: wall and building bases (not a heap of rubble: props_own.json no_gutter; E7b judge, a wet black square round the post's heaps).
        var boxes = new List<ColliderDef>();
        foreach (var c in z.Meta.Colliders)
            if (c.Kind == ColliderKind.Box && !c.Soft && Math.Min(c.Hw, c.Hd) >= 0.4 && !Heap(c)) boxes.Add(c);
        bool Heap(ColliderDef c) => OwnProps.For(z.Id)?.NoGutter is { } ng && ng.Exists(g => Math.Abs(g.X - c.X) < 0.5 && Math.Abs(g.Y - c.Z) < 0.5);
        var gut = new float[mr * mr];
        foreach (var c in boxes)
        {
            float rr = (float)Math.Sqrt(c.Hw * c.Hw + c.Hd * c.Hd) + 1.4f;
            int i0 = Math.Max(0, (int)(((float)c.X - rr + half) / mt)), i1 = Math.Min(mr - 1, (int)(((float)c.X + rr + half) / mt));
            int j0 = Math.Max(0, (int)(((float)c.Z - rr + half) / mt)), j1 = Math.Min(mr - 1, (int)(((float)c.Z + rr + half) / mt));
            double cos = Math.Cos(-c.Rot), sin = Math.Sin(-c.Rot);
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    double x = -half + (i + 0.5) * mt - c.X, zz = -half + (j + 0.5) * mt - c.Z;
                    double lx = Math.Abs(x * cos - zz * sin) - c.Hw, lz = Math.Abs(x * sin + zz * cos) - c.Hd;
                    double o = Math.Sqrt(Math.Max(lx, 0) * Math.Max(lx, 0) + Math.Max(lz, 0) * Math.Max(lz, 0));
                    if (lx < 0 && lz < 0) continue;
                    float g = 1f - Mathf.SmoothStep(0.15f, 1.1f, (float)o);
                    int at = j * mr + i;
                    if (g > gut[at]) gut[at] = g;
                }
        }

        // Puddles (judge 1, E3 fix 7): standing water 0.4-1.5 m across in the gutters along the walls, every few
        // metres, and the odd one in a low joint of open setts. Seeded, so a zone is the same every load.
        var pools = new float[mr * mr];
        var prng = new Random(77);
        float PU(float lo, float hi) => lo + (hi - lo) * (float)prng.NextDouble();
        bool Clear(float x, float zz)
        {
            if (Math.Abs(x) > half - 1 || Math.Abs(zz) > half - 1 || z.Meta.WaterAt(x, zz)) return false;
            foreach (var c in z.Meta.Colliders)
                if (!c.Soft && (c.Kind == ColliderKind.Box ? BoxOut(c, x, zz) : (float)Math.Sqrt((x - c.X) * (x - c.X) + (zz - c.Z) * (zz - c.Z)) - (float)c.R) < 0.15f) return false;
            return true;
        }
        void Pool(Vector2 at, Vector2 dir, float ra, float rb)
        {
            if (!Clear(at.X, at.Y)) return;
            float rr = Math.Max(ra, rb) + 0.3f;
            int i0 = Math.Max(0, (int)((at.X - rr + half) / mt)), i1 = Math.Min(mr - 1, (int)((at.X + rr + half) / mt));
            int j0 = Math.Max(0, (int)((at.Y - rr + half) / mt)), j1 = Math.Min(mr - 1, (int)((at.Y + rr + half) / mt));
            var nn = new Vector2(-dir.Y, dir.X);
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    var q = new Vector2(-half + (i + 0.5f) * mt, -half + (j + 0.5f) * mt) - at;
                    float u = q.Dot(dir) / ra, v = q.Dot(nn) / rb, e = Mathf.Sqrt(u * u + v * v);
                    float g = 1f - Mathf.SmoothStep(0.55f, 1.05f, e);
                    int at2 = j * mr + i;
                    if (g > pools[at2]) pools[at2] = g;
                }
        }
        if (PoolsOn)
        {
            var zimg = (Image)z.Splat.Duplicate();
            zimg.Convert(Image.Format.Rgba8);
            var zs = zimg.GetData();
            int zr = zimg.GetWidth();
            bool OnSetts(Vector2 p)
            {
                int si = Math.Clamp((int)((p.X + half) / size * zr), 0, zr - 1), sj = Math.Clamp((int)((p.Y + half) / size * zr), 0, zr - 1);
                return zs[(sj * zr + si) * 4 + 1] >= 160;
            }
            foreach (var c in boxes)
            {
                if (Math.Max(c.Hw, c.Hd) < 2.0) continue;
                double cs = Math.Cos(c.Rot), sn = Math.Sin(c.Rot);
                Vector2 W(double lx, double lz) => new((float)(c.X + lx * cs - lz * sn), (float)(c.Z + lx * sn + lz * cs));
                // Each side: along it, out from it.
                foreach (var (len, ox, oz, ax, az) in new[] { (c.Hw, 0.0, c.Hd, 1.0, 0.0), (c.Hw, 0.0, -c.Hd, 1.0, 0.0), (c.Hd, c.Hw, 0.0, 0.0, 1.0), (c.Hd, -c.Hw, 0.0, 0.0, 1.0) })
                {
                    var aw = (W(ax, az) - W(0, 0)).Normalized();
                    var outw = (W(ox, oz) - W(0, 0)).Normalized();
                    for (float t = (float)-len + PU(0.5f, 4f); t < len - 0.5f; t += PU(3f, 7f))
                    {
                        if (prng.NextDouble() > 0.4) continue;
                        float ra = PU(0.25f, 0.75f), rb = ra * PU(0.55f, 0.85f);
                        var at = W(ox, oz) + aw * t + outw * (0.3f + rb * 0.6f);   // across the gutter's lip onto the setts
                        // (Only on the setts, whose stone tops break its rim: on bare mud it read as a smooth dark
                        // ellipse; judge 3, E3 F. The draws above stay, so no other pool moves.)
                        if (OnSetts(at)) Pool(at, aw, ra, rb);
                    }
                }
            }
            // The open setts: one in PoolEvery square metres of them. (E9e r3: off by default: a round pool in the open square
            // with nothing over it read as a stain or a manhole; the mud pools gather at what stands instead.)
            int many = PoolEvery > 0f ? (int)(size * size / PoolEvery) : 0;
            for (int k = 0; k < many; k++)
            {
                float x = PU(-half, half), zz = PU(-half, half);
                int si = Math.Clamp((int)((x + half) / size * zr), 0, zr - 1), sj = Math.Clamp((int)((zz + half) / size * zr), 0, zr - 1);
                if (zs[(sj * zr + si) * 4 + 1] < 160) continue;
                float ra = PU(0.25f, 0.75f);
                float an = PU(0, Mathf.Tau);
                Pool(new Vector2(x, zz), new Vector2(Mathf.Cos(an), Mathf.Sin(an)), ra, ra * PU(0.6f, 0.9f));
            }
        }

        // (Env 22 r2) the zone's own puddles (props_own.json "puddles"), where a place wants standing water.
        if (OwnProps.For(z.Id)?.Puddles is { } own)
            foreach (var (at, ra, rb, turn) in own) Pool(at, new Vector2(Mathf.Cos(turn), Mathf.Sin(turn)), ra, rb);
        var mask = new byte[mr * mr * 4];
        var core = new float[mr * mr];
        var verge = new float[mr * mr];
        for (int j = 0; j < mr; j++)
            for (int i = 0; i < mr; i++)
            {
                int at = j * mr + i;
                float wx = -half + (i + 0.5f) * mt, wz = -half + (j + 0.5f) * mt;
                float r = 0, rut = 0, wet, pud, rutSpot = 0;
                if (dist[at] < 1e8f)
                {
                    float s = along[at], hw = hwOf[at];
                    // The width wanders, as a road worn by use does.
                    hw = HalfWidth(hw, s);
                    float d = dist[at];
                    float c = 1f - Mathf.SmoothStep(hw - 0.35f, hw + 0.45f, d);
                    float v = 1f - Mathf.SmoothStep(hw, hw + VergeW, d);
                    // The ruts wander a little off the centre line, the left and right together.
                    float off = side[at] - RutShift(s);
                    float ro = RutHalf(hw);
                    float dd = Mathf.Abs(Mathf.Abs(off) - ro);
                    float along0 = RutAlong(s, off < 0 ? 0 : 1, out float spot);
                    float prof = 1f - Mathf.SmoothStep(RutCore, RutCore + RutFeather, dd);
                    rut = prof * c * along0;
                    rutSpot = spot * (1f - Mathf.SmoothStep(RutCore * 0.6f, RutCore + RutFeather * 0.5f, dd)) * c;
                    float centre = Mathf.Exp(-(off / 0.38f) * (off / 0.38f));
                    // 0.8 the made surface; above it, up to 1, its centre strip (so no edge's ramp passes through the strip's values).
                    r = c * (0.8f + 0.2f * centre);
                    core[at] = c;
                    verge[at] = v;
                }
                float cv = Sample(lap, n, st, half, wx, wz);
                // (The blurred Laplacian: the zones' 80th percentile is about 0.045, the 95th about 0.1.)
                float hollow = Mathf.SmoothStep(0.06f, 0.15f, cv), deep = Mathf.SmoothStep(0.11f, 0.24f, cv);
                // (The ruts' own damp is the shader's, from G: here the hollows, the gutters and the made surface.)
                wet = Mathf.Max(hollow * 0.8f, Mathf.Max(gut[at] * 0.75f, core[at] * 0.12f));
                pud = Mathf.Max(rutSpot, Mathf.Max(deep * 0.8f, Mathf.Max(gut[at] * 0.4f, pools[at])));
                mask[at * 4] = (byte)(Mathf.Clamp(r, 0, 1) * 255);
                mask[at * 4 + 1] = (byte)(Mathf.Clamp(rut, 0, 1) * 255);
                mask[at * 4 + 2] = (byte)(Mathf.Clamp(wet, 0, 1) * 255);
                mask[at * 4 + 3] = (byte)(Mathf.Clamp(pud, 0, 1) * 255);
            }
        Mask = Image.CreateFromData(mr, mr, false, Image.Format.Rgba8, mask);
        Mask.GenerateMipmaps();

        // The paint: mud opened (strokes under ~1.2 m wide go), the road's
        // band repainted as its verge, dirt and mud at the wall bases.
        var sp = (Image)z.Splat.Duplicate();
        sp.Convert(Image.Format.Rgba8);
        int sr = sp.GetWidth();
        var px = sp.GetData();
        var mud = new float[sr * sr];
        for (int k = 0; k < mud.Length; k++) mud[k] = px[k * 4 + 3] / 255f;
        mud = Dilate(Erode(mud, sr, 2), sr, 2);
        // The old paint's road band, softened (about 1 m), so it meets the verge and the camps beside it without an edge.
        var dirt = new float[sr * sr];
        for (int k = 0; k < dirt.Length; k++) dirt[k] = px[k * 4] / 255f;
        var soft = Blur(Blur(dirt, sr, 3), sr, 3);
        float smt = size / sr;
        // Elsewhere (a camp's clearing, a yard) the dirt's own edge softened over about a metre (judge 1, E3 fix 4: the
        // shader's ramp and the heights then make a zone 0.6-1.2 m wide, with fingers of dirt into the grass).
        int cr = Math.Max(1, (int)Math.Round(ClearingSoft / smt / 2));
        var softC = Blur(Blur(dirt, sr, cr), sr, cr);
        for (int j = 0; j < sr; j++)
            for (int i = 0; i < sr; i++)
            {
                int k = j * sr + i;
                float wx = -half + (i + 0.5f) * smt, wz = -half + (j + 0.5f) * smt;
                int mi = Math.Clamp((int)((wx + half) / mt), 0, mr - 1), mj = Math.Clamp((int)((wz + half) / mt), 0, mr - 1);
                int at = mj * mr + mi;
                float rr = softC[k], a = Math.Min(px[k * 4 + 3] / 255f, mud[k]);
                if (dist[at] < 1e8f)
                {
                    float hw = hwOf[at];
                    float infl = 1f - Mathf.SmoothStep(hw + VergeW * 0.8f, hw + VergeW + 1.6f, dist[at]);
                    rr = Mathf.Lerp(rr, Mathf.Max(verge[at], soft[k] * 0.85f), infl);
                }
                float g = gut[at];
                rr = Mathf.Max(rr, g * 0.7f);
                a = Mathf.Max(a, g * g * 0.45f);
                px[k * 4] = (byte)(Mathf.Clamp(rr, 0, 1) * 255);
                px[k * 4 + 3] = (byte)(Mathf.Clamp(a, 0, 1) * 255);
            }
        Splat = Image.CreateFromData(sr, sr, false, Image.Format.Rgba8, px);

        // The sky over the ground: what stands over it (the flora's crowns, from their own meshes) and the walls.
        er = Math.Min(1536, (int)Math.Ceiling(size / 0.25f));
        et = size / er;
        this.half = half;
        foreach (var g in z.Flora)
        {
            if (g.Kind is "rock" or "boulder" or "cliff" or "pebble") continue;
            var b = Dressing.BoundsOf(g.Piece);
            foreach (var t in g.At)
            {
                float sc = t.Basis.Column0.Length(), top = b.End.Y * sc;
                if (top < 1.4f) continue;
                float r = 0.5f * Math.Max(b.Size.X, b.Size.Z) * sc * 0.85f;
                float k = g.Kind == "dead" ? 0.4f : top < 2.6f ? 0.7f : 0.95f;
                var c = new Vector2(t.Origin.X + b.GetCenter().X * sc, t.Origin.Z + b.GetCenter().Z * sc);
                shelters.Add((c, r, Math.Max(top * 0.3f, 0.8f), top, k));
            }
        }
        walls = boxes;
        var sky = new float[er * er];
        Array.Fill(sky, 1f);
        foreach (var (c, r, _, _, k) in shelters)
            Stamp(sky, c, c, r, k);
        foreach (var c in walls)
        {
            float rr = (float)Math.Sqrt(c.Hw * c.Hw + c.Hd * c.Hd) + 2.4f;
            int i0 = Math.Max(0, (int)(((float)c.X - rr + half) / et)), i1 = Math.Min(er - 1, (int)(((float)c.X + rr + half) / et));
            int j0 = Math.Max(0, (int)(((float)c.Z - rr + half) / et)), j1 = Math.Min(er - 1, (int)(((float)c.Z + rr + half) / et));
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    float o = BoxOut(c, -half + (i + 0.5f) * et, -half + (j + 0.5f) * et);
                    sky[j * er + i] *= Mathf.SmoothStep(0.25f, 2.2f, o);
                }
        }
        skyBlur = Blur(Blur(sky, er, 2), er, 2);
        // The lie of the land: the heights' curvature over tens of metres, scaled by its own spread.
        var lows = Blur(Blur(Blur(lap0, n, 5), n, 5), n, 5);
        double ss = 0;
        foreach (var v in lows) ss += v * v;
        float sd = (float)Math.Sqrt(ss / lows.Length) + 1e-6f;
        lie = new byte[er * er];
        for (int j = 0; j < er; j++)
            for (int i = 0; i < er; i++)
                lie[j * er + i] = (byte)(Mathf.Clamp(0.5f + Sample(lows, n, st, half, -half + (i + 0.5f) * et, -half + (j + 0.5f) * et) / (3f * sd), 0, 1) * 255);
        // (Near first: it lays the setts' course direction, which the exposure's A carries.)
        nearPx = MakeNear(z, px, sr);
        exposurePx = Pack(null);
        if (sun is Vector3 sdir) BakeSun(sdir);
        // --ground-dump DIR: both as PNGs, to check them by eye.
        if (Args.Get("ground-dump") is { } dumpDir)
        {
            Mask.SavePng($"{dumpDir}/{z.Id}_mask.png");
            Splat.SavePng($"{dumpDir}/{z.Id}_splat.png");
            Exposure.GetImage().SavePng($"{dumpDir}/{z.Id}_exposure.png");
            Near.GetImage().SavePng($"{dumpDir}/{z.Id}_near.png");
        }
    }

    /// <summary>What stands near the ground (judge 1, E3 fix 6), RGBA8 at the exposure's quarter metre: R the distance
    /// to a wall or a building's base (0-2 m), for the gutters and the weeds in the joints; G to anything standing (walls,
    /// the well, stalls, fences, posts), for the grime; B the setts' wear lane (1 down the middle of a street or the
    /// square's ways, about 1.5 m wide).</summary>
    public ImageTexture Near => near ??= ImageTexture.CreateFromImage(Image.CreateFromData(er, er, false, Image.Format.Rgba8, nearPx));
    ImageTexture? near;
    readonly byte[] nearPx;

    byte[] MakeNear(ZoneData z, byte[] sp, int sr)
    {
        var dw = new float[er * er];
        var da = new float[er * er];
        Array.Fill(dw, 2f);
        Array.Fill(da, 2f);
        foreach (var c in z.Meta.Colliders)
        {
            if (c.Soft) continue;
            bool box = c.Kind == ColliderKind.Box;
            if (!box && c.R < 0.25) continue;
            // (e22r1a, the Env 22 triage: a dark ring round the Watch-post's rubble) a heap (props_own.json no_gutter) is not
            // a thing standing: no damp foot or collar round it; its own spoil runs out into the soil and grass
            if (box && OwnProps.For(z.Id)?.NoGutter is { } ng && ng.Exists(g => Math.Abs(g.X - c.X) < 0.5 && Math.Abs(g.Y - c.Z) < 0.5)) continue;
            bool wall = box && Math.Max(c.Hw, c.Hd) >= 2.0 && Math.Min(c.Hw, c.Hd) >= 0.25;
            float rr = (float)(box ? Math.Sqrt(c.Hw * c.Hw + c.Hd * c.Hd) : c.R) + 2.1f;
            int i0 = Math.Max(0, (int)(((float)c.X - rr + half) / et)), i1 = Math.Min(er - 1, (int)(((float)c.X + rr + half) / et));
            int j0 = Math.Max(0, (int)(((float)c.Z - rr + half) / et)), j1 = Math.Min(er - 1, (int)(((float)c.Z + rr + half) / et));
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    float x = -half + (i + 0.5f) * et, zz = -half + (j + 0.5f) * et;
                    float o = box ? BoxOut(c, x, zz) : Mathf.Sqrt((x - (float)c.X) * (x - (float)c.X) + (zz - (float)c.Z) * (zz - (float)c.Z)) - (float)c.R;
                    o = Math.Max(o, 0);
                    int k = j * er + i;
                    if (o < da[k]) da[k] = o;
                    if (wall && o < dw[k]) dw[k] = o;
                }
        }
        // The wear lane: the ridge of the distance from the setts' edge (a street's middle, the square's ways).
        float smt = er * et / sr;
        var lane = new float[sr * sr];
        bool any = false;
        var dd = new float[sr * sr];
        for (int k = 0; k < dd.Length; k++) { bool st = sp[k * 4 + 1] > 128; dd[k] = st ? 1e6f : 0; any |= st; }
        if (any)
        {
            // Two-pass chamfer distance (metres).
            float a1 = smt, a2 = smt * 1.4142f;
            for (int j = 0; j < sr; j++)
                for (int i = 0; i < sr; i++)
                {
                    int k = j * sr + i;
                    if (dd[k] == 0) continue;
                    float v = dd[k];
                    if (i > 0) v = Math.Min(v, dd[k - 1] + a1);
                    if (j > 0) { v = Math.Min(v, dd[k - sr] + a1); if (i > 0) v = Math.Min(v, dd[k - sr - 1] + a2); if (i < sr - 1) v = Math.Min(v, dd[k - sr + 1] + a2); }
                    dd[k] = v;
                }
            for (int j = sr - 1; j >= 0; j--)
                for (int i = sr - 1; i >= 0; i--)
                {
                    int k = j * sr + i;
                    if (dd[k] == 0) continue;
                    float v = dd[k];
                    if (i < sr - 1) v = Math.Min(v, dd[k + 1] + a1);
                    if (j < sr - 1) { v = Math.Min(v, dd[k + sr] + a1); if (i < sr - 1) v = Math.Min(v, dd[k + sr + 1] + a2); if (i > 0) v = Math.Min(v, dd[k + sr - 1] + a2); }
                    dd[k] = v;
                }
            var mx = Dilate(dd, sr, Math.Max(1, (int)(3f / smt)));
            for (int k = 0; k < lane.Length; k++)
                lane[k] = (1f - Mathf.SmoothStep(0.45f, 1.0f, mx[k] - dd[k])) * Mathf.SmoothStep(1.0f, 2.0f, dd[k]);
            lane = Blur(lane, sr, Math.Max(1, (int)(0.3f / smt)));
            // The courses' direction (E9e r2: courses run across a street, so the east road's must turn): the structure
            // tensor of the distance's gradient over about 3 m. Across a street that gradient points from kerb to kerb, so
            // where it lies mostly along z (an east-west street) the courses run north-south. 0 courses along x, 1 along z.
            var jxx = new float[sr * sr];
            var jzz = new float[sr * sr];
            for (int j = 1; j < sr - 1; j++)
                for (int i = 1; i < sr - 1; i++)
                {
                    int k = j * sr + i;
                    if (dd[k] == 0) continue;
                    float gx = (dd[k + 1] - dd[k - 1]) / (2 * smt), gz = (dd[k + sr] - dd[k - sr]) / (2 * smt);
                    jxx[k] = gx * gx; jzz[k] = gz * gz;
                }
            int rb = Math.Max(1, (int)(1.5f / smt));
            jxx = Blur(Blur(jxx, sr, rb), sr, rb);
            jzz = Blur(Blur(jzz, sr, rb), sr, rb);
            dirS = new float[sr * sr];
            for (int k = 0; k < dirS.Length; k++) dirS[k] = jzz[k] / (jxx[k] + jzz[k] + 1e-6f);
            // (Env 22 r1c, the triage judge: diagonal seams across the Watch-post's floor and the gate's apron) in a square
            // the distance's ridge is its diagonals: the wear lane ran corner to corner and the courses turned along them, a
            // mitred X across the floor. A plaza (flora_species.json "ground" setts_plaza: paving whose half-width somewhere
            // within twice that many metres is over it; 0, the town's default: none) keeps one course direction and no
            // ridge lane; a street keeps both.
            float plaza = Args.Num("setts-plaza", FloraSpecies.GroundFor(z.Id).TryGetValue("setts_plaza", out var pz) ? pz : 0f);
            if (plaza > 0)
            {
                var wide = Dilate(dd, sr, Math.Max(1, (int)(2f * plaza / smt)));
                var pf = new float[sr * sr];
                for (int k = 0; k < pf.Length; k++) pf[k] = Mathf.SmoothStep(plaza, plaza * 1.4f, wide[k]);
                pf = Blur(pf, sr, Math.Max(1, (int)(1f / smt)));
                for (int k = 0; k < pf.Length; k++) { dirS[k] *= 1f - pf[k]; lane[k] *= 1f - pf[k]; }
            }
            // (and its ways, flora_species.json "setts_ways": a worn lane 2-3 m wide down each, where the ridge lane went)
            var ways = FloraSpecies.SettsWaysFor(z.Id);
            if (ways.Count > 0)
                for (int j = 0; j < sr; j++)
                    for (int i = 0; i < sr; i++)
                    {
                        int k = j * sr + i;
                        if (dd[k] == 0) continue;
                        var w = new Vector2(-half + (i + 0.5f) * smt, -half + (j + 0.5f) * smt);
                        float d = 1e9f;
                        foreach (var sg in ways)
                        {
                            Vector2 a = new(sg.X, sg.Y), ab = new Vector2(sg.Z, sg.W) - a;
                            float t = Math.Clamp((w - a).Dot(ab) / Math.Max(ab.LengthSquared(), 1e-4f), 0, 1);
                            d = Math.Min(d, (w - a - ab * t).Length());
                        }
                        lane[k] = Math.Max(lane[k], 1f - Mathf.SmoothStep(0.25f, 1.4f, d));   // (half at 0.8 m: the ruts, terrain setts_ruts)
                    }
            // (The distance off the splat's texels stair-stepped the kerb: centred on the texel's edge, blurred twice over
            // a texel, and read bilinearly below, its contours run smooth.)
            distS = new float[sr * sr];
            for (int k = 0; k < dd.Length; k++) distS[k] = dd[k] > 0 ? dd[k] - 0.5f * smt : -0.5f * smt;
            distS = Blur(Blur(distS, sr, 1), sr, 1);
        }
        var o8 = new byte[er * er * 4];
        courseDir = new byte[er * er];
        for (int j = 0; j < er; j++)
            for (int i = 0; i < er; i++)
            {
                int k = j * er + i;
                o8[k * 4] = (byte)(Mathf.Clamp(dw[k] / 2f, 0, 1) * 255);
                o8[k * 4 + 1] = (byte)(Mathf.Clamp(da[k] / 2f, 0, 1) * 255);
                float l = 0;
                if (any)
                {
                    int si = Math.Clamp((int)((i + 0.5f) * et / smt), 0, sr - 1), sj = Math.Clamp((int)((j + 0.5f) * et / smt), 0, sr - 1);
                    l = lane[sj * sr + si];
                }
                o8[k * 4 + 2] = (byte)(Mathf.Clamp(l, 0, 1) * 255);
                // A: the distance into the setts from their edge (0-2 m; the shader's edge band and kerb read it).
                float din = 0, dir = 0;
                if (any)
                {
                    float fx = Math.Clamp((i + 0.5f) * et / smt - 0.5f, 0, sr - 1.001f), fz = Math.Clamp((j + 0.5f) * et / smt - 0.5f, 0, sr - 1.001f);
                    int si = (int)fx, sj = (int)fz;
                    float ax = fx - si, az = fz - sj;
                    float Bi(float[] a) => (a[sj * sr + si] * (1 - ax) + a[sj * sr + si + 1] * ax) * (1 - az) + (a[(sj + 1) * sr + si] * (1 - ax) + a[(sj + 1) * sr + si + 1] * ax) * az;
                    din = Bi(distS); dir = Bi(dirS);
                }
                o8[k * 4 + 3] = (byte)(Mathf.Clamp(din / 2f, 0, 1) * 255);
                courseDir[k] = (byte)(Mathf.Clamp(dir, 0, 1) * 255);
            }
        return o8;
    }

    readonly int er;
    readonly float et, half;
    byte[] courseDir = Array.Empty<byte>();
    float[] dirS = Array.Empty<float>(), distS = Array.Empty<float>();
    readonly float[] skyBlur = Array.Empty<float>();
    readonly byte[] lie = Array.Empty<byte>();
    readonly List<(Vector2 C, float R, float Lo, float Hi, float K)> shelters = new();
    readonly List<ColliderDef> walls = new();
    /// <summary>How tall a wall stands, for its shadow at the thaw's sun (the colliders carry no height).</summary>
    const float WallH = 3.5f;

    /// <summary>The sun on the ground for a key toward `dir`: a crown shades the ground where the ray to the sun
    /// passes through it (a capsule from the crown along the shadow), a wall where it passes under its top.</summary>
    void BakeSun(Vector3 dir) => TakeSun(dir, SunPx(dir));

    void TakeSun(Vector3 dir, byte[] px)
    {
        baked = dir;
        exposurePx = px;
        exposure?.Update(Image.CreateFromData(er, er, false, Image.Format.Rgba8, exposurePx));
    }

    /// <summary>The exposure with the sun toward `dir` (reads only what the constructor made: any thread).</summary>
    byte[] SunPx(Vector3 dir)
    {
        var lit = new float[er * er];
        Array.Fill(lit, 1f);
        var s = new Vector2(dir.X, dir.Z) / dir.Y;
        foreach (var (c, r, lo, hi, k) in shelters)
            Stamp(lit, c - s * hi, c - s * lo, r, k);
        foreach (var c in walls)
        {
            float rr = (float)Math.Sqrt(c.Hw * c.Hw + c.Hd * c.Hd);
            Vector2 a = new((float)c.X, (float)c.Z), b = a - s * WallH;
            int i0 = Math.Max(0, (int)((Math.Min(a.X, b.X) - rr + half) / et)), i1 = Math.Min(er - 1, (int)((Math.Max(a.X, b.X) + rr + half) / et));
            int j0 = Math.Max(0, (int)((Math.Min(a.Y, b.Y) - rr + half) / et)), j1 = Math.Min(er - 1, (int)((Math.Max(a.Y, b.Y) + rr + half) / et));
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    float x = -half + (i + 0.5f) * et, zz = -half + (j + 0.5f) * et;
                    for (float h = 0.25f; h <= WallH; h += 0.25f)
                        if (BoxOut(c, x + s.X * h, zz + s.Y * h) <= 0) { lit[j * er + i] = 0; break; }
                }
        }
        lit = Blur(Blur(lit, er, 1), er, 1);
        return Pack(lit);
    }

    byte[] Pack(float[]? lit)
    {
        var ex = new byte[er * er * 4];
        for (int k = 0; k < er * er; k++)
        {
            ex[k * 4] = (byte)(Mathf.Clamp(skyBlur[k], 0, 1) * 255);
            ex[k * 4 + 1] = lit == null ? (byte)255 : (byte)(Mathf.Clamp(lit[k], 0, 1) * 255);
            ex[k * 4 + 2] = lie[k];
            ex[k * 4 + 3] = courseDir.Length == er * er ? courseDir[k] : (byte)0;   // the setts' course direction (MakeNear)
        }
        return ex;
    }

    /// <summary>Takes a share k off `g` within r of the segment a-b (a crown, or its shadow), soft at its rim.</summary>
    void Stamp(float[] g, Vector2 a, Vector2 b, float r, float k)
    {
        float rr = r * 1.15f;
        int i0 = Math.Max(0, (int)((Math.Min(a.X, b.X) - rr + half) / et)), i1 = Math.Min(er - 1, (int)((Math.Max(a.X, b.X) + rr + half) / et));
        int j0 = Math.Max(0, (int)((Math.Min(a.Y, b.Y) - rr + half) / et)), j1 = Math.Min(er - 1, (int)((Math.Max(a.Y, b.Y) + rr + half) / et));
        Vector2 ab = b - a;
        float l2 = Math.Max(ab.LengthSquared(), 1e-6f);
        for (int j = j0; j <= j1; j++)
            for (int i = i0; i <= i1; i++)
            {
                var p = new Vector2(-half + (i + 0.5f) * et, -half + (j + 0.5f) * et);
                float t = Math.Clamp((p - a).Dot(ab) / l2, 0, 1);
                float d = (p - a - ab * t).Length();
                if (d >= rr) continue;
                g[j * er + i] *= 1f - k * (1f - Mathf.SmoothStep(0.55f * r, 1.15f * r, d));
            }
    }

    /// <summary>How far (x, z) lies outside a box collider (0 or less: inside).</summary>
    static float BoxOut(ColliderDef c, float x, float z)
    {
        double cos = Math.Cos(-c.Rot), sin = Math.Sin(-c.Rot), dx = x - c.X, dz = z - c.Z;
        double lx = Math.Abs(dx * cos - dz * sin) - c.Hw, lz = Math.Abs(dx * sin + dz * cos) - c.Hd;
        if (lx < 0 && lz < 0) return (float)Math.Max(lx, lz);
        return (float)Math.Sqrt(Math.Max(lx, 0) * Math.Max(lx, 0) + Math.Max(lz, 0) * Math.Max(lz, 0));
    }

    static float Sample(float[] g, int n, float st, float half, float x, float z)
    {
        float fx = Math.Clamp((x + half) / st, 0, n - 1.001f), fz = Math.Clamp((z + half) / st, 0, n - 1.001f);
        int i = (int)fx, j = (int)fz;
        float tx = fx - i, tz = fz - j;
        float a = g[j * n + i] + (g[j * n + i + 1] - g[j * n + i]) * tx;
        float b = g[(j + 1) * n + i] + (g[(j + 1) * n + i + 1] - g[(j + 1) * n + i]) * tx;
        return a + (b - a) * tz;
    }

    static float[] Blur(float[] a, int n, int r)
    {
        var t = new float[a.Length];
        var o = new float[a.Length];
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                float s = 0; int c = 0;
                for (int k = Math.Max(0, i - r); k <= Math.Min(n - 1, i + r); k++) { s += a[j * n + k]; c++; }
                t[j * n + i] = s / c;
            }
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                float s = 0; int c = 0;
                for (int k = Math.Max(0, j - r); k <= Math.Min(n - 1, j + r); k++) { s += t[k * n + i]; c++; }
                o[j * n + i] = s / c;
            }
        return o;
    }

    static float[] Erode(float[] a, int n, int r) => MinMax(a, n, r, true);
    static float[] Dilate(float[] a, int n, int r) => MinMax(a, n, r, false);

    static float[] MinMax(float[] a, int n, int r, bool min)
    {
        var t = new float[a.Length];
        var o = new float[a.Length];
        for (int pass = 0; pass < 2; pass++)
        {
            var src = pass == 0 ? a : t;
            var dst = pass == 0 ? t : o;
            for (int j = 0; j < n; j++)
                for (int i = 0; i < n; i++)
                {
                    float v = min ? 1e9f : -1e9f;
                    for (int k = -r; k <= r; k++)
                    {
                        int x = pass == 0 ? Math.Clamp(i + k, 0, n - 1) : i, y = pass == 0 ? j : Math.Clamp(j + k, 0, n - 1);
                        float s = src[y * n + x];
                        v = min ? Math.Min(v, s) : Math.Max(v, s);
                    }
                    dst[j * n + i] = v;
                }
        }
        return o;
    }
}
