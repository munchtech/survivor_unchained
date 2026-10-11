using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play.Story;

namespace SurvivorUnchained.Maps.Arenas;

/* Behind the Sealed Door's own place (Play/Story/Vault.cs, VaultOpened.Ground: combat's outline, its
 * gates and points, built to as they stand): the Seventh Legion's hall under its howe, at the head of
 * the stair. The roof fell in long ago and the howe came down with it; the moon looks straight in.
 *
 *   the hall      22 m across and forty long, door at the south, its walls standing to the height
 *                 the centuries left them: ashlar laced with brick every fourth course, piers between
 *                 the bays, and in the bays the Legion's dead in niches, rows of them; a way of long
 *                 slabs, kerbed, down its middle, and in the way the chain of seven links inlaid in
 *                 bronze gone green, running to the stair (the chain the Legion laid on what it could
 *                 not burn; its last link broken)
 *   the landing   wider, before the north wall; the stair's mouth an arch in that wall, the stair
 *                 going down out of the moon into the Morrow's own light, far below
 *
 * The howe's turf lies over the wall tops, and where a wall broke its earth came in, in fans down
 * onto the floor. The roof's tiles lie broken in drifts; the floor's slabs are gone in places to the
 * earth under them. Cover is the fight's (the fallen beams and the sarcophagi, VaultOpened.Cover).
 * Nothing stands in the hall: what is tall is its walls, and the ranks of the dead along them. */
public sealed class Vault : ArenaShape
{
    StoryPlace P => B.Outline!;

    // The plan, in world metres (north is -z): the walls' inner faces, how thick they are, and
    // where the gates' piers, the door and the stair's mouth stand. View/Pieces.Hall builds them.
    public const double HallHalf = 11.25, LandHalf = 15.25, SouthFace = 22.85, NorthFace = -38.3, Cross = -19.4, GateZ = 6, Thick = 1.4;
    public const double DoorHalf = 1.7, StairHalf = 2.9;
    /// <summary>The way down the middle: its x, half-width, and the z it runs between.</summary>
    public static readonly (double X, double Hw, double Z0, double Z1) Aisle = (0, 2.2, NorthFace, SouthFace);
    /// <summary>The landing, the boss's ground, paved in rings about its middle from the gate north:
    /// its middle, where the rings begin, and how wide each is.</summary>
    public static readonly (double X, double Z, double From, double W) Rings = (0, -29, Cross - 0.6, 1.25);
    /// <summary>The dust blown in at the door, lying up the hall from it (how far, how thick), and
    /// Jessop's bootprints in it, going in and never coming out (the story's: STORY_BIBLE, the stair).</summary>
    public static readonly (double Z, double Reach, double Depth) Dust = (SouthFace, 15, 0.55);
    public static readonly (double X0, double Z0, double X1, double Z1) Prints = (-0.8, 22.4, -3.2, 5.0);
    /// <summary>The chain inlaid in the way: from, to, and its links.</summary>
    public static readonly (double X0, double Z0, double X1, double Z1, int Links) Chain = (0, -5.5, 0, -37.6, 7);

    /// <summary>A run of wall: its inner face from A to B, the way into the hall (N), how high it
    /// stands broken (Lo to Hi, metres over the floor), its own seed.</summary>
    public readonly record struct Run(double Ax, double Az, double Bx, double Bz, double Nx, double Nz, double Lo, double Hi, int Seed);

    /// <summary>A pier on a wall's face: its middle on the face, its width along the wall, how far it
    /// stands out of the face, how high, and the way into the hall.</summary>
    public readonly record struct Pier(double X, double Z, double W, double Out, double H, double Nx, double Nz);

    /// <summary>A breach where the howe came in: its middle on a wall's face, how wide, the way in.</summary>
    public readonly record struct Breach(double X, double Z, double W, double Nx, double Nz);

    public static readonly Run[] Runs = BuildRuns();
    public static readonly Pier[] Piers = BuildPiers();
    public static readonly Breach[] Breaches =
    [
        new(-HallHalf, 13.6, 3.8, 1, 0),
        new(HallHalf, -6.8, 5.0, -1, 0),
        new(-HallHalf, -12.6, 3.0, 1, 0),
    ];

    static Run[] BuildRuns()
    {
        var o = new List<Run>();
        foreach (int s in new[] { -1, 1 })
        {
            // The hall's sides, through the south corners.
            o.Add(new(s * HallHalf, SouthFace + Thick, s * HallHalf, Cross, -s, 0, 2.6, 5.8, 11 + s));
            // The south wall either side of the door: low, the camera's side.
            o.Add(new(s * (HallHalf + Thick), SouthFace, s * DoorHalf, SouthFace, 0, -1, 0.9, 2.3, 21 + s));
            // Where the hall opens into the landing, out to its sides.
            o.Add(new(s * HallHalf, Cross, s * (LandHalf + Thick), Cross, 0, -1, 4.0, 6.0, 31 + s));
            // The landing's sides, where the ranks stand.
            o.Add(new(s * LandHalf, Cross + Thick, s * LandHalf, NorthFace - Thick, -s, 0, 5.0, 7.4, 41 + s));
            // The north wall, the stair's mouth in its middle: the tallest, at the top of the picture.
            o.Add(new(s * (LandHalf + Thick), NorthFace, s * StairHalf, NorthFace, 0, 1, 7.0, 9.0, 51 + s));
        }
        return o.ToArray();
    }

    static Pier[] BuildPiers()
    {
        var o = new List<Pier>();
        foreach (int s in new[] { -1, 1 })
        {
            foreach (double z in new[] { 17.3, 11.7, 0.6, -4.6, -9.8, -15.0 }) o.Add(new(s * HallHalf, z, 1.1, 0.2, 0, -s, 0));
            // The gate's piers, where an arch across the hall stood: they fill the outline's waist.
            o.Add(new(s * HallHalf, GateZ, 2.2, 0.75, 7.2, -s, 0));
            foreach (double z in new[] { -25.6, -31.9 }) o.Add(new(s * LandHalf, z, 1.1, 0.2, 0, -s, 0));
            o.Add(new(s * 9.0, NorthFace, 1.2, 0.2, 0, 0, 1));
            // The stair arch's own piers.
            o.Add(new(s * (StairHalf + 0.6), NorthFace, 1.2, 0.35, 9.4, 0, 1));
            // The door's jambs.
            o.Add(new(s * (DoorHalf + 0.45), SouthFace, 0.9, 0.25, 3.9, 0, -1));
        }
        return o.ToArray();
    }

    /// <summary>The corner piers where the hall's sides end at the landing: square, tall.</summary>
    public static readonly (double X, double Z, double Half, double H)[] Corners = [(-12.0, -18.4, 1.1, 7.6), (12.0, -18.4, 1.1, 7.6)];

    /// <summary>How high a run stands at a point along it (0 to its length), broken: its courses
    /// (0.44 m, the ashlar's) stepping down and up, and down to a stump where the howe came in.</summary>
    public static double Standing(Run r, double s)
    {
        double len = MathX.Dist(r.Ax, r.Az, r.Bx, r.Bz);
        double t = s / Math.Max(len, 1e-6);
        double x = r.Ax + (r.Bx - r.Ax) * t, z = r.Az + (r.Bz - r.Az) * t;
        double n = 0.5 + 0.5 * Math.Sin(s * 0.21 + r.Seed * 1.7) * 0.6 + 0.2 * Math.Sin(s * 0.53 + r.Seed * 3.1) + 0.12 * Math.Sin(s * 1.37 + r.Seed);
        double h = r.Lo + (r.Hi - r.Lo) * Math.Clamp(n, 0, 1);
        foreach (var b in Breaches)
        {
            double d = MathX.Dist(x, z, b.X, b.Z);
            h = Math.Min(h, MathX.Lerp(0.5 + 0.3 * Math.Sin(s * 2.3), h, MathX.Smoothstep(b.W * 0.35, b.W * 0.5 + 1.2, d)));
        }
        return Math.Max(0.44, Math.Round(h / 0.44) * 0.44);
    }

    /// <summary>The top of a run's masonry at a point: its broken line, with a block knocked off it
    /// here and there (one in five of its 0.9 m stones).</summary>
    public static double Top(Run r, double s)
    {
        int block = (int)Math.Floor(s / 0.9);
        double hash = Frac(Math.Sin((r.Seed * 31 + block) * 12.9898 + 7 * 78.233) * 43758.547);
        return Math.Max(0.44, Standing(r, s) - (hash < 0.22 ? 0.44 : 0));
    }

    static double Frac(double v) => v - Math.Floor(v);

    public override bool Level => true;
    // (The walls' feet are soot-black under a full ring's char: a hall's edge is its walls.)
    public override double Scorch => 0.3;

    double[] wallF = null!;

    public override void Plan()
    {
        foreach (var g in P.Gates) B.Gates.Add((g.Id, g.X0, g.Z0, g.X1, g.Z1));
        // Metres to the nearest wall face, cell by cell (the floor's paint reads it).
        var segs = Runs.Select(r => (r.Ax, r.Az, r.Bx, r.Bz, 1.0)).ToList();
        wallF = B.SegsField(segs);
    }

    double WallD(double x, double z) => B.At(wallF, x, z);

    /// <summary>How deep a breach's fan of earth lies at a point (0 none, 1 at the breach).</summary>
    static double Fan(double x, double z)
    {
        double f = 0;
        foreach (var b in Breaches)
        {
            double into = (x - b.X) * b.Nx + (z - b.Z) * b.Nz;
            double along = Math.Abs((x - b.X) * -b.Nz + (z - b.Z) * b.Nx);
            if (into < -4 || into > 6 || along > b.W) continue;
            f = Math.Max(f, (1 - MathX.Smoothstep(-0.5, 3.6, into)) * (1 - MathX.Smoothstep(b.W * 0.3, b.W * 0.5 + 0.9 + Math.Max(0, into) * 0.25, along)));
        }
        return f;
    }

    /// <summary>The stair's well behind the north wall, cut down out of the howe.</summary>
    static bool Well(double x, double z) => Math.Abs(x) < StairHalf + 0.5 && z < NorthFace - 0.1 && z > NorthFace - 13;

    public override double Bank(double x, double z) => Well(x, z) ? 0 : 1;

    public override double Relief(double x, double z)
    {
        double h = 0;
        // Each breach's earth, fanned down onto the floor from the broken wall.
        h += 1.5 * Math.Pow(Fan(x, z), 1.3) * (1 + 0.15 * Noise.Noise(x * 0.6, z * 0.6));
        // The stair's well: down below where the stair goes, under the arch.
        if (Well(x, z)) h -= 9;
        return h;
    }

    public override void Paint(double x, double z, double inn, ref ArenaPaint p)
    {
        double n1 = Noise.Noise(x * 0.09, z * 0.09), n2 = Noise.Noise(x * 0.23 + 4, z * 0.23), n3 = Noise.Noise(x * 0.5 + 11, z * 0.5 - 3);
        double wd = WallD(x, z);
        bool inside = inn > -0.4;
        double fan = Fan(x, z);
        bool way = Math.Abs(x - Aisle.X) < Aisle.Hw;
        if (inside)
        {
            // The floor, paved; its slabs going where the walls shed their rubble on them, under the
            // breaches' earth, and here and there in patches where the roof came down hardest.
            double gone = MathX.Smoothstep(0.45, 0.8, Noise.Noise(x * 0.11 + 7, z * 0.11 - 3) + n2 * 0.3) * (way ? 0.15 : 0.4);
            double foot = (1 - MathX.Smoothstep(0.3, 1.8, wd + n1 * 0.6)) * 0.35;
            p.L2 = MathX.Clamp01(1 - gone - foot - fan * 1.2);
            // Under the slabs, the earth.
            p.BaseB = 1;
        }
        // The walls' rubble at their feet, heaped at the piers and the corners, and fallen in where
        // they are lowest.
        double rub = (1 - MathX.Smoothstep(0.4, 1.8 + n1 * 0.8, wd + n2 * 0.5)) * MathX.Smoothstep(-0.2, 0.3, n1 + n3 * 0.3);
        // Heaped at the piers' feet, where the arches came down.
        foreach (var pr in Piers)
        {
            if (Math.Abs(x - pr.X) > 5 || Math.Abs(z - pr.Z) > 5) continue;
            double d = MathX.Dist(x, z, pr.X + pr.Nx * pr.Out, pr.Z + pr.Nz * pr.Out) + n2 * 0.6;
            rub = Math.Max(rub, 1 - MathX.Smoothstep(pr.W * 0.6, pr.W * 0.6 + 1.6 + (pr.Out > 0.5 ? 1.2 : 0), d));
        }
        p.L3 = Math.Max(p.L3, rub * 0.95);
        // The roof's tiles, broken, drifted over the floor: thick toward the walls (the roof fell
        // from them), thin in the way, kicked aside by two thousand years of files coming up it.
        double drift = MathX.Smoothstep(0.25, 0.75, Noise.Noise(x * 0.07 - 23, z * 0.07 + 41) * 0.6 + n2 * 0.25 + MathX.Smoothstep(5, 0.5, wd) * 0.45);
        p.L4 = Math.Max(p.L4, drift * (way ? 0.15 : 0.65) * (inside ? 1 : 0.3) * (1 - fan));
        // The howe's earth where it came in, its turf riding down on it.
        p.L5 = Math.Max(p.L5, MathX.Smoothstep(0.15, 0.6, fan + n1 * 0.2) * (1 - MathX.Smoothstep(0.55, 0.9, fan + n2 * 0.2)));
        if (fan > 0.55 + n2 * 0.15) { p.L5 *= 0.4; p.L2 = 0; p.BaseB = 0; }
        // Damp at the walls' feet, out of the sun that never comes: moss in cushions on the rubble
        // and in the joints, more in the west wall's shadow.
        double damp = (1 - MathX.Smoothstep(0.3, 2.6, wd + n1 * 0.8)) * (x < 0 ? 0.9 : 0.6);
        p.Moss = Math.Max(p.Moss, damp * MathX.Smoothstep(0.0, 0.4, n2 + n3 * 0.3) * (inside ? 1 : 0));
        // Rain stands where slabs have sunk, in a few small pools.
        // (Not many: from above at night a pool holds the dark sky, and a floor of them read as
        // navy blots.)
        double pool = MathX.Smoothstep(0.74, 0.84, Noise.Noise(x * 0.13 + 50, z * 0.13 - 20) + n3 * 0.1) * (inside ? 1 : 0) * (1 - fan);
        p.Wet = Math.Max(p.Wet, pool * 0.85);
        // The ember's line across each gate, scorched into the stone where it burned: narrow and
        // broken. (Two metres of char across the floor read as a wall's shadow.)
        foreach (var g in P.Gates)
        {
            double d = MathX.DistToSegment(x, z, g.X0, g.Z0, g.X1, g.Z1) + n2 * 0.25 + n3 * 0.15;
            p.Char = Math.Max(p.Char, (1 - MathX.Smoothstep(0.15, 0.6, d)) * 0.55 * MathX.Smoothstep(-0.3, 0.2, n1 + n3 * 0.5));
        }
        // Dirt deeper toward the walls, where nothing has walked in two thousand years; the way
        // down the middle clean.
        if (inside) p.Trod = Math.Max(p.Trod, (1 - MathX.Smoothstep(0.5, 5.0, wd + n1 * 1.2)) * (way ? 0 : 0.85));
        // Outside: the howe's dead turf, bare in patches; its grass down the fans too.
        if (!inside)
        {
            // (Less bare earth over the howe than the barrow field has: from above, its pale patches
            // either side of the hall drew the eye off the fight.)
            p.BaseB *= 0.45;
            p.Grass = MathX.Smoothstep(-0.3, 0.2, n1 + n2 * 0.4) * (1 - p.BaseB * 0.5);
        }
        p.Grass = Math.Max(p.Grass, MathX.Smoothstep(0.45, 0.85, fan + n3 * 0.2) * 0.9);
        p.Open = 1;
    }

    public override void Wall(double x, double z, double d)
    {
        // The howe over the hall: tussocks, bramble and thorn over its turf, a stone of the walls
        // here and there in the grass. No trees near: their shadows would fill the hall.
        if (Well(x, z)) return;
        if (Rng.Chance(0.55)) B.Put(Rng.Pick(new[] { "scan_grass", "scan_grass", "scan_shrub", "bramble" }), x + Rng.Range(-1, 1), z + Rng.Range(-1, 1), Rng.Range(0.9, 1.35));
        if (d > 3 && Rng.Chance(0.07)) B.Put(Rng.Pick(new[] { "scan_rock", "scan_stones", "scan_mossrock" }), x, z, Rng.Range(0.6, 1.0), 0.15);
        if (d > 18 && Rng.Chance(0.1)) B.Put("dead", x, z, 1 + Math.Min(0.4, d * 0.012));
    }

    public override void Fringe(double x, double z, double inn)
    {
        if (Fan(x, z) > 0.3 && Rng.Chance(0.5)) B.Put(Rng.Pick(new[] { "scan_grass", "scan_grass", "scan_shrub" }), x, z, Rng.Range(0.7, 1.1));
    }

    public override void Open(double x, double z, double inn)
    {
        if (Fan(x, z) > 0.45 && Rng.Chance(0.35)) B.Put("scan_grass", x, z, Rng.Range(0.6, 1.0));
    }

    /// <summary>Kept clear: every point the fight is staged from.</summary>
    bool NearPoint(double x, double z, double r) => P.Points.Values.Any(p => MathX.Dist(p.X, p.Z, x, z) < r);

    public override void Dress()
    {
        // The hall itself: its walls, piers, niches, door and the stair's mouth (View/Pieces.Hall).
        B.Piece("arena/hall", 0, 0, 0);
        // The howe's grass over the wall tops, in stretches, where its turf has crept over them.
        double floor = B.HeightAt(0, 0);
        foreach (var r in Runs)
        {
            double len = MathX.Dist(r.Ax, r.Az, r.Bx, r.Bz), ux = (r.Bx - r.Ax) / len, uz = (r.Bz - r.Az) / len;
            for (double s = 0.3; s < len - 0.3; s += 0.45)
            {
                if (Noise.Noise(s * 0.3 + r.Seed * 5.1, r.Seed * 2.3) < 0.05 || !Rng.Chance(0.55)) continue;
                double top = Top(r, s);
                if (Math.Abs(Top(r, s - 0.3) - top) > 0.01 || Math.Abs(Top(r, s + 0.3) - top) > 0.01) continue;
                double d = Rng.Range(0.25, Thick - 0.2);
                double x = r.Ax + ux * s - r.Nx * d, z = r.Az + uz * s - r.Nz * d;
                if (Piers.Any(p => MathX.Dist(p.X, p.Z, x, z) < p.W / 2 + 0.6)) continue;
                B.PutOn(Rng.Chance(0.85) ? "scan_grass" : "scan_shrub", x, floor + top - 0.04, z, Rng.Range(0.6, 1.0));
            }
        }
        // The stair's breath: the Morrow's own light, far down, warm under the cold moon; and a little
        // of it up at the mouth, under the arch and out over the landing's floor.
        int glow = B.Glow(0, NorthFace - 9.5, "#ff6a2a", 8, height: 6, flicker: 0.05);
        B.Lights[glow].Distance = 10;
        int mouth = B.Glow(0, NorthFace - 1.6, "#ff7a3a", 3.2, height: 8.3, flicker: 0.04);
        B.Lights[mouth].Distance = 7.5;
        // (Out over the landing's floor before the stair, a warm pool: the boss's ground has its
        // own light at its far end, under the cold moon.)
        int spill = B.Glow(0, NorthFace + 0.4, "#ff8040", 2.4, height: 0.7, flicker: 0.04);
        B.Lights[spill].Distance = 6.5;
        // The walls' and arches' stones come down where nobody fights: the dead corners, the gate
        // piers' feet (where the arch over the hall fell), the landing's corners.
        foreach (var (x, z) in new[] { (-9.9, 21.4), (10.1, 21.2), (-10.2, 6.0), (10.3, 6.2), (-13.6, -20.9), (13.7, -20.8), (-14.0, -37.2), (14.1, -37.0) })
            B.Piece("arena/tumble", x, z, Rng.Range(0, Math.PI * 2), Rng.Range(0.9, 1.15));
        // The Legion's shields where they fell, the long curved scuta: by the walls, never on a point
        // the fight is staged from, never in the way.
        foreach (var (x, z) in new[] { (-8.6, 15.5), (7.9, 9.4), (-9.2, -3.6), (8.8, -15.8), (-12.6, -26.5), (12.4, -33.0), (5.6, 19.8) })
        {
            if (NearPoint(x, z, 1.4)) continue;
            B.Piece("arena/scutum", x, z, Rng.Range(0, Math.PI * 2));
        }
        // The dead's leavings on the floor, kept off the fight's points: bones, a skull, never much.
        for (int k = 0; k < 14; k++)
        {
            double x = Rng.Range(-HallHalf + 1, HallHalf - 1), z = Rng.Range(Cross + 1, SouthFace - 2);
            if (k >= 10) { x = Rng.Range(-LandHalf + 1, LandHalf - 1); z = Rng.Range(NorthFace + 1, Cross - 1); }
            if (!B.CanStand(x, z) || NearPoint(x, z, 1.5) || Math.Abs(x) < Aisle.Hw) continue;
            B.Piece(Rng.Pick(new[] { "halloween/bone_A", "halloween/bone_B", "halloween/bone_C", "halloween/bone_A", "halloween/skull" }), x, z, Rng.Range(0, Math.PI * 2), Rng.Range(0.55, 0.75));
        }
    }
}
