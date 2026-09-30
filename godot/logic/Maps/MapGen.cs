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
}

public enum AreaKind { Start, Clearing, Altar, Boss }

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
    public required List<Area> Areas;
    public required List<PackSpot> Packs;
    /// <summary>Can the survivor stand here: res by res, 1 m apart, as the heights.</summary>
    public required bool[] Walkable;
    public Area Start => Areas[0];
    public Area Boss => Areas[^1];
    public IEnumerable<Area> Altars => Areas.Where(a => a.Kind == AreaKind.Altar);

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
    const int Res = 301;
    /// <summary>The clearings stand in a Grid by Grid square, walked as a snake.</summary>
    const int Grid = 4;
    const int SplatRes = 512;
    const double Margin = 16;
    /// <summary>An arena's clearing, metres from its middle to its edge (give or take the edge's wander).</summary>
    public const double ArenaR = 84;

    public static MapBuild Generate(MapSpec spec)
    {
        var rng = new Rng((uint)spec.Seed ^ 0x5bd1e995u);
        var noise = new Noise2D((uint)spec.Seed);
        double half = Size / 2;

        // ---------------------------------------------------------- layout --
        // A snake through a grid of cells: the way crosses the whole square
        // and back, and back again, so the map is long for its size. An
        // arena is one clearing, as wide as the square allows.
        var order = spec.Arena ? new List<(int, int)>() : Snake(rng);
        double cell = (Size - Margin * 2) / Grid;
        var areas = new List<Area>();
        if (spec.Arena) areas.Add(new Area(0, AreaKind.Start, 0, 0, ArenaR));
        for (int k = 0; k < order.Count; k++)
        {
            var (ci, cj) = order[k];
            double cx = -half + Margin + cell * (ci + 0.5) + rng.Range(-0.18, 0.18) * cell;
            double cz = -half + Margin + cell * (cj + 0.5) + rng.Range(-0.18, 0.18) * cell;
            var kind = k == 0 ? AreaKind.Start : k == order.Count - 1 ? AreaKind.Boss : AreaKind.Clearing;
            double r = kind switch { AreaKind.Start => 11, AreaKind.Boss => 24, _ => rng.Range(14, 20) };
            areas.Add(new Area(k, kind, cx, cz, r));
        }
        // Three of the clearings between hold altars: early, midway, late.
        int na = areas.Count;
        if (!spec.Arena) foreach (int k in new[] { rng.Int((int)(na * 0.15), (int)(na * 0.25)), rng.Int((int)(na * 0.4), (int)(na * 0.5)), rng.Int((int)(na * 0.65), (int)(na * 0.75)) })
            areas[k] = areas[k] with { Kind = AreaKind.Altar, R = Math.Max(areas[k].R, 17) };

        // The ways between: a curve from each clearing to the next, bowed to one side.
        var ways = new List<(double X, double Z, double Hw)[]>();
        for (int k = 0; k + 1 < areas.Count; k++)
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
        System.Threading.Tasks.Parallel.For(0, Res, j =>
        {
            for (int i = 0; i < Res; i++)
            {
                double x = i - half, z = j - half;
                double edge = double.MinValue;      // > 0: walkable, by how much
                double tn = 9;
                foreach (var a in areas)
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
                        edge = Math.Max(edge, (ah + bh) / 2 - d);
                        tn = Math.Min(tn, d / ((ah + bh) / 2));
                    }
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
                double bank = MathX.Smoothstep(0.5, 12, d) * (4.5 + 3 * noise.Fbm(x * 0.03, z * 0.03, 3))
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
                mud = Math.Max(mud, MathX.Smoothstep(0.55, 0.8, noise.Noise(x * 0.05 - 9, z * 0.05)) * MathX.Smoothstep(-1, 2, inn) * 0.9);
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
                if (d > 1.2)
                {
                    // The walls: trees thick near the way, thinning into the dark beyond.
                    double keep = d < 16 ? 0.62 : d < 34 ? 0.34 : 0.1;
                    if (rng.Chance(keep)) Put(rng.Pick(trees), x, z, 1 + Math.Min(0.4, d * 0.012));
                    if (d < 12 && rng.Chance(0.45)) Put(rng.Pick(new[] { "bush", "fern", "bramble", "fern" }), x + rng.Range(-1, 1), z + rng.Range(-1, 1));
                    if (d < 8 && rng.Chance(0.12)) Put(rng.Pick(new[] { "boulder", "rock", "cliff" }), x, z, 1, 0.3);
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
        var pieces = new List<PropPlace>();
        var glows = new List<(double X, double Z, string Color, double Intensity, bool Fire)>();
        if (spec.Arena)
        {
            // Islands of cover across the arena, low enough to read from the
            // arena's high camera and the people's own: places to be cornered
            // by, and to lose a crowd round.
            var islands = new List<(double X, double Z)>();
            int crypts = 0;
            void Piece(string id, double px, double pz, double rot, double scale = 1) => pieces.Add(new PropPlace(id, px, ground.HeightAt(px, pz), pz, rot, scale));
            void Block(double bx, double bz, double r) => colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Circle, X = bx, Z = bz, R = r, Hw = r, Hd = r });
            void Slab(double bx, double bz, double hw, double hd, double rot) => colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Box, X = bx, Z = bz, Hw = hw, Hd = hd, Rot = rot, R = Math.Sqrt(hw * hw + hd * hd) });
            // A piece's own x axis, turned: where a row of them runs.
            (double X, double Z) Along(double rot) => (Math.Cos(rot), -Math.Sin(rot));
            double Square() => rng.Int(0, 3) * Math.PI / 2;
            for (int t = 0; t < 400 && islands.Count < 18; t++)
            {
                double ang = rng.Range(0, Math.PI * 2), rr = rng.Range(16, ArenaR - 14);
                double x = Math.Cos(ang) * rr, z = Math.Sin(ang) * rr;
                if (islands.Any(o => MathX.Dist(o.X, o.Z, x, z) < 19)) continue;
                islands.Add((x, z));
                int kind = rng.Int(0, 2);
                if (spec.People == "dead")
                {
                    // The barrow field: rows of graves, a crypt or two, pillars fallen among rubble.
                    if (kind == 1 && crypts < 2)
                    {
                        crypts++;
                        double rot = Square();
                        Piece("halloween/crypt", x, z, rot, 0.8);
                        Slab(x, z, 2.5, 3.3, rot);
                        var (ux, uz) = Along(rot);
                        // Its door faces the crypt's +z: a lantern either side of it.
                        double fx = Math.Sin(rot), fz = Math.Cos(rot);
                        foreach (int side in new[] { -1, 1 })
                        {
                            double lx = x + fx * 4.2 + ux * side * 1.8, lz = z + fz * 4.2 + uz * side * 1.8;
                            Piece("halloween/lantern_standing", lx, lz, rot);
                            glows.Add((lx, lz, "#ffc27a", 7, false));
                        }
                    }
                    else if (kind == 2)
                    {
                        double rot = rng.Range(0, Math.PI * 2);
                        var (ux, uz) = Along(rot);
                        foreach (int side in new[] { -1, 1 })
                        {
                            Piece("halloween/pillar", x + ux * side * 2.4, z + uz * side * 2.4, rng.Range(0, Math.PI * 2), rng.Range(0.6, 0.9));
                            Block(x + ux * side * 2.4, z + uz * side * 2.4, 0.55);
                        }
                        Piece("dungeon/rubble_half", x - 1.2, z, rot, 0.55);
                        Block(x, z, 1.3);
                        Piece("halloween/skull_candle", x + uz * 1.6, z - ux * 1.6, rng.Range(0, Math.PI * 2));
                        glows.Add((x + uz * 1.6, z - ux * 1.6, "#9fe0c8", 5, false));
                    }
                    else
                    {
                        double rot = rng.Range(0, Math.PI * 2);
                        var (ux, uz) = Along(rot);
                        int n = rng.Int(3, 5);
                        string[] graves = ["halloween/grave_A", "halloween/grave_B", "halloween/grave_A_destroyed", "halloween/gravestone"];
                        for (int g = 0; g < n; g++)
                        {
                            double o = (g - (n - 1) / 2.0) * 2.5;
                            double gx = x + ux * o, gz = z + uz * o;
                            Piece(rng.Pick(graves), gx, gz, rot + rng.Range(-0.12, 0.12), rng.Range(0.8, 0.95));
                            Block(gx, gz, 0.9);
                        }
                        Piece("halloween/bone_A", x + uz * 2, z - ux * 2, rng.Range(0, Math.PI * 2));
                        Piece("halloween/ribcage", x - uz * 2.2, z + ux * 2.2, rng.Range(0, Math.PI * 2));
                    }
                    continue;
                }
                if (spec.People == "kerchiefs")
                {
                    // The raided camp: a broken wall's corner, its stores broken open, a fire still going.
                    if (kind == 0)
                    {
                        double rot = Square();
                        var (ux, uz) = Along(rot);
                        Piece("dungeon/wall_broken", x, z, rot, 0.8);
                        Slab(x, z, 1.6, 0.4, rot);
                        double cx = x + ux * 1.6 + uz * 1.6, cz = z + uz * 1.6 - ux * 1.6;
                        Piece("dungeon/wall_broken", cx, cz, rot + Math.PI / 2, 0.7);
                        Slab(cx, cz, 1.4, 0.35, rot + Math.PI / 2);
                        for (int n = 0; n < 3; n++)
                        {
                            double bx = x - uz * rng.Range(1.2, 2.2) + ux * rng.Range(-1.5, 1.5), bz = z + ux * rng.Range(1.2, 2.2) + uz * rng.Range(-1.5, 1.5);
                            Piece(rng.Pick(new[] { "props/Barrel", "props/Crate_Wooden" }), bx, bz, rng.Range(0, Math.PI * 2), rng.Range(0.9, 1.2));
                            Block(bx, bz, 0.55);
                        }
                    }
                    else if (kind == 1)
                    {
                        foreach (var (id, dx, dz, r) in new[] { ("props/Crate_Wooden", -1.6, 0.0, 0.6), ("props/Crate_Wooden", -1.4, 1.1, 0.6), ("props/Barrel_Holder", 1.6, -0.6, 0.9), ("props/Chest_Wood", 0.2, 1.8, 0.6), ("props/Barrel", 1.3, 1.4, 0.55) })
                        {
                            Piece(id, x + dx, z + dz, rng.Range(0, Math.PI * 2));
                            Block(x + dx, z + dz, r);
                        }
                        glows.Add((x + 0.2, z - 2.4, "#ff9a48", 11, true));
                    }
                    else
                    {
                        double rot = rng.Range(0, Math.PI * 2);
                        var (ux, uz) = Along(rot);
                        foreach (int side in new[] { -1, 1 })
                        {
                            Piece(side < 0 ? "halloween/fence_broken" : "halloween/fence", x + ux * side * 2, z + uz * side * 2, rot, 0.9);
                            Slab(x + ux * side * 2, z + uz * side * 2, 1.8, 0.25, rot);
                        }
                        Put("boulder", x - uz * 2, z + ux * 2, 1.0, 0.2);
                        Block(x - uz * 2, z + ux * 2, 1.1);
                    }
                    continue;
                }
                if (spec.People == "lamplings")
                {
                    // The dig: spoil heaps and broken stone, lamps on poles, the blasting ember kept in barrels.
                    if (kind == 0)
                    {
                        double rot = Square();
                        Piece("dungeon/rubble_large", x, z, rot, 0.7);
                        Slab(x, z, 2.6, 1.0, rot);
                    }
                    else if (kind == 1)
                    {
                        Piece("dungeon/pillar", x, z, rng.Range(0, Math.PI * 2), 0.7);
                        Block(x, z, 0.6);
                        for (int n = 0; n < 2; n++)
                        {
                            double bx = x + rng.Range(-2.5, 2.5), bz = z + rng.Range(-2.5, 2.5);
                            Put("boulder", bx, bz, rng.Range(0.8, 1.1), 0.2);
                            Block(bx, bz, 1.0);
                        }
                    }
                    else
                    {
                        for (int n = 0; n < 3; n++)
                        {
                            double bx = x + rng.Range(-1.8, 1.8), bz = z + rng.Range(-1.8, 1.8);
                            Piece("props/Barrel", bx, bz, rng.Range(0, Math.PI * 2), 1.1);
                            Block(bx, bz, 0.55);
                        }
                    }
                    double lx = x + rng.Range(-3.5, 3.5), lz = z + rng.Range(3, 4);
                    Piece("halloween/lantern_standing", lx, lz, rng.Range(0, Math.PI * 2), 1.2);
                    glows.Add((lx, lz, "#ffcf7a", 8, false));
                    continue;
                }
                // The Pack's wood: bare trees (they read from above; full crowns do not) and stone.
                if (kind == 0)
                {
                    // A stand of trees, undergrowth between.
                    for (int n = rng.Int(3, 5); n > 0; n--)
                    {
                        double tx = x + rng.Range(-3, 3), tz = z + rng.Range(-3, 3);
                        Put("dead", tx, tz, 0.9);
                        colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Circle, X = tx, Z = tz, R = 0.7, Hw = 0.7, Hd = 0.7 });
                    }
                    for (int n = 0; n < 5; n++) Put(rng.Pick(new[] { "fern", "bush", "bramble" }), x + rng.Range(-4, 4), z + rng.Range(-4, 4));
                }
                else
                {
                    // An outcrop: a boulder or two and a tooth of rock.
                    for (int n = rng.Int(1, 2); n > 0; n--)
                    {
                        double bx = x + rng.Range(-2, 2), bz = z + rng.Range(-2, 2), sc = rng.Range(1.0, 1.5);
                        Put("boulder", bx, bz, sc, 0.2);
                        colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Circle, X = bx, Z = bz, R = 1.1 * sc, Hw = 1.1 * sc, Hd = 1.1 * sc });
                    }
                    if (kind == 2)
                    {
                        double cx = x + rng.Range(-2.5, 2.5), cz = z + rng.Range(-2.5, 2.5);
                        Put("cliff", cx, cz, 0.4, 0.4);
                        colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Circle, X = cx, Z = cz, R = 1.0, Hw = 1.0, Hd = 1.0 });
                    }
                    for (int n = 0; n < 3; n++) Put(rng.Pick(new[] { "rock", "fern", "mushroom" }), x + rng.Range(-3.5, 3.5), z + rng.Range(-3.5, 3.5));
                }
            }
        }
        foreach (var a in areas.Where(a => a.Kind is AreaKind.Clearing))
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
        // An arena's lanterns and camp fires.
        foreach (var (gx, gz, color, intensity, fire) in glows)
        {
            if (fire) { Fire(gx, gz, 0.7, intensity, color); continue; }
            lights.Add(new LightDef { X = gx, Y = ground.HeightAt(gx, gz) + 1.1, Z = gz, Color = color, Intensity = intensity, Distance = intensity, Flicker = 0.14, On = true });
        }
        // Where you come in: a fire someone left (in an arena, the fires are round the edge).
        var st = areas[0];
        if (!spec.Arena) Fire(st.X + 2.5, st.Z + 1.5, 0.8, 12);
        foreach (var a in areas.Where(a => a.Kind == AreaKind.Altar))
        {
            // A ring of standing stones round a cold hearth (lit when the altar is woken).
            for (int n = 0; n < 6; n++)
            {
                double ang = n * Math.PI / 3 + 0.3;
                double x = a.X + Math.Cos(ang) * 6.2, z = a.Z + Math.Sin(ang) * 6.2;
                Put("cliff", x, z, 0.32, 0.4);
                colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Circle, X = x, Z = z, R = 0.9, Hw = 0.9, Hd = 0.9 });
            }
            Fire(a.X, a.Z, 1.0, 16, "#8ab4ff");
            lights[^1].On = false;
        }
        var boss = areas[^1];
        // Standing stones round the last clearing (an arena's edge), fires between.
        int stones = spec.Arena ? 12 : 8;
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
        foreach (var (i0, j0, w, h) in Merge(outside, 4.5))
        {
            double hw = w / 2.0, hd = h / 2.0;
            colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Box, X = i0 - half - 0.5 + hw, Z = j0 - half - 0.5 + hd, Hw = hw, Hd = hd, R = Math.Sqrt(hw * hw + hd * hd), Tag = "wall" });
        }

        // ----------------------------------------------------------- packs --
        var packs = new List<PackSpot>();
        foreach (var a in areas.Where(a => a.Kind is AreaKind.Clearing or AreaKind.Altar))
            for (int n = rng.Int(2, 3); n > 0; n--)
            {
                double ang = rng.Range(0, Math.PI * 2), rr = rng.Range(0.2, 0.6) * a.R;
                packs.Add(new PackSpot(a.X + Math.Cos(ang) * rr, a.Z + Math.Sin(ang) * rr, a.Index, rng.Range(0.9, 1.4)));
            }
        foreach (var w in ways.Select((w, k) => (w, k)))
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
            Id = spec.Arena ? "arena" : "map", Size = Size, Res = Res, SplatRes = SplatRes, Leaves = spec.Theme == "autumn" ? 0.6 : 0.42, BlightGlow = "#9aff4a",
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
            Spec = spec, Meta = meta, Ground = ground, SplatRes = SplatRes, Splat = splat, Flora = flora, Props = props, Pieces = pieces,
            Kinds = kinds, Areas = areas, Packs = packs, Walkable = walk,
        };
    }

    static byte B(double v) => (byte)Math.Round(MathX.Clamp01(v) * 255);

    static int Idx(double x, double z, double half)
    {
        int i = (int)Math.Round(MathX.Clamp(x + half, 0, Res - 1)), j = (int)Math.Round(MathX.Clamp(z + half, 0, Res - 1));
        return j * Res + i;
    }

    /// <summary>A grid value at a point, between its four samples.</summary>
    static double Bilinear(double[] grid, double x, double z, double half)
    {
        double fx = MathX.Clamp(x + half, 0, Res - 1.001), fz = MathX.Clamp(z + half, 0, Res - 1.001);
        int i = (int)fx, j = (int)fz;
        double tx = fx - i, tz = fz - j;
        double a = grid[j * Res + i], b = grid[j * Res + i + 1], c = grid[(j + 1) * Res + i], d = grid[(j + 1) * Res + i + 1];
        return (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz;
    }

    /// <summary>A grid value at a point (nearest sample).</summary>
    static double Sample(double[] grid, double x, double z, double half) => grid[Idx(x, z, half)];

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
    static double[] DistanceOut(bool[] walk)
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
    static List<(int, int, int, int)> Merge(double[] outside, double reach)
    {
        var want = new bool[Res * Res];
        for (int k = 0; k < want.Length; k++) want[k] = outside[k] > 0 && outside[k] <= reach;
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
        catalog = by.ToDictionary(kv => kv.Key, kv =>
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
        return catalog;
    }
}
