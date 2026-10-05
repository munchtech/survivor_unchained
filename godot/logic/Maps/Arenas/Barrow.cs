using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Maps.Arenas;

/* The Risen's barrow field. The Seventh Legion buried its dead in rows, the
 * way it did everything, beside the road it built through the valley; the
 * road is still there under the turf, its slabs sunk and broken, and the long
 * barrows lie along it. Tonight the graves are open from below. Where the
 * ember came up the turf is burned to ash. At one end of the road, at the
 * edge, the sealed door in its mound; at the other, what is left of a gate.
 *
 * Read from above: a straight pale line of slabs across the dark turf (the
 * one straight thing in the valley), long grass mounds throwing moon
 * shadows, the dark mouths of opened graves with their spoil, ash. */
public sealed class Barrow : ArenaShape
{
    (double X, double Z, double Hw)[] way = null!;
    double[] wayF = null!;
    double wayAng;
    readonly List<(double X, double Z, double Ang, double L, double W, double H)> mounds = new();
    readonly List<(double X, double Z, double Ang)> graves = new();
    readonly List<(double X, double Z, double R)> ashes = new();
    readonly List<(double X, double Z, double R)> rubble = new();
    double doorAng, gateAng;

    bool Ashen => B.Place.HasMood("ashen");
    bool Drowned => B.Place.HasMood("drowned");

    public override void Plan()
    {
        // The road: straight, near the middle, from edge to edge and on out.
        wayAng = Rng.Range(0, Math.PI);
        double off = Rng.Range(-14, 14);
        double dx = Math.Cos(wayAng), dz = Math.Sin(wayAng), nx = -dz, nz = dx;
        way = B.Curve(nx * off - dx * 140, nz * off - dz * 140, nx * off + dx * 140, nz * off + dz * 140, 0, 2.7, 0.12);
        wayF = B.PathField(way);
        B.Lane(way);
        // Where the road meets the edge: the door at one end, the gate at the other. The howe
        // at the road's end away from the camera (the camera stands to +z, and the road runs
        // along (dx, dz) with dz >= 0, so its -z end is the top of the picture): there it is
        // seen whole, never under the HUD behind her.
        doorAng = EdgeBearing(nx * off, nz * off, -dx, -dz);
        gateAng = EdgeBearing(nx * off, nz * off, dx, dz);
        var (doorX, doorZ) = B.AtEdge(doorAng, 7);
        // The door's own barrow, the biggest, across the road's end.
        mounds.Add((doorX, doorZ, wayAng + Math.PI / 2, 15, 9, 3.4));
        // Long barrows along the road, in the Legion's order.
        for (int t = 0; t < 200 && mounds.Count < 6; t++)
        {
            double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(34, ArenaGen.R - 10);
            double x = Math.Cos(a) * rr, z = Math.Sin(a) * rr;
            double l = Rng.Range(8, 12.5), w = Rng.Range(3, 4.2);
            if (B.At(wayF, x, z) * 2.7 < w + 7) continue;
            if (mounds.Exists(m => MathX.Dist(m.X, m.Z, x, z) < m.L + l + 4)) continue;
            double ang = wayAng + (Rng.Chance(0.75) ? 0 : Math.PI / 2) + Rng.Range(-0.12, 0.12);
            mounds.Add((x, z, ang, l, w, Rng.Range(1.0, 1.5)));
        }
        // Graves opened from below: some on the barrows, most in the turf.
        for (int t = 0; t < 400 && graves.Count < 22; t++)
        {
            double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(10, ArenaGen.R - 6);
            double x = Math.Cos(a) * rr, z = Math.Sin(a) * rr;
            if (B.At(wayF, x, z) < 1.8 || graves.Exists(g => MathX.Dist(g.X, g.Z, x, z) < 5)) continue;
            graves.Add((x, z, wayAng + Rng.Range(-0.15, 0.15)));
        }
        // Where the ember came up and burned the turf.
        int burns = Ashen ? 14 : 6;
        for (int k = 0; k < burns; k++)
        {
            double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(8, ArenaGen.R);
            ashes.Add((Math.Cos(a) * rr, Math.Sin(a) * rr, Rng.Range(4, Ashen ? 12 : 8)));
        }
    }

    /// <summary>The bearing from a point along a direction to where it leaves the clearing.</summary>
    double EdgeBearing(double px, double pz, double dx, double dz)
    {
        double s = 0;
        while (s < 200 && MathX.Len(px + dx * s, pz + dz * s) < B.EdgeR(Math.Atan2(pz + dz * s, px + dx * s))) s += 1;
        return Math.Atan2(pz + dz * s, px + dx * s);
    }

    static double Ellipse(double x, double z, double cx, double cz, double ang, double l, double w)
    {
        double c = Math.Cos(ang), s = Math.Sin(ang), dx = x - cx, dz = z - cz;
        double u = dx * c + dz * s, v = -dx * s + dz * c;
        return Math.Sqrt(u * u / (l * l) + v * v / (w * w));
    }

    public override double Relief(double x, double z)
    {
        double h = 0;
        double f = B.At(wayF, x, z);
        if (f < 1.4) h -= 0.08 * (1 - MathX.Smoothstep(0.8, 1.4, f));
        foreach (var m in mounds)
        {
            if (Math.Abs(x - m.X) > m.L + 2 || Math.Abs(z - m.Z) > m.L + 2) continue;
            double e = Ellipse(x, z, m.X, m.Z, m.Ang, m.L, m.W);
            if (e < 1.1) h += m.H * (1 - MathX.Smoothstep(0.25, 1.05, e)) * (1 + 0.08 * Noise.Noise(x * 0.3, z * 0.3));
        }
        foreach (var g in graves)
        {
            if (Math.Abs(x - g.X) > 3 || Math.Abs(z - g.Z) > 3) continue;
            double e = Ellipse(x, z, g.X, g.Z, g.Ang, 1.2, 0.65);
            if (e < 1) h -= 0.4 * (1 - MathX.Smoothstep(0.4, 1, e));
            // The spoil thrown up beside it.
            double c = Math.Cos(g.Ang), s = Math.Sin(g.Ang);
            double es = Ellipse(x, z, g.X - s * 1.4, g.Z + c * 1.4, g.Ang, 1.4, 0.7);
            if (es < 1) h += 0.32 * (1 - MathX.Smoothstep(0.2, 1, es));
        }
        return h;
    }

    public override void Paint(double x, double z, double inn, ref ArenaPaint p)
    {
        double n1 = Noise.Noise(x * 0.09, z * 0.09), n2 = Noise.Noise(x * 0.23 + 4, z * 0.23);
        // The road's slabs, sunk and broken: whole runs of it gone under the turf.
        double f = B.At(wayF, x, z);
        double gone = MathX.Smoothstep(0.25, 0.6, Noise.Noise(x * 0.07 + 9, z * 0.07 - 2) + n2 * 0.25);
        double slabs = (1 - MathX.Smoothstep(0.8, 1.05, f + n2 * 0.12)) * (1 - gone * 0.85);
        // Stray slabs heaved out to the side.
        slabs = Math.Max(slabs, (1 - MathX.Smoothstep(1.2, 2.2, f)) * MathX.Smoothstep(0.55, 0.7, Noise.Noise(x * 0.31 - 7, z * 0.31)));
        p.L2 = slabs;
        // The road's verges, rubbled.
        p.L5 = (1 - MathX.Smoothstep(1.0, 1.8, f + n1 * 0.3)) * MathX.Smoothstep(0.75, 1.0, f) * 0.8;
        // Bare grey soil along the road and round the graves: the dead walked here.
        p.BaseB = Math.Max(p.BaseB * 0.8, (1 - MathX.Smoothstep(1.2, 3.2, f + n1 * 0.6)) * 0.75);
        foreach (var g in graves)
        {
            if (Math.Abs(x - g.X) > 6 || Math.Abs(z - g.Z) > 6) continue;
            double e = Ellipse(x, z, g.X, g.Z, g.Ang, 1.3, 0.75);
            double c = Math.Cos(g.Ang), s = Math.Sin(g.Ang);
            double es = Ellipse(x, z, g.X - s * 1.4, g.Z + c * 1.4, g.Ang, 1.6, 0.85);
            p.L3 = Math.Max(p.L3, 1 - MathX.Smoothstep(0.8, 1.3, Math.Min(e, es) + n2 * 0.2));
            double d = MathX.Dist(x, z, g.X, g.Z);
            p.BaseB = Math.Max(p.BaseB, (1 - MathX.Smoothstep(2, 5.5, d + n1)) * 0.8);
            p.Wet = Math.Max(p.Wet, (1 - MathX.Smoothstep(0.3, 0.75, e)) * (Drowned ? 0.9 : 0.35));
        }
        foreach (var a in ashes)
        {
            double d = MathX.Dist(x, z, a.X, a.Z);
            if (d > a.R + 4) continue;
            double k = 1 - MathX.Smoothstep(a.R * 0.45, a.R, d + n1 * 2.2 + n2);
            p.L4 = Math.Max(p.L4, k);
            p.Char = Math.Max(p.Char, (1 - MathX.Smoothstep(a.R * 0.1, a.R * 0.45, d + n1 * 1.5)) * (Ashen ? 0.3 : 0.15));
        }
        foreach (var r in rubble)
        {
            double d = MathX.Dist(x, z, r.X, r.Z);
            if (d < r.R + 2) p.L5 = Math.Max(p.L5, (1 - MathX.Smoothstep(r.R * 0.4, r.R, d + n2 * 1.2)) * 0.9);
        }
        // Low ground holds water under the Drowned.
        if (Drowned) p.Wet = Math.Max(p.Wet, MathX.Smoothstep(0.35, 0.7, Noise.Noise(x * 0.05 - 9, z * 0.05)) * MathX.Smoothstep(-1, 3, inn));
        // Just inside the ring, the turf is scorched before it chars.
        p.L4 = Math.Max(p.L4, (1 - MathX.Smoothstep(3, 9, inn + n1 * 2)) * 0.7);
        // Dead grass on the turf, thinning on the bare and gone on stone, earth and ash.
        double hard = Math.Max(Math.Max(p.L2, p.L3), Math.Max(p.L4, p.L5));
        p.Grass = (1 - hard) * (1 - p.BaseB * 0.6) * MathX.Smoothstep(-0.45, 0.1, n1 + n2 * 0.4);
    }

    public override void Wall(double x, double z, double d)
    {
        // Past the edge the field goes on into the dark: thorn, dead trees,
        // more graves, mounds; thin, so the ring's glow shows through it.
        double keep = d < 16 ? 0.22 : d < 34 ? 0.18 : 0.06;
        if (Rng.Chance(keep)) B.Put(Ashen ? "dead" : Rng.Chance(0.75) ? "dead" : "pine", x, z, 1 + Math.Min(0.4, d * 0.012));
        if (d < 14 && Rng.Chance(0.3)) B.Put(Rng.Pick(new[] { "scan_grass", "scan_shrub", "scan_grass", "bramble" }), x + Rng.Range(-1, 1), z + Rng.Range(-1, 1), Rng.Range(0.9, 1.3));
        if (d < 12 && Rng.Chance(0.06)) B.Put(Rng.Pick(new[] { "scan_mossrock", "scan_trunk", "scan_stump" }), x, z, Rng.Range(0.8, 1.2), 0.15);
    }

    public override void Fringe(double x, double z, double inn)
    {
        if (Rng.Chance(0.25)) B.Put(Rng.Pick(new[] { "scan_grass", "scan_grass", "scan_shrub" }), x, z, Rng.Range(0.7, 1.1));
        if (Rng.Chance(0.1)) B.Put(Rng.Pick(new[] { "scan_stones", "scan_rock", "scan_stump" }), x, z, Rng.Range(0.7, 1.1), 0.1);
    }

    public override void Open(double x, double z, double inn)
    {
        double f = B.At(wayF, x, z);
        if (f < 1.1) return;
        double patch = Noise.Noise(x * 0.07 + 31, z * 0.07 - 17);
        // Turf in tussocks, thin: the field is grazed by nothing but the wind.
        if (patch > 0.3 && Rng.Chance(0.3)) B.Put("scan_grass", x, z, Rng.Range(0.7, 1.1));
        if (f < 2.4 && Rng.Chance(0.25)) B.Put("scan_stones", x, z, Rng.Range(0.8, 1.3), 0.05);
        else if (Rng.Chance(0.02)) B.Put("scan_stones", x, z, Rng.Range(0.7, 1.1), 0.05);
    }

    public override void Dress()
    {
        // ------------------------------------------------- the edge's places --
        // The great howe at the road's end, its mouth sealed with a slab (the
        // seven-notch sigil cut on it, dark), the Watch's lamp-posts either side
        // of the road rusted and empty: there has been no oil for them in years.
        var (dx, dz) = B.AtEdge(doorAng, 2.5);
        double face = ArenaGen.Builder.Facing(dx, dz, 0, 0);
        var (ux, uz) = ArenaGen.Builder.Along(face);
        double fx = Math.Sin(face), fz = Math.Cos(face);
        B.Piece("dungeon/wall_cracked", dx, dz, face, 0.62);
        B.Slab(dx, dz, 1.4, 0.5, face);
        foreach (int side in new[] { -1, 1 })
        {
            double px = dx + ux * side * 1.6 + fx * 0.2, pz = dz + uz * side * 1.6 + fz * 0.2;
            B.Piece("dungeon/pillar", px, pz, face, 0.55);
            B.Block(px, pz, 0.6);
            double lx = dx + fx * 5.5 + ux * side * 3.8, lz = dz + fz * 5.5 + uz * side * 3.8;
            B.Piece("halloween/post_lantern", lx, lz, face);
            B.Block(lx, lz, 0.3);
        }
        // The Legion's standard, what is left of it, planted by the howe.
        double sx0 = dx + ux * 5.5 - fx * 1.0, sz0 = dz + uz * 5.5 - fz * 1.0;
        B.Piece("props/Banner_1", sx0, sz0, face + 0.3, 1.2);
        B.Block(sx0, sz0, 0.3);
        // The gate at the road's other end: its two piers still standing, its arch down.
        var (gx, gz) = B.AtEdge(gateAng, 1.5);
        double gface = ArenaGen.Builder.Facing(gx, gz, 0, 0);
        var (gux, guz) = ArenaGen.Builder.Along(gface);
        foreach (int side in new[] { -1, 1 })
        {
            double px = gx + gux * side * 3.6, pz = gz + guz * side * 3.6;
            B.Piece("dungeon/pillar", px, pz, gface + Rng.Range(-0.1, 0.1), Rng.Range(0.95, 1.15));
            B.Block(px, pz, 0.8);
        }
        B.Piece("dungeon/rubble_large", gx + Math.Sin(gface) * -2.5, gz + Math.Cos(gface) * -2.5, gface + 0.3, 0.55);
        rubble.Add((gx, gz, 7));
        B.Take(gx, gz, 9);
        B.Take(dx, dz, 10);

        // ------------------------------------------------- the road's stones --
        // Boundary stones either side of the road, every so often, some fallen away.
        for (int k = 0; k < way.Length; k += 7)
        {
            var (x, z, hw) = way[k];
            if (B.In(x, z) < 6) continue;
            int side = (k / 7) % 2 == 0 ? 1 : -1;
            double c = Math.Cos(wayAng), s = Math.Sin(wayAng);
            double sx = x - s * side * (hw + 1.1), sz = z + c * side * (hw + 1.1);
            if (Rng.Chance(0.3)) continue;
            B.Piece(Rng.Chance(0.5) ? "halloween/gravemarker_A" : "halloween/gravemarker_B", sx, sz, -wayAng + Math.PI / 2 + Rng.Range(-0.2, 0.2), Rng.Range(1.15, 1.4));
            B.Block(sx, sz, 0.35);
        }

        // ----------------------------------------------------------- cover --
        // Islands of low cover: rows of graves, a ruin's column stumps, a fallen
        // stone; nothing taller than a man, so the fight shows round them.
        var islands = new List<(double X, double Z)>();
        for (int t = 0; t < 500 && islands.Count < 17; t++)
        {
            double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(16, ArenaGen.R - 14);
            double x = Math.Cos(a) * rr, z = Math.Sin(a) * rr;
            if (!B.Free(x, z, 4) || islands.Exists(o => MathX.Dist(o.X, o.Z, x, z) < 19)) continue;
            islands.Add((x, z));
            B.Take(x, z, 5);
            int kind = Rng.Int(0, 3);
            if (kind <= 1)
            {
                // A row of the Legion's graves, in its order, some broken open.
                double rot = -wayAng + Rng.Range(-0.1, 0.1);
                var (rx, rz) = ArenaGen.Builder.Along(rot);
                int n = Rng.Int(3, 5);
                string[] stones = ["halloween/grave_A", "halloween/grave_B", "halloween/grave_A_destroyed", "halloween/gravestone", "halloween/grave_A_destroyed"];
                for (int g = 0; g < n; g++)
                {
                    double o = (g - (n - 1) / 2.0) * 2.4;
                    double sx = x + rx * o, sz = z + rz * o;
                    B.Piece(Rng.Pick(stones), sx, sz, rot + Rng.Range(-0.15, 0.15), Rng.Range(0.75, 0.9));
                    B.Block(sx, sz, 0.85);
                }
                B.Piece(Rng.Pick(new[] { "halloween/bone_A", "halloween/bone_C", "halloween/ribcage" }), x + rz * 2.2, z - rx * 2.2, Rng.Range(0, Math.PI * 2));
            }
            else if (kind == 2)
            {
                // A ruin of the Legion's: column stumps among their own rubble.
                double rot = Rng.Range(0, Math.PI * 2);
                var (rx, rz) = ArenaGen.Builder.Along(rot);
                foreach (int side in new[] { -1, 1 })
                {
                    double px = x + rx * side * 2.4, pz = z + rz * side * 2.4;
                    B.Piece("halloween/pillar", px, pz, Rng.Range(0, Math.PI * 2), Rng.Range(0.3, 0.38));
                    B.Block(px, pz, 0.5);
                }
                B.Piece("dungeon/rubble_half", x - 0.8, z + 0.4, rot, 0.4);
                B.Block(x, z, 1.1);
                B.Piece("halloween/skull", x + rz * 1.7, z - rx * 1.7, Rng.Range(0, Math.PI * 2), 0.45);
                rubble.Add((x, z, 6));
            }
            else
            {
                // A great headstone alone, its lesser markers about it.
                double rot = Rng.Range(0, Math.PI * 2);
                B.Piece("halloween/gravestone", x, z, rot, Rng.Range(1.15, 1.3));
                B.Block(x, z, 1.0);
                for (int g = 0; g < 2; g++)
                {
                    double a2 = Rng.Range(0, Math.PI * 2);
                    double mx = x + Math.Cos(a2) * 2.6, mz = z + Math.Sin(a2) * 2.6;
                    B.Piece(Rng.Pick(new[] { "halloween/gravemarker_A", "halloween/gravemarker_B" }), mx, mz, rot + Rng.Range(-0.6, 0.6));
                    B.Block(mx, mz, 0.35);
                }
                B.Piece("halloween/skull", x + 1.6, z - 1.1, Rng.Range(0, Math.PI * 2), 0.5);
            }
        }
        // A broken marker by most of the opened graves, its own dead risen out from under it.
        foreach (var g in graves)
        {
            if (Rng.Chance(0.35) || !B.CanStand(g.X, g.Z)) continue;
            double c = Math.Cos(g.Ang), s = Math.Sin(g.Ang);
            B.Piece(Rng.Pick(new[] { "halloween/gravemarker_A", "halloween/gravemarker_B" }), g.X + c * 1.6, g.Z + s * 1.6, -g.Ang + Math.PI / 2 + Rng.Range(-0.5, 0.5), Rng.Range(0.8, 1.0));
            if (Rng.Chance(0.4)) B.Piece(Rng.Pick(new[] { "halloween/bone_A", "halloween/bone_B", "halloween/bone_C" }), g.X - s * 1.8, g.Z + c * 1.8, Rng.Range(0, Math.PI * 2));
        }
    }
}
