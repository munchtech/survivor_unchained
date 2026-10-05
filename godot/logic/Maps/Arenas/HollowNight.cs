using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play.Story;

namespace SurvivorUnchained.Maps.Arenas;

/* The Hollow by Night's own place (Play/Story/Hollow.cs, HollowByNight.Ground: combat's outline,
 * its gates and points, built to as they stand). Three spaces down into the Pack's Hollow, on the
 * Hollow's ground:
 *
 *   the clough      a cut in the wood fourteen metres wide, its banks steep and rooted, an old dry
 *                   watercourse of stones down the middle, bracken at the banks' feet; Old Blue's
 *                   three rocks are knolls of bare rock he stands up on to howl
 *   the sick water  the stream comes in out of the bank, spreads into a pool and goes out again
 *                   under the far bank; reeds at its edges (the blighted come out of them), the
 *                   shallows thick with the Dig's slurry and its sick light; on the far bank, two
 *                   deadfalls the ember will light
 *   the den floor   a bowl of trodden mud, the runs worn into it, bones about it; four deadfalls at
 *                   its corners; at its north edge the den's mouth, a hole under the root plate of
 *                   a giant come down, where Greymuzzle sleeps with his sick
 *
 * The gates are the ember's: its burning line across each way until the stage is won (ArenaEdge).
 * Rotting wood and roots glow faintly with foxfire: the cold light the place has of its own, so
 * a moonless night is never flat black. Cover inside is low, and never on a point the fight is
 * staged from. */
public sealed class HollowNight : ArenaShape
{
    StoryPlace P => B.Outline!;
    (double X, double Z, double Hw)[] stream = null!;
    double[] streamF = null!, runsF = null!;
    readonly List<(double Ax, double Az, double Bx, double Bz, double Hw)> runs = new();
    /// <summary>Old Blue's rocks: knolls of bare rock.</summary>
    readonly List<(double X, double Z, double R, double H)> rocks = new();
    (double X, double Z) mouth, den;
    /// <summary>The way out of the den through its mouth (unit), how far a point lies past the
    /// mouth along it, and the point that far past it.</summary>
    double ox, oz;
    double Beyond(double x, double z) => (x - mouth.X) * ox + (z - mouth.Z) * oz;
    (double X, double Z) Past(double d) => (mouth.X + ox * d, mouth.Z + oz * d);
    readonly List<(double X, double Z, double R)> reeds = new();

    (double X, double Z) Pt(string id) => P[id];

    /// <summary>Kept clear: every point the fight is staged from.</summary>
    bool NearPoint(double x, double z, double r) => P.Points.Values.Any(p => MathX.Dist(p.X, p.Z, x, z) < r);

    public override void Plan()
    {
        foreach (var (id, h) in new[] { ("rock_low", 0.7), ("rock_mid", 0.85), ("rock", 1.05) })
        {
            var (x, z) = Pt(id);
            rocks.Add((x, z, 2.4, h));
        }
        den = Pt("den");
        mouth = Pt("den_mouth");
        double ol = Math.Max(1e-6, MathX.Dist(den.X, den.Z, mouth.X, mouth.Z));
        (ox, oz) = ((mouth.X - den.X) / ol, (mouth.Z - den.Z) / ol);
        // The stream: in out of the north-west bank, spreading into the pool across the shallows,
        // out under the south-east bank.
        var (ax, az) = Pt("shallow_a");
        var (bx, bz) = Pt("shallow_b");
        stream = Smooth(new (double, double, double)[]
        {
            (-40, -30, 1.3), (-24, -18, 1.3), (-12, -9, 1.5), (-5, -3, 1.8), (ax, az, 2.0), (bx, bz, 1.8), (12, 4, 1.5), (22, 12, 1.3), (40, 24, 1.2),
        });
        streamF = B.PathField(stream);
        B.Streams.Add(stream);
        foreach (var r in new[] { "reeds_w", "reeds_s", "reeds_n" })
        {
            var (x, z) = Pt(r);
            reeds.Add((x, z, 2.6));
        }
        // The Pack's runs: from the den's mouth out across its floor, and down to the water.
        var rng = B.Rng;
        foreach (var to in new[] { "den_in", "den_w", "den_e", "boss_start" })
        {
            var (tx, tz) = Pt(to);
            double x = mouth.X, z = mouth.Z - 2;
            int n = 10;
            for (int k = 0; k < n; k++)
            {
                double t = (k + 1.0) / n;
                double nx = mouth.X + (tx - mouth.X) * t + Math.Sin(t * Math.PI) * rng.Range(-3, 3), nz = mouth.Z - 2 + (tz - mouth.Z + 2) * t;
                runs.Add((x, z, nx, nz, 0.9));
                (x, z) = (nx, nz);
            }
        }
        runsF = B.SegsField(runs);
        foreach (var g in P.Gates) B.Gates.Add((g.Id, g.X0, g.Z0, g.X1, g.Z1));
    }

    /// <summary>A few points made a smooth line, a metre apart (Catmull-Rom).</summary>
    static (double X, double Z, double Hw)[] Smooth((double X, double Z, double Hw)[] k)
    {
        var o = new List<(double, double, double)>();
        for (int i = 0; i + 1 < k.Length; i++)
        {
            var p0 = k[Math.Max(i - 1, 0)]; var p1 = k[i]; var p2 = k[i + 1]; var p3 = k[Math.Min(i + 2, k.Length - 1)];
            double len = MathX.Dist(p1.X, p1.Z, p2.X, p2.Z);
            int n = Math.Max(2, (int)len);
            for (int s = 0; s < n; s++)
            {
                double t = s / (double)n, t2 = t * t, t3 = t2 * t;
                double C(double a, double b, double c, double d) => 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
                o.Add((C(p0.X, p1.X, p2.X, p3.X), C(p0.Z, p1.Z, p2.Z, p3.Z), p1.Hw + (p2.Hw - p1.Hw) * t));
            }
        }
        o.Add(k[^1]);
        return o.ToArray();
    }

    double Stream(double x, double z) => B.At(streamF, x, z);

    public override double Bank(double x, double z)
    {
        // Where the stream comes in and goes out, the bank is cut down to it; the den's mouth is a
        // hole into the bank under the root plate.
        double f = Stream(x, z);
        double cut = MathX.Smoothstep(1.2, 3.5, f);
        var (hx, hz) = Past(1.5);
        double m = MathX.Dist(x, z, hx, hz);
        double hole = MathX.Smoothstep(2.2, 5.5, m + Math.Max(0, -Beyond(x, z)) * 0.6);
        return Math.Min(cut, 0.25 + 0.75 * hole);
    }

    public override double Relief(double x, double z)
    {
        double h = 0;
        // The clough's floor falls a little to its old watercourse.
        if (P.In("clough", x, z, -3))
        {
            double cx = -18 + 1.6 * Math.Sin(z * 0.17);
            h -= 0.3 * (1 - MathX.Smoothstep(0, 5, Math.Abs(x - cx)));
        }
        foreach (var r in rocks)
        {
            double d = MathX.Dist(x, z, r.X, r.Z);
            if (d < r.R + 1) h += r.H * (1 - MathX.Smoothstep(r.R * 0.45, r.R + 0.8, d + 0.4 * Noise.Noise(x * 0.9, z * 0.9)));
        }
        // The pool's bowl, and the stream's bed.
        double dp = MathX.Dist(x, z, 1, 1);
        h -= 0.6 * (1 - MathX.Smoothstep(3, 12, dp));
        double f = Stream(x, z);
        if (f < 2.5) h += -0.55 * (1 - MathX.Smoothstep(0.2, 1.25, f));
        // The den floor, a bowl worn by the Pack lying in it.
        double dd = MathX.Dist(x, z, den.X, den.Z);
        h -= 0.45 * (1 - MathX.Smoothstep(4, 15, dd));
        // The hole under the root plate.
        var (px2, pz2) = Past(2);
        double m = MathX.Dist(x, z, px2, pz2);
        h -= 1.6 * (1 - MathX.Smoothstep(0.8, 4.0, m)) * MathX.Smoothstep(-3, 0.5, Beyond(x, z));
        return h;
    }

    public override void Paint(double x, double z, double inn, ref ArenaPaint p)
    {
        double n1 = Noise.Noise(x * 0.09, z * 0.09), n2 = Noise.Noise(x * 0.23 + 4, z * 0.23), n3 = Noise.Noise(x * 0.5 + 11, z * 0.5 - 3);
        string? space = P.SpaceAt(x, z);
        // Old litter rotted dark in broad patches, drier needles toward the banks.
        p.BaseB = MathX.Smoothstep(-0.2, 0.4, Noise.Noise(x * 0.04 + 40, z * 0.04 - 13) + n2 * 0.3);
        p.L5 = MathX.Smoothstep(0.1, 0.5, Noise.Noise(x * 0.06 + 21, z * 0.06 + 3) + n2 * 0.25) * MathX.Smoothstep(6, 1.5, inn) * 0.9;
        // The clough's old watercourse: stones, dry, meandering down it.
        double cx = -18 + 1.6 * Math.Sin(z * 0.17);
        if (x < -6 && z > 4)
        {
            double wc = Math.Abs(x - cx) + n2 * 0.6 + n3 * 0.3;
            double bed = 1 - MathX.Smoothstep(1.0, 2.0, wc);
            p.L4 = Math.Max(p.L4, bed * MathX.Smoothstep(-44, -40, -z) * (1 - MathX.Smoothstep(-12, -8, -z)));
        }
        // Old Blue's rocks: bare stone on top, scree round their feet.
        foreach (var r in rocks)
        {
            double d = MathX.Dist(x, z, r.X, r.Z) + n2 * 0.6;
            p.L4 = Math.Max(p.L4, 1 - MathX.Smoothstep(r.R * 0.9, r.R + 1.6, d));
            p.Moss = Math.Max(p.Moss, (1 - MathX.Smoothstep(r.R * 0.5, r.R, d)) * MathX.Smoothstep(0.1, 0.4, n1) * 0.8);
        }
        // The water: its bed and its banks of black mud, wet; the slurry in the shallows.
        double f = Stream(x, z) + n2 * 0.15;
        double dp = MathX.Dist(x, z, 1, 1);
        double pool = 1 - MathX.Smoothstep(5.5, 8.5, dp + n1 * 2.2 + n3 * 0.8);
        double bed2 = Math.Max(1 - MathX.Smoothstep(0.75, 1.05, f), pool * 0.85);
        p.L4 = Math.Max(p.L4, bed2);
        double bank = (1 - MathX.Smoothstep(1.2, 2.8, f + n1 * 0.4)) * MathX.Smoothstep(0.6, 1.0, f);
        double poolBank = (1 - MathX.Smoothstep(8, 11.5, dp + n1 * 2)) * (1 - pool);
        p.L3 = Math.Max(p.L3, Math.Max(bank, poolBank * 0.9));
        p.Wet = Math.Max(p.Wet, Math.Max(1 - MathX.Smoothstep(0.9, 1.25, f), Math.Max(pool * 0.95, Math.Max(bank, poolBank) * 0.5)));
        foreach (var (pt, r) in new[] { ("shallow_a", 3.5), ("shallow_b", 2.6) })
        {
            var (sx, sz) = Pt(pt);
            double d = MathX.Dist(x, z, sx, sz) + n1 * 0.8 + n3 * 0.3;
            double k = 1 - MathX.Smoothstep(r * 0.55, r * 1.15, d);
            p.Glow = Math.Max(p.Glow, k);
            p.Wet = Math.Max(p.Wet, k);
            p.L3 = Math.Max(p.L3, k * 0.6);
        }
        // Reed beds: mud, sedge.
        foreach (var r in reeds)
        {
            double d = MathX.Dist(x, z, r.X, r.Z) + n1 * 1.2;
            double k = 1 - MathX.Smoothstep(r.R * 0.6, r.R + 1.5, d);
            p.L3 = Math.Max(p.L3, k * 0.8);
            p.Wet = Math.Max(p.Wet, k * 0.45);
            p.Grass = Math.Max(p.Grass, k);
        }
        // The den floor: trodden to mud, the runs worn into it; the mouth black and wet.
        double dd = MathX.Dist(x, z, den.X, den.Z);
        double floor = (1 - MathX.Smoothstep(6, 11, dd + n1 * 2.5 + n3)) ;
        double run = 1 - MathX.Smoothstep(0.5, 1.2, B.At(runsF, x, z) + n1 * 0.35);
        if (space == "den" || dd < 17)
        {
            p.L3 = Math.Max(p.L3, Math.Max(floor * 0.8, run * 0.85));
            p.Trod = Math.Max(p.Trod, Math.Max(floor * 0.8, run * 0.7));
            p.L5 *= 1 - floor;
        }
        var (mx1, mz1) = Past(1);
        double m = MathX.Dist(x, z, mx1, mz1);
        double mud = 1 - MathX.Smoothstep(2.5, 6, m + n1 * 1.5);
        p.L3 = Math.Max(p.L3, mud);
        p.Wet = Math.Max(p.Wet, mud * 0.6);
        p.Trod = Math.Max(p.Trod, mud);
        // Roots from the trees on the banks, breaking the ground at their feet.
        double rootn = Noise.Ridged(x * 0.14 + 3, z * 0.14 - 8, 2);
        p.L2 = Math.Max(p.L2, MathX.Smoothstep(0.55, 0.8, rootn) * MathX.Smoothstep(4, 0.5, inn) * (1 - p.L3));
        // Moss in cushions where it is damp and nobody treads: the banks' feet, the clough.
        double isle = MathX.Smoothstep(0.5, 0.66, Noise.Noise(x * 0.13 + 70, z * 0.13 - 31) + n2 * 0.25);
        double foot = MathX.Smoothstep(5, 1.5, inn);
        p.Moss = Math.Max(p.Moss, Math.Max(isle * (space == "clough" ? 0.85 : 0.55), foot * MathX.Smoothstep(0.0, 0.35, n2) * 0.8));
        p.Moss *= (1 - p.Trod) * (1 - p.L4 * 0.7) * (1 - MathX.Smoothstep(0.3, 0.7, p.Wet));
        // Foxfire: rotting wood and roots at the banks' feet glowing a little, cold.
        p.Fox = Math.Max(p.L2 * 0.8, foot * MathX.Smoothstep(0.35, 0.7, n3)) * (1 - p.Trod) * (1 - p.Wet);
        // The ember's char where each gate burns.
        foreach (var g in P.Gates)
        {
            double d = MathX.DistToSegment(x, z, g.X0, g.Z0, g.X1, g.Z1) + n2 * 0.4;
            p.Char = Math.Max(p.Char, (1 - MathX.Smoothstep(0.6, 2.2, d)) * 0.8);
        }
        // Where the canopy opens: the den's floor (the boss's ground, under the moon whole), the
        // pool (it holds the sky), and the clough's middle.
        double cl = Math.Abs(x - cx) + n1 * 2;
        p.Open = Math.Max(Math.Max(1 - MathX.Smoothstep(7, 13, dd + n1 * 3), 1 - MathX.Smoothstep(5, 10, dp + n1 * 2)),
            space == "clough" ? (1 - MathX.Smoothstep(2, 6, cl)) * 0.7 : 0);
        // Grass where the canopy opens: a little along the clough and round the pool.
        double hard = Math.Max(Math.Max(p.L3, p.L4), p.Trod);
        p.Grass = Math.Max(p.Grass, (1 - hard) * MathX.Smoothstep(0.25, 0.6, Noise.Noise(x * 0.05 - 40, z * 0.05 + 12) + n2 * 0.2) * 0.8);
    }

    public override void Wall(double x, double z, double d)
    {
        // The wood standing over the Hollow: trees back from the banks' lips, so the cut shows;
        // roots and ferns over its edges.
        // (Thin near the lips: the moon is low, and a tree's shadow over a cut fourteen metres
        // wide would black it out.)
        // Bare trees read from above as tangles over the fight; the crowns stand back.
        double keep = d < 11 ? 0 : d < 18 ? 0.22 : d < 32 ? 0.34 : 0.15;
        if (Rng.Chance(keep)) B.Put(Rng.Pick(new[] { "pine", "broadleaf", "pine", "broadleaf" }), x, z, 0.9 + Math.Min(0.6, d * 0.02));
        if (d < 11 && Rng.Chance(0.5)) B.Put(Rng.Pick(new[] { "scan_fern", "scan_fern", "scan_shrub", "fern", "bramble", "scan_shrub" }), x + Rng.Range(-1, 1), z + Rng.Range(-1, 1), Rng.Range(1.0, 1.6));
        if (d < 7 && Rng.Chance(0.16)) B.Put(Rng.Pick(new[] { "scan_root", "scan_root", "scan_mossrock", "scan_stump", "scan_branches" }), x, z, Rng.Range(0.9, 1.4), 0.15);
    }

    public override void Fringe(double x, double z, double inn)
    {
        if (NearPoint(x, z, 2.2)) return;
        if (Rng.Chance(0.5)) B.Put(Rng.Pick(new[] { "scan_fern", "scan_fern", "scan_shrub", "fern" }), x, z, Rng.Range(0.8, 1.25));
        if (Rng.Chance(0.14)) B.Put(Rng.Pick(new[] { "scan_root", "scan_stump", "scan_branches", "scan_mossrock" }), x, z, Rng.Range(0.8, 1.2), 0.1);
    }

    public override void Open(double x, double z, double inn)
    {
        if (NearPoint(x, z, 2.5) || Stream(x, z) < 1.1) return;
        double patch = Noise.Noise(x * 0.07 + 31, z * 0.07 - 17);
        if (patch < -0.1 && Rng.Chance(0.4)) B.Put(Rng.Chance(0.6) ? "scan_bark" : "scan_moss", x, z, Rng.Range(0.8, 1.2), 0.02);
        if (patch > 0.3 && Rng.Chance(0.2)) B.Put("scan_fern", x, z, Rng.Range(0.7, 1.0));
        if (Stream(x, z) < 2.4 && Rng.Chance(0.35)) B.Put(Rng.Pick(new[] { "scan_stones", "scan_stones", "scan_fern" }), x, z, Rng.Range(0.7, 1.1), 0.05);
        if (Rng.Chance(0.03)) B.Put(Rng.Pick(new[] { "mushroom", "scan_branches", "scan_bark" }), x, z);
    }

    public override void Dress()
    {
        // ------------------------------------------------------------ the clough --
        // Old Blue's rocks: boulders shouldered against each knoll's back, scree at its foot.
        foreach (var r in rocks)
        {
            for (int k = 0; k < 3; k++)
            {
                double a = Rng.Range(0, Math.PI * 2), rr = r.R + Rng.Range(0.2, 0.9);
                double bx = r.X + Math.Cos(a) * rr, bz = r.Z + Math.Sin(a) * rr;
                if (!B.CanStand(bx, bz) || NearPoint(bx, bz, 1.6)) continue;
                B.Put(k == 0 ? "scan_mossrock" : "scan_boulder", bx, bz, Rng.Range(0.55, 0.8), 0.3);
            }
            for (int k = 0; k < 3; k++) B.Put("scan_stones", r.X + Rng.Range(-3, 3), r.Z + Rng.Range(-3, 3), Rng.Range(1.0, 1.4), 0.05);
        }
        // Low cover down the cut: a mossed boulder or two, a stump.
        foreach (var (x, z) in new[] { (-23.0, 36.0), (-13.0, 33.0), (-22.5, 24.0), (-13.5, 16.5) })
        {
            if (!B.CanStand(x, z) || NearPoint(x, z, 2.5)) continue;
            B.Put(Rng.Chance(0.5) ? "scan_mossrock" : "scan_stump", x, z, Rng.Range(0.8, 1.0), 0.2);
            B.Block(x, z, 0.8);
        }

        // ------------------------------------------------------------- the water --
        // Pale stones along the stream's banks and in its bed; reeds at the pool's edges.
        for (int k = 0; k < stream.Length; k += 2)
        {
            var (x, z, hw) = stream[k];
            if (B.In(x, z) < -6) continue;
            var (nx, nz, _) = stream[Math.Min(k + 1, stream.Length - 1)];
            var (px, pz, _) = stream[Math.Max(k - 1, 0)];
            double dx = nx - px, dz = nz - pz, len = Math.Max(1e-6, Math.Sqrt(dx * dx + dz * dz));
            foreach (int side in new[] { -1, 1 })
            {
                if (!Rng.Chance(0.5)) continue;
                double o = side * hw * Rng.Range(0.8, 1.3);
                double sx = x - dz / len * o + Rng.Range(-0.5, 0.5), sz = z + dx / len * o + Rng.Range(-0.5, 0.5);
                if (NearPoint(sx, sz, 1.5)) continue;
                B.Put(Rng.Chance(0.3) ? "scan_boulder" : "scan_rock", sx, sz, Rng.Range(0.22, 0.42), 0.12);
            }
        }
        foreach (var r in reeds)
            for (int k = 0; k < 9; k++)
            {
                double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(0.6, r.R + 0.8);
                double x = r.X + Math.Cos(a) * rr, z = r.Z + Math.Sin(a) * rr;
                B.Piece("arena/reeds", x, z, Rng.Range(0, Math.PI * 2), Rng.Range(0.8, 1.15));
            }

        // ------------------------------------------------------------ the deadfalls --
        // Each a dead tree come down and dried, its brash heaped with it: the ember lights it
        // where she stands at it (Hollow.cs). Its fire is laid ready, out until she does.
        foreach (var id in new[] { "fire:a", "fire:b", "fire:c", "fire:d", "fire:e", "fire:f" })
        {
            var (x, z) = Pt(id);
            // Laid across the way she comes at it, so she meets its side.
            double rot = Rng.Range(0, Math.PI);
            var (ux, uz) = ArenaGen.Builder.Along(rot);
            B.Piece("arena/deadfall", x, z, rot);
            int light = B.Glow(x, z, "#ff8a3a", 12, fire: true, height: 1.4, size: 1.15);
            B.Lights[light].On = false;
            // A second fire in its brash, burning with the first.
            B.Fires.Add(new World.FireDef { X = x + ux * 2.1, Y = B.HeightAt(x + ux * 2.1, z + uz * 2.1) + 0.1, Z = z + uz * 2.1, Size = 0.95, Light = light, Ring = false });
            B.Fires[^2].Ring = false;
            B.FireLights[id] = light;
        }

        // ---------------------------------------------------------- the den --
        // The giant come down across the north edge: its root plate standing over the hole, its
        // trunk running back into the wood.
        var (rx0, rz0) = Past(1.2);
        double face = ArenaGen.Builder.Facing(rx0, rz0, den.X, den.Z);
        B.Piece("arena/rootplate", rx0, rz0, face, 1);
        // The sick lying in it: a faint light of the slurry's, deep in the hole.
        var (gx0, gz0) = Past(3.2);
        B.Glow(gx0, gz0, "#b8d060", 2.4, height: 0.3, flicker: 0.05);
        // Their bones about the floor: deer and boar, never a man's.
        for (int k = 0; k < 10; k++)
        {
            double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(3, 13);
            double bx = den.X + Math.Cos(a) * rr, bz = den.Z + Math.Sin(a) * rr;
            if (!B.CanStand(bx, bz) || NearPoint(bx, bz, 1.2)) continue;
            B.Piece(Rng.Pick(new[] { "halloween/bone_A", "halloween/bone_B", "halloween/bone_C", "halloween/ribcage" }), bx, bz, Rng.Range(0, Math.PI * 2), Rng.Range(0.5, 0.75));
        }
        // Where the Pack comes out of the banks: root tangles over runs into the wood.
        foreach (var id in new[] { "den_w", "den_e", "den_n" })
        {
            var (x, z) = Pt(id);
            double ox = x - den.X, oz = z - den.Z, l = Math.Max(1e-6, Math.Sqrt(ox * ox + oz * oz));
            double ex = x + ox / l * 4.5, ez = z + oz / l * 4.5;
            B.PutAt("scan_root", ex, ez, Math.Atan2(ox, oz) + Math.PI / 2, 1.6, 0.2);
        }
        // Low cover on the den floor's edge: two mossed rocks and a stump.
        foreach (var (a, rr) in new[] { (2.6, 11.5), (5.4, 12.0), (0.9, 11.0) })
        {
            double x = den.X + Math.Cos(a) * rr, z = den.Z + Math.Sin(a) * rr;
            if (!B.CanStand(x, z) || NearPoint(x, z, 2.5)) continue;
            B.Put(Rng.Chance(0.6) ? "scan_mossrock" : "scan_stump", x, z, Rng.Range(0.75, 0.95), 0.25);
            B.Block(x, z, 0.8);
        }
    }
}
