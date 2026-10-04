using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Maps.Arenas;

/* The Pack's Hollow. A bowl of old wood, the leaf litter of years black
 * underfoot, roots of the great trees round its rim breaking the ground; the
 * stream along one side, slow, with the Dig's slurry in it (the wolves are
 * sick, not bold); the den under a fallen giant across the far edge, its runs
 * worn into the mud, the bones of what they brought home.
 *
 * Read from above: dark litter, the pale stony line of the stream and its
 * wet black banks, roots like veins from the rim inward, mossed rock and
 * fallen trunks for cover, the moon coming through in pools. */
public sealed class Hollow : ArenaShape
{
    (double X, double Z, double Hw)[] stream = null!;
    double[] streamF = null!, rootsF = null!, runsF = null!;
    double denAng;
    double denX, denZ;
    readonly List<(double Ang, double X, double Z)> greats = new();

    bool Drowned => B.Place.HasMood("drowned");
    bool Autumn => B.Spec.Theme == "autumn";

    public override void Plan()
    {
        // The stream: across one side of the bowl, curving.
        double beta = Rng.Range(0, Math.PI * 2), dist = Rng.Range(34, 50);
        double cx = Math.Cos(beta) * dist, cz = Math.Sin(beta) * dist, dx = -Math.Sin(beta), dz = Math.Cos(beta);
        stream = B.Curve(cx - dx * 140, cz - dz * 140, cx + dx * 140, cz + dz * 140, Rng.Range(-30, 30), Drowned ? 3.4 : 2.4, 0.35);
        streamF = B.PathField(stream);
        B.Lane(stream);
        B.Streams.Add(stream);
        // The den, across the bowl from the water.
        denAng = beta + Math.PI + Rng.Range(-0.6, 0.6);
        (denX, denZ) = B.AtEdge(denAng, 2);
        B.Take(denX, denZ, 14);
        // The great trees round the rim, their roots reaching in.
        var roots = new List<(double, double, double, double, double)>();
        var runs = new List<(double, double, double, double, double)>();
        for (int k = 0; k < 7; k++)
        {
            double a = k * Math.PI * 2 / 7 + Rng.Range(-0.25, 0.25);
            if (Math.Abs(MathX.Wrap(a - denAng)) < 0.35) continue;
            var (tx, tz) = B.AtEdge(a, 3.5);
            greats.Add((a, tx, tz));
            for (int r = Rng.Int(4, 7); r > 0; r--)
            {
                // A root: in from the trunk, wandering, thinning.
                double ra = a + Math.PI + Rng.Range(-0.9, 0.9), len = Rng.Range(7, 17), x = tx, z = tz, hw = Rng.Range(0.7, 1.0);
                for (double s = 0; s < len; s += 2.5)
                {
                    double nx = x + Math.Cos(ra) * 2.5, nz = z + Math.Sin(ra) * 2.5;
                    roots.Add((x, z, nx, nz, hw * (1 - s / len * 0.6)));
                    ra += Rng.Range(-0.35, 0.35);
                    (x, z) = (nx, nz);
                }
            }
        }
        rootsF = B.SegsField(roots);
        // The Pack's runs: worn paths from the den out across the bowl, and down to the water.
        for (int k = 0; k < 4; k++)
        {
            double a = denAng + Math.PI + Rng.Range(-0.9, 0.9), x = denX, z = denZ, len = Rng.Range(40, 80);
            for (double s = 0; s < len; s += 4)
            {
                double nx = x + Math.Cos(a) * 4, nz = z + Math.Sin(a) * 4;
                runs.Add((x, z, nx, nz, 1.3));
                a += Rng.Range(-0.3, 0.3);
                (x, z) = (nx, nz);
            }
        }
        runsF = B.SegsField(runs);
    }

    public override double Relief(double x, double z)
    {
        double r = Math.Sqrt(x * x + z * z);
        // A bowl: the middle lies lower than its rim.
        double h = -1.4 * (1 - MathX.Smoothstep(0, ArenaGen.R + 8, r));
        double f = B.At(streamF, x, z);
        if (f < 2.5) h += -0.75 * (1 - MathX.Smoothstep(0.2, 1.25, f)) + 0.12 * (1 - Math.Abs(f - 1.6) / 0.9) * (f > 0.7 ? 1 : 0);
        double rf = B.At(rootsF, x, z);
        if (rf < 1) h += 0.14 * (1 - rf);
        return h;
    }

    public override void Paint(double x, double z, double inn, ref ArenaPaint p)
    {
        double n1 = Noise.Noise(x * 0.09, z * 0.09), n2 = Noise.Noise(x * 0.23 + 4, z * 0.23);
        double f = B.At(streamF, x, z) + n2 * 0.18;
        // The bed, the banks of black mud, wet.
        p.L4 = 1 - MathX.Smoothstep(0.75, 1.05, f);
        double bank = (1 - MathX.Smoothstep(1.2, 2.6, f + n1 * 0.4)) * MathX.Smoothstep(0.6, 1.0, f);
        p.L3 = bank;
        p.Wet = Math.Max(1 - MathX.Smoothstep(0.9, 1.25, f), bank * 0.55);
        // Moss loves the water's side.
        p.BaseB = Math.Max(p.BaseB * 0.7, (1 - MathX.Smoothstep(2, 5, f)) * 0.8);
        // Roots.
        double rf = B.At(rootsF, x, z) + n2 * 0.25;
        p.L2 = (1 - MathX.Smoothstep(0.6, 1.0, rf)) * (1 - p.L4);
        // The runs, worn to mud; the den's yard.
        double run = 1 - MathX.Smoothstep(0.5, 1.1, B.At(runsF, x, z) + n1 * 0.3);
        double yard = 1 - MathX.Smoothstep(6, 13, MathX.Dist(x, z, denX, denZ) + n1 * 3);
        p.Trod = Math.Max(run * 0.7, yard);
        p.L3 = Math.Max(p.L3, Math.Max(run * 0.55, yard * 0.85));
        // Drier litter, needles and twigs, in drifts across the bowl, thickest toward the rim.
        p.L5 = MathX.Smoothstep(0.05, 0.45, Noise.Noise(x * 0.035 + 21, z * 0.035 + 3) + n2 * 0.2 + MathX.Smoothstep(30, 8, inn) * 0.3) * (1 - p.L3);
        if (Drowned) p.Wet = Math.Max(p.Wet, MathX.Smoothstep(0.35, 0.7, Noise.Noise(x * 0.05 - 9, z * 0.05)) * 0.8);
        // Grass only where the canopy opens, in clearings of the litter.
        double hard = Math.Max(Math.Max(p.L2, p.L3), Math.Max(p.L4, p.L5));
        p.Grass = (1 - hard) * MathX.Smoothstep(0.2, 0.55, Noise.Noise(x * 0.03 - 40, z * 0.03 + 12) + n2 * 0.2);
    }

    public override void Wall(double x, double z, double d)
    {
        // The wood: thick near the bowl's rim, thinning into the dark.
        double keep = d < 16 ? 0.62 : d < 34 ? 0.36 : 0.12;
        string[] trees = Autumn ? ["autumn", "autumn", "broadleaf", "pine"] : ["pine", "pine", "broadleaf", "pine", "broadleaf", "dead"];
        if (Rng.Chance(keep)) B.Put(Rng.Pick(trees), x, z, 1 + Math.Min(0.5, d * 0.014));
        if (d < 12 && Rng.Chance(0.45)) B.Put(Rng.Pick(new[] { "scan_fern", "scan_shrub", "fern", "bramble" }), x + Rng.Range(-1, 1), z + Rng.Range(-1, 1), Rng.Range(0.9, 1.3));
        if (d < 14 && Rng.Chance(0.12)) B.Put(Rng.Pick(new[] { "scan_root", "scan_stump", "scan_trunk", "scan_mossrock", "scan_branches" }), x, z, Rng.Range(0.8, 1.3), 0.15);
    }

    public override void Fringe(double x, double z, double inn)
    {
        if (Rng.Chance(0.45)) B.Put(Rng.Pick(new[] { "scan_fern", "scan_fern", "scan_shrub", "fern" }), x, z, Rng.Range(0.8, 1.2));
        if (Rng.Chance(0.12)) B.Put(Rng.Pick(new[] { "scan_root", "scan_stump", "scan_branches", "scan_mossrock" }), x, z, Rng.Range(0.8, 1.2), 0.1);
    }

    public override void Open(double x, double z, double inn)
    {
        double f = B.At(streamF, x, z);
        if (f < 1.0) return;
        double patch = Noise.Noise(x * 0.07 + 31, z * 0.07 - 17);
        // Litter: bark, twigs, moss in the hollows; ferns where the light comes down.
        if (patch < -0.15 && Rng.Chance(0.35)) B.Put(Rng.Chance(0.6) ? "scan_bark" : "scan_moss", x, z, Rng.Range(0.8, 1.2), 0.02);
        if (patch > 0.35 && Rng.Chance(0.18)) B.Put("scan_fern", x, z, Rng.Range(0.7, 1.0));
        if (f < 2.2 && Rng.Chance(0.3)) B.Put(Rng.Pick(new[] { "scan_stones", "scan_grass", "scan_fern" }), x, z, Rng.Range(0.7, 1.1), 0.05);
        if (B.At(rootsF, x, z) < 0.8 && Rng.Chance(0.35)) B.Put(Rng.Pick(new[] { "scan_root", "scan_root", "scan_branches" }), x, z, Rng.Range(0.8, 1.2), 0.08);
        if (Rng.Chance(0.02)) B.Put(Rng.Pick(new[] { "mushroom", "scan_branches", "scan_bark" }), x, z);
    }

    public override void Dress()
    {
        // ------------------------------------------------- the edge's places --
        // The great trees round the rim.
        foreach (var (a, tx, tz) in greats)
        {
            B.Put(Rng.Chance(0.5) ? "broadleaf" : "dead", tx, tz, Rng.Range(1.9, 2.4));
            B.Put("scan_root", tx + Math.Cos(a + Math.PI) * 2, tz + Math.Sin(a + Math.PI) * 2, 1.6, 0.2);
        }
        // The den: a giant fallen across the far edge, its root plate the roof
        // of the hole they sleep in; their bones about the yard.
        double face = ArenaGen.Builder.Facing(denX, denZ, 0, 0);
        var (ux, uz) = ArenaGen.Builder.Along(face);
        for (int k = -1; k <= 1; k++)
        {
            double lx = denX + ux * k * 7.5 + Math.Sin(face) * 3, lz = denZ + uz * k * 7.5 + Math.Cos(face) * 3;
            B.PutAt("scan_trunk", lx, lz, face + Rng.Range(-0.08, 0.08), 2.4, 0.4);
        }
        B.PutAt("scan_root", denX + ux * 11, denZ + uz * 11, face + Math.PI / 2, 2.6, 0.3);
        B.Slab(denX + Math.Sin(face) * 3, denZ + Math.Cos(face) * 3, 11, 1.6, face);
        for (int k = 0; k < 9; k++)
        {
            double a = face + Rng.Range(-1.2, 1.2), rr = Rng.Range(3, 10);
            double bx = denX + Math.Sin(a) * rr, bz = denZ + Math.Cos(a) * rr;
            if (!B.CanStand(bx, bz)) continue;
            // Deer and boar: never a man's (the Pack once brought a child home alive).
            B.Piece(Rng.Pick(new[] { "halloween/bone_A", "halloween/bone_B", "halloween/bone_C" }), bx, bz, Rng.Range(0, Math.PI * 2), Rng.Range(0.5, 0.8));
        }

        // ----------------------------------------------------------- cover --
        // Fallen trunks, mossed boulders, stumps where something was brought down;
        // low, so the Pack shows round them. Bare trees only in the outer ring.
        var islands = new List<(double X, double Z)>();
        for (int t = 0; t < 500 && islands.Count < 17; t++)
        {
            double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(16, ArenaGen.R - 14);
            double x = Math.Cos(a) * rr, z = Math.Sin(a) * rr;
            if (!B.Free(x, z, 4) || islands.Exists(o => MathX.Dist(o.X, o.Z, x, z) < 19)) continue;
            islands.Add((x, z));
            B.Take(x, z, 5);
            int kind = Rng.Int(0, 3);
            if (kind == 3 && rr < 48) kind = 1;
            if (kind == 0)
            {
                // A trunk come down, ferns grown up along it.
                double rot = Rng.Range(0, Math.PI * 2);
                var (rx, rz) = ArenaGen.Builder.Along(rot);
                double sc = Rng.Range(1.2, 1.6);
                B.PutAt("scan_trunk", x, z, rot, sc, 0.25);
                for (int k = -1; k <= 1; k++) B.Block(x + rx * k * 1.5 * sc, z + rz * k * 1.5 * sc, 0.75);
                for (int k = 0; k < 4; k++) B.Put("scan_fern", x + rz * Rng.Range(-1.8, 1.8) + rx * Rng.Range(-3, 3), z - rx * Rng.Range(-1.8, 1.8) + rz * Rng.Range(-3, 3), Rng.Range(0.8, 1.1));
            }
            else if (kind == 1)
            {
                // Mossed rock, two or three, a fern in each lee.
                for (int n = Rng.Int(2, 3); n > 0; n--)
                {
                    double bx = x + Rng.Range(-2.2, 2.2), bz = z + Rng.Range(-2.2, 2.2), sc = Rng.Range(0.8, 1.1);
                    B.Put(n == 1 ? "scan_boulder" : "scan_mossrock", bx, bz, sc, 0.25);
                    B.Block(bx, bz, 1.1 * sc);
                }
                for (int k = 0; k < 3; k++) B.Put(Rng.Pick(new[] { "scan_fern", "fern", "scan_shrub" }), x + Rng.Range(-3.5, 3.5), z + Rng.Range(-3.5, 3.5));
            }
            else if (kind == 2)
            {
                // A kill: stumps, a tangle of roots, bones picked clean.
                for (int n = Rng.Int(2, 3); n > 0; n--)
                {
                    double sx = x + Rng.Range(-2.5, 2.5), sz = z + Rng.Range(-2.5, 2.5);
                    B.Put("scan_stump", sx, sz, Rng.Range(0.9, 1.2), 0.1);
                    B.Block(sx, sz, 0.7);
                }
                B.Put("scan_root", x, z, 1.2, 0.1);
                for (int k = 0; k < 3; k++)
                    B.Piece(Rng.Pick(new[] { "halloween/bone_A", "halloween/bone_B", "halloween/bone_C" }), x + Rng.Range(-3, 3), z + Rng.Range(-3, 3), Rng.Range(0, Math.PI * 2), Rng.Range(0.5, 0.7));
            }
            else
            {
                // A stand of bare trees (they read from above; crowns do not).
                for (int n = Rng.Int(2, 3); n > 0; n--)
                {
                    double tx = x + Rng.Range(-2.5, 2.5), tz = z + Rng.Range(-2.5, 2.5);
                    B.Put("dead", tx, tz, 0.85);
                    B.Block(tx, tz, 0.7);
                }
                for (int k = 0; k < 4; k++) B.Put(Rng.Pick(new[] { "fern", "bramble", "scan_fern" }), x + Rng.Range(-4, 4), z + Rng.Range(-4, 4));
            }
        }
    }
}
