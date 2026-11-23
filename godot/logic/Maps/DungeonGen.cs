using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Maps;

/* A dungeon: hand-made rooms joined by a seeded generator (docs/design/ARPG.md 6, "authored set-piece
 * rooms joined by generated halls"; the owner, 15 November: "dungeons should not be the same
 * everytime").
 *
 * Each dungeon keeps its own set of rooms, drawn by hand: a room is a union of lobes (capsules), the
 * holes in it (a knoll, a rock spine, pillars to fight round), and its sockets: where packs rest, where
 * a cache lies, where the way out is cut. The generator lays them on a coarse grid of cells:
 *
 *   - the entrance on any edge of the square, anywhere along it;
 *   - the route, a self-avoiding walk of 8 to 10 cells, to the ruler's room at its end, the way out
 *     cut past the ruler on the far side from where she came in;
 *   - one room on the route holds the event (the map's altar), somewhere in its middle third;
 *   - two to four branches off the route, one or two rooms deep, ending in a cache (a deep branch's
 *     cache is the richer, behind a fight); some caches are guarded;
 *   - sometimes a loop: a squeeze between two route rooms that meet on the grid, a way round;
 *   - each cell's room drawn from the dungeon's set (never the same twice running), turned, mirrored
 *     and scaled.
 *
 * MapGen builds the ground, the walls and the dressing from this exactly as it does a map's, so the
 * view and the runtime (MapRun) take a dungeon as they take a map. The same seed always makes the
 * same dungeon; a new run draws a new seed. */

/// <summary>A capsule: the round-ended band from one point to another (a circle when they meet).</summary>
public readonly record struct Lobe(double X0, double Z0, double X1, double Z1, double R)
{
    public static Lobe O(double x, double z, double r) => new(x, z, x, z, r);
    /// <summary>Signed distance: negative inside.</summary>
    public double Dist(double x, double z) => MathX.DistToSegment(x, z, X0, Z0, X1, Z1) - R;
    /// <summary>Furthest reach from the room's middle.</summary>
    public double Reach => Math.Max(Math.Sqrt(X0 * X0 + Z0 * Z0), Math.Sqrt(X1 * X1 + Z1 * Z1)) + R;
    public Lobe Moved(Func<(double, double), (double, double)> f, double s)
    {
        var (a, b) = f((X0, Z0)); var (c, d) = f((X1, Z1));
        return new Lobe(a, b, c, d, R * s);
    }
}

public enum RoomRole { Entrance, Fight, Event, Side, Treasure, Boss }

/// <summary>A hand-made room: its shape, its holes and its sockets, drawn facing +Z (a boss room's
/// way out lies at +Z, away from where she comes in).</summary>
public sealed record RoomPlan(string Id, RoomRole Role, Lobe[] Shape, Lobe[] Holes, (double X, double Z)[] Packs,
    (double X, double Z)? Cache = null, (double X, double Z)? Out = null, string Dress = "", Lobe[]? Spurs = null)
{
    public double Reach => Shape.Max(l => l.Reach);
}

/// <summary>A dungeon kind: who holds it, its look, its lowest level, and its rooms.</summary>
public sealed record DungeonDef(string Id, string Name, string People, string Theme, int Floor, string Region, RoomPlan[] Rooms)
{
    /// <summary>(den-wall, 22 Nov) Whether a dungeon of this theme draws the map's flora: the den grows nothing under its roof
    /// (the view leaves its flora out: src/World/ZoneView.cs "The den grows nothing"). Where none is drawn, no flora stands
    /// solid: nothing she cannot see blocks her (MapGen's altar ring; tests/DenWallTests.cs).</summary>
    public static bool GrowsFlora(string? theme) => theme != "den";
}

/// <summary>A room as laid: its area's index, its plan, its cell, where it hangs from, its shape in the world.</summary>
public sealed record DungeonRoom(int Area, RoomPlan Plan, int Ci, int Cj, int Parent, bool OnRoute, double X, double Z, double Rot, bool Mirror, double Scale,
    Lobe[] Shape, Lobe[] Holes, Lobe[]? Spurs = null)
{
    public RoomRole Role => Plan.Role;
    public double Dist(double x, double z)
    {
        double d = Shape.Min(l => l.Dist(x, z));
        foreach (var h in Holes) d = Math.Max(d, -h.Dist(x, z));
        // Spurs: rock and root walls run in from the rim (wall, not a pit: no hole field).
        if (Spurs != null) foreach (var s in Spurs) d = Math.Max(d, -s.Dist(x, z));
        return d;
    }
}

/// <summary>What the generator lays: the rooms (one per area, in area order), the halls between them,
/// the packs' sockets, the caches and the way out.</summary>
public sealed class DungeonLayout
{
    public required DungeonDef Def;
    public required List<Area> Areas;
    public required List<DungeonRoom> Rooms;
    public required List<(int A, int B, bool Loop)> Edges;
    public required List<(double X, double Z, double Hw)[]> Halls;
    public required List<PackSpot> Sockets;
    public required List<(double X, double Z, int Area, bool Rich)> Caches;
    public required (double X, double Z) Exit;
    /// <summary>The route, in rooms' area indices, entrance to ruler.</summary>
    public required List<int> Route;

    /// <summary>The whole layout as text: cells, rooms, turns and edges (two seeds that lay the same have the same).</summary>
    public string Signature => string.Join(";", Rooms.Select(r => $"{r.Ci},{r.Cj}:{r.Plan.Id}:{Math.Round(r.Rot, 1)}{(r.Mirror ? "m" : "")}"))
        + "|" + string.Join(";", Edges.Select(e => $"{Rooms[e.A].Ci}{Rooms[e.A].Cj}-{Rooms[e.B].Ci}{Rooms[e.B].Cj}"));
    /// <summary>The room graph alone, its cells forgotten: the route's length, where each branch hangs and how deep, the
    /// event's place, the loop, and the rooms' kinds along the route.</summary>
    public string Graph
    {
        get
        {
            var at = Route.Select((a, k) => (a, k)).ToDictionary(p => p.a, p => p.k);
            var branches = Rooms.Where(r => !r.OnRoute && at.ContainsKey(r.Parent)).Select(r =>
            {
                int depth = 1; var tip = r;
                while (Rooms.FirstOrDefault(c => c.Parent == tip.Area && !c.OnRoute) is { } next) { depth++; tip = next; }
                return $"{at[r.Parent]}x{depth}";
            }).OrderBy(s => s);
            var loops = Edges.Where(e => e.Loop).Select(e => $"{at.GetValueOrDefault(e.A, -1)}~{at.GetValueOrDefault(e.B, -1)}");
            return $"{Route.Count}|{string.Join(",", branches)}|{string.Join(",", loops)}|{string.Join("", Route.Select(a => Rooms[a].Plan.Id[0]))}";
        }
    }
}

public static class DungeonGen
{
    /// <summary>Cells on a side: the square cut into 5 by 5, a room to a cell.</summary>
    public const int Grid = 5;
    const double Margin = 18;
    /// <summary>Metres kept clear between two rooms that are not joined (a wall wide enough for the wood to stand in).</summary>
    public const double Gap = 9;

    static RoomPlan R(string id, RoomRole role, Lobe[] shape, Lobe[]? holes = null, (double, double)[]? packs = null,
        (double, double)? cache = null, (double, double)? exit = null, string dress = "", Lobe[]? spurs = null)
        => new(id, role, shape, holes ?? [], packs ?? [], cache, exit, dress, spurs);

    /// <summary>(den r16 G, R15f item 11) The den lair's root-wall spurs, run in from its rim to about 9-10 m
    /// from the middle so the lair reads walled in (den_boss) from the fixed camera: 1 = on (the default),
    /// 0 = the old open 21 m bowl. Set by the Godot layer from --den-lair-spurs before a map is made.
    /// (den r16 G2, R15f item 11) 2 (the default) adds the way in as a mouth (MouthSpurs): a spur either side of
    /// the hall where it enters, so a lair turned with its way in across the frame (seed 11) shows banks there.</summary>
    public static double LairSpurs = 2;
    // Each spur a broad root at the rim and a narrower tongue in: E and W level with the middle (between the
    // pits and the way out), NE and NW either side of the way out; the S side (the way in, the pits) kept open.
    /// <summary>(den r17 G, R16 item 1) The den lair's pits laid in the fixed camera's frame, as den_boss.png's: the plan's two
    /// (2.6 m, 14.4 m out) lie off the boss frame, so the lit "pits" judged were the walkable hollows. With the halls and the
    /// mouth known, a lobed main pit (4.6-5.4 m across) and one or two smaller (2.6-3.4 m) are laid in WORLD space (the camera
    /// looks north whatever way the lair turns), the main's middle in the frame's open middle band, each 3.5 m or more clear of
    /// the ruler's spot (her arrival, the fight's middle), with 2.5 m of floor round it (rim, spurs, halls, the charge lane in,
    /// the way out). No rng drawn: the layout is unchanged. 1 (the default) = these as well as the plan's two; 0 = the plan's two.
    /// Set by the Godot layer from --den-lair-pits before a map is made.</summary>
    public static double LairPits = 1;
    /// <summary>(den r17 P3, R16 item 1) The lair's pits sized by the frame, not in metres: G's 4.8-5.3 m main drew about 300 px
    /// across in the boss frame (its lobes' rim projected 342 px; the stamped outline, a 6-harmonic fit, draws about 0.88 of
    /// that), den_boss.png's about 420. 1 (the default): the main's rim spans 435-485 px across the frame (drawn about 385-425),
    /// the smaller 240-310 (about 210-270), the size found at each spot tried (the lens shrinks a pit up the frame); where none
    /// fits, 0.9x steps down to G's. 0: G's sizes in metres. Set by the Godot layer from --den-lair-pit-px.</summary>
    public static double LairPitPx = 1;
    /// <summary>The boss frame's camera over the lair's middle (--at boss-mid, play's fixed view): pitch 62, 24.3 m off,
    /// aimed 0.8 m up her, fov 34 (vertical), 1920x1080, looking north (-Z up the frame).</summary>
    public static (double X, double Y) LairScreen(double dx, double dz)
    {
        const double pitch = 62 * Math.PI / 180, dist = 24.3, look = 0.8;
        double sp = Math.Sin(pitch), cp = Math.Cos(pitch), f = 540 / Math.Tan(17 * Math.PI / 180);
        double vy = -(look + sp * dist), vz = dz - cp * dist;
        double depth = -sp * vy - cp * vz, up = cp * vy - sp * vz;
        return (960 + f * dx / depth, 540 - f * up / depth);
    }
    /// <summary>Whether a frame pixel is clear of the HUD: the bars along the bottom, the ruler's bar at the top, the quest text and map top right.</summary>
    public static bool LairScreenClear(double x, double y) =>
        x > 20 && x < 1900 && y < 850 && y > 20 && !(y < 90 && x > 500 && x < 1420) && !(x > 1340 && y < 470);
    // The pits' shapes, unit-ish, laid turned and scaled: the main five lobes (a broad core and four bays), the small three.
    static readonly Lobe[] PitMain = [new(-0.95, -0.15, 0.85, 0.2, 1.35), Lobe.O(-0.35, 1.05, 1.0), Lobe.O(0.55, -1.0, 0.95), Lobe.O(1.75, 0.55, 0.75), Lobe.O(-1.9, -0.75, 0.7)];
    // (den r17 P3) LairPitPx's main: the five lobes laid broad (about 1.6:1), laid within 20 degrees of the frame's across: a
    // round 400 px pit stands 3 m deep into the floor and cannot clear her spot, the lanes and the spurs in the frame's band
    static readonly Lobe[] PitMainWide = [new(-1.2, 0, 1.2, 0.1, 1.15), Lobe.O(-0.2, 0.95, 0.8), Lobe.O(0.6, -0.85, 0.8), Lobe.O(2.05, 0.35, 0.7), Lobe.O(-2.1, -0.45, 0.65)];
    static readonly Lobe[] PitSmall = [new(-0.5, 0, 0.45, 0.15, 0.95), Lobe.O(0.2, 0.75, 0.6), Lobe.O(-0.75, -0.45, 0.55)];
    /// <summary>A pit's widest span across, in metres.</summary>
    public static double Across(IReadOnlyList<Lobe> pit)
    {
        double best = 0;
        for (int k = 0; k < 24; k++)
        {
            double a = k * Math.PI / 24, ux = Math.Cos(a), uz = Math.Sin(a), lo = double.MaxValue, hi = double.MinValue;
            foreach (var l in pit)
            {
                double p0 = l.X0 * ux + l.Z0 * uz, p1 = l.X1 * ux + l.Z1 * uz;
                lo = Math.Min(lo, Math.Min(p0, p1) - l.R); hi = Math.Max(hi, Math.Max(p0, p1) + l.R);
            }
            best = Math.Max(best, hi - lo);
        }
        return best;
    }
    /// <summary>Points round a pit's outline (each lobe's), for the clearances.</summary>
    public static IEnumerable<(double X, double Z)> Rim(IEnumerable<Lobe> pit)
    {
        foreach (var l in pit)
            for (int t = 0; t <= 2; t++)
            {
                double cx = l.X0 + (l.X1 - l.X0) * t / 2, cz = l.Z0 + (l.Z1 - l.Z0) * t / 2;
                for (int k = 0; k < 16; k++) yield return (cx + Math.Cos(k * Math.PI / 8) * l.R, cz + Math.Sin(k * Math.PI / 8) * l.R);
            }
    }
    /// <summary>The lair's pits in view (LairPits): see LairPits. The lair as laid (spurs and mouth on), the halls that reach it.</summary>
    static DungeonRoom LairPitsIn(DungeonRoom r, IEnumerable<(double X, double Z, double Hw)[]> halls)
    {
        const double ring = 2.5, mid = 3.5, gap = 4, lane = 3.5;
        uint h = (uint)((int)Math.Round(r.X * 37) * 73856093 ^ (int)Math.Round(r.Z * 37) * 19349663 ^ 0x5bd1e995);
        var rng = new Rng(h);
        var hs = halls.ToArray();
        // the way in: the hall's point furthest out still inside the lair's bowl; the charge runs from the middle to it.
        // The way out: its corridor from 0.4 of the way there (the bowl short of it is open floor).
        (double X, double Z) mouth = (r.X, r.Z);
        double far = -1;
        foreach (var w in hs) foreach (var p in w)
        {
            double d = MathX.Dist(p.X, p.Z, r.X, r.Z);
            if (d <= r.Shape[0].R && d > far) { far = d; mouth = (p.X, p.Z); }
        }
        var exit = Xf(r, r.Plan.Out ?? (0, 0));
        var spurs = r.Spurs ?? [];
        var laid = new List<Lobe[]>();
        bool Fits(Lobe[] pit)
        {
            foreach (var (x, z) in Rim(pit))
            {
                if (r.Shape.Min(l => l.Dist(x, z)) > -ring) return false;
                if (spurs.Any(s => s.Dist(x, z) < ring)) return false;
                if (r.Holes.Any(o => o.Dist(x, z) < gap)) return false;
                if (laid.Any(p => p.Any(o => o.Dist(x, z) < gap))) return false;
                if (MathX.Dist(x, z, r.X, r.Z) < mid) return false;
                if (MathX.DistToSegment(x, z, r.X, r.Z, mouth.X, mouth.Z) < lane) return false;
                if (MathX.DistToSegment(x, z, r.X + (exit.X - r.X) * 0.4, r.Z + (exit.Z - r.Z) * 0.4, exit.X, exit.Z) < ring) return false;
                // the hall where it comes in (inside the bowl it is the lair's floor: the charge lane above holds the way open)
                foreach (var w in hs)
                    for (int i = 1; i < w.Length; i++)
                        if (MathX.Dist(w[i].X, w[i].Z, r.X, r.Z) > r.Shape[0].R * 0.6
                            && MathX.DistToSegment(x, z, w[i - 1].X, w[i - 1].Z, w[i].X, w[i].Z) < w[i].Hw * 1.3 + ring) return false;
                var (sx, sy) = LairScreen(x - r.X, z - r.Z);
                if (!LairScreenClear(sx, sy)) return false;
            }
            return true;
        }
        Lobe[] Lay(Lobe[] shape, double across, double rot, double x, double z)
        {
            double s = across / Across(shape), c = Math.Cos(rot), n = Math.Sin(rot);
            return shape.Select(l => new Lobe(x + (l.X0 * c - l.Z0 * n) * s, z + (l.X0 * n + l.Z0 * c) * s, x + (l.X1 * c - l.Z1 * n) * s, z + (l.X1 * n + l.Z1 * c) * s, l.R * s)).ToArray();
        }
        // The main: its middle in the frame's open band, as near the fight as it may (about 6 m), low in the frame as den_boss's.
        double rot0 = rng.Range(0, Math.PI * 2), side = rng.Chance(0.5) ? -1 : 1, acrossM = rng.Range(4.8, 5.3);
        // (den r17 P3) LairPitPx: the across that spans this many px of the frame at this spot and turn (two linear steps)
        double PxWide(Lobe[] pit) { var px = Rim(pit).Select(p => LairScreen(p.X - r.X, p.Z - r.Z).X).ToArray(); return px.Max() - px.Min(); }
        Lobe[] LayPx(Lobe[] shape, double px, double rot, double x, double z)
        {
            double a = 5;
            for (int it = 0; it < 2; it++) a *= px / PxWide(Lay(shape, a, rot, x, z));
            return Lay(shape, a, rot, x, z);
        }
        double mainPx = 435 + (acrossM - 4.8) / 0.5 * 50;
        // The floor the fight's paths can use (half-metre cells): 2 m in from the rim, 1.5 m off the spurs, 2 m off every pit (its
        // carved lip and the rim's dressing, then her width), flooded from the middle; a pit is laid only if the way in, the way
        // out and all the floor reached before are still reached (no pocket cut off, no way pinched shut).
        double reach = r.Plan.Reach * r.Scale + 1;
        int nG = (int)(reach * 4) + 1;
        var baseFree = new bool[nG * nG];
        for (int j = 0; j < nG; j++)
            for (int i = 0; i < nG; i++)
            {
                double x = r.X - reach + i * 0.5, z = r.Z - reach + j * 0.5;
                baseFree[j * nG + i] = r.Shape.Min(l => l.Dist(x, z)) <= -2 && spurs.All(o => o.Dist(x, z) >= 1.5) && r.Holes.All(o => o.Dist(x, z) >= 2);
            }
        int Cell(double x, double z) => Math.Clamp((int)Math.Round((z - r.Z + reach) * 2), 0, nG - 1) * nG + Math.Clamp((int)Math.Round((x - r.X + reach) * 2), 0, nG - 1);
        var inPt = (r.X + (mouth.X - r.X) * 0.85, r.Z + (mouth.Z - r.Z) * 0.85);
        var outPt = Xf(r, (0, 19));
        (int Count, bool Ways) Flood(IEnumerable<Lobe> extra)
        {
            var holes = extra.ToArray();
            var free = new bool[nG * nG];
            for (int c = 0; c < free.Length; c++)
                free[c] = baseFree[c] && holes.All(o => o.Dist(r.X - reach + c % nG * 0.5, r.Z - reach + c / nG * 0.5) >= 2);
            var seen = new bool[nG * nG];
            var q = new Queue<int>();
            int s0 = Cell(r.X, r.Z), n = 0;
            if (free[s0]) { seen[s0] = true; q.Enqueue(s0); }
            while (q.Count > 0)
            {
                int c = q.Dequeue(); n++;
                int ci = c % nG, cj = c / nG;
                foreach (var (di, dj) in Steps)
                {
                    int ni = ci + di, nj = cj + dj, nc = nj * nG + ni;
                    if (ni < 0 || nj < 0 || ni >= nG || nj >= nG || seen[nc] || !free[nc]) continue;
                    seen[nc] = true; q.Enqueue(nc);
                }
            }
            bool Near((double X, double Z) p)
            {
                for (double ox = -2; ox <= 2; ox += 0.5)
                    for (double oz = -2; oz <= 2; oz += 0.5)
                        if (seen[Cell(p.X + ox, p.Z + oz)]) return true;
                return false;
            }
            return (n, Near(inPt) && Near(outPt));
        }
        var before = Flood([]);
        bool Open(Lobe[] pit)
        {
            var all = laid.SelectMany(p => p).Concat(pit).ToArray();
            int lost = 0;
            for (int c = 0; c < baseFree.Length; c++)
                if (baseFree[c] && all.Any(o => o.Dist(r.X - reach + c % nG * 0.5, r.Z - reach + c / nG * 0.5) < 2)) lost++;
            var after = Flood(all);
            return (after.Ways || !before.Ways) && after.Count >= before.Count - lost - 8;
        }
        Lobe[]? best = null;
        for (double shrink = 1; best == null && shrink > 0.7; shrink -= 0.1)
        {
        var mains = new List<(double S, Lobe[] Pit)>();
        for (int k = 0; k < (LairPitPx > 0 ? 12 : 6); k++)
            for (double dx = -13; dx <= 13; dx += 0.5)
                for (double dz = -9; dz <= 7; dz += 0.5)
                {
                    var (sx, sy) = LairScreen(dx, dz);
                    if (LairPitPx > 0 ? sx < 300 || sx > 1620 || sy < 280 || sy > 720 : sx < 380 || sx > 1420 || sy < 300 || sy > 700) continue;   // (den r17 P3) the bigger main needs the band's ends: 3.5 m off her spot its middle stands 7 m out
                    double d = Math.Sqrt(dx * dx + dz * dz), sc = Math.Abs(d - 6) + Math.Abs(sy - 600) / 150 + (Math.Sign(dx) == side ? 0 : 0.6) + k * 0.05;
                    var pit = LairPitPx > 0 ? LayPx(PitMainWide, mainPx * shrink, (rot0 > Math.PI ? Math.PI : 0) + (k % 2 == 0 ? 1 : -1) * (k / 2) * 0.07, r.X + dx, r.Z + dz) : Lay(PitMain, acrossM, rot0 + k * Math.PI / 3, r.X + dx, r.Z + dz);
                    // big in the frame as den_boss's (350-450 px): low enough in it that the lens does not shrink it
                    if (LairPitPx <= 0 && PxWide(pit) < 330) continue;
                    if (Fits(pit)) mains.Add((sc, pit));
                }
        best = mains.OrderBy(c => c.S).Select(c => c.Pit).Take(40).FirstOrDefault(Open);
        if (LairPitPx <= 0) break;
        }
        if (best == null) return r;
        laid.Add(best);
        // One or two smaller elsewhere in the frame, spread from the main and each other.
        int want = rng.Chance(0.65) ? 2 : 1;
        for (int n = 0; n < want; n++)
        {
            double across = rng.Range(2.6, 3.4), rot = rng.Range(0, Math.PI * 2), smallPx = 240 + (across - 2.6) / 0.8 * 70;
            Lobe[]? pick = null;
            for (double shrink = 1; pick == null && shrink > 0.7; shrink -= 0.1)
            {
            var smalls = new List<(double S, Lobe[] Pit)>();
            for (double dx = -13; dx <= 13; dx += 0.5)
                for (double dz = -9; dz <= 7; dz += 0.5)
                {
                    var (sx, sy) = LairScreen(dx, dz);
                    if (sx < 150 || sx > 1770 || sy < 150 || sy > 800) continue;
                    double spread = laid.Min(p => { var (px, py) = LairScreen(p.Average(o => o.X0) - r.X, p.Average(o => o.Z0) - r.Z); return MathX.Dist(sx, sy, px, py); });
                    double d = Math.Sqrt(dx * dx + dz * dz), sc = -Math.Min(spread, 900) / 200 + Math.Abs(d - 7.5) * 0.4;
                    var pit = LairPitPx > 0 ? LayPx(PitSmall, smallPx * shrink, rot, r.X + dx, r.Z + dz) : Lay(PitSmall, across, rot, r.X + dx, r.Z + dz);
                    if (Fits(pit)) smalls.Add((sc, pit));
                }
            pick = smalls.OrderBy(c => c.S).Select(c => c.Pit).Take(40).FirstOrDefault(Open);
            if (LairPitPx <= 0) break;
            }
            if (pick != null) laid.Add(pick);
        }
        return r with { Holes = [.. r.Holes, .. laid.SelectMany(p => p)] };
    }
    static readonly Lobe[] LairSpurPlan =
    [
        new(25, 0, 15, 1.5, 4.2), new(15, 1.5, 11.6, 2.4, 2.4),
        new(-25, 2, -15, 3, 4.2), new(-15, 3, -12, 4.2, 2.3),
        new(17, 19, 11.5, 12.5, 3.8), new(11.5, 12.5, 8.2, 9.4, 2.2),
        new(-18, 18, -12, 12, 3.8), new(-12, 12, -8.6, 8.8, 2.1),
    ];

    /// <summary>(den r16 G2, R15f item 11) The lair's way in as a mouth, as the rooms' halls open between banks: a
    /// spur either side of the hall that reaches the lair, laid along it from past the rim to about 12 m from the
    /// middle, its inner edge clear of the hall's widest (noise x1.3) by 0.6 m; pulled out along the hall until it
    /// stands 3 m clear of every pit, dropped if it cannot. No rng: the layout is unchanged.</summary>
    static Lobe[] MouthSpurs(DungeonRoom r, (double X, double Z, double Hw)[] hall)
    {
        // the hall's points by distance from the lair's middle, outward
        var pts = hall.OrderBy(p => MathX.Dist(p.X, p.Z, r.X, r.Z)).ToArray();
        (double X, double Z, double Hw) At(double rad)
        {
            for (int i = 1; i < pts.Length; i++)
            {
                double d0 = MathX.Dist(pts[i - 1].X, pts[i - 1].Z, r.X, r.Z), d1 = MathX.Dist(pts[i].X, pts[i].Z, r.X, r.Z);
                if (d1 < rad) continue;
                double t = d1 > d0 ? Math.Clamp((rad - d0) / (d1 - d0), 0, 1) : 0;
                return (pts[i - 1].X + (pts[i].X - pts[i - 1].X) * t, pts[i - 1].Z + (pts[i].Z - pts[i - 1].Z) * t, pts[i].Hw);
            }
            return pts[^1];
        }
        double R = r.Shape[0].R;
        var res = new List<Lobe>();
        foreach (double side in new[] { -1.0, 1.0 })
            foreach (double inR in new[] { 0.55, 0.62, 0.69, 0.76, 0.83 })
            {
                var a = At(R * 1.12); var m = At(R * (inR + 0.13)); var b = At(R * inR);
                double tx = a.X - b.X, tz = a.Z - b.Z, tl = Math.Max(Math.Sqrt(tx * tx + tz * tz), 1e-6);
                double nx = -tz / tl * side, nz = tx / tl * side, c = b.Hw * 1.3 + 0.6;
                var root = new Lobe(a.X + nx * (c + 3.4), a.Z + nz * (c + 3.4), m.X + nx * (c + 3.0), m.Z + nz * (c + 3.0), 3.4 * r.Scale);
                var tip = new Lobe(m.X + nx * (c + 3.0), m.Z + nz * (c + 3.0), b.X + nx * (c + 2.3), b.Z + nz * (c + 2.3), 2.3 * r.Scale);
                if (r.Holes.Any(h => root.Dist(h.X0, h.Z0) < h.R + 3 || tip.Dist(h.X0, h.Z0) < h.R + 3)) continue;
                res.Add(root); res.Add(tip);
                break;
            }
        return res.ToArray();
    }

    // ------------------------------------------------------------ the rooms --
    // Drawn by hand, in metres, facing +Z. Shared shapes first, then each dungeon's own.
    static readonly RoomPlan Bowl = R("bowl", RoomRole.Fight, [Lobe.O(0, 0, 14.5)], null, [(-6, 4), (5, -5), (3, 7)]);
    static readonly RoomPlan Twin = R("twin", RoomRole.Fight, [Lobe.O(-7, -1, 10), Lobe.O(7.5, 2, 10.5)], null, [(-8, -2), (8, 3), (0, 0)]);
    static readonly RoomPlan Gully = R("gully", RoomRole.Fight, [new(-14, 0, 14, 0, 7.5)], null, [(-10, 0), (0, 1), (10, -1)]);
    static readonly RoomPlan Ring = R("ring", RoomRole.Fight, [Lobe.O(0, 0, 16)], [Lobe.O(0, 0, 5.5)], [(11, 0), (-11, 1), (0, 11), (0, -11)]);
    static readonly RoomPlan Crook = R("crook", RoomRole.Fight, [new(-12, -7, 0, 5, 7.5), new(0, 5, 12, -4, 7.5)], null, [(-9, -4), (0, 5), (9, -2)]);
    static readonly RoomPlan Clover = R("clover", RoomRole.Fight, [Lobe.O(0, 7.5, 8.5), Lobe.O(6.5, -3.8, 8.5), Lobe.O(-6.5, -3.8, 8.5), Lobe.O(0, 0, 6)], null, [(0, 9), (8, -4), (-8, -4)]);
    static readonly RoomPlan Pillars = R("pillars", RoomRole.Fight, [Lobe.O(0, 0, 15.5)], [Lobe.O(7, 4, 2.4), Lobe.O(-7.5, 3, 2.2), Lobe.O(0, -8, 2.6)], [(0, 3), (-9, -6), (9, -5)]);
    static readonly RoomPlan Spine = R("spine", RoomRole.Fight, [new(-12, 0, 12, 0, 10.5)], [new(-5, 0, 5, 0, 2.6)], [(-9, 6), (9, -6), (0, 7)]);
    static readonly RoomPlan Event = R("hearth", RoomRole.Event, [Lobe.O(0, 0, 17)], null, [(9, 7), (-9, -7)]);
    static readonly RoomPlan Nook = R("nook", RoomRole.Side, [Lobe.O(0, 0, 8.5)], null, [], (0, 1.5));
    static readonly RoomPlan Alcove = R("alcove", RoomRole.Side, [new(0, -4, 0, 6, 6.5)], null, [(0, -2)], (0, 8));
    static readonly RoomPlan Hoard = R("hoard", RoomRole.Treasure, [Lobe.O(0, 0, 10.5), Lobe.O(0, 5, 7)], [Lobe.O(-4, -3, 1.8)], [(3, -4)], (0, 6.5));

    /// <summary>The Pack's den under Wolf Hollow: rock-walled hollows, bones in the corners, the den-mother's lair.</summary>
    public static readonly DungeonDef Hollow = new("hollow", "The Den under Wolf Hollow", "pack", "den", 5, "Wolf Hollow", [
        R("mouth", RoomRole.Entrance, [Lobe.O(0, 0, 9), new(0, 0, 0, -8, 6)], null, [], dress: "bones"),
        Bowl with { Dress = "bones" }, Twin, Gully, Ring with { Dress = "bones" }, Crook, Clover with { Dress = "bones" }, Pillars, Spine,
        Event,
        Nook with { Dress = "bones" }, Alcove with { Dress = "bones" }, Hoard with { Dress = "bones" },
        R("lair", RoomRole.Boss, [Lobe.O(0, 0, 21), new(0, 18, 0, 26, 5)], [Lobe.O(-12, -8, 2.6), Lobe.O(12, -8, 2.6)], [], exit: (0, 27), dress: "bones", spurs: LairSpurPlan),
        R("throat", RoomRole.Boss, [new(-7, -2, 7, -2, 17), new(0, 14, 0, 24, 5)], null, [], exit: (0, 25), dress: "bones"),
    ]);

    /// <summary>Redcowl's Roost, up the ravine: the Kerchiefs' camps and caches along a broken cut.</summary>
    public static readonly DungeonDef Roost = new("roost", "The Roost, up the Ravine", "kerchiefs", "ravine", 6, "Thornhollow Verge", [
        R("cut", RoomRole.Entrance, [new(0, -6, 0, 5, 7)], null, [], dress: "camp"),
        Bowl with { Dress = "camp" }, Twin with { Dress = "camp" }, Gully, Crook with { Dress = "camp" }, Spine, Pillars with { Dress = "camp" },
        R("shelf", RoomRole.Fight, [new(-13, -3, 13, -3, 8), Lobe.O(0, 5, 9)], [Lobe.O(9, 4, 2.4)], [(-9, -3), (8, -4), (0, 6)], dress: "camp"),
        Event with { Dress = "camp" },
        Nook with { Dress = "stash" }, Alcove with { Dress = "stash" }, Hoard with { Dress = "stash" },
        R("camp", RoomRole.Boss, [Lobe.O(0, 0, 20), Lobe.O(-10, 8, 9), new(0, 17, 0, 25, 5)], [Lobe.O(9, -9, 2.4)], [], exit: (0, 26), dress: "camp"),
        R("yard", RoomRole.Boss, [new(-9, 0, 9, 0, 16.5), new(0, 14, 0, 23, 5)], [Lobe.O(-10, -7, 2.2), Lobe.O(10, -7, 2.2)], [], exit: (0, 24), dress: "camp"),
    ]);

    public static readonly DungeonDef[] All = [Hollow, Roost];
    public static DungeonDef? Get(string id) => Array.Find(All, d => d.Id == id);

    // ------------------------------------------------------------ the layout --
    public static DungeonLayout Layout(DungeonDef def, Rng rng, double size)
    {
        double half = size / 2, cell = (size - Margin * 2) / Grid;
        for (int attempt = 0; ; attempt++)
        {
            var l = TryLayout(def, rng, half, cell);
            if (l != null) return l;
            if (attempt > 400) throw new InvalidOperationException($"dungeon {def.Id}: no layout");
        }
    }

    static readonly (int, int)[] Steps = [(1, 0), (-1, 0), (0, 1), (0, -1)];
    static bool InGrid(int i, int j) => i >= 0 && j >= 0 && i < Grid && j < Grid;

    static DungeonLayout? TryLayout(DungeonDef def, Rng rng, double half, double cell)
    {
        // The entrance: any edge, anywhere along it.
        int side = rng.Int(0, 3), along = rng.Int(0, Grid - 1);
        var start = side switch { 0 => (along, 0), 1 => (along, Grid - 1), 2 => (0, along), _ => (Grid - 1, along) };
        // The route: a self-avoiding walk, its ruler at least four cells from the entrance as the crow walks.
        int len = rng.Int(8, 10);
        var route = new List<(int, int)> { start };
        var used = new HashSet<(int, int)> { start };
        if (!Walk(route, used, len, rng)) return null;
        var (ei, ej) = route[^1];
        if (Math.Abs(ei - start.Item1) + Math.Abs(ej - start.Item2) < 3) return null;
        // The branches: off route rooms (never the entrance, the ruler's or the room before it), into free cells.
        int want = rng.Int(2, 4);
        var branches = new List<List<(int, int)>>();
        var parents = Enumerable.Range(1, route.Count - 3).OrderBy(_ => rng.Next()).ToList();
        foreach (int k in parents)
        {
            if (branches.Count >= want) break;
            var free = Steps.Select(s => (route[k].Item1 + s.Item1, route[k].Item2 + s.Item2)).Where(c => InGrid(c.Item1, c.Item2) && !used.Contains(c)).ToList();
            if (free.Count == 0) continue;
            var b = new List<(int, int)> { route[k], free[rng.Int(0, free.Count - 1)] };
            used.Add(b[1]);
            if (rng.Chance(0.4))
            {
                var on = Steps.Select(s => (b[1].Item1 + s.Item1, b[1].Item2 + s.Item2)).Where(c => InGrid(c.Item1, c.Item2) && !used.Contains(c)).ToList();
                if (on.Count > 0) { b.Add(on[rng.Int(0, on.Count - 1)]); used.Add(b[2]); }
            }
            branches.Add(b);
        }
        if (branches.Count < 2) return null;

        // Rooms, in the area order MapRun reads: the entrance first, the ruler's last and the route's last room
        // before it (its breath), the branches between.
        var cells = new List<((int, int) C, int ParentCell, bool OnRoute, RoomRole Role)>();
        int evAt = rng.Int(route.Count / 3, (2 * route.Count) / 3);
        for (int k = 0; k < route.Count; k++)
            cells.Add((route[k], k - 1, true, k == 0 ? RoomRole.Entrance : k == route.Count - 1 ? RoomRole.Boss : k == evAt ? RoomRole.Event : RoomRole.Fight));
        var branchCells = new List<((int, int) C, (int, int) Parent, RoomRole Role)>();
        foreach (var b in branches)
            for (int n = 1; n < b.Count; n++)
                branchCells.Add((b[n], b[n - 1], n < b.Count - 1 ? RoomRole.Fight : b.Count > 2 ? RoomRole.Treasure : RoomRole.Side));
        var order = new List<((int, int) C, bool OnRoute, RoomRole Role)>();
        order.AddRange(cells.Take(route.Count - 2).Select(c => (c.C, true, c.Role)));
        order.AddRange(branchCells.Select(c => (c.C, false, c.Role)));
        order.AddRange(cells.Skip(route.Count - 2).Select(c => (c.C, true, c.Role)));
        var index = order.Select((o, k) => (o.C, k)).ToDictionary(p => p.C, p => p.k);
        int ParentOf((int, int) c, bool onRoute)
        {
            if (onRoute) { int k = route.IndexOf(c); return k == 0 ? -1 : index[route[k - 1]]; }
            return index[branchCells.First(b => b.C == c).Parent];
        }

        // Each cell's room, from the dungeon's own set: never the same fight room twice running along a line.
        var rooms = new List<DungeonRoom>();
        string last = "";
        foreach (var (c, onRoute, role) in order)
        {
            var pool = def.Rooms.Where(r => r.Role == role).ToList();
            if (role == RoomRole.Treasure && pool.Count == 0) pool = def.Rooms.Where(r => r.Role == RoomRole.Side).ToList();
            var plan = pool.Count > 1 ? rng.Pick(pool.Where(p => p.Id != last).ToList()) : pool[0];
            if (role == RoomRole.Fight) last = plan.Id;
            int parent = ParentOf(c, onRoute);
            double cx = -half + Margin + cell * (c.Item1 + 0.5) + rng.Range(-0.08, 0.08) * cell;
            double cz = -half + Margin + cell * (c.Item2 + 0.5) + rng.Range(-0.08, 0.08) * cell;
            double rot = rng.Range(0, Math.PI * 2);
            if (role is RoomRole.Boss or RoomRole.Side or RoomRole.Treasure)
            {
                // Its far side (+Z: the way out, the cache) turned away from the room it is reached from.
                var p = rooms[parent];
                rot = Math.Atan2(cx - p.X, cz - p.Z) + rng.Range(-0.45, 0.45);
            }
            bool mirror = rng.Chance(0.5);
            double scale = role == RoomRole.Boss ? rng.Range(0.97, 1.05) : rng.Range(0.9, 1.08);
            rooms.Add(Place(rooms.Count, plan, c, parent, onRoute, cx, cz, rot, mirror, scale));
        }
        var boss = rooms[^1];
        var exit = Xf(boss, boss.Plan.Out ?? (0, 0));
        if (Math.Abs(exit.X) > half - 10 || Math.Abs(exit.Z) > half - 10)
        {
            // The way out would run off the square: turn it to the side with the most room.
            double best = double.MinValue, bestRot = boss.Rot;
            for (int t = 0; t < 16; t++)
            {
                double r = t * Math.PI / 8;
                var trial = Place(boss.Area, boss.Plan, (boss.Ci, boss.Cj), boss.Parent, true, boss.X, boss.Z, r, boss.Mirror, boss.Scale);
                var e = Xf(trial, boss.Plan.Out!.Value);
                var p = rooms[boss.Parent];
                double room = Math.Min(half - 10 - Math.Abs(e.X), half - 10 - Math.Abs(e.Z));
                double score = room > 0 ? MathX.Dist(e.X, e.Z, p.X, p.Z) : room - 100;
                if (score > best) { best = score; bestRot = r; }
            }
            rooms[^1] = boss = Place(boss.Area, boss.Plan, (boss.Ci, boss.Cj), boss.Parent, true, boss.X, boss.Z, bestRot, boss.Mirror, boss.Scale);
            exit = Xf(boss, boss.Plan.Out!.Value);
            if (Math.Abs(exit.X) > half - 8 || Math.Abs(exit.Z) > half - 8) return null;
        }

        // The edges: each room to the room it hangs from; a loop, sometimes, between two route rooms that meet.
        var edges = rooms.Where(r => r.Parent >= 0).Select(r => (r.Parent, r.Area, false)).ToList();
        var routeIdx = route.Select(c => index[c]).ToList();
        if (rng.Chance(0.45))
        {
            var pairs = new List<(int, int)>();
            for (int a = 1; a < routeIdx.Count - 2; a++)
                for (int b = a + 3; b < routeIdx.Count - 1; b++)
                {
                    var ra = rooms[routeIdx[a]]; var rb = rooms[routeIdx[b]];
                    if (Math.Abs(ra.Ci - rb.Ci) + Math.Abs(ra.Cj - rb.Cj) == 1) pairs.Add((routeIdx[a], routeIdx[b]));
                }
            if (pairs.Count > 0) { var (a, b) = rng.Pick(pairs); edges.Add((a, b, true)); }
        }
        // Rooms not joined keep a wall between them; a room that crowds another is drawn smaller, or the layout goes.
        var joined = new HashSet<(int, int)>(edges.SelectMany(e => new[] { (e.Item1, e.Item2), (e.Item2, e.Item1) }));
        for (int pass = 0; pass < 4; pass++)
        {
            bool tight = false;
            for (int a = 0; a < rooms.Count; a++)
                for (int b = a + 1; b < rooms.Count; b++)
                {
                    if (joined.Contains((a, b))) continue;
                    double gap = MathX.Dist(rooms[a].X, rooms[a].Z, rooms[b].X, rooms[b].Z) - rooms[a].Plan.Reach * rooms[a].Scale - rooms[b].Plan.Reach * rooms[b].Scale;
                    if (gap >= Gap) continue;
                    if (pass > 0 && ShapeGap(rooms[a], rooms[b]) >= Gap) continue;
                    tight = true;
                    int shrink = rooms[a].Role == RoomRole.Boss ? b : rooms[b].Role == RoomRole.Boss ? a : rooms[a].Plan.Reach * rooms[a].Scale > rooms[b].Plan.Reach * rooms[b].Scale ? a : b;
                    var s = rooms[shrink];
                    rooms[shrink] = Place(s.Area, s.Plan, (s.Ci, s.Cj), s.Parent, s.OnRoute, s.X, s.Z, s.Rot, s.Mirror, s.Scale * 0.92);
                }
            if (!tight) break;
            if (pass == 3) return null;
        }
        boss = rooms[^1];
        exit = Xf(boss, boss.Plan.Out!.Value);

        // The halls: a bowed curve from room to room, narrow enough to fight along, a loop's squeeze narrower.
        var halls = new List<(double X, double Z, double Hw)[]>();
        foreach (var (a, b, loop) in edges)
        {
            var ra = rooms[a]; var rb = rooms[b];
            double dx = rb.X - ra.X, dz = rb.Z - ra.Z, len2 = Math.Sqrt(dx * dx + dz * dz);
            double bow = rng.Range(0.05, 0.18) * len2 * rng.Sign();
            double cxp = (ra.X + rb.X) / 2 - dz / len2 * bow, czp = (ra.Z + rb.Z) / 2 + dx / len2 * bow;
            int n = Math.Max(8, (int)(len2 / 2));
            double hw = loop ? rng.Range(2.6, 3.2) : rb.Role is RoomRole.Side or RoomRole.Treasure ? rng.Range(3, 3.8) : rng.Range(3.6, 4.8);
            var pts = new (double, double, double)[n + 1];
            for (int i = 0; i <= n; i++)
            {
                double t = (double)i / n, u = 1 - t;
                pts[i] = (u * u * ra.X + 2 * u * t * cxp + t * t * rb.X, u * u * ra.Z + 2 * u * t * czp + t * t * rb.Z, hw);
            }
            halls.Add(pts);
        }
        // (den r16 G2, R15f item 11) the lair's way in as a mouth: banks either side of the hall that reaches it
        if (LairSpurs >= 2 && rooms[^1] is { Spurs: not null } br)
            for (int k = 0; k < edges.Count; k++)
                if (edges[k].Item2 == rooms.Count - 1 || edges[k].Item1 == rooms.Count - 1)
                    rooms[^1] = br = br with { Spurs = [.. br.Spurs!, .. MouthSpurs(br, halls[k])] };
        // (den r17 G, R16 item 1) the lair's pits in view, laid in the world with the halls and the mouth known
        if (LairPits > 0 && rooms[^1].Plan.Id == "lair")
            rooms[^1] = LairPitsIn(rooms[^1], Enumerable.Range(0, edges.Count).Where(k => edges[k].Item2 == rooms.Count - 1 || edges[k].Item1 == rooms.Count - 1).Select(k => halls[k]));

        // The packs' sockets: the rooms' own, and along the halls a pack every 13 m or so, none on the last hall to the ruler.
        var sockets = new List<PackSpot>();
        foreach (var r in rooms)
            foreach (var p in r.Plan.Packs)
            {
                var (x, z) = Xf(r, p);
                sockets.Add(new PackSpot(x, z, r.Area, r.Role is RoomRole.Side or RoomRole.Treasure ? rng.Range(1.0, 1.3) : rng.Range(0.9, 1.4)));
            }
        for (int k = 0; k < edges.Count; k++)
        {
            var (a, b, _) = edges[k];
            if (rooms[b].Role == RoomRole.Boss || rooms[b].Role is RoomRole.Side) continue;
            var w = halls[k];
            double run = 0, next = rng.Range(9, 14);
            for (int s = 1; s < w.Length; s++)
            {
                run += MathX.Dist(w[s].X, w[s].Z, w[s - 1].X, w[s - 1].Z);
                if (run < next) continue;
                next = run + rng.Range(11, 16);
                var p = w[s];
                if (rooms[a].Dist(p.X, p.Z) < 4 || rooms[b].Dist(p.X, p.Z) < 3) continue;
                sockets.Add(new PackSpot(p.X + rng.Range(-1, 1), p.Z + rng.Range(-1, 1), a, rng.Range(0.7, 1.1)));
            }
        }
        var caches = rooms.Where(r => r.Plan.Cache != null && r.Role is RoomRole.Side or RoomRole.Treasure)
            .Select(r => { var (x, z) = Xf(r, r.Plan.Cache!.Value); return (x, z, r.Area, r.Role == RoomRole.Treasure); }).ToList();

        var areas = rooms.Select(r => new Area(r.Area, r.Role switch
        {
            RoomRole.Entrance => AreaKind.Start, RoomRole.Boss => AreaKind.Boss, RoomRole.Event => AreaKind.Altar,
            RoomRole.Fight => AreaKind.Clearing, _ => AreaKind.Bend,
        }, r.X, r.Z, r.Role == RoomRole.Boss ? r.Plan.Shape[0].R * r.Scale : r.Plan.Reach * r.Scale)).ToList();
        return new DungeonLayout
        {
            Def = def, Areas = areas, Rooms = rooms, Edges = edges, Halls = halls, Sockets = sockets, Caches = caches, Exit = exit,
            Route = routeIdx,
        };
    }

    /// <summary>A self-avoiding walk to the length asked, by depth-first search in a random order (it backs out of dead ends).</summary>
    static bool Walk(List<(int, int)> path, HashSet<(int, int)> used, int len, Rng rng)
    {
        if (path.Count == len) return true;
        var (i, j) = path[^1];
        var steps = Steps.OrderBy(_ => rng.Next()).ToList();
        foreach (var (di, dj) in steps)
        {
            var c = (i + di, j + dj);
            if (!InGrid(c.Item1, c.Item2) || used.Contains(c)) continue;
            path.Add(c); used.Add(c);
            if (Walk(path, used, len, rng)) return true;
            path.RemoveAt(path.Count - 1); used.Remove(c);
        }
        return false;
    }

    static DungeonRoom Place(int area, RoomPlan plan, (int, int) c, int parent, bool onRoute, double x, double z, double rot, bool mirror, double scale)
    {
        var tmp = new DungeonRoom(area, plan, c.Item1, c.Item2, parent, onRoute, x, z, rot, mirror, scale, [], []);
        (double, double) F((double X, double Z) p) => Xf(tmp, p);
        return tmp with { Shape = plan.Shape.Select(l => l.Moved(F, scale)).ToArray(), Holes = plan.Holes.Select(l => l.Moved(F, scale)).ToArray(),
            Spurs = plan.Spurs != null && LairSpurs > 0 ? plan.Spurs.Select(l => l.Moved(F, scale)).ToArray() : null };
    }

    /// <summary>A point of a room's plan, in the world: mirrored, scaled, turned so +Z faces along Rot, and moved.</summary>
    public static (double X, double Z) Xf(DungeonRoom r, (double X, double Z) p)
    {
        double px = (r.Mirror ? -p.X : p.X) * r.Scale, pz = p.Z * r.Scale;
        double s = Math.Sin(r.Rot), c = Math.Cos(r.Rot);
        // Rot is a heading (atan2(dx, dz)): local +Z maps to (sin, cos).
        return (r.X + px * c + pz * s, r.Z - px * s + pz * c);
    }

    /// <summary>The narrowest gap between two rooms' shapes, by sampling their lobes' outlines.</summary>
    static double ShapeGap(DungeonRoom a, DungeonRoom b)
    {
        double best = double.MaxValue;
        foreach (var l in a.Shape)
            for (int k = 0; k <= 8; k++)
            {
                double t = k / 8.0, x = l.X0 + (l.X1 - l.X0) * t, z = l.Z0 + (l.Z1 - l.Z0) * t;
                best = Math.Min(best, b.Shape.Min(m => m.Dist(x, z)) - l.R);
            }
        return best;
    }
}
