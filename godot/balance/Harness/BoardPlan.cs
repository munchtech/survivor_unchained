using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using SurvivorUnchained.Maps;

namespace SurvivorUnchained.Balance;

/* A board's plan, top-down (H1 item 6): `board --people pack --tier 1 --seed 3,17,311 --out plan.png` (or .pgm). The
 * app can now draw any arena's walkable ground, its colliders, the fold, its chokepoints, the lamp and its pool, the
 * lanes and the streams, and check the board by numbers (Maps/ArenaBoard.cs, BoardCheck): the fold reached only
 * through its gaps, each gap's clear width, the walkable ground against the same seed made as it was. */
public static class BoardPlan
{
    public static void Run(string people, int tier, IEnumerable<int> seeds, string outPath, double ppm)
    {
        foreach (int seed in seeds)
        {
            var m = MapGen.Generate(new MapSpec { Seed = seed, Arena = true, People = people, Tier = tier });
            // The same seed made as it was (a story night never takes a board).
            var was = MapGen.Generate(new MapSpec { Seed = seed, Arena = true, People = people, Tier = tier, StoryNight = true });
            var r = BoardCheck.Measure(m);
            var r0 = BoardCheck.Measure(was);
            Console.WriteLine($"seed {seed}: {people} tier {tier}: " + (m.Board == null ? "no board" : $"board radius {m.Board.Radius:0}"));
            Console.WriteLine($"  open ground {r.Open} m2, as it was {r0.Open} m2: {(double)r.Open / r0.Open:0.000} (radius ratio squared {(m.Board == null ? 1 : Math.Pow(m.Board.Radius / ArenaGen.R, 2)):0.000})");
            if (m.Board is { } b)
            {
                var f = b.Fold;
                Console.WriteLine($"  fold at ({f.X:0.0}, {f.Z:0.0}), {MathX(f.X, f.Z):0.0} m from the start, wall {f.WallR:0.0} m (open inside {f.InnerR:0.0}), {r.FoldInside} m2 open inside");
                Console.WriteLine($"  leaks with its gaps shut: {r.Leaks}; start outside: {r.StartOutside}; fold reached from the start: {r.FoldReached}");
                foreach (var g in r.Gaps)
                    Console.WriteLine($"  gap at {g.Bearing * 180 / Math.PI:0} deg: made {g.Width:0.00} m, clear {g.ClearWidth:0.00} m, {g.NavCells} nav cells across, passable alone: {g.Passable}");
                for (int k = 0; k < b.Lanes.Count; k++)
                {
                    var l = b.Lanes[k];
                    double len = 0;
                    for (int i = 0; i + 1 < l.Length; i++) len += Math.Sqrt(Math.Pow(l[i + 1].X - l[i].X, 2) + Math.Pow(l[i + 1].Z - l[i].Z, 2));
                    Console.WriteLine($"  lane {k}: {len:0} m, {l[0].Hw * 2:0.0} m wide, ends {Math.Sqrt(l[^1].X * l[^1].X + l[^1].Z * l[^1].Z):0} m out");
                }
                if (Environment.GetEnvironmentVariable("SU_BOARD_DEBUG") == "1")
                    foreach (var c in b.Chokes)
                        foreach (var cd in m.Meta.Colliders.Where(cd => Math.Sqrt(Math.Pow(cd.X - c.X, 2) + Math.Pow(cd.Z - c.Z, 2)) < cd.R + 3))
                            Console.WriteLine($"    near gap {c.Bearing * 180 / Math.PI:0}: {cd.Kind} id {cd.Id} at ({cd.X:0.0}, {cd.Z:0.0}) hw {cd.Hw:0.00} hd {cd.Hd:0.00} rot {cd.Rot:0.00} tag {cd.Tag}; gap ({c.X:0.0}, {c.Z:0.0})");
                foreach (var l in b.Lamps) Console.WriteLine($"  lamp at ({l.X:0.0}, {l.Z:0.0}), pool {l.Pool:0} m, light {l.Light}");
            }
            if (outPath == "") continue;
            string path = seeds.Count() > 1 ? Path.Combine(Path.GetDirectoryName(Path.GetFullPath(outPath))!, $"{Path.GetFileNameWithoutExtension(outPath)}_s{seed}{Path.GetExtension(outPath)}") : outPath;
            Draw(m, path, ppm);
            Console.WriteLine($"  plan: {path}");
        }
    }

    static double MathX(double x, double z) => Math.Sqrt(x * x + z * z);

    static void Draw(MapBuild m, string path, double ppm)
    {
        var col = m.Meta.Collision();
        double ext = (m.Board?.Radius ?? ArenaGen.R) * 1.3;
        int w = (int)(ext * 2 * ppm);
        var px = new byte[w * w * 3];
        void Set(int i, int j, (byte R, byte G, byte B) c)
        {
            if (i < 0 || j < 0 || i >= w || j >= w) return;
            int o = (j * w + i) * 3;
            px[o] = c.R; px[o + 1] = c.G; px[o + 2] = c.B;
        }
        (double X, double Z) World(int i, int j) => (-ext + (i + 0.5) / ppm, ext - (j + 0.5) / ppm);
        (int I, int J) Pix(double x, double z) => ((int)((x + ext) * ppm), (int)((ext - z) * ppm));
        // Ground: walkable pale, closed dark, colliders brown, the nav's blocked cells a shade darker round them.
        for (int j = 0; j < w; j++)
            for (int i = 0; i < w; i++)
            {
                var (x, z) = World(i, j);
                var c = !m.CanStand(x, z) ? ((byte)34, (byte)44, (byte)34)
                    : col.Blocked(x, z, 0.01) ? ((byte)110, (byte)70, (byte)40)
                    : col.IsNavBlocked((int)Math.Floor(x + col.Half), (int)Math.Floor(z + col.Half)) ? ((byte)170, (byte)150, (byte)120)
                    : ((byte)214, (byte)212, (byte)200);
                Set(i, j, c);
            }
        void Line(double ax, double az, double bx, double bz, (byte, byte, byte) c, double thick = 1)
        {
            double len = Math.Sqrt((bx - ax) * (bx - ax) + (bz - az) * (bz - az));
            int n = Math.Max(1, (int)(len * ppm * 2));
            for (int k = 0; k <= n; k++)
            {
                var (i, j) = Pix(ax + (bx - ax) * k / n, az + (bz - az) * k / n);
                int t = (int)Math.Ceiling(thick / 2);
                for (int dj = -t + 1; dj < t; dj++) for (int di = -t + 1; di < t; di++) Set(i + di, j + dj, c);
                if (t <= 1) Set(i, j, c);
            }
        }
        void Ring(double cx, double cz, double r, (byte, byte, byte) c, double thick = 1)
        {
            int n = Math.Max(24, (int)(r * ppm * 6));
            for (int k = 0; k < n; k++)
            {
                double a = k * Math.PI * 2 / n, b2 = (k + 1) * Math.PI * 2 / n;
                Line(cx + Math.Cos(a) * r, cz + Math.Sin(a) * r, cx + Math.Cos(b2) * r, cz + Math.Sin(b2) * r, c, thick);
            }
        }
        foreach (var s in m.Streams)
            for (int k = 0; k + 1 < s.Length; k++) Line(s[k].X, s[k].Z, s[k + 1].X, s[k + 1].Z, (70, 120, 200), s[k].Hw * 2 * ppm);
        if (m.Board is { } b)
        {
            foreach (var l in b.Lanes)
                for (int k = 0; k + 1 < l.Length; k++) Line(l[k].X, l[k].Z, l[k + 1].X, l[k + 1].Z, (200, 150, 60), Math.Max(2, l[k].Hw * 2 * ppm * 0.5));
            Ring(b.Fold.X, b.Fold.Z, b.Fold.InnerR, (40, 90, 200));
            Ring(b.Fold.X, b.Fold.Z, b.Fold.OuterR, (40, 90, 200));
            foreach (var l in b.Lamps) { Ring(l.X, l.Z, l.Pool, (240, 200, 40), 2); Ring(l.X, l.Z, 0.8, (240, 200, 40), 3); }
            foreach (var c in b.Chokes) Ring(c.X, c.Z, 0.9, (220, 30, 30), 3);
        }
        // The start: a cross.
        Line(-2, 0, 2, 0, (0, 0, 0), 2); Line(0, -2, 0, 2, (0, 0, 0), 2);
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path))!);
        if (path.EndsWith(".pgm", StringComparison.OrdinalIgnoreCase))
        {
            using var f = File.Create(path);
            var head = System.Text.Encoding.ASCII.GetBytes($"P5\n{w} {w}\n255\n");
            f.Write(head);
            for (int k = 0; k < w * w; k++) f.WriteByte((byte)((px[k * 3] * 3 + px[k * 3 + 1] * 6 + px[k * 3 + 2]) / 10));
            return;
        }
        File.WriteAllBytes(path, Png(px, w, w));
    }

    /// <summary>An RGB image as a PNG (no filter, zlib).</summary>
    static byte[] Png(byte[] rgb, int w, int h)
    {
        var raw = new MemoryStream();
        for (int j = 0; j < h; j++) { raw.WriteByte(0); raw.Write(rgb, j * w * 3, w * 3); }
        var z = new MemoryStream();
        using (var zs = new ZLibStream(z, CompressionLevel.Optimal, true)) raw.WriteTo(zs);
        var o = new MemoryStream();
        o.Write(new byte[] { 137, 80, 78, 71, 13, 10, 26, 10 });
        void Chunk(string type, byte[] data)
        {
            var t = System.Text.Encoding.ASCII.GetBytes(type);
            o.Write(Be((uint)data.Length));
            o.Write(t); o.Write(data);
            o.Write(Be(Crc(t.Concat(data).ToArray())));
        }
        var ihdr = new byte[13];
        Be((uint)w).CopyTo(ihdr, 0); Be((uint)h).CopyTo(ihdr, 4);
        ihdr[8] = 8; ihdr[9] = 2;
        Chunk("IHDR", ihdr);
        Chunk("IDAT", z.ToArray());
        Chunk("IEND", Array.Empty<byte>());
        return o.ToArray();
    }

    static byte[] Be(uint v) => new[] { (byte)(v >> 24), (byte)(v >> 16), (byte)(v >> 8), (byte)v };

    static uint Crc(byte[] d)
    {
        uint c = 0xffffffff;
        foreach (byte x in d)
        {
            c ^= x;
            for (int k = 0; k < 8; k++) c = (c & 1) != 0 ? 0xedb88320 ^ (c >> 1) : c >> 1;
        }
        return ~c;
    }
}
