using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Maps.Arenas;

/* The Kerchiefs' ruts. The caravan road runs down a ravine below the Roost,
 * churned to mud by wheels and hooves, its ruts full of standing water; where
 * the wagons were taken they still lie, their loads broken open and spilled;
 * the Roost's camp sits off the road against the ravine's side, its fires
 * going, its palisade, its cage.
 *
 * Read from above: one broad curving band of mud with its two dark wet
 * ruts (the moon in them), the ravine's rock close on two sides, the warm
 * pools of the camp's fires, wreckage along the road. */
public sealed class Ruts : ArenaShape
{
    (double X, double Z, double Hw)[] road = null!;
    double[] roadF = null!;
    double roadAng, campAng, campX, campZ;
    const double CampR = 12;
    readonly List<(double X, double Z)> wrecks = new();

    bool Drowned => B.Place.HasMood("drowned");
    bool Gallows => B.Place.HasMood("gallows");

    public override void Plan()
    {
        roadAng = Rng.Range(0, Math.PI);
        double off = Rng.Range(-10, 10), dx = Math.Cos(roadAng), dz = Math.Sin(roadAng), nx = -dz, nz = dx;
        road = B.Curve(nx * off - dx * 140, nz * off - dz * 140, nx * off + dx * 140, nz * off + dz * 140, Rng.Range(-22, 22), 4.2, 0.15);
        roadF = B.PathField(road);
        B.Lane(road);
        // The camp: off the road, against the ravine's side.
        campAng = Math.Atan2(nz, nx) + (Rng.Chance(0.5) ? 0 : Math.PI) + Rng.Range(-0.5, 0.5);
        (campX, campZ) = B.AtEdge(campAng, -CampR - 2);
        B.Take(campX, campZ, CampR + 3);
        // Where the wagons were taken: on the road, one each side of the middle.
        foreach (double t in new[] { Rng.Range(0.36, 0.44), Rng.Range(0.56, 0.64) })
        {
            var (x, z, _) = road[(int)(t * (road.Length - 1))];
            if (B.In(x, z) > 14) wrecks.Add((x, z));
        }
    }

    /// <summary>How far a point lies across the road from its middle, in metres.</summary>
    double Across(double x, double z) => B.At(roadF, x, z) * 4.2;

    public override double Relief(double x, double z)
    {
        double h = 0, f = B.At(roadF, x, z);
        // A hollow way: the road sunk by its use, its ruts deeper still.
        if (f < 1.6) h -= 0.22 * (1 - MathX.Smoothstep(0.7, 1.6, f));
        double a = Across(x, z);
        if (a < 3) h -= 0.14 * (1 - MathX.Smoothstep(0.15, 0.5, Math.Abs(a - 1.3)));
        // The ravine: its sides rise steep on the two flanks of the road.
        double inn = B.In(x, z);
        if (inn < 0)
        {
            double side = Math.Abs(Math.Sin(Math.Atan2(z, x) - roadAng));
            h += MathX.Smoothstep(0.35, 0.8, side) * MathX.Smoothstep(0, 9, -inn) * 7;
        }
        return h;
    }

    public override void Paint(double x, double z, double inn, ref ArenaPaint p)
    {
        double n1 = Noise.Noise(x * 0.09, z * 0.09), n2 = Noise.Noise(x * 0.23 + 4, z * 0.23);
        double f = B.At(roadF, x, z) + n2 * 0.12, a = Across(x, z);
        // The road: ruts and hoof-churn, a churned verge either side.
        p.L2 = 1 - MathX.Smoothstep(0.85, 1.1, f);
        p.BaseB = Math.Max(p.BaseB * 0.8, (1 - MathX.Smoothstep(1.0, 2.6, f + n1 * 0.4)) * 0.9);
        double rut = 1 - MathX.Smoothstep(0.12, 0.42, Math.Abs(a - 1.3) + n2 * 0.08);
        // Standing water in the ruts and the low places.
        double pool = MathX.Smoothstep(0.25, 0.6, Noise.Noise(x * 0.11 - 3, z * 0.11 + 8)) * (1 - MathX.Smoothstep(0.8, 1.2, f));
        p.L3 = Math.Max(rut * 0.8, pool);
        p.Wet = Math.Max(rut * (0.55 + 0.45 * MathX.Smoothstep(-0.2, 0.4, n1)), pool * 0.95);
        // The old road's metalling, where the mud has worn off it.
        p.L5 = MathX.Smoothstep(0.35, 0.65, Noise.Noise(x * 0.06 + 2, z * 0.06 - 30)) * (1 - MathX.Smoothstep(0.5, 0.95, f)) * (1 - rut);
        p.Trod = (1 - MathX.Smoothstep(0.9, 1.4, f)) * 0.6;
        // The camp's floor.
        double dc = MathX.Dist(x, z, campX, campZ);
        double camp = 1 - MathX.Smoothstep(CampR * 0.65, CampR + 1, dc + n1 * 2.5);
        p.L4 = camp;
        p.Trod = Math.Max(p.Trod, camp * 0.8);
        // A trodden track from the camp to the road.
        foreach (var (wx, wz) in wrecks)
        {
            double d = MathX.Dist(x, z, wx, wz);
            p.L4 = Math.Max(p.L4, (1 - MathX.Smoothstep(2, 6, d + n1 * 1.5)) * 0.6);
        }
        if (Drowned) p.Wet = Math.Max(p.Wet, MathX.Smoothstep(0.3, 0.65, Noise.Noise(x * 0.05 - 9, z * 0.05)) * 0.9);
        // Grass on the verges, never on the road or in the camp.
        p.Grass = MathX.Smoothstep(1.4, 2.6, f + n1 * 0.4) * (1 - camp) * (1 - p.L4) * MathX.Smoothstep(-0.5, 0.0, n2 + n1 * 0.5);
    }

    public override void Wall(double x, double z, double d)
    {
        double side = Math.Abs(Math.Sin(Math.Atan2(z, x) - roadAng));
        if (side > 0.55)
        {
            // The ravine's sides: rock, and what roots in it.
            if (d < 10 && Rng.Chance(0.16)) B.Put(Rng.Pick(new[] { "scan_mossrock", "scan_boulder", "scan_mossrock" }), x, z, Rng.Range(1.2, 2.2), 0.4);
            if (Rng.Chance(d < 16 ? 0.2 : 0.3)) B.Put(Rng.Pick(new[] { "pine", "dead", "pine" }), x, z, 1 + Math.Min(0.4, d * 0.012));
            if (d < 12 && Rng.Chance(0.25)) B.Put(Rng.Pick(new[] { "scan_shrub", "bramble", "scan_grass" }), x, z, Rng.Range(0.9, 1.3));
            return;
        }
        // Up and down the road: the wood it runs through.
        if (Rng.Chance(d < 16 ? 0.4 : 0.25)) B.Put(Rng.Pick(new[] { "pine", "broadleaf", "dead" }), x, z, 1 + Math.Min(0.4, d * 0.012));
        if (d < 12 && Rng.Chance(0.35)) B.Put(Rng.Pick(new[] { "scan_shrub", "bramble", "scan_grass", "scan_fern" }), x + Rng.Range(-1, 1), z + Rng.Range(-1, 1), Rng.Range(0.9, 1.3));
    }

    public override void Fringe(double x, double z, double inn)
    {
        if (Rng.Chance(0.35)) B.Put(Rng.Pick(new[] { "scan_grass", "scan_shrub", "scan_grass", "bramble" }), x, z, Rng.Range(0.8, 1.2));
        if (Rng.Chance(0.1)) B.Put(Rng.Pick(new[] { "scan_stones", "scan_rock", "scan_stump" }), x, z, Rng.Range(0.8, 1.2), 0.1);
    }

    public override void Open(double x, double z, double inn)
    {
        double f = B.At(roadF, x, z);
        if (f < 1.0) { if (Rng.Chance(0.05)) B.Put("scan_stones", x, z, Rng.Range(0.8, 1.2), 0.05); return; }
        // The verges: grass in clumps, trodden flat nearer the road.
        double patch = Noise.Noise(x * 0.07 + 31, z * 0.07 - 17);
        if (f > 2.2 && patch > 0.05 && Rng.Chance(0.4)) B.Put("scan_grass", x, z, Rng.Range(0.8, 1.2));
        if (Rng.Chance(0.03)) B.Put(Rng.Pick(new[] { "scan_stones", "scan_branches", "scan_bark" }), x, z, 1, 0.03);
    }

    public override void Dress()
    {
        // --------------------------------------------------------- the camp --
        double face = ArenaGen.Builder.Facing(campX, campZ, 0, 0);
        var (ux, uz) = ArenaGen.Builder.Along(face);
        double fx = Math.Sin(face), fz = Math.Cos(face);
        // Its fires.
        for (int k = 0; k < 2; k++)
        {
            double a = face + (k == 0 ? -0.8 : 0.8), r = Rng.Range(3.5, 5.5);
            double cx = campX + Math.Sin(a) * r * 0.6 + ux * (k == 0 ? -3 : 3), cz = campZ + Math.Cos(a) * r * 0.6 + uz * (k == 0 ? -3 : 3);
            B.Glow(cx, cz, "#ff9a48", 13, fire: true, size: 0.8);
            B.Block(cx, cz, 0.9);
        }
        // The palisade behind it, against the ravine: stakes, a gate left open toward the road.
        for (int k = -4; k <= 4; k++)
        {
            if (k == 0) continue;
            double a = face + Math.PI + k * 0.16;
            double px = campX + Math.Sin(a) * (CampR + 1), pz = campZ + Math.Cos(a) * (CampR + 1);
            B.Piece("village/Prop_WoodenFence_Single", px, pz, a + Math.PI / 2, 1.3);
            B.Block(px, pz, 0.5);
        }
        // Forty-one mouths from a town nobody may name twice: one pot big enough
        // for all of them, their stores, the wagon they came in, and the cage
        // with the prisoners' bowls in it (they were fed).
        foreach (var (id, ox, oz, r) in new[] { ("props/Crate_Wooden", -5.5, -4.0, 0.6), ("props/Crate_Wooden", -6.2, -2.8, 0.6), ("props/Barrel", -4.6, -5.3, 0.5),
                     ("props/Barrel_Holder", 5.8, -4.5, 0.9), ("props/Cage_Small", 0.0, -7.5, 0.9), ("props/Mug", 0.6, -7.2, 0.0), ("props/Chest_Wood", 3.8, -6.2, 0.6),
                     ("village/Prop_Wagon", -1.0, -9.0, 1.8), ("props/Cauldron", 1.5, 1.0, 0.8), ("props/Bucket_Wooden_1", 2.6, 1.6, 0.0) })
        {
            // Across the camp (ox) and toward the road (oz; behind it, negative).
            double px = campX + ux * ox + fx * oz, pz = campZ + uz * ox + fz * oz;
            B.Piece(id, px, pz, face + Rng.Range(-0.3, 0.3), id.Contains("Cage") ? 1.6 : id.Contains("Cauldron") ? 1.8 : 1.0);
            if (r > 0) B.Block(px, pz, r);
        }
        // Their colours: red rags on poles, at the camp's edge.
        foreach (int side in new[] { -1, 1 })
        {
            double px = campX + ux * side * (CampR - 1), pz = campZ + uz * side * (CampR - 1);
            B.Piece("props/Banner_2", px, pz, face, 1.1);
            B.Block(px, pz, 0.3);
        }
        if (Gallows)
        {
            var (gx, gz) = B.AtEdge(campAng + Math.PI * 0.5, -2);
            B.Piece("halloween/post", gx, gz, ArenaGen.Builder.Facing(gx, gz, 0, 0), 1.4);
            B.Block(gx, gz, 0.4);
        }

        // ------------------------------------------------------ the wrecks --
        // The taken wagons where they were left, their loads spilled across the road.
        foreach (var (wx, wz) in wrecks)
        {
            double rot = -roadAng + Rng.Range(-0.6, 0.6);
            B.Piece("village/Prop_Wagon", wx, wz, rot, 1.0);
            B.Slab(wx, wz, 1.3, 2.2, rot);
            B.Take(wx, wz, 6);
            for (int n = 0; n < 5; n++)
            {
                double a = Rng.Range(0, Math.PI * 2), r = Rng.Range(2.6, 5);
                double cx = wx + Math.Cos(a) * r, cz = wz + Math.Sin(a) * r;
                string id = Rng.Pick(new[] { "props/Crate_Wooden", "props/Barrel", "props/Bag", "props/Crate_Wooden", "props/Pouch_Large" });
                B.Piece(id, cx, cz, Rng.Range(0, Math.PI * 2), Rng.Range(0.9, 1.1));
                if (!id.Contains("Bag") && !id.Contains("Pouch")) B.Block(cx, cz, 0.5);
            }
        }

        // ----------------------------------------------------------- cover --
        var islands = new List<(double X, double Z)>();
        for (int t = 0; t < 500 && islands.Count < 16; t++)
        {
            double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(16, ArenaGen.R - 14);
            double x = Math.Cos(a) * rr, z = Math.Sin(a) * rr;
            if (!B.Free(x, z, 4) || islands.Exists(o => MathX.Dist(o.X, o.Z, x, z) < 19)) continue;
            islands.Add((x, z));
            B.Take(x, z, 5);
            int kind = Rng.Int(0, 2);
            if (kind == 0)
            {
                // A drover's shelter, its walls broken down to the knee, its stores broken open.
                double rot = Rng.Int(0, 3) * Math.PI / 2 + Rng.Range(-0.2, 0.2);
                var (rx, rz) = ArenaGen.Builder.Along(rot);
                B.Piece("dungeon/wall_broken", x, z, rot, 0.6);
                B.Slab(x, z, 1.2, 0.3, rot);
                double cx = x + rx * 1.3 + rz * 1.3, cz = z + rz * 1.3 - rx * 1.3;
                B.Piece("dungeon/wall_broken", cx, cz, rot + Math.PI / 2, 0.55);
                B.Slab(cx, cz, 1.1, 0.28, rot + Math.PI / 2);
                for (int n = 0; n < 2; n++)
                {
                    double bx = x - rz * Rng.Range(1.2, 2.2) + rx * Rng.Range(-1.5, 1.5), bz = z + rx * Rng.Range(1.2, 2.2) + rz * Rng.Range(-1.5, 1.5);
                    B.Piece(Rng.Pick(new[] { "props/Barrel", "props/Crate_Wooden" }), bx, bz, Rng.Range(0, Math.PI * 2), Rng.Range(0.9, 1.1));
                    B.Block(bx, bz, 0.55);
                }
            }
            else if (kind == 1)
            {
                // A heap of cargo dragged off the road and gone through.
                foreach (var (id, dx, dz, r) in new[] { ("props/Crate_Wooden", -1.6, 0.0, 0.6), ("props/Crate_Wooden", -1.4, 1.1, 0.6), ("props/Barrel", 1.4, -0.5, 0.5), ("props/Bag", 0.2, 1.6, 0.0), ("props/Barrel", 1.3, 1.3, 0.5) })
                {
                    B.Piece(id, x + dx, z + dz, Rng.Range(0, Math.PI * 2));
                    if (r > 0) B.Block(x + dx, z + dz, r);
                }
            }
            else
            {
                // A fence that kept nothing in, and a stone it leans on.
                double rot = Rng.Range(0, Math.PI * 2);
                var (rx, rz) = ArenaGen.Builder.Along(rot);
                foreach (int side in new[] { -1, 1 })
                {
                    B.Piece(side < 0 ? "halloween/fence_broken" : "halloween/fence", x + rx * side * 2, z + rz * side * 2, rot, 0.7);
                    B.Slab(x + rx * side * 2, z + rz * side * 2, 1.4, 0.2, rot);
                }
                B.Put("scan_mossrock", x - rz * 2, z + rx * 2, 0.8, 0.2);
                B.Block(x - rz * 2, z + rx * 2, 1.0);
            }
        }
        // Lanterns on posts along the road, the Roost's watch.
        for (int k = 4; k < road.Length - 4; k += 12)
        {
            var (x, z, hw) = road[k];
            if (B.In(x, z) < 8) continue;
            double c = Math.Cos(roadAng), s = Math.Sin(roadAng);
            int side = (k / 12) % 2 == 0 ? 1 : -1;
            double px = x - s * side * (hw + 1.4), pz = z + c * side * (hw + 1.4);
            if (!B.Free(px, pz, 0.5)) continue;
            B.Piece("halloween/post_lantern", px, pz, -roadAng + (side > 0 ? 0 : Math.PI));
            B.Block(px, pz, 0.3);
            B.Glow(px, pz, "#ffb060", 7, height: 3.0, flicker: 0.18);
        }
    }
}
