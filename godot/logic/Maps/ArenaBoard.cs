using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Maps;

/* A table arena as a board (H1 combat teeth, item 6; data/content/boards.json, Content/Boards.cs): the walkable
 * ground cut down to what its crowd fills; a fold to hold (a clearing round a lamp, ringed by a broken wall, three
 * chokepoints in it, one facing where she starts); lanes from each gap out to the edge, kept free of cover.
 *
 * What is common to every place is made here (where the fold goes, its wall's colliders, the gaps, the lanes, the
 * lamp); the wall's dressing is the place's (its ArenaShape, in its own kit). The zone, the harness and the view read
 * the result off MapBuild.Board (and ZoneMeta.Board); `Balance.dll board` draws its plan and checks it (BoardCheck). */

/// <summary>The app can now make a table arena a board: its walkable radius, the fold to hold, the chokepoints into
/// it, the lamp at its middle and the lanes out (MapBuild.Board; null where the arena is no board). Bearings are
/// radians as Math.Atan2(z, x).</summary>
public sealed class ArenaBoard
{
    /// <summary>The walkable ground's radius in metres (the edge wanders about it).</summary>
    public double Radius;
    /// <summary>The place to hold.</summary>
    public BoardFold Fold = new();
    /// <summary>The gaps in the fold's wall: the only ways in.</summary>
    public List<BoardChoke> Chokes = new();
    /// <summary>The lamps to hold (the fold's, at its middle).</summary>
    public List<BoardLamp> Lamps = new();
    /// <summary>The lanes from each gap out to the edge (Chokes[k]'s is Lanes[k]): points along the middle, each
    /// with its half-width.</summary>
    public List<(double X, double Z, double Hw)[]> Lanes = new();
}

/// <summary>The fold: a clearing ringed by a wall `Thick` metres through, its middle line `WallR` from (X, Z).</summary>
public sealed class BoardFold
{
    public double X, Z, WallR, Thick;
    /// <summary>The open ground inside the wall, metres from the middle.</summary>
    public double InnerR => WallR - Thick / 2;
    public double OuterR => WallR + Thick / 2;
    /// <summary>Is a point inside the wall (in the fold's clearing).</summary>
    public bool Contains(double x, double z) => MathX.Dist(x, z, X, Z) < InnerR;
}

/// <summary>A chokepoint: a gap in the fold's wall at (X, Z) on its middle line, `Width` metres clear, at `Bearing`
/// from the fold's middle (pointing out).</summary>
public sealed class BoardChoke
{
    public double X, Z, Width, Bearing;
}

/// <summary>A lamp to hold: at (X, Z), its pool `Pool` metres round; `Light` is its index in ZoneMeta.Lights (to turn
/// it on and off).</summary>
public sealed class BoardLamp
{
    public double X, Z, Pool;
    public int Light = -1;
    /// <summary>The lantern's height in metres over its foot (where its life bar hangs above).</summary>
    public double Top = 3.3;
    /// <summary>Its numbers (Content/Boards.LampDef: when it catches, what it pays, who comes to douse it).</summary>
    public SurvivorUnchained.Content.Boards.LampDef Def = new();
}

/// <summary>A board's common making (a place's ArenaShape calls it: Plan in its Plan, Raise in its Dress).</summary>
public static class BoardGen
{
    /// <summary>Choose the fold, its gaps and the lanes, and keep them clear (Take, Lane). `clear` is metres from a
    /// point to the nearest thing the fold keeps off (a stream, a den).</summary>
    public static ArenaBoard Plan(ArenaGen.Builder b, Boards.Def d, Func<double, double, double> clear)
    {
        var f = d.Fold;
        var rng = b.Rng;
        double half = f.Thick / 2;
        // The fold: a seeded bearing and distance from the start, off what it keeps off, a way round behind it.
        (double Score, double A, double Off, double R) best = (double.NegativeInfinity, 0, 0, 0);
        for (int t = 0; t < 400; t++)
        {
            double a = rng.Range(0, Math.PI * 2), off = rng.Range(f.Offset[0], f.Offset[1]), r = rng.Range(f.Wall[0], f.Wall[1]);
            double cx = Math.Cos(a) * off, cz = Math.Sin(a) * off, outer = r + half;
            double s = Math.Min(off - outer - 2.5, clear(cx, cz) - outer - 4);
            for (int k = 0; k < 24 && s > best.Score; k++)
            {
                double q = k * Math.PI * 2 / 24, px = cx + Math.Cos(q) * (outer + f.ClearEdge), pz = cz + Math.Sin(q) * (outer + f.ClearEdge);
                s = Math.Min(s, b.In(px, pz) - 1);
            }
            if (s > best.Score) best = (s, a, off, r);
            if (s >= 0) break;
        }
        var board = new ArenaBoard { Radius = b.R };
        var fold = board.Fold;
        fold.X = Math.Cos(best.A) * best.Off; fold.Z = Math.Sin(best.A) * best.Off; fold.WallR = best.R; fold.Thick = f.Thick;
        // The gaps: one facing the start, the rest about evenly round, each a little off.
        double g0 = Math.Atan2(-fold.Z, -fold.X) + rng.Range(-0.15, 0.15);
        for (int k = 0; k < f.Gaps; k++)
        {
            double g = MathX.Wrap(g0 + k * Math.PI * 2 / f.Gaps + (k > 0 ? rng.Range(-f.Jitter, f.Jitter) : 0));
            board.Chokes.Add(new BoardChoke { X = fold.X + Math.Cos(g) * fold.WallR, Z = fold.Z + Math.Sin(g) * fold.WallR, Width = rng.Range(f.GapWidth[0], f.GapWidth[1]), Bearing = g });
        }
        b.Take(fold.X, fold.Z, fold.OuterR + 1.5);
        // The lanes: out of each gap, bending away to a far stretch of the edge (the start's across the board, the
        // others to either side), so the three reach the whole board.
        double ua = Math.Atan2(fold.Z, fold.X);
        foreach (var c in board.Chokes)
        {
            double side = Math.Sign(Math.Cos(ua) * Math.Sin(c.Bearing) - Math.Sin(ua) * Math.Cos(c.Bearing));
            double tb = c == board.Chokes[0] ? ua + Math.PI + rng.Range(-0.4, 0.4) : ua + side * (1.75 + rng.Range(-0.3, 0.3));
            var (tx, tz) = b.AtEdge(tb, -2);
            double hw = rng.Range(d.Lanes.Width[0], d.Lanes.Width[1]) / 2, h = c.Bearing;
            double x = fold.X + Math.Cos(h) * (fold.OuterR + 0.5), z = fold.Z + Math.Sin(h) * (fold.OuterR + 0.5);
            var pts = new List<(double, double, double)> { (x, z, hw) };
            for (int s = 0; s < 60; s++)
            {
                double want = Math.Atan2(tz - z, tx - x);
                h += Math.Clamp(MathX.Wrap(want - h), -0.3, 0.3) + rng.Range(-0.12, 0.12);
                double nx = x + Math.Cos(h) * 3, nz = z + Math.Sin(h) * 3;
                // Never back across the fold.
                if (MathX.Dist(nx, nz, fold.X, fold.Z) < fold.OuterR + 1.5)
                {
                    double away = Math.Atan2(nz - fold.Z, nx - fold.X);
                    nx = fold.X + Math.Cos(away) * (fold.OuterR + 1.5); nz = fold.Z + Math.Sin(away) * (fold.OuterR + 1.5);
                }
                (x, z) = (nx, nz);
                pts.Add((x, z, hw));
                if (b.In(x, z) < 2.5 || MathX.Dist(x, z, tx, tz) < 3) break;
            }
            var lane = pts.ToArray();
            board.Lanes.Add(lane);
            b.Lane(lane);
        }
        return board;
    }

    /// <summary>Raise the fold's wall (its colliders: boxes end to end, nothing slips through) and the lamp. `dress`
    /// is the place's: called every few metres along the wall's middle line with the point, the way it runs (a piece's
    /// rot, ArenaGen.Builder.Along), and whether it is a gap's post (the wall's end at a gap).</summary>
    public static void Raise(ArenaGen.Builder b, ArenaBoard board, Boards.Def d, Action<double, double, double, bool> dress)
    {
        var fold = board.Fold;
        double r = fold.WallR, half = fold.Thick / 2;
        var gaps = board.Chokes.OrderBy(c => c.Bearing).ToList();
        for (int k = 0; k < gaps.Count; k++)
        {
            var g = gaps[k]; var gn = gaps[(k + 1) % gaps.Count];
            // The wall's ends cut so the gap is its width clear at the wall's inner face, its narrowest (the boxes are
            // chords: their inner corners stand a little in from the circle, 0.2 m at the gap).
            double a0 = g.Bearing + Math.Asin(Math.Min(1, (g.Width + 0.2) / (2 * (r - half))));
            double a1 = gn.Bearing - Math.Asin(Math.Min(1, (gn.Width + 0.2) / (2 * (r - half))));
            if (k == gaps.Count - 1) a1 += Math.PI * 2;
            if (a1 <= a0) continue;
            int n = Math.Max(1, (int)Math.Ceiling(r * (a1 - a0) / 2.5));
            for (int i = 0; i < n; i++)
            {
                double p = a0 + (a1 - a0) * i / n, q = a0 + (a1 - a0) * (i + 1) / n;
                double px = fold.X + Math.Cos(p) * r, pz = fold.Z + Math.Sin(p) * r, qx = fold.X + Math.Cos(q) * r, qz = fold.Z + Math.Sin(q) * r;
                double len = MathX.Dist(px, pz, qx, qz), tx = (qx - px) / len, tz = (qz - pz) / len;
                // Each box over its neighbors' joints; the ends at the gaps exactly where they are cut.
                double lo = i == 0 ? 0 : 0.35, hi = i == n - 1 ? 0 : 0.35;
                double mx = (px + qx) / 2 + tx * (hi - lo) / 2, mz = (pz + qz) / 2 + tz * (hi - lo) / 2;
                b.Slab(mx, mz, len / 2 + (lo + hi) / 2, half, Math.Atan2(tz, tx));
            }
            // The dressing, every few metres (FoldDef.Dress), a post at either end.
            int m = Math.Max(1, (int)Math.Round(r * (a1 - a0) / d.Fold.Dress));
            for (int i = 0; i <= m; i++)
            {
                double p = a0 + (a1 - a0) * i / m;
                double x = fold.X + Math.Cos(p) * r, z = fold.Z + Math.Sin(p) * r;
                double tx = -Math.Sin(p), tz = Math.Cos(p);
                dress(x, z, Math.Atan2(-tz, tx), i == 0 || i == m);
            }
            // Each end a door light, a little in from the post so the gap and the wall's inner face both catch it.
            var door = d.Fold.Door;
            if (door.Energy > 0)
                foreach (double p in new[] { a0, a1 })
                {
                    double dr = r - door.In;
                    b.Glow(fold.X + Math.Cos(p) * dr, fold.Z + Math.Sin(p) * dr, door.Color, door.Energy, height: door.Height, flicker: 0.12, range: door.Range);
                }
        }
        // The lamp at the middle.
        var l = d.Lamp;
        double rot = b.Rng.Range(0, Math.PI * 2);
        b.Piece(l.Piece, fold.X, fold.Z, rot, l.Scale);
        b.Block(fold.X, fold.Z, 0.3 * l.Scale);
        // Its light at the flame in its glass (the piece turned by rot about up: its own +z is (sin, cos) on the ground),
        // reaching past the wall so the wall's inner faces are lit by it.
        double hx = fold.X, hz = fold.Z, hy = l.Height;
        if (l.Head.Length == 3)
        {
            hx += (Math.Cos(rot) * l.Head[0] + Math.Sin(rot) * l.Head[2]) * l.Scale;
            hz += (-Math.Sin(rot) * l.Head[0] + Math.Cos(rot) * l.Head[2]) * l.Scale;
            hy = l.Head[1] * l.Scale;
        }
        double range = l.Reach > 0 ? fold.WallR + l.Reach : 0;
        int light = b.Glow(hx, hz, l.Color, l.Energy, height: hy + (b.HeightAt(fold.X, fold.Z) - b.HeightAt(hx, hz)), flicker: l.Flicker, range: range, core: l.Core * l.Scale);
        board.Lamps.Add(new BoardLamp { X = fold.X, Z = fold.Z, Pool = l.Pool, Light = light, Def = l, Top = 3.3 * l.Scale });
    }
}

/// <summary>The app can now check a board by numbers (the harness's `board`, the tests): the walkable ground, the
/// fold reached only through its gaps, each gap's clear width.</summary>
public static class BoardCheck
{
    /// <summary>A gap: its bearing, its width as made, clear collider to collider at its narrowest, nav cells open
    /// across it, and whether the fold reaches the outside through it alone.</summary>
    public sealed record Gap(double Bearing, double Width, double ClearWidth, int NavCells, bool Passable);
    /// <summary>Open cells (walkable and off the foes' nav colliders), open cells inside the fold, whether the fold
    /// leaks with every gap shut, the start outside the wall, the fold reached from the start.</summary>
    public sealed record Result(int Open, int FoldInside, bool Leaks, bool StartOutside, bool FoldReached, List<Gap> Gaps);

    /// <summary>Open ground (walkable, off every collider as the foes' nav sees it), flooded: the fold's inside with
    /// its gaps' mouths shut must not reach the outside; each gap alone open must.</summary>
    public static Result Measure(MapBuild m)
    {
        var col = m.Meta.Collision();
        int n = col.NavSize;
        double h = col.Half;
        var open = new bool[n * n];
        int total = 0;
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                double x = -h + i + 0.5, z = -h + j + 0.5;
                if (m.CanStand(x, z) && !col.IsNavBlocked(i, j)) { open[j * n + i] = true; total++; }
            }
        var bd = m.Board;
        if (bd == null) return new Result(total, 0, false, true, false, new());
        var fold = bd.Fold;
        int Cell(double x, double z) => (int)Math.Floor(z + h) * n + (int)Math.Floor(x + h);
        (double X, double Z) At(int idx) => (-h + idx % n + 0.5, -h + idx / n + 0.5);
        bool Mouth(int idx, BoardChoke c)
        {
            var (x, z) = At(idx);
            double d = MathX.Dist(x, z, fold.X, fold.Z);
            return d > fold.InnerR - 1.5 && d < fold.OuterR + 1.5 && MathX.Dist(x, z, c.X, c.Z) < c.Width / 2 + 2.5;
        }
        bool Outside(int idx)
        {
            var (x, z) = At(idx);
            return MathX.Dist(x, z, fold.X, fold.Z) > fold.OuterR + 1.5;
        }
        HashSet<int> Flood(int s0, Func<int, bool> shut)
        {
            var seen = new HashSet<int>();
            if (s0 < 0 || s0 >= open.Length || !open[s0]) return seen;
            var todo = new Queue<int>();
            seen.Add(s0); todo.Enqueue(s0);
            while (todo.Count > 0)
            {
                int c = todo.Dequeue(), ci = c % n, cj = c / n;
                foreach (var (di, dj) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                {
                    int ni = ci + di, nj = cj + dj;
                    if (ni < 0 || nj < 0 || ni >= n || nj >= n) continue;
                    int k = nj * n + ni;
                    if (!open[k] || shut(k) || !seen.Add(k)) continue;
                    todo.Enqueue(k);
                }
            }
            return seen;
        }
        // From beside the lamp (its own post is a collider).
        int c0 = Cell(fold.X + 2.5, fold.Z);
        bool leaks = Flood(c0, k => bd.Chokes.Any(c => Mouth(k, c))).Any(Outside);
        int inside = 0;
        for (int k = 0; k < open.Length; k++)
            if (open[k] && fold.Contains(At(k).X, At(k).Z)) inside++;
        var gaps = new List<Gap>();
        foreach (var c in bd.Chokes)
        {
            bool passable = Flood(c0, k => bd.Chokes.Any(o => o != c && Mouth(k, o))).Any(Outside);
            // Clear width: round the wall's run through the gap (at its inner face, middle and outer face), from the
            // last open point either side, straight across.
            double clearW = double.MaxValue;
            foreach (double rr in new[] { fold.InnerR + 0.05, fold.WallR, fold.OuterR - 0.05 })
            {
                var ends = new List<(double X, double Z)>();
                foreach (int sgn in new[] { -1, 1 })
                    for (double s = 0; s < 12; s += 0.02)
                    {
                        double a = c.Bearing + sgn * s / rr, x = fold.X + Math.Cos(a) * rr, z = fold.Z + Math.Sin(a) * rr;
                        if (col.Blocked(x, z, 0.01)) { ends.Add((x, z)); break; }
                    }
                clearW = Math.Min(clearW, ends.Count == 2 ? MathX.Dist(ends[0].X, ends[0].Z, ends[1].X, ends[1].Z) : double.PositiveInfinity);
            }
            // Nav cells open across it, round the wall's middle line.
            var across = new HashSet<int>();
            for (double s = -8; s <= 8; s += 0.25)
            {
                double a = c.Bearing + s / fold.WallR;
                int k = Cell(fold.X + Math.Cos(a) * fold.WallR, fold.Z + Math.Sin(a) * fold.WallR);
                if (k >= 0 && k < open.Length && open[k]) across.Add(k);
            }
            int navW = across.Count;
            gaps.Add(new Gap(c.Bearing, c.Width, clearW, navW, passable));
        }
        bool startOut = MathX.Dist(0, 0, fold.X, fold.Z) > fold.OuterR;
        int st = Cell(0, 0);
        if (!open[st]) st = Cell(1.5, 0);
        bool reached = Flood(st, _ => false).Contains(c0);
        return new Result(total, inside, leaks, startOut, reached, gaps);
    }
}
