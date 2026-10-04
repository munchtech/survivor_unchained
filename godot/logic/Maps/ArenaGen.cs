using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Maps;

/* An arena, made from its seed: one great clearing, 84 m across its middle
 * (give or take the edge's wander), in the place its people keep
 * (ArenaPlaces). What is common to every arena is made here: the edge and the
 * walls that hold it, the ground's roll, the ember's ring round the edge
 * (charred, cracked, glowing: the scar holding the survivor in), the colliders
 * and the meta. What makes each place itself (its ground's shapes and paint,
 * its cover, its landmarks at the edge, its lights) is its ArenaShape's
 * (Arenas/*.cs).
 *
 * The rules every place keeps, for the fight's sake (docs/team/arena_art.md):
 * landmarks and anything taller than a person stand at the edge, never in the
 * play space; cover inside is low (graves, trunks, crates, rubble); the ground
 * stays darker than everything that moves on it; the ember's glow keeps to the
 * ring, away from where telegraphs are drawn. */

/// <summary>What a place paints at a point of its ground: the four painted
/// layers (2..5 of its atlas), and the second paint.</summary>
public struct ArenaPaint
{
    public double L2, L3, L4, L5;
    /// <summary>Standing water, mud's shine.</summary>
    public double Wet;
    /// <summary>The ember's char (the ring, and a place's own burns).</summary>
    public double Char;
    /// <summary>Trodden flat: darker, less growing.</summary>
    public double Trod;
    /// <summary>The ground's second material (layer 1) over its first.</summary>
    public double BaseB;
    /// <summary>How thick the place's grass grows here (0 none).</summary>
    public double Grass;
    /// <summary>Moss in cushions over whatever is under it.</summary>
    public double Moss;
    /// <summary>The slurry's own sick light, where it stands or runs.</summary>
    public double Glow;
}

/// <summary>A place's own making: its shapes, paint and dressing.</summary>
public abstract class ArenaShape
{
    protected ArenaGen.Builder B = null!;
    protected Rng Rng => B.Rng;
    protected Noise2D Noise => B.Noise;
    public void Bind(ArenaGen.Builder b) => B = b;

    /// <summary>Choose the big shapes (a way, a stream, mounds, a pit).</summary>
    public abstract void Plan();
    /// <summary>Metres the ground rises (or sinks) at a point, over the clearing's roll.</summary>
    public virtual double Relief(double x, double z) => 0;
    /// <summary>Where the ground cannot be stood on, inside the edge (a pit).</summary>
    public virtual bool Closed(double x, double z) => false;
    /// <summary>The paint at a point; `inn` is metres inside the edge (negative outside).</summary>
    public abstract void Paint(double x, double z, double inn, ref ArenaPaint p);
    /// <summary>The wall's dressing at a point `d` metres outside the edge.</summary>
    public abstract void Wall(double x, double z, double d);
    /// <summary>The dressing just inside the edge (inn under 2.2 m).</summary>
    public abstract void Fringe(double x, double z, double inn);
    /// <summary>What grows or lies about on the open ground.</summary>
    public abstract void Open(double x, double z, double inn);
    /// <summary>Cover, landmarks and lights.</summary>
    public abstract void Dress();
}

public static class ArenaGen
{
    public const double R = MapGen.ArenaR;
    const double Size = MapGen.Size;
    const int Res = MapGen.Res;
    /// <summary>The paint is finer than a map's: the camera is closer to an arena's ground than a texel of 0.6 m allows.</summary>
    public const int SplatRes = 1024;

    public static ArenaShape ShapeFor(string place) => place switch
    {
        "barrow" => new Arenas.Barrow(),
        "ruts" => new Arenas.Ruts(),
        "dig" => new Arenas.Dig(),
        _ => new Arenas.Hollow(),
    };

    public static MapBuild Generate(MapSpec spec)
    {
        var place = ArenaPlaces.For(spec);
        var shape = ShapeFor(place.Id);
        var b = new Builder(spec, place);
        shape.Bind(b);
        b.Edge();
        shape.Plan();
        b.Close(shape);
        b.Shape(shape);
        b.Paint(shape);
        b.Grow(shape);
        shape.Dress();
        b.Ring();
        return b.Build();
    }

    /// <summary>Everything an arena is made of, as it is made.</summary>
    public sealed class Builder
    {
        public readonly MapSpec Spec;
        public readonly ArenaPlace Place;
        public readonly Rng Rng;
        public readonly Noise2D Noise;
        public const double Half = Size / 2;
        public readonly bool[] Walk = new bool[Res * Res];
        /// <summary>Metres inside the edge (negative outside), cell by cell.</summary>
        public readonly double[] Inside = new double[Res * Res];
        /// <summary>Metres outside the walkable ground, cell by cell (0 on it).</summary>
        public double[] Outside = Array.Empty<double>();
        public readonly float[] Heights = new float[Res * Res];
        public Heightfield Ground = null!;
        readonly byte[] splat = new byte[SplatRes * SplatRes * 4];
        readonly byte[] splat2 = new byte[SplatRes * SplatRes * 4];
        readonly byte[] splat3 = new byte[SplatRes * SplatRes * 4];
        readonly byte[] grass = new byte[SplatRes * SplatRes];
        public readonly List<FloraPlace> Flora = new();
        public readonly List<PropPlace> Pieces = new();
        public readonly List<ColliderDef> Colliders = new();
        public readonly List<LightDef> Lights = new();
        public readonly List<FireDef> Fires = new();
        public readonly List<(double X, double Z, double R)> Taken = new();
        public readonly List<(double X, double Z, double Hw)[]> Streams = new();
        public readonly List<(double X, double Z, double Hw)[]> Rails = new();
        public readonly List<(double X, double Z, double R)> Vents = new();
        public readonly Dictionary<string, FloraKind> Kinds = MapGen.Catalog();
        int cid = 1;

        public Builder(MapSpec spec, ArenaPlace place)
        {
            Spec = spec;
            Place = place;
            Rng = new Rng((uint)spec.Seed ^ 0x5bd1e995u);
            Noise = new Noise2D((uint)spec.Seed);
        }

        /// <summary>The edge's radius at a bearing (it wanders, so the clearing is no circle).</summary>
        public double EdgeR(double ang) => R * (1 + 0.16 * Noise.Noise(Math.Cos(ang) * 1.7, Math.Sin(ang) * 1.7));

        /// <summary>Metres inside the edge at a point (negative outside).</summary>
        public double In(double x, double z) => MapGen.Bilinear(Inside, x, z, Half);
        public double Out(double x, double z) => MapGen.Sample(Outside, x, z, Half);
        public double HeightAt(double x, double z) => Ground?.HeightAt(x, z) ?? Heights[MapGen.Idx(x, z, Half)];
        public bool CanStand(double x, double z) => Walk[MapGen.Idx(x, z, Half)];

        /* ------------------------------------------------------------ edge -- */

        public void Edge()
        {
            System.Threading.Tasks.Parallel.For(0, Res, j =>
            {
                for (int i = 0; i < Res; i++)
                {
                    double x = i - Half, z = j - Half;
                    double d = Math.Sqrt(x * x + z * z);
                    double edge = EdgeR(Math.Atan2(z, x)) - d;
                    bool inBounds = Math.Abs(x) < Half - 6 && Math.Abs(z) < Half - 6;
                    Walk[j * Res + i] = inBounds && edge > 0;
                    Inside[j * Res + i] = edge;
                }
            });
        }

        /// <summary>A place's closed ground (a pit) taken out of what can be stood on.</summary>
        public void Close(ArenaShape shape)
        {
            for (int j = 0; j < Res; j++)
                for (int i = 0; i < Res; i++)
                    if (Walk[j * Res + i] && shape.Closed(i - Half, j - Half)) Walk[j * Res + i] = false;
            Outside = MapGen.DistanceOut(Walk);
        }

        /* --------------------------------------------------------- heights -- */

        public void Shape(ArenaShape shape)
        {
            for (int j = 0; j < Res; j++)
                for (int i = 0; i < Res; i++)
                {
                    double x = i - Half, z = j - Half;
                    double roll = Noise.Fbm(x * 0.012 + 3.1, z * 0.012 - 1.7, 3) * 2.2;
                    double d = Outside[j * Res + i];
                    // The ground climbs away from the clearing into banks and knolls.
                    double bank = MathX.Smoothstep(0.5, 12, d) * (4.5 + 3 * Noise.Fbm(x * 0.03, z * 0.03, 3))
                        + MathX.Smoothstep(10, 40, d) * 3 * (1 + Noise.Ridged(x * 0.02 + 7, z * 0.02, 3));
                    Heights[j * Res + i] = (float)(roll + bank);
                }
            // The clearing lies level-ish, pulled toward its middle's height.
            double h0 = Heights[MapGen.Idx(0, 0, Half)];
            for (int j = 0; j < Res; j++)
                for (int i = 0; i < Res; i++)
                {
                    double x = i - Half, z = j - Half, d = Math.Sqrt(x * x + z * z);
                    if (d > R + 20) continue;
                    double k = 1 - MathX.Smoothstep(R * 0.7, R + 6, d);
                    float h = Heights[j * Res + i];
                    Heights[j * Res + i] = (float)MathX.Lerp(h, h0 + Math.Min(0, h - h0) * 0.3, k * 0.85);
                }
            for (int j = 0; j < Res; j++)
                for (int i = 0; i < Res; i++)
                    Heights[j * Res + i] += (float)shape.Relief(i - Half, j - Half);
            Ground = new Heightfield(Size, Res, Heights);
        }

        /* ----------------------------------------------------------- paint -- */

        public void Paint(ArenaShape shape)
        {
            double ps = Size / SplatRes;
            System.Threading.Tasks.Parallel.For(0, SplatRes, j =>
            {
                for (int i = 0; i < SplatRes; i++)
                {
                    double x = -Half + (i + 0.5) * ps, z = -Half + (j + 0.5) * ps;
                    double inn = In(x, z);
                    var p = new ArenaPaint();
                    // Every place's ground in broad patches of its two materials.
                    p.BaseB = MathX.Smoothstep(-0.25, 0.35, Noise.Fbm(x * 0.018 + 40, z * 0.018 - 13, 3));
                    shape.Paint(x, z, inn, ref p);
                    p.Char = Math.Max(p.Char, RingChar(x, z, inn));
                    int o = (j * SplatRes + i) * 4;
                    splat[o] = MapGen.B(p.L2); splat[o + 1] = MapGen.B(p.L3); splat[o + 2] = MapGen.B(p.L4); splat[o + 3] = MapGen.B(p.L5);
                    splat2[o] = MapGen.B(p.Wet); splat2[o + 1] = MapGen.B(p.Char); splat2[o + 2] = MapGen.B(p.Trod); splat2[o + 3] = MapGen.B(p.BaseB);
                    // Nothing grows on char.
                    splat3[o] = MapGen.B(p.Moss * (1 - p.Char)); splat3[o + 1] = MapGen.B(p.Glow);
                    // Nothing grows on char, in water or where it is trodden flat.
                    grass[j * SplatRes + i] = MapGen.B(p.Grass * (1 - p.Char) * (1 - p.Wet * 0.9) * (1 - p.Trod * 0.7));
                }
            });
        }

        /// <summary>The ember's ring: char a few metres either side of the edge,
        /// fraying inward in fingers along the noise, as a fire's edge does.</summary>
        public double RingChar(double x, double z, double inn)
        {
            if (inn > 14 || inn < -14) return 0;
            double n = Noise.Noise(x * 0.11 + 17, z * 0.11 - 5);
            double finger = Math.Pow(Math.Max(0, Noise.Ridged(x * 0.045 - 3, z * 0.045 + 9, 3)), 3) * 9;
            double inward = 1 - MathX.Smoothstep(1.5, 4.5 + finger, inn + n * 1.6);
            double outward = MathX.Smoothstep(-12, -3, inn + n * 2);
            // Never past 0.85: what is hotter than that (a pit's mouth) glows whole.
            return MathX.Clamp01(inward * outward) * 0.85;
        }

        /* ----------------------------------------------------------- flora -- */

        public void Grow(ArenaShape shape)
        {
            for (double gz = -Half; gz < Half; gz += 3.2)
                for (double gx = -Half; gx < Half; gx += 3.2)
                {
                    double x = gx + Rng.Range(0, 3.2), z = gz + Rng.Range(0, 3.2);
                    double d = Out(x, z), inn = In(x, z);
                    if (d > 1.2) shape.Wall(x, z, d);
                    else if (inn < 2.2) shape.Fringe(x, z, inn);
                    else shape.Open(x, z, inn);
                }
        }

        /* ------------------------------------------------- what a place uses -- */

        /// <summary>A piece of flora (the kit's or a scan) where it stands.</summary>
        public void Put(string kind, double x, double z, double scale = 1, double sink = 0)
        {
            var k = Kinds[kind];
            Flora.Add(new FloraPlace(kind, k.Pieces[Rng.Int(0, k.Pieces.Length - 1)], x, HeightAt(x, z) - sink, z,
                Rng.Range(0, Math.PI * 2), k.Scale * scale * Rng.Range(0.85, 1.2)));
        }

        /// <summary>A piece of flora turned as asked (a trunk laid along a line).</summary>
        public void PutAt(string kind, double x, double z, double rot, double scale = 1, double sink = 0)
        {
            var k = Kinds[kind];
            Flora.Add(new FloraPlace(kind, k.Pieces[Rng.Int(0, k.Pieces.Length - 1)], x, HeightAt(x, z) - sink, z, rot, k.Scale * scale));
        }

        /// <summary>A piece set down as the arena begins (kit, KayKit or the arena's own art).</summary>
        public void Piece(string id, double x, double z, double rot, double scale = 1) =>
            Pieces.Add(new PropPlace(id, x, HeightAt(x, z), z, rot, scale));

        public void Block(double x, double z, double r) =>
            Colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Circle, X = x, Z = z, R = r, Hw = r, Hd = r });

        public void Slab(double x, double z, double hw, double hd, double rot) =>
            Colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Box, X = x, Z = z, Hw = hw, Hd = hd, Rot = rot, R = Math.Sqrt(hw * hw + hd * hd) });

        /// <summary>A lamp's light (or a fire's, with its flames) at a point.</summary>
        public int Glow(double x, double z, string color, double intensity, bool fire = false, double height = 1.1, double flicker = 0.14, double size = 0.7)
        {
            double y = HeightAt(x, z);
            Lights.Add(new LightDef { X = x, Y = y + height, Z = z, Color = color, Intensity = intensity, Distance = intensity, Flicker = fire ? 0.28 : flicker, On = true });
            if (fire) Fires.Add(new FireDef { X = x, Y = y + 0.1, Z = z, Size = size, Light = Lights.Count - 1 });
            return Lights.Count - 1;
        }

        /// <summary>Is a spot free for something of radius r: on open ground, off
        /// what is taken (a way, a stream, other cover).</summary>
        public bool Free(double x, double z, double r) =>
            CanStand(x, z) && In(x, z) > r + 2 && !Taken.Any(t => MathX.Dist(t.X, t.Z, x, z) < t.R + r)
            && !Lanes.Any(l => MathX.DistToSegment(x, z, l.Ax, l.Az, l.Bx, l.Bz) < l.Hw + r);

        public void Take(double x, double z, double r) => Taken.Add((x, z, r));

        /// <summary>Kept clear for its length (a way, a road, a stream, rails): cover keeps off it.</summary>
        public readonly List<(double Ax, double Az, double Bx, double Bz, double Hw)> Lanes = new();
        public void Lane((double X, double Z, double Hw)[] path)
        {
            for (int k = 0; k + 1 < path.Length; k++)
                Lanes.Add((path[k].X, path[k].Z, path[k + 1].X, path[k + 1].Z, Math.Max(path[k].Hw, path[k + 1].Hw)));
        }

        /// <summary>A gentle curve from a to b bowed to one side: points with a half-width each.</summary>
        public (double X, double Z, double Hw)[] Curve(double ax, double az, double bx, double bz, double bow, double hw, double wander = 0.25, int step = 2)
        {
            double mx = (ax + bx) / 2, mz = (az + bz) / 2, dx = bx - ax, dz = bz - az, len = Math.Sqrt(dx * dx + dz * dz);
            double cx = mx - dz / len * bow, cz = mz + dx / len * bow;
            int n = Math.Max(8, (int)(len / step));
            var pts = new (double, double, double)[n + 1];
            for (int i = 0; i <= n; i++)
            {
                double t = (double)i / n, u = 1 - t;
                double x = u * u * ax + 2 * u * t * cx + t * t * bx, z = u * u * az + 2 * u * t * cz + t * t * bz;
                pts[i] = (x, z, hw * (1 + wander * Noise.Noise(x * 0.04 + 11, z * 0.04)));
            }
            return pts;
        }

        /// <summary>A path as a field, cell by cell (1 m apart): metres to its
        /// middle over its half-width there (1 at its edge), so painting and
        /// shaping read it at any point without walking the path.</summary>
        public double[] PathField((double X, double Z, double Hw)[] path)
        {
            var f = new double[Res * Res];
            System.Threading.Tasks.Parallel.For(0, Res, j =>
            {
                for (int i = 0; i < Res; i++)
                {
                    double x = i - Half, z = j - Half, best = 99, hw = 1;
                    for (int k = 0; k + 1 < path.Length; k++)
                    {
                        var (ax, az, ah) = path[k]; var (bx, bz, bh) = path[k + 1];
                        if (Math.Abs(x - ax) > 24 && Math.Abs(x - bx) > 24) continue;
                        if (Math.Abs(z - az) > 24 && Math.Abs(z - bz) > 24) continue;
                        double d = MathX.DistToSegment(x, z, ax, az, bx, bz);
                        if (d < best) { best = d; hw = (ah + bh) / 2; }
                    }
                    f[j * Res + i] = best / hw;
                }
            });
            return f;
        }

        /// <summary>Many short strokes (roots, runs, rails) as one field, as PathField.</summary>
        public double[] SegsField(List<(double Ax, double Az, double Bx, double Bz, double Hw)> segs)
        {
            var f = new double[Res * Res];
            System.Threading.Tasks.Parallel.For(0, Res, j =>
            {
                for (int i = 0; i < Res; i++)
                {
                    double x = i - Half, z = j - Half, best = 99;
                    foreach (var s in segs)
                    {
                        if (x < Math.Min(s.Ax, s.Bx) - 12 || x > Math.Max(s.Ax, s.Bx) + 12) continue;
                        if (z < Math.Min(s.Az, s.Bz) - 12 || z > Math.Max(s.Az, s.Bz) + 12) continue;
                        best = Math.Min(best, MathX.DistToSegment(x, z, s.Ax, s.Az, s.Bx, s.Bz) / s.Hw);
                    }
                    f[j * Res + i] = best;
                }
            });
            return f;
        }

        /// <summary>A field's value at a point (between its cells).</summary>
        public double At(double[] field, double x, double z) => MapGen.Bilinear(field, x, z, Half);

        /// <summary>The nearest point of a path: metres to its middle, its half-width there, and how far along (0..1).</summary>
        public static (double D, double Hw, double T) Near((double X, double Z, double Hw)[] path, double x, double z)
        {
            double best = double.MaxValue, hw = 0, t = 0;
            for (int k = 0; k + 1 < path.Length; k++)
            {
                var (ax, az, ah) = path[k]; var (bx, bz, bh) = path[k + 1];
                if (Math.Abs(x - ax) > best + 8 && Math.Abs(x - bx) > best + 8) continue;
                if (Math.Abs(z - az) > best + 8 && Math.Abs(z - bz) > best + 8) continue;
                double d = MathX.DistToSegment(x, z, ax, az, bx, bz);
                if (d < best) { best = d; hw = (ah + bh) / 2; t = (k + 0.5) / (path.Length - 1); }
            }
            return (best, hw, t);
        }

        /// <summary>A bearing's point at the edge, `off` metres out from it (negative: in).</summary>
        public (double X, double Z) AtEdge(double ang, double off = 0)
        {
            double r = EdgeR(ang) + off;
            return (Math.Cos(ang) * r, Math.Sin(ang) * r);
        }

        /// <summary>A piece's own x axis, turned: where a row of them runs.</summary>
        public static (double X, double Z) Along(double rot) => (Math.Cos(rot), -Math.Sin(rot));

        /// <summary>A rotation facing a point (the piece's +z toward it).</summary>
        public static double Facing(double fx, double fz, double tx, double tz) => Math.Atan2(tx - fx, tz - fz);

        /* ------------------------------------------------------------ ring -- */

        /// <summary>The ember's ring: its lights, low and red, all the way round.</summary>
        public void Ring()
        {
            int n = 14;
            double a0 = Rng.Range(0, Math.PI * 2);
            for (int k = 0; k < n; k++)
            {
                double a = a0 + k * Math.PI * 2 / n + Rng.Range(-0.08, 0.08);
                var (x, z) = AtEdge(a, -1.5);
                Lights.Add(new LightDef { X = x, Y = HeightAt(x, z) + 0.7, Z = z, Color = Place.Air.Ember, Intensity = 3.6, Distance = 9, Flicker = 0.35, On = true });
            }
        }

        /* ----------------------------------------------------------- build -- */

        public MapBuild Build()
        {
            // The walls: solid boxes over the closed cells within reach of the
            // clearing, merged into as few boxes as will cover them.
            foreach (var (i0, j0, w, h) in MapGen.Merge(Outside, 4.5))
            {
                double hw = w / 2.0, hd = h / 2.0;
                Colliders.Add(new ColliderDef { Id = cid++, Kind = ColliderKind.Box, X = i0 - Half - 0.5 + hw, Z = j0 - Half - 0.5 + hd, Hw = hw, Hd = hd, R = Math.Sqrt(hw * hw + hd * hd), Tag = "wall" });
            }
            var rim = new List<(double, double)>();
            for (int k = 0; k < 180; k++) rim.Add(AtEdge(k * Math.PI / 90));
            var start = new Area(0, AreaKind.Start, 0, 0, R);
            var meta = new ZoneMeta
            {
                Id = "arena", Size = Size, Res = Res, SplatRes = SplatRes, Leaves = 0.22, BlightGlow = "#9aff4a",
                Bound = Half - 4,
                Start = new Start { X = 0, Z = 0, Facing = 0 },
                Atmosphere = Place.Night,
                Lights = Lights, Fires = Fires, Colliders = Colliders,
                Refs = JsonSerializer.SerializeToElement(new { }),
                Places = new Dictionary<string, JsonElement> { ["M"] = JsonSerializer.SerializeToElement(new Dictionary<string, object> { ["start"] = new { x = 0, z = 0 }, ["boss"] = new { x = 0, z = 0 }, ["area0"] = new { x = 0, z = 0 } }) },
                Paths = new Dictionary<string, double[][]> { ["RIM"] = rim.Select(p => new[] { p.Item1, p.Item2 }).ToArray() },
                Map = new ZoneMapDef
                {
                    Flora = Flora.Where(f => f.Kind is "pine" or "broadleaf" or "autumn" or "dead" or "scan_boulder" or "scan_rock" or "scan_cliff")
                        .Select(f => JsonSerializer.SerializeToElement(new object[] { f.Kind, f.X, f.Z, f.Scale })).ToList(),
                },
            };
            return new MapBuild
            {
                Spec = Spec, Meta = meta, Ground = Ground, SplatRes = SplatRes, Splat = splat, Splat2 = splat2, Splat3 = splat3, Grass = grass, Flora = Flora, Props = new(), Pieces = Pieces,
                Kinds = Kinds, Areas = new List<Area> { start }, Packs = new(), Walkable = Walk, Place = Place, Rim = rim, Streams = Streams, Rails = Rails, Vents = Vents, Inside = Inside,
            };
        }
    }
}
