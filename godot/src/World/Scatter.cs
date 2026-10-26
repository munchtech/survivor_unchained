using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// The small things lying on the ground that the paint cannot carry: pebbles at the ruts' edges, small
/// stones on the verge and the odd larger one at the road's edge, leaves and twigs under the trees, and
/// crumbs and weeds at the foot of a town's walls. Our own meshes, placed along the same roads
/// GroundPaint paints (its helpers), merged into one mesh per 32 m cell so each visible cell is one draw
/// and culls by its own box. Seeded, so a zone is the same every load. --no-scatter leaves it out.
/// </summary>
public static class Scatter
{
    const float Cell = 32f, Step = 0.25f, WallStep = 0.3f;
    static readonly bool EdgeStones = SurvivorUnchained.Args.Has("edge-stones");   // cut (judge 1, E3 fix 9: they read as eggs); the pebbles stay
    static readonly float CampLitter = SurvivorUnchained.Args.Num("camp-litter", 6f);

    // A needle cluster: three thin pointed slivers crossed at a root, length 1 (fir needles lie in little drifts).
    static Tpl Needle()
    {
        var t = new Tpl();
        for (int k = 0; k < 3; k++)
        {
            float a = k * 1.05f + 0.2f;
            var d = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            var side = new Vector3(-d.Z, 0, d.X) * 0.03f;
            int o = t.V.Count;
            t.V.Add(-d * 0.5f + Vector3.Up * 0.01f); t.V.Add(side + Vector3.Up * 0.03f); t.V.Add(d * 0.5f + Vector3.Up * 0.01f); t.V.Add(-side + Vector3.Up * 0.03f);
            t.Tri(o, o + 1, o + 2, Vector3.Up); t.Tri(o, o + 2, o + 3, Vector3.Up);
        }
        return t.Finish(true);
    }

    /// <summary>A base shape: positions, smooth normals, triangles. Sits on y = 0 and up, about 1 across.</summary>
    sealed class Tpl
    {
        public readonly List<Vector3> V = new();
        public readonly List<int> I = new();
        public Vector3[] N = Array.Empty<Vector3>();
        public float Top;

        /// <summary>A triangle wound clockwise (Godot's front) as seen from the side the hint points to.</summary>
        public void Tri(int a, int b, int c, Vector3 hint)
        {
            var n = (V[c] - V[a]).Cross(V[b] - V[a]);
            if (n.Dot(hint) < 0) (b, c) = (c, b);
            I.Add(a); I.Add(b); I.Add(c);
        }

        /// <summary>Smooth normals (area weighted), or all straight up for things that should light as the ground.</summary>
        public Tpl Finish(bool up = false)
        {
            N = new Vector3[V.Count];
            for (int i = 0; i < I.Count; i += 3)
            {
                var n = (V[I[i + 2]] - V[I[i]]).Cross(V[I[i + 1]] - V[I[i]]);
                for (int k = 0; k < 3; k++) N[I[i + k]] += n;
            }
            for (int i = 0; i < N.Length; i++) N[i] = up || N[i].LengthSquared() < 1e-12f ? Vector3.Up : N[i].Normalized();
            foreach (var v in V) Top = Math.Max(Top, v.Y);
            return this;
        }
    }

    // An octahedron cut once (32 triangles), each vertex pushed to 0.8-1.1 of its radius, flattened, sat on y = 0.
    static Tpl Pebble(int seed)
    {
        var rng = new Random(seed);
        var t = new Tpl();
        var axes = new[] { Vector3.Right, Vector3.Left, Vector3.Up, Vector3.Down, Vector3.Back, Vector3.Forward };
        var flat = new Vector3(1f, 0.55f, 0.85f);
        var mids = new Dictionary<(int, int), int>();
        int Add(Vector3 d)
        {
            t.V.Add(d.Normalized() * (0.8f + 0.3f * (float)rng.NextDouble()) * flat);
            return t.V.Count - 1;
        }
        foreach (var d in axes) Add(d);
        int Mid(int a, int b)
        {
            var key = a < b ? (a, b) : (b, a);
            return mids.TryGetValue(key, out int m) ? m : mids[key] = Add(axes[a] + axes[b]);
        }
        foreach (int x in new[] { 0, 1 }) foreach (int y in new[] { 2, 3 }) foreach (int z in new[] { 4, 5 })
        {
            int ab = Mid(x, y), bc = Mid(y, z), ca = Mid(z, x);
            foreach (var (p, q, r) in new[] { (x, ab, ca), (ab, y, bc), (ca, bc, z), (ab, bc, ca) })
                t.Tri(p, q, r, t.V[p] + t.V[q] + t.V[r]);
        }
        float low = 0;
        foreach (var v in t.V) low = Math.Min(low, v.Y);
        for (int i = 0; i < t.V.Count; i++) t.V[i] += Vector3.Up * -low;
        return t.Finish();
    }

    // A pointed oval of six triangles round a raised centre, length 1 (the shape of Grass.cs's leaves).
    static Tpl Leaf()
    {
        var t = new Tpl();
        t.V.Add(new Vector3(0, 0.12f, 0));
        (float u, float w)[] ring = { (-0.5f, 0), (-0.25f, 0.42f), (0.12f, 0.5f), (0.5f, 0), (0.12f, -0.5f), (-0.25f, -0.42f) };
        foreach (var (u, w) in ring) t.V.Add(new Vector3(u, 0, w * 0.96f));
        for (int s = 0; s < ring.Length; s++) t.Tri(0, 1 + s, 1 + (s + 1) % ring.Length, Vector3.Up);
        return t.Finish();
    }

    // Three bent segments of square section, no caps, length 1 and 0.025 thick.
    static Tpl Twig()
    {
        var t = new Tpl();
        var p = new Vector3(-0.5f, 0, 0);
        float[] ang = { 0.25f, -0.35f, 0.3f };
        var centres = new List<Vector3>();
        const float th = 0.025f;
        for (int k = 0; k <= 3; k++)
        {
            float a = ang[Math.Min(k, 2)];
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            var side = Vector3.Up.Cross(dir).Normalized() * (th / 2);
            var lift = Vector3.Up * (th / 2);
            centres.Add(p + lift);
            t.V.Add(p - side); t.V.Add(p + side); t.V.Add(p + side + lift * 2); t.V.Add(p - side + lift * 2);
            if (k < 3) p += dir / 3f;
        }
        for (int k = 0; k < 3; k++)
            for (int e = 0; e < 4; e++)
            {
                int a = k * 4 + e, b = k * 4 + (e + 1) % 4, c = a + 4, d = b + 4;
                var hint = (t.V[a] + t.V[b]) / 2 - centres[k];
                t.Tri(a, b, c, hint); t.Tri(b, d, c, hint);
            }
        return t.Finish();
    }

    // Five thin blades fanned from a root, leaning out, height 1.
    static Tpl Weed()
    {
        var t = new Tpl();
        for (int k = 0; k < 5; k++)
        {
            float a = k * Mathf.Tau / 5 + 0.3f * k;
            var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            var side = new Vector3(-o.Z, 0, o.X) * 0.07f;
            int b = t.V.Count;
            t.V.Add(o * 0.05f - side); t.V.Add(o * 0.05f + side); t.V.Add(o * 0.35f + Vector3.Up * (0.8f + 0.05f * k));
            t.Tri(b, b + 1, b + 2, o);
        }
        return t.Finish(true);
    }

    /// <summary>What goes into one cell's mesh.</summary>
    sealed class Bin
    {
        public readonly List<Vector3> V = new(), N = new();
        public readonly List<Color> C = new();
        public readonly List<int> I = new();
    }

    public static Node3D? Build(ZoneData z)
    {
        if (SurvivorUnchained.Args.Has("no-scatter") || z.Place != null) return null;
        var paths = GroundPaint.RoadPaths(z);
        var boxes = new List<ColliderDef>();
        foreach (var c in z.Meta.Colliders)
            if (c.Kind == ColliderKind.Box && !c.Soft && Math.Min(c.Hw, c.Hd) >= 0.4) boxes.Add(c);
        if (paths.Count == 0 && boxes.Count == 0) return null;

        var paint = GroundPaint.Of(z);
        var expo = paint.Exposure.GetImage();
        int ew = expo.GetWidth(), eh = expo.GetHeight();
        // (E9e r2: twigs and needles on the setts read as black hairline cracks at the close camera: none there. Near's A
        // is the distance into the setts, 0 off them.)
        var nearImg = paint.Near.GetImage();
        bool OnSetts(float x, float zz) =>
            nearImg.GetPixel(Math.Clamp((int)((x + z.Half) / z.Size * ew), 0, ew - 1), Math.Clamp((int)((zz + z.Half) / z.Size * eh), 0, eh - 1)).A > 0.01f;
        float half = z.Half, lim = half - 2f;
        // The open sky over a point (1 in the open, 0 under a crown).
        float Sky(float x, float zz) =>
            expo.GetPixel(Math.Clamp((int)((x + half) / z.Size * ew), 0, ew - 1), Math.Clamp((int)((zz + half) / z.Size * eh), 0, eh - 1)).R;
        // Dry ground inside the zone and away from a fire's pit.
        bool Ok(float x, float zz)
        {
            if (Math.Abs(x) > lim || Math.Abs(zz) > lim || z.Meta.WaterAt(x, zz)) return false;
            // (E9c2) nothing inside a closed house (the cutaway shows its floor)
            if (OwnWalls.InsideAny(z, x, zz, -0.05f)) return false;
            foreach (var f in z.Meta.Fires)
                if ((x - f.X) * (x - f.X) + (zz - f.Z) * (zz - f.Z) < 1.6f * 1.6f) return false;
            return true;
        }

        var rng = new Random(1234);
        float U(float a, float b) => a + (b - a) * (float)rng.NextDouble();
        bool Chance(float p) => rng.NextDouble() < p;
        var pebbles = new[] { Pebble(11), Pebble(23), Pebble(37), Pebble(51) };
        var leaf = Leaf();
        var twig = Twig();
        var weed = Weed();
        var bins = new Dictionary<(int, int), Bin>();
        int pieces = 0, tris = 0;

        // One piece of a shape at (x, zz), turned and tilted a little, sunk into the ground by a share of its height
        // (squashed to `ys` of it; `low`: the colour its lower half grades to, dirt on a stone).
        void Put(Tpl t, float x, float zz, float scale, float sink, float tilt, Color col, float lift, float ys = 1f, Color? low = null)
        {
            int ci = (int)Math.Floor((x + half) / Cell), cj = (int)Math.Floor((zz + half) / Cell);
            if (!bins.TryGetValue((ci, cj), out var bin)) bins[(ci, cj)] = bin = new Bin();
            var basis = Godot.Basis.FromEuler(new Vector3((float)(rng.NextDouble() - 0.5) * tilt, U(0, Mathf.Tau), (float)(rng.NextDouble() - 0.5) * tilt));
            var at = new Vector3(x, z.HeightAt(x, zz) + lift - sink * t.Top * scale * ys, zz);
            int o = bin.V.Count;
            var sq = new Vector3(1, ys, 1);
            var nq = new Vector3(1, 1 / ys, 1);
            for (int i = 0; i < t.V.Count; i++)
            {
                bin.V.Add(at + basis * (t.V[i] * sq * scale));
                bin.N.Add((basis * (t.N[i] * nq)).Normalized());
                bin.C.Add(low is Color lc ? lc.Lerp(col, Mathf.SmoothStep(0.25f, 0.6f, t.V[i].Y / Math.Max(t.Top, 1e-4f))) : col);
            }
            foreach (int i in t.I) bin.I.Add(o + i);
            pieces++; tris += t.I.Count / 3;
        }
        Color Grey()
        {
            var b = Chance(0.3f) ? new Vector3(0.12f, 0.12f, 0.115f) : new Vector3(0.135f, 0.12f, 0.1f);
            b *= U(0.6f, 1.15f);
            return new Color(b.X, b.Y, b.Z, 0);
        }
        Color Plant(Vector3 lo, Vector3 hi, float k)
        {
            var v = lo.Lerp(hi, (float)rng.NextDouble()) * k;
            return new Color(v.X, v.Y, v.Z, 1);
        }
        void Stone(float x, float zz, float size, float sink)
        {
            if (Ok(x, zz)) Put(pebbles[rng.Next(4)], x, zz, size, sink, 0.4f, Grey(), 0);
        }

        foreach (var (p, hw0) in paths)
        {
            float s0 = 0, next = 0;
            for (int k = 0; k < p.Length - 1; k++)
            {
                Vector2 a = p[k], ab = p[k + 1] - a;
                float len = ab.Length();
                if (len < 1e-4f) continue;
                Vector2 dir = ab / len, n = new(-dir.Y, dir.X);
                for (; next <= s0 + len; next += Step)
                {
                    var c = a + dir * (next - s0);
                    float hw = GroundPaint.HalfWidth(hw0, next);
                    foreach (int sg in new[] { -1, 1 })
                    {
                        // Pebbles strewn over the road on this side, small stones on the verge, the odd large one at the edge.
                        // (Judge 3, E3 F: the pebbles at both edges of each rut, 0.55 a 0.25 m step, read as beaded rows along
                        // the ruts' shoulders; now loose across the road's half, no band.)
                        if (Chance(0.3f))
                        {
                            var q = c + n * (sg * U(0f, hw)) + dir * U(0, Step);
                            Stone(q.X, q.Y, U(0.03f, 0.07f), 0);
                        }
                        if (Chance(0.5f)) { var q = c + n * (sg * (hw + U(-0.2f, 1.2f))) + dir * U(0, Step); Stone(q.X, q.Y, U(0.03f, 0.08f), 0.3f); }
                        // (Judge 1, E3 fix 9: the odd edge stone sunk 30-50%, flat, dark as the road, dirt up its lower half,
                        // 0.25 m at most; the pale smooth ones read as eggs.)
                        if (Chance(0.04f))
                        {
                            var q = c + n * (sg * (hw + U(-0.1f, 0.4f))) + dir * U(0, Step);
                            if (EdgeStones && Ok(q.X, q.Y))
                            {
                                var g = Grey();
                                var col = new Color(g.R * 0.68f * 1.04f, g.G * 0.68f, g.B * 0.68f * 0.92f, 0);
                                Put(pebbles[rng.Next(4)], q.X, q.Y, U(0.055f, 0.115f), U(0.3f, 0.5f), 0.3f, col, 0, 0.8f, new Color(0.085f, 0.07f, 0.055f, 0));
                            }
                        }

                        // Under the trees: a drift of leaves and now and then a twig.
                        var m = c + n * (sg * (hw - 0.3f + U(0, 2.8f)));
                        float sky = Sky(m.X, m.Y);
                        if (sky >= 0.55f) continue;
                        for (int i = 0; i < 6; i++)
                        {
                            float lx = m.X + U(-0.5f, 0.5f), lz = m.Y + U(-0.5f, 0.5f);
                            if (Chance(1 - sky) && Ok(lx, lz))
                                Put(leaf, lx, lz, U(0.06f, 0.10f), 0, 0.2f, Plant(new(0.12f, 0.085f, 0.045f), new(0.15f, 0.12f, 0.06f), U(0.6f, 1f)), 0.005f);
                        }
                        if (Chance(0.08f) && Ok(m.X, m.Y))
                            Put(twig, m.X, m.Y, U(0.2f, 0.55f), 0, 0.2f, Plant(new(0.07f, 0.055f, 0.04f), new(0.07f, 0.055f, 0.04f), U(0.7f, 1.1f)), 0.005f);
                    }
                }
                s0 += len;
            }
        }

        // Under every tree (judge 1, E3 fix 8): drifts of needles or leaves within 2-4 m of the trunk, and a twig or two.
        var needle = Needle();
        foreach (var g in z.Flora)
        {
            if (g.Kind is not ("pine" or "broadleaf" or "dead" or "autumn")) continue;
            bool pine = g.Kind == "pine";
            foreach (var t in g.At)
            {
                float tx = t.Origin.X, tz = t.Origin.Z;
                for (int d = 0; d < 3; d++)
                {
                    float an = U(0, Mathf.Tau), rr = U(0.5f, 3.5f);
                    float cx = tx + Mathf.Cos(an) * rr, cz = tz + Mathf.Sin(an) * rr;
                    int many = rng.Next(3, 7);
                    for (int i = 0; i < many; i++)
                    {
                        float lx = cx + U(-0.45f, 0.45f), lz = cz + U(-0.45f, 0.45f);
                        if (!Ok(lx, lz) || OnSetts(lx, lz)) continue;
                        if (pine) Put(needle, lx, lz, U(0.07f, 0.12f), 0, 0.15f, Plant(new(0.13f, 0.08f, 0.04f), new(0.17f, 0.11f, 0.05f), U(0.6f, 1f)), 0.004f);
                        else Put(leaf, lx, lz, U(0.06f, 0.10f), 0, 0.2f, Plant(new(0.12f, 0.085f, 0.045f), new(0.16f, 0.12f, 0.06f), U(0.6f, 1f)), 0.005f);
                    }
                }
                if (Chance(0.35f))
                {
                    float an = U(0, Mathf.Tau), rr = U(0.6f, 3f);
                    float lx = tx + Mathf.Cos(an) * rr, lz = tz + Mathf.Sin(an) * rr;
                    if (Ok(lx, lz) && !OnSetts(lx, lz)) Put(twig, lx, lz, U(0.2f, 0.5f), 0, 0.2f, Plant(new(0.07f, 0.055f, 0.04f), new(0.08f, 0.06f, 0.045f), U(0.7f, 1.1f)), 0.005f);
                }
            }
        }

        // A camp's ground (judge 1, E3 fix 10: the close-up's near ground had nothing on it): within a few metres of the
        // fire, chips, twigs, pebbles and needles, about six to the square metre (10+ a screen quarter at the close-up).
        foreach (var f in z.Meta.Fires)
        {
            float fx = (float)f.X, fz = (float)f.Z, R = 7f;
            int many = (int)(Mathf.Pi * R * R * CampLitter);
            for (int i = 0; i < many; i++)
            {
                float an = U(0, Mathf.Tau), rr = R * Mathf.Sqrt(U(0.05f, 1f));
                float lx = fx + Mathf.Cos(an) * rr, lz = fz + Mathf.Sin(an) * rr;
                if (!Ok(lx, lz)) continue;
                double u = rng.NextDouble();
                if (u < 0.35) Put(pebbles[rng.Next(4)], lx, lz, U(0.02f, 0.05f), 0.3f, 0.4f, Grey(), 0);
                else if (u < 0.55) { if (!OnSetts(lx, lz)) Put(twig, lx, lz, U(0.12f, 0.4f), 0, 0.2f, Plant(new(0.07f, 0.055f, 0.04f), new(0.09f, 0.07f, 0.05f), U(0.7f, 1.1f)), 0.005f); }
                else if (u < 0.7) Put(pebbles[rng.Next(4)], lx, lz, U(0.025f, 0.05f), 0.2f, 0.5f, Plant(new(0.16f, 0.11f, 0.07f), new(0.2f, 0.15f, 0.09f), U(0.6f, 1f)), 0, 0.45f);   // a wood chip
                else if (!OnSetts(lx, lz)) Put(needle, lx, lz, U(0.07f, 0.12f), 0, 0.15f, Plant(new(0.13f, 0.08f, 0.04f), new(0.17f, 0.11f, 0.05f), U(0.6f, 1f)), 0.004f);
            }
        }

        // The foot of each wall: crumbs of dirt and weeds, within a hand's breadth or two of it.
        foreach (var c in boxes)
        {
            double cos = Math.Cos(c.Rot), sin = Math.Sin(c.Rot);
            void At(float lx, float lz)
            {
                float x = (float)(c.X + lx * cos - lz * sin), zz = (float)(c.Z + lx * sin + lz * cos);
                if (!Ok(x, zz)) return;
                if (Chance(0.5f)) Put(pebbles[rng.Next(4)], x, zz, U(0.02f, 0.05f), 0.3f, 0.4f, Grey(), 0);
                if (Chance(0.12f)) Put(weed, x, zz, U(0.08f, 0.2f), 0, 0.3f, Plant(new(0.05f, 0.07f, 0.03f), new(0.05f, 0.07f, 0.03f), U(0.7f, 1.1f)), 0);
            }
            float hw = (float)c.Hw, hd = (float)c.Hd;
            for (float t = -hd; t <= hd; t += WallStep) { At(hw + U(0.05f, 0.45f), t); At(-hw - U(0.05f, 0.45f), t); }
            for (float t = -hw; t <= hw; t += WallStep) { At(t, hd + U(0.05f, 0.45f)); At(t, -hd - U(0.05f, 0.45f)); }
        }
        if (pieces == 0) return null;

        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/scatter.gdshader") };
        mat.SetShaderParameter("expo_tex", paint.Exposure);
        mat.SetShaderParameter("zone_size", z.Size);
        mat.SetShaderParameter("debug_view", (int)SurvivorUnchained.Args.Num("scatter-debug", 0f));
        mat.SetShaderParameter("warm_at", Ground.WarmAt(z));
        mat.SetShaderParameter("night_dew", SurvivorUnchained.Args.Num("scatter-night-dew", 0.5f));
        mat.SetShaderParameter("night_spec", SurvivorUnchained.Args.Num("ground-night-spec", 0.12f));
        var root = new Node3D { Name = "Scatter" };
        foreach (var ((ci, cj), bin) in bins)
        {
            var arrays = new Godot.Collections.Array();
            arrays.Resize((int)Mesh.ArrayType.Max);
            arrays[(int)Mesh.ArrayType.Vertex] = bin.V.ToArray();
            arrays[(int)Mesh.ArrayType.Normal] = bin.N.ToArray();
            arrays[(int)Mesh.ArrayType.Color] = bin.C.ToArray();
            arrays[(int)Mesh.ArrayType.Index] = bin.I.ToArray();
            var mesh = new ArrayMesh();
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
            root.AddChild(new MeshInstance3D { Name = $"Cell_{ci}_{cj}", Mesh = mesh, MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        }
        GD.Print($"scatter {z.Id}: {pieces} pieces, {tris} tris, {bins.Count} cells");
        return root;
    }
}
