using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Maps;

/* A map: a place made for one run, from a seed. Clearings strung along a
 * winding way across a square of wild country, joined by paths between
 * walls of forest and rock; the first clearing is where you come in, the
 * last is the boss's, and some between hold an altar that calls the horde.
 * Everything the zone's build would have exported is made here instead: the
 * ground's heights and paint, where every tree, rock and fire stands, the
 * walls as colliders, the places. The view draws it as it draws any zone;
 * the runtime (Play/Zones/MapRun.cs) fills it with what lives there. */

/// <summary>A map as offered on the table: where it leads, how hard, and
/// the oaths it is sworn under (its affixes).</summary>
public sealed class MapSpec
{
    public int Seed;
    public int Tier = 1;
    public string Theme = "wood";
    public List<string> Oaths = new();
    public bool Night = true;
    public string Name = "";
    /// <summary>An arena rather than a map: one great clearing ringed by
    /// forest, cover scattered through it, for a survivors fight.</summary>
    public bool Arena;
    /// <summary>Who holds it (an arena's cover is theirs: the Risen's barrow
    /// field, the Kerchiefs' raided camp, the Lamplings' dig, the Pack's dead wood).</summary>
    public string People = "pack";
    /// <summary>An arena's mood (ArenaPlaces.Moods: ashen, drowned, moonless...);
    /// empty, it is read from the name.</summary>
    public string Mood = "";
    /// <summary>A Wayfinder's map: how many clearings stand between the start and the ruler's (and
    /// how many of them hold altars). 0: the old map of fourteen clearings and three altars. The
    /// way between is the same snake, cut shorter, its other turns only bends in the way.</summary>
    public int Clearings, AltarCount;
    /// <summary>An arena made to a story fight's own place (Play/Story: its outline, its gates and
    /// points), by the fight's id; empty, the round ember arena.</summary>
    public string Story = "";
    /// <summary>A story night (ArenaSpec.Story), with a place of its own or not: never made a board (Content/Boards).</summary>
    public bool StoryNight;
    /// <summary>A dungeon's kind (DungeonGen: "hollow", "roost"): hand-made rooms joined by the seed, not the snake.</summary>
    public string Dungeon = "";
}

/// <summary>A Bend: a widening of the way where it turns, with nothing placed in it but the way's own.</summary>
public enum AreaKind { Start, Clearing, Altar, Boss, Bend }

/// <summary>A clearing: where it is, how big, what it is for.</summary>
public sealed record Area(int Index, AreaKind Kind, double X, double Z, double R);

/// <summary>Where a pack waits, and how big it is relative to the map's own.</summary>
public sealed record PackSpot(double X, double Z, int Area, double Size);

/// <summary>A piece of the nature kit where it stands (the view's flora).</summary>
public sealed record FloraPlace(string Kind, string Piece, double X, double Y, double Z, double Rot, double Scale);

/// <summary>A kit piece set down (the view's props: 'kit/Piece').</summary>
public sealed record PropPlace(string Id, double X, double Y, double Z, double Rot, double Scale);

/// <summary>A kind of flora as the Verge has it: its piece(s), its scale,
/// its look (wind, leaf colours, moss).</summary>
public sealed record FloraKind(string Kind, string[] Pieces, double Scale, double Wind, string? LeavesA, string? LeavesB, double LeavesAmount, double Moss);

/// <summary>A map, made: everything the view and the runtime need.</summary>
public sealed class MapBuild
{
    public required MapSpec Spec;
    public required ZoneMeta Meta;
    public required Heightfield Ground;
    public required int SplatRes;
    /// <summary>RGBA, row by row from -z: dirt, setts, blight, mud (the terrain shader's paint).</summary>
    public required byte[] Splat;
    public required List<FloraPlace> Flora;
    public required List<PropPlace> Props;
    /// <summary>Pieces the zone sets down as it begins (KayKit and props, made
    /// in play): an arena's graves, walls, rubble, lanterns.</summary>
    public List<PropPlace> Pieces = new();
    public required Dictionary<string, FloraKind> Kinds;
    /// <summary>An arena's place (its ground, its night), or null for a map.</summary>
    public ArenaPlace? Place;
    /// <summary>An arena's second paint, as Splat: R wet, G the ember's char,
    /// B trodden, A the ground's second material (ArenaGen).</summary>
    public byte[]? Splat2;
    /// <summary>An arena's third paint: R moss, G the slurry's glow (ArenaGen).</summary>
    public byte[]? Splat3;
    /// <summary>An arena's grass, one byte a texel as Splat: how thick it grows.</summary>
    public byte[]? Grass;
    /// <summary>An arena's fallen leaves, one byte a texel as Grass: how thick they lie.</summary>
    public byte[]? Leaves;
    /// <summary>An arena's edge, all the way round: (x, z) every two degrees.</summary>
    public List<(double X, double Z)> Rim = new();
    /// <summary>Still water laid in an arena (a stream's course): points along
    /// its middle, each with its half-width; the water's top is HeightAt + Depth.</summary>
    public List<(double X, double Z, double Hw)[]> Streams = new();
    /// <summary>Rails laid in an arena (the Dig's): points along their middle, a metre apart.</summary>
    public List<(double X, double Z, double Hw)[]> Rails = new();
    /// <summary>Where an arena breathes smoke up out of the ground (the Dig's pit): middle and radius.</summary>
    public List<(double X, double Z, double R)> Vents = new();
    /// <summary>An arena's metres inside its edge (negative outside), as the heights.</summary>
    public double[]? Inside;
    /// <summary>A story place's gates (id, from, to): the ember burning across a way until its stage is won.</summary>
    public List<(string Id, double X0, double Z0, double X1, double Z1)> Gates = new();
    /// <summary>A story place's fires by point id (a deadfall): the light its flames burn with (Meta.Lights).</summary>
    public Dictionary<string, int> FireLights = new();
    /// <summary>A table arena made a board (ArenaBoard.cs: the fold, its chokepoints, the lamp, the lanes), or null.</summary>
    public ArenaBoard? Board;
    public required List<Area> Areas;
    public required List<PackSpot> Packs;
    /// <summary>A dungeon's rooms, halls, caches and way out (DungeonGen); null on a map.</summary>
    public DungeonLayout? Dungeon;
    /// <summary>A dungeon's theme ("den", "ravine"; DungeonDef.Theme), "" on a map: the view builds its walls, floor and light by it.</summary>
    public string DungeonTheme = "";
    /// <summary>A dungeon's walls as a field, Res by Res as the heights: metres inside the walkable edge (negative
    /// outside, clamped to -16..8), smooth (the rooms' and halls' own distances, not the walkable cells), so the
    /// view's wall mass follows the edge without the grid's steps. Null on a map.</summary>
    public float[]? WallField;
    /// <summary>A dungeon's holes as a field, as WallField: metres outside the nearest hole (negative inside it),
    /// clamped to -8..8. The den sinks them into pits, the ravine raises them as rock. Null on a map.</summary>
    public float[]? HoleField;
    /// <summary>The ways between the clearings, in order: from area k to area k + 1, point by point
    /// (where to walk, and how wide it is).</summary>
    public List<(double X, double Z, double Hw)[]> Ways = new();
    /// <summary>Can the survivor stand here: res by res, 1 m apart, as the heights.</summary>
    public required bool[] Walkable;
    public Area Start => Areas[0];
    public Area Boss => Areas[^1];
    public IEnumerable<Area> Altars => Areas.Where(a => a.Kind == AreaKind.Altar);

    /// <summary>The dev arrival "at the ruler" (the game's and the harness's --at boss): the south edge of its clearing, a metre
    /// in, moved to the nearest open standing ground that leads to the clearing's middle. The plain edge point lay inside the
    /// den's rock (hollow seed 1: she walked through 6 m of stone and out of the clearing, and the ruler never reached her).</summary>
    public (double X, double Z) BossEdge(CollisionWorld w, double body = 0.6)
    {
        var bc = Boss;
        double x0 = bc.X, z0 = bc.Z - bc.R + 1;
        var flow = new FlowField(w, (int)Math.Ceiling(bc.R + 8));
        flow.Update(bc.X, bc.Z, true);
        bool Ok(double x, double z) => CanStand(x, z) && !w.Blocked(x, z, body) && !double.IsPositiveInfinity(flow.DistanceAt(x, z));
        if (Ok(x0, z0)) return (x0, z0);
        for (double r = 0.5; r <= bc.R; r += 0.5)
            for (int k = 0, n = Math.Max(8, (int)(r * 12)); k < n; k++)
            {
                // (nearest the clearing's middle first, at each ring: into the clearing, not round its back)
                double a = Math.PI / 2 + (k % 2 == 0 ? 1 : -1) * ((k + 1) / 2) * Math.PI * 2 / n;
                double x = x0 + Math.Cos(a) * r, z = z0 + Math.Sin(a) * r;
                if (Ok(x, z)) return (x, z);
            }
        return (bc.X, bc.Z);
    }

    public bool CanStand(double x, double z)
    {
        int res = Meta.Res;
        int i = (int)Math.Round(x + Meta.Size / 2), j = (int)Math.Round(z + Meta.Size / 2);
        return i >= 0 && j >= 0 && i < res && j < res && Walkable[j * res + i];
    }
}

public static class MapGen
{
    /// <summary>The square of country a map is cut from, metres across.</summary>
    public const double Size = 300;
    internal const int Res = 301;
    /// <summary>The clearings stand in a Grid by Grid square, walked as a snake.</summary>
    const int Grid = 4;
    internal const int SplatRes = 512;
    const double Margin = 16;
    /// <summary>An arena's clearing, metres from its middle to its edge (give or take the edge's wander).</summary>
    public const double ArenaR = 84;

    public static MapBuild Generate(MapSpec spec)
    {
        // An arena is a place of its own people's (ArenaGen).
        if (spec.Arena) return ArenaGen.Generate(spec);
        var rng = new Rng((uint)spec.Seed ^ 0x5bd1e995u);
        var noise = new Noise2D((uint)spec.Seed);
        double half = Size / 2;

        // ---------------------------------------------------------- layout --
        // A snake through a grid of cells: the way crosses the whole square
        // and back, and back again, so the map is long for its size.
        var lay = spec.Dungeon != "" ? DungeonGen.Layout(DungeonGen.Get(spec.Dungeon) ?? throw new ArgumentException($"no dungeon {spec.Dungeon}"), rng, Size) : null;
        var order = lay != null ? new List<(int, int)>() : Snake(rng);
        // A map's way is cut to its clearings (the experience lead's shape: 9-10 minutes at tiers 1-2,
        // 10-12 from 3, a pack every 13-15 s): 15 turns of the snake for three clearings, 14 for four
        // (they are bigger fights), all 16 for five. (12 turns for three measured 7 minutes.)
        if (spec.Clearings > 0) order = order.Take(Math.Min(order.Count, spec.Clearings switch { 3 => 15, 4 => 14, _ => 16 })).ToList();
        double cell = (Size - Margin * 2) / Grid;
        var areas = new List<Area>();
        for (int k = 0; k < order.Count; k++)
        {
            var (ci, cj) = order[k];
            double cx = -half + Margin + cell * (ci + 0.5) + rng.Range(-0.18, 0.18) * cell;
            double cz = -half + Margin + cell * (cj + 0.5) + rng.Range(-0.18, 0.18) * cell;
            var kind = k == 0 ? AreaKind.Start : k == order.Count - 1 ? AreaKind.Boss : AreaKind.Clearing;
            double r = kind switch { AreaKind.Start => 11, AreaKind.Boss => 24, _ => rng.Range(14, 20) };
            areas.Add(new Area(k, kind, cx, cz, r));
        }
        if (lay != null) areas = lay.Areas;
        // Three of the clearings between hold altars: early, midway, late.
        int na = areas.Count;
        if (spec.Clearings == 0 && lay == null) foreach (int k in new[] { rng.Int((int)(na * 0.15), (int)(na * 0.25)), rng.Int((int)(na * 0.4), (int)(na * 0.5)), rng.Int((int)(na * 0.65), (int)(na * 0.75)) })
            areas[k] = areas[k] with { Kind = AreaKind.Altar, R = Math.Max(areas[k].R, 17) };
        // A Wayfinder's map: its clearings spread evenly along the way, the rest of the turns bends;
        // the altars among the clearings, never the first (the way is learned before its question).
        if (spec.Clearings > 0 && lay == null)
        {
            int between = na - 2, n = Math.Min(spec.Clearings, between);
            var at = Enumerable.Range(0, n).Select(i => 1 + (int)Math.Round((i + 0.5) * between / n - 0.5)).ToList();
            for (int k = 1; k < na - 1; k++)
                if (!at.Contains(k)) areas[k] = areas[k] with { Kind = AreaKind.Bend, R = rng.Range(8, 10) };
            int altars = Math.Clamp(spec.AltarCount, 0, Math.Max(0, n - 1));
            for (int i = 0; i < altars; i++)
            {
                int k = at[altars == 1 ? n / 2 : 1 + (int)Math.Round(i * (n - 2) / (double)(altars - 1))];
                areas[k] = areas[k] with { Kind = AreaKind.Altar, R = Math.Max(areas[k].R, 17) };
            }
        }

        // The ways between: a curve from each clearing to the next, bowed to one side.
        var ways = lay?.Halls ?? new List<(double X, double Z, double Hw)[]>();
        for (int k = 0; lay == null && k + 1 < areas.Count; k++)
        {
            var a = areas[k]; var b = areas[k + 1];
            double mx = (a.X + b.X) / 2, mz = (a.Z + b.Z) / 2;
            double dx = b.X - a.X, dz = b.Z - a.Z, len = Math.Sqrt(dx * dx + dz * dz);
            double bow = rng.Range(0.12, 0.3) * len * rng.Sign();
            double cxp = mx - dz / len * bow, czp = mz + dx / len * bow;
            int n = Math.Max(8, (int)(len / 2));
            var pts = new (double, double, double)[n + 1];
            double hw0 = rng.Range(4.5, 6.5);
            for (int i = 0; i <= n; i++)
            {
                double t = (double)i / n, u = 1 - t;
                double x = u * u * a.X + 2 * u * t * cxp + t * t * b.X;
                double z = u * u * a.Z + 2 * u * t * czp + t * t * b.Z;
                // Wider and narrower as it goes: a way you fight along, not a corridor.
                double hw = hw0 * (1 + 0.35 * noise.Noise(x * 0.04 + 11, z * 0.04));
                pts[i] = (x, z, hw);
            }
            ways.Add(pts);
        }

        // ------------------------------------------------------ walkable --
        var walk = new bool[Res * Res];
        var inside = new double[Res * Res];         // how far in from the edge, where walkable
        var trailN = new double[Res * Res];         // distance from a way's middle, in its half-widths
        var wallIn = new double[Res * Res];         // a dungeon's edge before its holes (the wall mesh's field)
        var holeD = new double[Res * Res];          // a dungeon's nearest hole's distance (negative inside), 99 if none near
        System.Threading.Tasks.Parallel.For(0, Res, j =>
        {
            for (int i = 0; i < Res; i++)
            {
                double x = i - half, z = j - half;
                double edge = double.MinValue;      // > 0: walkable, by how much
                double tn = 9;
                if (lay != null)
                    // A dungeon's rooms as drawn, their edges wandering a metre or two (holes stay holes).
                    foreach (var r in lay.Rooms)
                    {
                        if (Math.Abs(x - r.X) > 40 || Math.Abs(z - r.Z) > 40) continue;
                        edge = Math.Max(edge, -r.Dist(x, z) + 1.5 * noise.Noise(x * 0.11 + r.Area * 5.1, z * 0.11));
                    }
                else foreach (var a in areas)
                {
                    double d = MathX.Dist(x, z, a.X, a.Z);
                    double ang = Math.Atan2(z - a.Z, x - a.X);
                    double r = a.R * (1 + 0.16 * noise.Noise(Math.Cos(ang) * 1.7 + a.Index * 5.1, Math.Sin(ang) * 1.7));
                    edge = Math.Max(edge, r - d);
                }
                foreach (var w in ways)
                    for (int s = 0; s + 1 < w.Length; s++)
                    {
                        var (ax, az, ah) = w[s]; var (bx, bz, bh) = w[s + 1];
                        if (Math.Abs(x - ax) > 12 && Math.Abs(x - bx) > 12) continue;
                        if (Math.Abs(z - az) > 12 && Math.Abs(z - bz) > 12) continue;
                        double d = MathX.DistToSegment(x, z, ax, az, bx, bz);
                        // (a dungeon's halls wander in width as a map's ways do, by the noise here)
                        double hwk = lay != null ? (ah + bh) / 2 * (1 + 0.3 * noise.Noise(x * 0.05 + 11, z * 0.05)) : (ah + bh) / 2;
                        edge = Math.Max(edge, hwk - d);
                        tn = Math.Min(tn, d / hwk);
                    }
                // A room's holes stand even where a hall runs into them.
                double hd = 99;
                wallIn[j * Res + i] = edge;
                if (lay != null) foreach (var r in lay.Rooms) foreach (var h in r.Holes)
                {
                    double dh = h.Dist(x, z);
                    hd = Math.Min(hd, dh);
                    edge = Math.Min(edge, dh);
                }
                holeD[j * Res + i] = hd;
                bool inBounds = Math.Abs(x) < half - 6 && Math.Abs(z) < half - 6;
                walk[j * Res + i] = inBounds && edge > 0;
                inside[j * Res + i] = edge;
                trailN[j * Res + i] = tn;
            }
        });
        // Distance outside, in metres, from every cell to the nearest walkable one.
        var outside = DistanceOut(walk);

        // --------------------------------------------------------- ground --
        var heights = new float[Res * Res];
        for (int j = 0; j < Res; j++)
            for (int i = 0; i < Res; i++)
            {
                double x = i - half, z = j - half;
                double roll = noise.Fbm(x * 0.012 + 3.1, z * 0.012 - 1.7, 3) * 2.2;
                double d = outside[j * Res + i];
                // The ground climbs away from the way into banks, knolls and rock.
                double bank = lay != null
                    // A dungeon's walls are meshes (DungeonWalls), not a bank: the floor stays as rolled.
                    ? 0
                    : MathX.Smoothstep(0.5, 12, d) * (4.5 + 3 * noise.Fbm(x * 0.03, z * 0.03, 3))
                    + MathX.Smoothstep(10, 40, d) * 3 * (1 + noise.Ridged(x * 0.02 + 7, z * 0.02, 3));
                heights[j * Res + i] = (float)(roll + bank);
            }
        // Clearings lie level-ish: pulled toward their own middle's height.
        foreach (var a in areas)
        {
            double h0 = heights[Idx(a.X, a.Z, half)];
            for (int j = 0; j < Res; j++)
                for (int i = 0; i < Res; i++)
                {
                    double d = MathX.Dist(i - half, j - half, a.X, a.Z);
                    if (d > a.R + 6) continue;
                    double k = 1 - MathX.Smoothstep(a.R * 0.7, a.R + 6, d);
                    heights[j * Res + i] = (float)MathX.Lerp(heights[j * Res + i], h0 + Math.Min(0, heights[j * Res + i] - h0) * 0.3, k * 0.85);
                }
        }
        // The den's holes sink into pits, a metre down at the rim and flat below (after the clearings' pull, which
        // would shallow them).
        if (lay != null && lay.Def.Theme == "den")
            for (int k = 0; k < heights.Length; k++)
                heights[k] -= (float)(2.4 * MathX.Smoothstep(0.3, -1.6, holeD[k]));
        var ground = new Heightfield(Size, Res, heights);

        // ---------------------------------------------------------- paint --
        var splat = new byte[SplatRes * SplatRes * 4];
        double ps = Size / SplatRes;
        var marked = areas.Where(a => a.Kind is AreaKind.Altar or AreaKind.Boss).ToArray();
        System.Threading.Tasks.Parallel.For(0, SplatRes, j =>
        {
            for (int i = 0; i < SplatRes; i++)
            {
                double x = -half + (i + 0.5) * ps, z = -half + (j + 0.5) * ps;
                double inn = Bilinear(inside, x, z, half);
                double n1 = noise.Noise(x * 0.09, z * 0.09), n2 = noise.Noise(x * 0.23 + 4, z * 0.23);
                // A trodden line down the middle of each way; worn patches in the clearings.
                double trail = 1 - MathX.Smoothstep(0.25, 0.6, Bilinear(trailN, x, z, half) + n2 * 0.14);
                double dirt = Math.Max(trail * 0.85, MathX.Smoothstep(0.3, 0.8, n1) * MathX.Smoothstep(2, 8, inn) * 0.6);
                // A dungeon's floors are trodden: the den's bare earth with a little grass left in its corners, the
                // ravine's worn floor greener at its walls.
                if (lay != null)
                    dirt = Math.Max(dirt, MathX.Smoothstep(-0.4, 3, inn) * MathX.Smoothstep(-0.7, 0.1, n1 + n2 * 0.4) * (lay.Def.Theme == "den" ? 0.9 : 0.7));
                double setts = 0, blight = 0, mud = 0;
                foreach (var a in marked)
                {
                    double d = MathX.Dist(x, z, a.X, a.Z);
                    if (a.Kind == AreaKind.Altar)
                    {
                        setts = Math.Max(setts, 1 - MathX.Smoothstep(4.2, 5.2, d + n2 * 0.5));
                        blight = Math.Max(blight, (1 - MathX.Smoothstep(5, 13, d)) * MathX.Smoothstep(0.1, 0.6, n1 + 0.3));
                    }
                    else if (a.Kind == AreaKind.Boss)
                    {
                        blight = Math.Max(blight, (1 - MathX.Smoothstep(a.R * 0.5, a.R + 4, d)) * MathX.Smoothstep(-0.2, 0.5, n1));
                        mud = Math.Max(mud, (1 - MathX.Smoothstep(3, 9, d)) * 0.8);
                    }
                }
                double wet = MathX.Smoothstep(0.55, 0.8, noise.Noise(x * 0.05 - 9, z * 0.05)) * MathX.Smoothstep(-1, 2, inn);
                mud = Math.Max(mud, wet * 0.9);
                int o = (j * SplatRes + i) * 4;
                splat[o] = B(dirt); splat[o + 1] = B(setts); splat[o + 2] = B(blight); splat[o + 3] = B(mud);
            }
        });

        // ----------------------------------------------------------- flora --
        var kinds = Catalog();
        var flora = new List<FloraPlace>();
        var props = new List<PropPlace>();
        void Put(string kind, double x, double z, double scale = 1, double sink = 0)
        {
            var k = kinds[kind];
            flora.Add(new FloraPlace(kind, k.Pieces[rng.Int(0, k.Pieces.Length - 1)], x, ground.HeightAt(x, z) - sink, z,
                rng.Range(0, Math.PI * 2), k.Scale * scale * rng.Range(0.85, 1.2)));
        }
        // The same, turned as asked (a trunk laid along a wall).
        void PutAt(string kind, double x, double z, double rot, double scale = 1, double sink = 0)
        {
            var k = kinds[kind];
            flora.Add(new FloraPlace(kind, k.Pieces[rng.Int(0, k.Pieces.Length - 1)], x, ground.HeightAt(x, z) - sink, z, rot, k.Scale * scale * rng.Range(0.9, 1.1)));
        }
        string[] trees = spec.Theme switch
        {
            "blight" => new[] { "dead", "dead", "pine", "autumn" },
            "autumn" => new[] { "autumn", "autumn", "broadleaf", "pine" },
            _ => new[] { "pine", "pine", "broadleaf", "autumn", "pine", "broadleaf" },
        };
        // Poisson-ish: a jittered grid, thinned by how far from the way.
        for (double gz = -half; gz < half; gz += 3.2)
            for (double gx = -half; gx < half; gx += 3.2)
            {
                double x = gx + rng.Range(0, 3.2), z = gz + rng.Range(0, 3.2);
                double d = Sample(outside, x, z, half), inn = Sample(inside, x, z, half);
                if (lay != null)
                {
                    // A dungeon's walls are meshes (DungeonWalls): only a sparse scatter of pebbles on the floor.
                    if (inn > 1.5 && rng.Chance(0.04)) Put("pebble", x, z);
                }
                else if (d > 1.2)
                {
                    // The walls: trees thick near the way, thinning into the dark beyond.
                    double keep = d < 16 ? (lay != null ? 0.7 : 0.62) : d < 34 ? 0.34 : 0.1;
                    if (rng.Chance(keep)) Put(rng.Pick(trees), x, z, 1 + Math.Min(0.4, d * 0.012));
                    if (d < 12 && rng.Chance(0.45)) Put(rng.Pick(new[] { "bush", "fern", "bramble", "fern" }), x + rng.Range(-1, 1), z + rng.Range(-1, 1));
                    if (d < 8 && rng.Chance(0.12)) Put(rng.Pick(lay != null ? new[] { "boulder", "rock", "scan_mossrock" } : new[] { "boulder", "rock", "cliff" }), x, z, 1, 0.3);
                }
                else if (inn < 2.2)
                {
                    // The edge of the way: undergrowth and stones you brush past.
                    if (rng.Chance(0.4)) Put(rng.Pick(new[] { "fern", "bush", "rock", "plant", "mushroom" }), x, z);
                }
                else
                {
                    // Out in the open: a little life underfoot.
                    if (rng.Chance(0.06)) Put(rng.Pick(new[] { "flowers", "clover", "pebble", "mushroom" }), x, z);
                }
            }
        // A few boulders to fight round in the bigger clearings (not the start).
        var colliders = new List<ColliderDef>();
        int cid = 1;
        foreach (var a in areas.Where(a => a.Kind is AreaKind.Clearing && lay == null))
            for (int n = rng.Int(1, 3); n > 0; n--)
            {
                double ang = rng.Range(0, Math.PI * 2), rr = rng.Range(0.35, 0.65) * a.R;
                double x = a.X + Math.Cos(ang) * rr, z = a.Z + Math.Sin(ang) * rr;
                double s = rng.Range(0.9, 1.3);
                Put("boulder", x, z, s, 0.2);
                colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Circle, X = x, Z = z, R = 1.1 * s, Hw = 1.1 * s, Hd = 1.1 * s });
            }

        // ------------------------------------------------ places and lights --
        var lights = new List<LightDef>();
        var fires = new List<FireDef>();
        void Fire(double x, double z, double size, double intensity, string color = "#ff9a48")
        {
            double y = ground.HeightAt(x, z);
            lights.Add(new LightDef { X = x, Y = y + 1.1, Z = z, Color = color, Intensity = intensity, Distance = intensity, Flicker = 0.28, On = true });
            fires.Add(new FireDef { X = x, Y = y + 0.1, Z = z, Size = size, Light = lights.Count - 1 });
        }
        // Where you come in: a fire someone left.
        var st = areas[0];
        // (den r19 K, R18b item 8) in a den the start fire's spot is the old bearing turned by a hash of the seed (+-40 degrees) and 5.2-7 m out (it was 2.9 m off her
        // and clipped her in r17); the first of a few turns that is >= 3 m inside a room and its holes. --den-fire-jitter 0 = the fixed (2.5, 1.5) offset.
        double fx = st.X + 2.5, fz = st.Z + 1.5;
        var fcl = Environment.GetCommandLineArgs();
        int fji = Array.IndexOf(fcl, "--den-fire-jitter");
        if (lay != null && lay.Def.Theme == "den" && !(fji >= 0 && fji + 1 < fcl.Length && fcl[fji + 1] == "0"))
        {
            uint hs = (uint)spec.Seed * 2654435761u + 0x9e3779b9u; hs ^= hs >> 15; hs *= 2246822519u; hs ^= hs >> 13;
            double h1 = (hs & 0xffff) / 65535.0, h2 = ((hs >> 16) & 0xffff) / 65535.0;
            double a0 = Math.Atan2(1.5, 2.5) + (h1 - 0.5) * 2 * 40 * Math.PI / 180, dist = 5.2 + 1.8 * h2;
            for (int t = 0; t < 12; t++)
            {
                double a = a0 + (t % 2 == 0 ? 1 : -1) * (t / 2) * 30 * Math.PI / 180, x = st.X + Math.Cos(a) * dist, z = st.Z + Math.Sin(a) * dist;
                if (lay.Rooms.Any(r => -r.Dist(x, z) >= 3.0)) { fx = x; fz = z; break; }
            }
        }
        Fire(fx, fz, 0.8, 12);
        foreach (var a in areas.Where(a => a.Kind == AreaKind.Altar))
        {
            // A ring of standing stones round a cold hearth (lit when the altar is woken).
            // (den-wall; the owner, 22 Nov: "strongboxes load in before they appear causing an invisible wall") Where the
            // dungeon draws no flora (the den) the stones are never seen, so they hold nothing: no collider. The id is still
            // spent, so every later piece keeps its id. tests/DenWallTests.cs.
            bool solid = DungeonDef.GrowsFlora(lay?.Def.Theme);
            for (int n = 0; n < 6; n++)
            {
                double ang = n * Math.PI / 3 + 0.3;
                double x = a.X + Math.Cos(ang) * 6.2, z = a.Z + Math.Sin(ang) * 6.2;
                Put("cliff", x, z, 0.32, 0.4);
                int id = cid++;
                if (solid) colliders.Add(new ColliderDef { Id = id, Kind = ColliderKind.Circle, X = x, Z = z, R = 0.9, Hw = 0.9, Hd = 0.9 });
            }
            Fire(a.X, a.Z, 1.0, 16, "#8ab4ff");
            lights[^1].On = false;
        }
        var boss = areas[^1];
        if (lay != null) DressDungeon(lay, rng, ground, Put, PutAt, props, colliders, ref cid, Fire, lights);
        // Standing stones round the last clearing, fires between.
        int stones = lay != null ? 0 : 8;
        for (int n = 0; n < stones; n++)
        {
            double ang = n * Math.PI * 2 / stones;
            double x = boss.X + Math.Cos(ang) * (boss.R - 2.5), z = boss.Z + Math.Sin(ang) * (boss.R - 2.5);
            Put("cliff", x, z, 0.45, 0.5);
            colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Circle, X = x, Z = z, R = 1.1, Hw = 1.1, Hd = 1.1 });
            if (n % 2 == 0) Fire(boss.X + Math.Cos(ang + Math.PI / stones) * (boss.R - 4), boss.Z + Math.Sin(ang + Math.PI / stones) * (boss.R - 4), 0.7, 11, "#ff6a3a");
        }

        // ----------------------------------------------------- the walls --
        // Solid boxes over the unwalkable cells within reach of the way (the
        // survivor and everything chasing them stop at the trees), merged
        // into as few boxes as will cover them.
        // A dungeon's are of two kinds, merged apart: the edges its view shows as a drop (a foe forced over one dies of it,
        // Sim/LedgeKills.cs) and the walls that rise (LedgeEdges, data/content/ledge.json "edges").
        bool[]? dropCell = null;
        if (lay != null)
        {
            var rule = LedgeEdges.For(lay.Def.Id);
            dropCell = new bool[Res * Res];
            for (int j = 0; j < Res; j++)
                for (int i = 0; i < Res; i++)
                {
                    int k = j * Res + i;
                    if (outside[k] > 0 && outside[k] <= 4.5) dropCell[k] = LedgeEdges.Drops(rule, LedgeEdges.KindAt(wallIn, holeD, Res, i, j, rule));
                }
        }
        foreach (bool drop in dropCell != null ? new[] { false, true } : new[] { false })
            foreach (var (i0, j0, w, h) in Merge(outside, 4.5, dropCell == null ? null : k => dropCell[k] == drop))
            {
                double hw = w / 2.0, hd = h / 2.0;
                colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Box, X = i0 - half - 0.5 + hw, Z = j0 - half - 0.5 + hd, Hw = hw, Hd = hd, R = Math.Sqrt(hw * hw + hd * hd), Tag = "wall", Drop = drop });
            }

        // ----------------------------------------------------------- packs --
        var packs = new List<PackSpot>();
        // A dungeon's packs rest where its rooms were drawn to hold them, and along its halls.
        if (lay != null) packs.AddRange(lay.Sockets.Where(p => walk[Idx(p.X, p.Z, half)]));
        foreach (var a in areas.Where(a => a.Kind is AreaKind.Clearing or AreaKind.Altar && lay == null))
            for (int n = rng.Int(2, 3); n > 0; n--)
            {
                double ang = rng.Range(0, Math.PI * 2), rr = rng.Range(0.2, 0.6) * a.R;
                packs.Add(new PackSpot(a.X + Math.Cos(ang) * rr, a.Z + Math.Sin(ang) * rr, a.Index, rng.Range(0.9, 1.4)));
            }
        foreach (var w in ways.Select((w, k) => (w, k)).Where(_ => lay == null))
        {
            // Along each way, a pack every 14 m or so, past the first stretch.
            double run = 0;
            double next = rng.Range(10, 16);
            for (int s = 1; s < w.w.Length; s++)
            {
                run += MathX.Dist(w.w[s].X, w.w[s].Z, w.w[s - 1].X, w.w[s - 1].Z);
                if (run < next) continue;
                next = run + rng.Range(11, 17);
                var p = w.w[s];
                if (MathX.Dist(p.X, p.Z, areas[w.k].X, areas[w.k].Z) < areas[w.k].R + 4) continue;
                if (MathX.Dist(p.X, p.Z, areas[w.k + 1].X, areas[w.k + 1].Z) < areas[w.k + 1].R + 2) continue;
                packs.Add(new PackSpot(p.X + rng.Range(-1.5, 1.5), p.Z + rng.Range(-1.5, 1.5), w.k, rng.Range(0.7, 1.1)));
            }
        }

        // ------------------------------------------------------------ meta --
        var placesJson = new Dictionary<string, object>
        {
            ["start"] = new { x = st.X, z = st.Z },
            ["boss"] = new { x = boss.X, z = boss.Z },
        };
        foreach (var a in areas) placesJson[$"area{a.Index}"] = new { x = a.X, z = a.Z };
        var meta = new ZoneMeta
        {
            Id = "map", Size = Size, Res = Res, SplatRes = SplatRes, Leaves = spec.Theme == "autumn" ? 0.5 : 0.42,
            // A map is walked by day, where the night's bright veins read as neon over the whole of its
            // ruler's clearing: there they smoulder.
            BlightGlow = spec.Night ? "#9aff4a" : "#3d6420",
            Bound = half - 4,
            Start = new Start { X = st.X, Z = st.Z, Facing = areas.Count > 1 ? Math.Atan2(areas[1].X - st.X, areas[1].Z - st.Z) : 0 },
            Atmosphere = spec.Night ? Atmospheres.Night : Atmospheres.Day,
            Lights = lights, Fires = fires, Colliders = colliders,
            Refs = JsonSerializer.SerializeToElement(new { }),
            Places = new Dictionary<string, JsonElement> { ["M"] = JsonSerializer.SerializeToElement(placesJson) },
            Paths = new Dictionary<string, double[][]> { ["WAY"] = ways.SelectMany(w => w).Select(p => new[] { p.X, p.Z }).ToArray() },
            Map = new ZoneMapDef
            {
                Flora = flora.Where(f => f.Kind is "pine" or "broadleaf" or "autumn" or "dead" or "boulder" or "cliff")
                    .Select(f => JsonSerializer.SerializeToElement(new object[] { f.Kind, f.X, f.Z, f.Scale })).ToList(),
            },
        };
        return new MapBuild
        {
            Spec = spec, Meta = meta, Ground = ground, SplatRes = SplatRes, Splat = splat, Flora = flora, Props = props,
            Kinds = kinds, Areas = areas, Packs = packs, Walkable = walk, Ways = ways, Dungeon = lay,
            DungeonTheme = lay?.Def.Theme ?? "",
            WallField = lay == null ? null : wallIn.Select(v => (float)Math.Clamp(v, -16, 8)).ToArray(),
            HoleField = lay == null ? null : holeD.Select(v => (float)Math.Clamp(v, -8, 8)).ToArray(),
        };
    }

    /// <summary>A dungeon's rooms dressed as their people keep them (RoomPlan.Dress): the Pack's bones in the corners, the
    /// Kerchiefs' crates, fences and cookfires, a stash's barrels by its cache; crags on every hole; lanterns at the way out.</summary>
    static void DressDungeon(DungeonLayout lay, Rng rng, Heightfield ground, Action<string, double, double, double, double> put,
        Action<string, double, double, double, double, double> putAt,
        List<PropPlace> props, List<ColliderDef> colliders, ref int cid, Action<double, double, double, double, string> fire, List<LightDef> lights)
    {
        void Prop(string id, double x, double z, double rot, double scale) => props.Add(new PropPlace(id, x, ground.HeightAt(x, z), z, rot, scale));
        // A point inside a room, its edge so far in (from the edge), by trying.
        (double X, double Z)? Near(DungeonRoom r, double lo, double hi)
        {
            double reach = r.Plan.Reach * r.Scale;
            for (int t = 0; t < 40; t++)
            {
                double ang = rng.Range(0, Math.PI * 2), rr = rng.Range(0, reach);
                double x = r.X + Math.Cos(ang) * rr, z = r.Z + Math.Sin(ang) * rr, d = -r.Dist(x, z);
                if (d >= lo && d <= hi) return (x, z);
            }
            return null;
        }
        foreach (var r in lay.Rooms)
        {
            // (a den's holes are pits and a ravine's rock outcrops in the wall mesh: nothing heaped on them)
            string dress = r.Plan.Dress;
            if (dress == "bones")
                for (int n = rng.Int(3, 6); n > 0; n--)
                    if (Near(r, 0.6, 3.2) is { } p) Prop(rng.Pick(new[] { "halloween/bone_A", "halloween/bone_B", "halloween/bone_C", "halloween/bone_A", "halloween/ribcage", "halloween/skull" }), p.X, p.Z, rng.Range(0, Math.PI * 2), rng.Range(0.9, 1.3));
            if (dress == "camp")
            {
                for (int n = rng.Int(3, 6); n > 0; n--)
                    if (Near(r, 0.8, 2.6) is { } p) Prop(rng.Pick(new[] { "props/Crate_Wooden", "props/Barrel", "props/Bag", "props/Crate_Wooden", "village/Prop_WoodenFence_Single", "props/WeaponStand", "props/Shield_Wooden" }), p.X, p.Z, rng.Range(0, Math.PI * 2), 1.0);
                // A cookfire kept in the bigger rooms: a light to fight by.
                if (r.Role is RoomRole.Fight or RoomRole.Boss && Near(r, 4, 9) is { } f) { fire(f.X, f.Z, 0.7, 10, "#ff8a3a"); Prop("arena/cookpot", f.X + 0.9, f.Z, rng.Range(0, Math.PI * 2), 1); }
            }
            if (dress == "stash")
                for (int n = rng.Int(2, 4); n > 0; n--)
                    if (Near(r, 0.6, 2.2) is { } p) Prop(rng.Pick(new[] { "props/Barrel", "props/Crate_Wooden", "props/Bag", "props/Pouch_Large" }), p.X, p.Z, rng.Range(0, Math.PI * 2), 1.0);
            if (r.Role == RoomRole.Boss)
            {
                // Torches round the ruler's room, inside its edge. (den r15: one in a den lair, the judge's one fire per view;
                // the four spots are still drawn so the rng runs as before)
                int torches = lay.Def.Theme == "den" ? 1 : 4, lit = 0;
                // (den r18 D5, R18 item 2) --den-fire-clear 0 = the first spot lit; else the spot >= 3 m from the room's middle (her arrival)
                // farthest from the holes, or the farthest from the middle when none is 3 m out. The four spots are drawn as ever.
                var cl = Environment.GetCommandLineArgs();
                int ci = Array.IndexOf(cl, "--den-fire-clear");
                bool far = lay.Def.Theme == "den" && !(ci >= 0 && ci + 1 < cl.Length && cl[ci + 1] == "0");
                var spots = new List<(double X, double Z)>();
                for (int n = 0; n < 4; n++)
                    if (Near(r, 2.5, 4.5) is { } p) { spots.Add(p); if (!far && lit < torches) { fire(p.X, p.Z, 0.6, 11, "#ff6a3a"); lit++; } }
                if (far && spots.Count > 0)
                {
                    double Cd((double X, double Z) s) => MathX.Dist(s.X, s.Z, r.X, r.Z);
                    double Hd((double X, double Z) s) { double m = 99; foreach (var h in r.Holes) m = Math.Min(m, h.Dist(s.X, s.Z)); return m; }
                    var out3 = spots.Where(s => Cd(s) >= 3).ToList();
                    // (den r18 lead, d9c: the farthest-from-holes spot fell under the HUD or off the lair's view) first the spots the
                    // lair's play view shows from its middle (13 m either side, 9 m north to 4 m south) clear of the holes by 2.5 m
                    bool Seen((double X, double Z) s) => Math.Abs(s.X - r.X) < 13 && s.Z - r.Z > -9 && s.Z - r.Z < 4;
                    var best = out3.Count > 0 ? out3.OrderByDescending(s => (Seen(s) ? 2 : 0) + (Hd(s) >= 2.5 ? 1 : 0)).ThenByDescending(Hd).First() : spots.OrderByDescending(Cd).First();
                    fire(best.X, best.Z, 0.6, 11, "#ff6a3a");
                }
            }
        }
        // The way out: two lantern posts either side of it, dark until the ruler is down (MapRun lights it).
        var b = lay.Rooms[^1];
        var (ex, ez) = lay.Exit;
        double dx = ex - b.X, dz = ez - b.Z, dl = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz));
        foreach (int side in new[] { -1, 1 })
            Prop("halloween/post_lantern", ex - dz / dl * 3.2 * side, ez + dx / dl * 3.2 * side, Math.Atan2(dx, dz), 1.1);
    }

    internal static byte B(double v) => (byte)Math.Round(MathX.Clamp01(v) * 255);

    internal static int Idx(double x, double z, double half)
    {
        int i = (int)Math.Round(MathX.Clamp(x + half, 0, Res - 1)), j = (int)Math.Round(MathX.Clamp(z + half, 0, Res - 1));
        return j * Res + i;
    }

    /// <summary>A grid value at a point, between its four samples.</summary>
    internal static double Bilinear(double[] grid, double x, double z, double half)
    {
        double fx = MathX.Clamp(x + half, 0, Res - 1.001), fz = MathX.Clamp(z + half, 0, Res - 1.001);
        int i = (int)fx, j = (int)fz;
        double tx = fx - i, tz = fz - j;
        double a = grid[j * Res + i], b = grid[j * Res + i + 1], c = grid[(j + 1) * Res + i], d = grid[(j + 1) * Res + i + 1];
        return (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz;
    }

    /// <summary>A grid value at a point (nearest sample).</summary>
    internal static double Sample(double[] grid, double x, double z, double half) => grid[Idx(x, z, half)];

    /// <summary>The cells of a 3 by 3 grid in a snake from one corner to the
    /// far one (turned and mirrored at random).</summary>
    static List<(int, int)> Snake(Rng rng)
    {
        var path = new List<(int, int)>();
        const int n = Grid - 1;
        for (int j = 0; j < Grid; j++)
            for (int k = 0; k < Grid; k++) path.Add((j % 2 == 0 ? k : n - k, j));
        bool swap = rng.Chance(0.5), fx = rng.Chance(0.5), fz = rng.Chance(0.5);
        return path.Select(p =>
        {
            var (i, j) = swap ? (p.Item2, p.Item1) : p;
            return (fx ? n - i : i, fz ? n - j : j);
        }).ToList();
    }

    /// <summary>For every cell, metres to the nearest walkable one (0 on the
    /// walkable ones): a two-pass chamfer over the grid.</summary>
    internal static double[] DistanceOut(bool[] walk)
    {
        var d = new double[Res * Res];
        for (int k = 0; k < d.Length; k++) d[k] = walk[k] ? 0 : 1e9;
        const double S = 1, D = 1.41421356;
        for (int j = 0; j < Res; j++)
            for (int i = 0; i < Res; i++)
            {
                int k = j * Res + i;
                if (i > 0) d[k] = Math.Min(d[k], d[k - 1] + S);
                if (j > 0) d[k] = Math.Min(d[k], d[k - Res] + S);
                if (i > 0 && j > 0) d[k] = Math.Min(d[k], d[k - Res - 1] + D);
                if (i < Res - 1 && j > 0) d[k] = Math.Min(d[k], d[k - Res + 1] + D);
            }
        for (int j = Res - 1; j >= 0; j--)
            for (int i = Res - 1; i >= 0; i--)
            {
                int k = j * Res + i;
                if (i < Res - 1) d[k] = Math.Min(d[k], d[k + 1] + S);
                if (j < Res - 1) d[k] = Math.Min(d[k], d[k + Res] + S);
                if (i < Res - 1 && j < Res - 1) d[k] = Math.Min(d[k], d[k + Res + 1] + D);
                if (i > 0 && j < Res - 1) d[k] = Math.Min(d[k], d[k + Res - 1] + D);
            }
        return d;
    }

    /// <summary>The unwalkable cells within `reach` of the way, as few
    /// axis-aligned boxes as a greedy sweep finds: (i, j, width, height).</summary>
    internal static List<(int, int, int, int)> Merge(double[] outside, double reach, Func<int, bool>? only = null)
    {
        var want = new bool[Res * Res];
        for (int k = 0; k < want.Length; k++) want[k] = outside[k] > 0 && outside[k] <= reach && (only == null || only(k));
        var boxes = new List<(int, int, int, int)>();
        for (int j = 0; j < Res; j++)
            for (int i = 0; i < Res; i++)
            {
                if (!want[j * Res + i]) continue;
                int w = 1;
                while (i + w < Res && want[j * Res + i + w]) w++;
                int h = 1;
                while (j + h < Res)
                {
                    bool row = true;
                    for (int q = 0; q < w && row; q++) row = want[(j + h) * Res + i + q];
                    if (!row) break;
                    h++;
                }
                for (int b = 0; b < h; b++)
                    for (int q = 0; q < w; q++) want[(j + b) * Res + i + q] = false;
                boxes.Add((i, j, w, h));
            }
        return boxes;
    }

    static Dictionary<string, FloraKind>? catalog;

    /// <summary>The photoscanned kinds (Poly Haven, CC0, brought to a game's
    /// weight in art/world by tools/assets/game_ready.py), at their own size
    /// in metres: what makes a clearing seen from high up read as ground
    /// rather than paint.</summary>
    public static readonly Dictionary<string, string[]> ScanKinds = new()
    {
        ["scan_grass"] = ["grass_medium_01", "grass_medium_02", "weed_plant_02"],
        ["scan_stones"] = ["stone_01", "namaqualand_stones_01"],
        ["scan_moss"] = ["moss_01"],
        ["scan_bark"] = ["bark_debris_01"],
        ["scan_fern"] = ["fern_02", "nettle_plant", "shrub_03"],
        ["scan_shrub"] = ["shrub_01", "shrub_02", "shrub_04"],
        ["scan_root"] = ["root_cluster_01", "root_cluster_02", "single_root", "pine_roots"],
        ["scan_stump"] = ["tree_stump_01", "tree_stump_02"],
        ["scan_branches"] = ["dry_branches_medium_01"],
        ["scan_rock"] = ["rock_07", "rock_09"],
        ["scan_mossrock"] = ["rock_moss_set_01", "rock_moss_set_02"],
        ["scan_trunk"] = ["dead_tree_trunk", "dead_tree_trunk_02"],
        ["scan_boulder"] = ["boulder_01"],
    };

    /// <summary>The kinds of flora, as the Verge has them (its flora.json):
    /// each kind's pieces, scale and look.</summary>
    public static Dictionary<string, FloraKind> Catalog()
    {
        if (catalog != null) return catalog;
        using var doc = JsonDocument.Parse(DataFiles.Text("zones/verge/flora.json"));
        var by = new Dictionary<string, (HashSet<string> Pieces, JsonElement First)>();
        foreach (var g in doc.RootElement.EnumerateArray())
        {
            var kind = g.GetProperty("kind").GetString()!;
            if (!by.TryGetValue(kind, out var e)) by[kind] = e = (new HashSet<string>(), g.Clone());
            e.Pieces.Add(g.GetProperty("piece").GetString()!);
        }
        var made = by.ToDictionary(kv => kv.Key, kv =>
        {
            var g = kv.Value.First;
            string? la = null, lb = null;
            double amount = 0;
            if (g.TryGetProperty("leaves", out var lv) && lv.ValueKind == JsonValueKind.Object)
            {
                la = lv.GetProperty("a").GetString(); lb = lv.GetProperty("b").GetString(); amount = lv.GetProperty("amount").GetDouble();
            }
            return new FloraKind(kv.Key, kv.Value.Pieces.OrderBy(p => p).ToArray(), g.GetProperty("sx").GetDouble(),
                g.TryGetProperty("wind", out var w) && w.ValueKind == JsonValueKind.Number ? w.GetDouble() : 0, la, lb, amount,
                g.TryGetProperty("moss", out var m) && m.ValueKind == JsonValueKind.Number ? m.GetDouble() : 0);
        });
        foreach (var (kind, pieces) in ScanKinds)
            made[kind] = new FloraKind(kind, pieces.Select(p => "scan:" + p).ToArray(), 1, 0, null, null, 0, 0);
        catalog = made;
        return catalog;
    }
}
