using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Maps.Arenas;

/* The Lamplings' dig. An open working cut down through the valley's clay,
 * stained with ember; its terraces climbing round the edge; black spoil tipped
 * in heaps; the slurry the Dig cooks spilled and pooling; rails from the pit
 * across the working, carts left where they stopped; and the lamps, open
 * lamps on poles everywhere, burning gold and very steady. At the edge, the
 * pit: the hole Grimtunnel comes up out of, its timbers over it, its glow.
 *
 * Read from above: warm pools of lamplight on dark clay, the rails' straight
 * line, black heaps, glossy slurry, the stepped walls round it all and the
 * pit's red mouth at one side. */
public sealed class Dig : ArenaShape
{
    double pitAng, pitX, pitZ;
    const double PitR = 7.5;
    (double X, double Z, double Hw)[] rails = null!;
    double[] railsF = null!;
    readonly List<(double X, double Z, double R, double H)> heaps = new();
    readonly List<(double X, double Z, double R)> pools = new();
    readonly List<(double X, double Z, double R)> bakes = new();

    bool Drowned => B.Place.HasMood("drowned");
    bool Ashen => B.Place.HasMood("ashen");

    public override void Plan()
    {
        // The pit, cut into the working's edge.
        pitAng = Rng.Range(0, Math.PI * 2);
        (pitX, pitZ) = B.AtEdge(pitAng, -PitR + 1.5);
        B.Take(pitX, pitZ, PitR + 5);
        // The rails: from the pit's lip across the working, nearly through its middle.
        double across = pitAng + Math.PI + Rng.Range(-0.35, 0.35);
        var (ex, ez) = B.AtEdge(across, 10);
        double lipX = pitX - Math.Cos(pitAng) * (PitR + 1), lipZ = pitZ - Math.Sin(pitAng) * (PitR + 1);
        rails = B.Curve(lipX, lipZ, ex, ez, Rng.Range(-8, 8), 1.1, 0, 1);
        railsF = B.PathField(rails);
        B.Lane(rails);
        B.Rails.Add(rails);
        // Spoil heaps, toward the edge.
        for (int t = 0; t < 200 && heaps.Count < 6; t++)
        {
            double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(46, ArenaGen.R - 6);
            double x = Math.Cos(a) * rr, z = Math.Sin(a) * rr, r = Rng.Range(6, 9.5);
            if (B.At(railsF, x, z) * 1.1 < r + 3 || MathX.Dist(x, z, pitX, pitZ) < PitR + r + 4) continue;
            if (heaps.Exists(h => MathX.Dist(h.X, h.Z, x, z) < h.R + r + 3)) continue;
            heaps.Add((x, z, r, Rng.Range(2.4, 3.6)));
        }
        // Slurry spilled and pooling in the low places; baked clay where it dried.
        for (int k = 0; k < (Drowned ? 9 : 5); k++)
        {
            double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(10, ArenaGen.R - 10);
            pools.Add((Math.Cos(a) * rr, Math.Sin(a) * rr, Rng.Range(2.5, 6)));
        }
        for (int k = 0; k < 7; k++)
        {
            double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(6, ArenaGen.R - 6);
            bakes.Add((Math.Cos(a) * rr, Math.Sin(a) * rr, Rng.Range(6, 12)));
        }
    }

    public override bool Closed(double x, double z) => MathX.Dist(x, z, pitX, pitZ) < PitR;

    public override double Relief(double x, double z)
    {
        double h = 0;
        double dp = MathX.Dist(x, z, pitX, pitZ);
        // The pit: steep-sided, deep; a lip of spoil round it.
        if (dp < PitR + 6) h += -8 * (1 - MathX.Smoothstep(PitR - 2.5, PitR + 0.3, dp)) + 0.6 * (1 - Math.Abs(dp - PitR - 2) / 3) * (dp > PitR ? 1 : 0);
        foreach (var hp in heaps)
        {
            double d = MathX.Dist(x, z, hp.X, hp.Z);
            // A tip: a cone at the rock's angle of rest, its top rounded where the last tub
            // was emptied, its flanks lumpy with what rolled down them.
            if (d >= hp.R) continue;
            double k = 1 - d / hp.R;
            h += hp.H * Math.Pow(k, 1.1) * MathX.Smoothstep(0, 0.2, k) * (1 - 0.25 * MathX.Smoothstep(0.75, 1, k))
                * (1 + 0.12 * Noise.Noise(x * 0.4, z * 0.4) + 0.08 * Noise.Noise(x * 1.3 + 5, z * 1.3));
        }
        foreach (var p in pools)
        {
            double d = MathX.Dist(x, z, p.X, p.Z);
            if (d < p.R + 1) h -= 0.2 * (1 - MathX.Smoothstep(p.R * 0.4, p.R + 1, d));
        }
        // The working's walls: cut in terraces, outside the edge.
        double inn = B.In(x, z);
        if (inn < 0)
        {
            double t = -inn / 6.5;
            double step = Math.Floor(t) + MathX.Smoothstep(0.78, 1.0, t - Math.Floor(t));
            h += Math.Min(step, 4) * 2.1;
        }
        return h;
    }

    public override void Paint(double x, double z, double inn, ref ArenaPaint p)
    {
        double n1 = Noise.Noise(x * 0.09, z * 0.09), n2 = Noise.Noise(x * 0.23 + 4, z * 0.23);
        // Spoil (the ground's second material) tipped in heaps and spread round them.
        p.BaseB = 0;
        foreach (var hp in heaps)
        {
            double d = MathX.Dist(x, z, hp.X, hp.Z);
            if (d < hp.R + 6) p.BaseB = Math.Max(p.BaseB, 1 - MathX.Smoothstep(hp.R * 0.7, hp.R + 4, d + n1 * 2));
        }
        // The rails' bed of broken stone.
        double rf = B.At(railsF, x, z) + n2 * 0.15;
        p.L2 = 1 - MathX.Smoothstep(0.9, 1.6, rf);
        p.Trod = (1 - MathX.Smoothstep(0.8, 2.5, rf)) * 0.5;
        // Broken stone in a few drifts, where the rock was blasted.
        p.L2 = Math.Max(p.L2, MathX.Smoothstep(0.55, 0.8, Noise.Noise(x * 0.035 + 13, z * 0.035 - 1) + n2 * 0.15) * 0.85);
        foreach (var s in pools)
        {
            double d = MathX.Dist(x, z, s.X, s.Z);
            if (d > s.R + 3) continue;
            double k = 1 - MathX.Smoothstep(s.R * 0.5, s.R + 1.2, d + n1 * 1.4 + n2 * 0.6);
            p.L3 = Math.Max(p.L3, k);
            double wet = 1 - MathX.Smoothstep(s.R * 0.3, s.R * 0.9, d + n1 * 1.2);
            p.Wet = Math.Max(p.Wet, wet);
            // The slurry's own light in the pools, faint, deepest in the middle.
            p.Glow = Math.Max(p.Glow, 1 - MathX.Smoothstep(s.R * 0.15, s.R * 0.75, d + n1 * 1.2));
        }
        // The clay stained rust by the ember, in the planned patches and in
        // broad drifts across the working, so the floor is never one colour.
        // A mottle, never a blob: small stains a metre or two across, gathered where the broad
        // drifts and the planned patches are, frayed by the clay's own grain.
        double n3 = Noise.Noise(x * 0.42 - 3, z * 0.42 + 8), n4 = Noise.Noise(x * 0.13 + 9, z * 0.13 - 4);
        double drift = MathX.Smoothstep(0.2, 0.6, Noise.Noise(x * 0.03 - 17, z * 0.03 + 5) + n1 * 0.3);
        foreach (var bk in bakes)
        {
            double d = MathX.Dist(x, z, bk.X, bk.Z);
            if (d < bk.R + 2) drift = Math.Max(drift, 1 - MathX.Smoothstep(bk.R * 0.3, bk.R, d + n1 * 2.5));
        }
        p.L4 = MathX.Smoothstep(0.42, 0.62, n4 * 0.6 + n3 * 0.4 + drift * 0.45 - 0.2) * (0.35 + 0.6 * drift);
        p.L4 *= 1 - p.L3;
        // Burnt round the pit's mouth (and, in an ashen dig, where the blasting was).
        double dp = MathX.Dist(x, z, pitX, pitZ);
        p.L5 = Math.Max(Ashen ? MathX.Smoothstep(0.55, 0.85, Noise.Noise(x * 0.05 - 7, z * 0.05 + 7)) : 0, 1 - MathX.Smoothstep(PitR + 1, PitR + 8, dp + n1 * 2));
        // The pit: its lip charred; its walls bare rock, lit red by what is down
        // there (the pit's light); its floor, eight metres down, glowing whole.
        // A throat with fire at the bottom, never a pool of it.
        p.Char = Math.Max(p.Char, 0.85 * (1 - MathX.Smoothstep(PitR - 0.5, PitR + 3.5, dp + n1 * 1.5)) * MathX.Smoothstep(PitR - 1.5, PitR - 0.5, dp));
        if (dp < PitR - 4) p.Char = Math.Max(p.Char, 0.9 + 0.1 * (1 - MathX.Smoothstep(0, PitR - 4, dp)));
        if (Drowned) p.Wet = Math.Max(p.Wet, MathX.Smoothstep(0.35, 0.7, Noise.Noise(x * 0.05 - 9, z * 0.05)) * 0.7);
        // Dry grass where nobody walks: along the working's edge, round the tips' feet, between
        // the stones; never on the rails' bed, in the slurry or the char.
        double feet = 0;
        foreach (var hp in heaps)
        {
            double d = MathX.Dist(x, z, hp.X, hp.Z);
            feet = Math.Max(feet, (1 - MathX.Smoothstep(1.5, 4, Math.Abs(d - hp.R - 1.2))));
        }
        double wild = Math.Max(MathX.Smoothstep(16, 5, inn), feet * 0.9);
        p.Grass = wild * MathX.Smoothstep(0.35, 0.7, Noise.Noise(x * 0.09 + 31, z * 0.09 - 7) * 0.7 + n2 * 0.3 + 0.15)
            * (1 - p.L2 * 0.9) * (1 - p.L3) * (1 - p.Trod) * (1 - p.L5);
    }

    public override void Wall(double x, double z, double d)
    {
        // The working's walls: cut clay and stone, a few trees clinging at the top.
        if (d > 24 && Rng.Chance(0.2)) B.Put(Rng.Pick(new[] { "dead", "pine" }), x, z, 1 + Math.Min(0.4, d * 0.01));
        if (d < 20 && Rng.Chance(0.07)) B.Put(Rng.Pick(new[] { "scan_boulder", "scan_mossrock", "scan_rock" }), x, z, Rng.Range(0.9, 1.6), 0.3);
        if (d < 16 && Rng.Chance(0.06)) B.Put(Rng.Pick(new[] { "scan_stones", "scan_branches", "scan_stump" }), x, z, Rng.Range(0.9, 1.3), 0.05);
    }

    public override void Fringe(double x, double z, double inn)
    {
        if (Rng.Chance(0.18)) B.Put(Rng.Pick(new[] { "scan_stones", "scan_rock", "scan_stones" }), x, z, Rng.Range(0.8, 1.3), 0.05);
        if (Rng.Chance(0.05)) B.Put(Rng.Pick(new[] { "scan_branches", "scan_grass" }), x, z, Rng.Range(0.8, 1.1));
    }

    public override void Open(double x, double z, double inn)
    {
        // Stone broken off and left where it fell; nothing grows here.
        if (B.At(railsF, x, z) < 1.2) return;
        if (Noise.Noise(x * 0.08 + 13, z * 0.08 - 1) > 0.45 && Rng.Chance(0.35)) B.Put("scan_stones", x, z, Rng.Range(0.9, 1.4), 0.05);
        else if (Rng.Chance(0.02)) B.Put("scan_stones", x, z, Rng.Range(0.8, 1.2), 0.05);
    }

    public override void Dress()
    {
        // --------------------------------------------------------- the pit --
        // Its glow from below, red; the lamps round its lip, gold.
        // Its light down on the floor, lighting the walls red from below.
        B.Glow(pitX, pitZ, "#ff5a1e", 16, height: -5.5, flicker: 0.3);
        B.Vents.Add((pitX, pitZ, PitR - 3));
        double face = ArenaGen.Builder.Facing(pitX, pitZ, 0, 0);
        var (ux, uz) = ArenaGen.Builder.Along(face);
        // The headframe over the throat, its back-stays out past the edge.
        B.Piece("arena/headframe", pitX, pitZ, face);
        double fx0 = Math.Sin(face), fz0 = Math.Cos(face);
        foreach (int side in new[] { -1, 1 })
            foreach (int fore in new[] { -1, 1 })
                B.Block(pitX + ux * side * 5.6 + fx0 * fore * 5.6, pitZ + uz * side * 5.6 + fz0 * fore * 5.6, 0.5);
        // Their own dead, wrapped small, waiting at the mouth to be carried down
        // ("Nobody's! Nobody's lost!").
        for (int k = 0; k < 4; k++)
        {
            double bx = pitX + Math.Sin(face) * (PitR + 2.6) + ux * (k - 1.5) * 0.9, bz = pitZ + Math.Cos(face) * (PitR + 2.6) + uz * (k - 1.5) * 0.9;
            if (B.CanStand(bx, bz)) B.Piece("props/Bag", bx, bz, face + Math.PI / 2 + Rng.Range(-0.2, 0.2), 1.3);
        }
        for (int k = 0; k < 5; k++)
        {
            double a = face + Math.PI + (k - 2) * 0.5;
            double lx = pitX - Math.Sin(a) * (PitR + 2.2), lz = pitZ - Math.Cos(a) * (PitR + 2.2);
            if (!B.CanStand(lx, lz)) continue;
            B.Piece("halloween/lantern_standing", lx, lz, Rng.Range(0, Math.PI * 2), 1.2);
            B.Glow(lx, lz, "#ffcf7a", 6, height: 0.8, flicker: 0.05);
        }

        // A windlass at the lip, the way down for what the cage won't carry; a fence of
        // stakes along the lip either side of the headframe's feet.
        var (wx, wz) = (pitX + Math.Sin(face) * (PitR + 1.4) + ux * 4.2, pitZ + Math.Cos(face) * (PitR + 1.4) + uz * 4.2);
        if (B.CanStand(wx, wz)) { B.Piece("arena/winch", wx, wz, face + Math.PI); B.Block(wx, wz, 1.0); }
        for (int k = -6; k <= 6; k++)
        {
            if (Math.Abs(k) < 2) continue;
            double a = face + k * 0.16;
            double fx1 = pitX + Math.Sin(a) * (PitR + 0.6), fz1 = pitZ + Math.Cos(a) * (PitR + 0.6);
            if (!B.CanStand(fx1, fz1)) continue;
            B.Piece("village/Prop_WoodenFence_Single", fx1, fz1, a + Math.PI / 2, 1.0);
        }

        // ---------------------------------------------------------- the rails --
        // Tubs stopped on them: a train of them near the pit, full, and one
        // here and there across the working where it was left.
        int train = rails.Length / 4 + Rng.Int(0, 6);
        for (int k = 0; k < rails.Length; k++)
        {
            bool inTrain = k >= train && k < train + 8 && (k - train) % 2 == 0;
            if (!inTrain && k % 23 != 17) continue;
            var (x, z, _) = rails[k];
            if (B.In(x, z) < 6 || MathX.Dist(x, z, pitX, pitZ) < PitR + 3) continue;
            var (nx, nz, _) = rails[Math.Min(k + 1, rails.Length - 1)];
            double rot = Math.Atan2(nx - x, nz - z);
            B.Piece("arena/tub", x, z, rot);
            B.Slab(x, z, 0.6, 0.85, rot);
        }

        // ----------------------------------------------------------- cover --
        // Rubble, barrels of blasting ember, timber shoring: low, and lit.
        var islands = new List<(double X, double Z)>();
        for (int t = 0; t < 500 && islands.Count < 16; t++)
        {
            double a = Rng.Range(0, Math.PI * 2), rr = Rng.Range(16, ArenaGen.R - 14);
            double x = Math.Cos(a) * rr, z = Math.Sin(a) * rr;
            if (!B.Free(x, z, 4) || islands.Exists(o => MathX.Dist(o.X, o.Z, x, z) < 19)) continue;
            if (heaps.Exists(h => MathX.Dist(h.X, h.Z, x, z) < h.R)) continue;
            islands.Add((x, z));
            B.Take(x, z, 5);
            int kind = Rng.Int(0, 2);
            if (kind == 0)
            {
                double rot = Rng.Int(0, 3) * Math.PI / 2;
                B.Piece("dungeon/rubble_large", x, z, rot, 0.5);
                B.Slab(x, z, 2.0, 0.8, rot);
            }
            else if (kind == 1)
            {
                // Shoring timbers stacked, a broken prop.
                B.Piece("dungeon/pillar", x, z, Rng.Range(0, Math.PI * 2), 0.38);
                B.Block(x, z, 0.6);
                for (int n = 0; n < 2; n++)
                {
                    double bx = x + Rng.Range(-2.5, 2.5), bz = z + Rng.Range(-2.5, 2.5);
                    B.Put("scan_boulder", bx, bz, Rng.Range(0.7, 0.95), 0.25);
                    B.Block(bx, bz, 0.9);
                }
            }
            else
            {
                // Blasting ember in barrels, kept apart.
                for (int n = 0; n < 3; n++)
                {
                    double bx = x + Rng.Range(-1.8, 1.8), bz = z + Rng.Range(-1.8, 1.8);
                    B.Piece("props/Barrel", bx, bz, Rng.Range(0, Math.PI * 2), 1.1);
                    B.Block(bx, bz, 0.55);
                }
            }
            // Every working place has its lamp.
            double lx = x + Rng.Range(-3.5, 3.5), lz = z + Rng.Range(3, 4);
            if (!B.CanStand(lx, lz)) continue;
            B.Piece("halloween/post_lantern", lx, lz, Rng.Range(0, Math.PI * 2), 0.9);
            B.Block(lx, lz, 0.3);
            B.Glow(lx, lz, "#ffcf7a", 8, height: 2.7, flicker: 0.04);
        }
        // Timber stacked by the rails where it was unloaded, sleepers and props for the workings.
        for (int k = 14; k < rails.Length - 8; k += 19)
        {
            var (x, z, hw) = rails[k];
            var (nx, nz, _) = rails[k + 1];
            double dx = nx - x, dz = nz - z, len = Math.Sqrt(dx * dx + dz * dz);
            int side = (k / 19) % 2 == 0 ? 1 : -1;
            double px = x - dz / len * side * (hw + 2.2), pz = z + dx / len * side * (hw + 2.2);
            if (!B.Free(px, pz, 1.6)) continue;
            B.Piece("arena/timber", px, pz, Math.Atan2(dx, dz) + Rng.Range(-0.2, 0.2));
            B.Slab(px, pz, 1.2, 0.7, Math.Atan2(dx, dz));
            B.Take(px, pz, 2);
        }
        // Lamps along the rails.
        for (int k = 8; k < rails.Length - 4; k += 16)
        {
            var (x, z, hw) = rails[k];
            var (nx, nz, _) = rails[k + 1];
            double dx = nx - x, dz = nz - z, len = Math.Sqrt(dx * dx + dz * dz);
            double px = x - dz / len * (hw + 1.6), pz = z + dx / len * (hw + 1.6);
            if (B.In(px, pz) < 6) continue;
            B.Piece("halloween/post_lantern", px, pz, Math.Atan2(dx, dz), 0.9);
            B.Block(px, pz, 0.3);
            B.Glow(px, pz, "#ffcf7a", 8, height: 2.7, flicker: 0.04);
        }
    }
}
