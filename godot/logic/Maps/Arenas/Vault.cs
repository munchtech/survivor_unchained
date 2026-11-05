using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play.Story;

namespace SurvivorUnchained.Maps.Arenas;

/* The Vault's own place (Play/Story/Vault.cs, VaultOpened.Ground: combat's outline, its gates and points,
 * built to as they stand; P5, the P9 set). A roofless hall of the Seventh Legion dug into the barrow field,
 * open to the moon, north up the screen (-z):
 *
 *   the court       the forecourt before the door (z 22..40.5): flat, paved, open; the way in at its south
 *                   mouth between knee-high stubs; its side walls low and fallen; nothing standing near
 *                   Corvane's mark, nothing tall between her arrival and the door
 *   the door        in the court's north wall (the facade, z 22): black stone smooth as glass, the sigil of
 *                   seven arms cut in it, the cut letters over it; it sinks into the ground to open
 *                   (handle "vaultdoor"), the sigil wakes violet (handle "vaultsigil", its light with it)
 *   the hall        z 22..-20, 22 m wide: paved, its walls standing five metres and broken, the earth of
 *                   the barrow banked against them outside; the cover is the fight's (Furnish)
 *   the stair head  the landing (z -20..-38, 30 m wide) and, in its north wall, the stair's mouth: a flight
 *                   of 26 steps cut in black stone down north into the dark (out of bounds; the terrain is
 *                   cut to its treads so the dead stand on them)
 *
 * Derived from (a) the game's need: combat's outline and points (VaultOpened.Ground, Cover), the films'
 * shots (docs/cinematics/shoot/c13.md), the play camera (StoryNight: pitch 64, 22-27 m); (c) inherited: the
 * story-place pattern (HollowNight, arena art), the barrow's ground layers (tools/godot/arena_ground.py), the
 * E7b stone kit (tools/assets/env_props.py, the vault_* presets made for this set). */
public sealed class Vault : ArenaShape
{
    StoryPlace P => B.Outline!;
    double floor = double.NaN;

    /// <summary>The stair's mouth, and its numbers (vault_stair's, binding both ways): a threshold a metre
    /// deep, then 26 treads 0.62 m deep, each 0.28 m down; the bottom floor; its walls from 2.9 m out.</summary>
    public const double MouthZ = -38, Tread = 0.62, Rise = 0.28, Threshold = 1.0, InnerX = 2.9, OuterX = 4.4, WallTop = 2.2;
    public const int Steps = 26;
    /// <summary>A tread's top under the mouth's floor, and the z (world) of its back edge (the riser above it).</summary>
    public static double TreadY(int k) => -Rise * k;
    public static double TreadBack(int k) => MouthZ - Threshold - (k - 1) * Tread;
    /// <summary>The line through the treads' inner corners (under every tread, by up to a riser), m under the
    /// mouth's floor, at a distance down the flight.</summary>
    static double UnderTreads(double sz)
    {
        if (sz > -Threshold) return 0;
        double k = 1 + (-Threshold - sz) / Tread;
        return Math.Max(-Rise * k, -Rise * Steps);
    }

    bool NearPoint(double x, double z, double r) => P.Points.Values.Any(p => MathX.Dist(p.X, p.Z, x, z) < r);

    public override void Plan()
    {
        foreach (var g in P.Gates) B.Gates.Add((g.Id, g.X0, g.Z0, g.X1, g.Z1));
    }

    public override double Bank(double x, double z)
    {
        // The court's south side is the way in: the barrow's bank low there (it stood in the foot of every
        // frame from the court), and a sunken way through it to the south.
        double south = 1 - 0.75 * MathX.Smoothstep(36, 44, z);
        double way = Math.Abs(x) < 6 && z > 38 ? 0.15 + 0.85 * MathX.Smoothstep(3.5, 6, Math.Abs(x)) : 1;
        return Math.Min(south, way);
    }

    public override double Level(double x, double z, double h)
    {
        if (double.IsNaN(floor)) floor = B.Heights[MapGen.Idx(0, 0, ArenaGen.Builder.Half)];
        double sz = z - MouthZ;
        // The stair: the ground cut to the line under its treads, its walls' cores at their tops' height.
        double ax = Math.Abs(x);
        if (sz <= 0.5 && sz > -26 && ax <= InnerX + 0.5) return floor + UnderTreads(sz) - 0.01;
        // (From a metre in: the ground cells at the mouth stay the landing's, so no earth rises before the jambs.)
        if (sz <= -0.9 && sz > -26)
        {
            if (ax <= OuterX + 0.4) return floor + WallTop - 0.2;
            if (ax <= OuterX + 3) return Math.Max(h, floor + WallTop - 0.2);
        }
        // The place's floor is paved and level; just outside it the walls stand on it; then the barrow's
        // earth banked against them, never under the floor.
        double d = P.Dist(x, z);
        if (d < 0.3) return floor;
        if (d < 8) return Math.Max(h, floor + MathX.Smoothstep(0.3, 2.5, d) * 0.6);
        return h;
    }

    public override void Paint(double x, double z, double inn, ref ArenaPaint p)
    {
        double n1 = Noise.Noise(x * 0.09, z * 0.09), n2 = Noise.Noise(x * 0.23 + 4, z * 0.23), n3 = Noise.Noise(x * 0.5 + 11, z * 0.5 - 3);
        p.Open = 1;
        if (inn > -0.4)
        {
            // The Legion's paving (layer 2, the way's slabs), whole down the middle; at the walls' feet the
            // fallen stone and grit (5); broken through in a few places to the earth (the turf's patches).
            double broken = MathX.Smoothstep(0.45, 0.7, Noise.Noise(x * 0.06 + 13, z * 0.06 - 7) + n2 * 0.25);
            p.L2 = 1 - broken * 0.85;
            double foot = MathX.Smoothstep(3.2, 0.8, inn + n1 * 0.8);
            p.L5 = Math.Max(foot * (0.55 + 0.45 * MathX.Smoothstep(-0.2, 0.3, n3)), broken * 0.5);
            p.L2 *= 1 - p.L5 * 0.6;
            p.BaseB = 0.75;
            // The court is the forecourt, older and more open: more of its paving lost to the turf.
            if (z > 22.5) p.L2 *= 0.75 + 0.25 * MathX.Smoothstep(0.1, 0.5, n1);
            // Worn down the middle, where the files came and went.
            p.Trod = (1 - MathX.Smoothstep(2.5, 6, Math.Abs(x) + n1 * 1.5)) * 0.45;
            p.Grass = broken * MathX.Smoothstep(0.2, 0.6, n3) * 0.35;
            p.Moss = foot * MathX.Smoothstep(0.25, 0.6, n2) * 0.25;
        }
        else
        {
            // The barrow's turf, banked against the walls: dead grass over chalk, bare where it slid.
            p.BaseB = MathX.Smoothstep(-0.2, 0.45, Noise.Noise(x * 0.04 + 40, z * 0.04 - 13) + n2 * 0.3);
            p.L5 = MathX.Smoothstep(-0.5, -2.5, inn) * (1 - MathX.Smoothstep(-2.5, -5, inn)) * 0.6;
            p.Grass = MathX.Smoothstep(-1.5, -4, inn) * (0.55 + 0.45 * MathX.Smoothstep(-0.3, 0.3, n1));
        }
        // The ember's char where each gate burns.
        foreach (var g in P.Gates)
        {
            double d = MathX.DistToSegment(x, z, g.X0, g.Z0, g.X1, g.Z1) + n2 * 0.4;
            p.Char = Math.Max(p.Char, (1 - MathX.Smoothstep(0.6, 2.2, d)) * 0.8);
        }
        p.Leaves = 0;
    }

    public override void Wall(double x, double z, double d)
    {
        // The barrow over the hall: its stone come up through the turf here and there, well back from the walls.
        if (d > 5 && d < 16 && Rng.Chance(0.035) && Math.Abs(z - MouthZ + 12) > 14) B.Piece("own/vault_rubble", x, z, Rng.Range(0, Math.PI * 2), Rng.Range(0.8, 1.1));
    }

    public override void Fringe(double x, double z, double inn) { }
    public override void Open(double x, double z, double inn) { }

    /// <summary>A run of wall from a to b (its centre line), its face (+z of each piece) toward (nx, nz).</summary>
    void Run(double ax, double az, double bx, double bz, string[] kinds, double len = 6)
    {
        double l = MathX.Dist(ax, az, bx, bz);
        int n = Math.Max(1, (int)Math.Ceiling(l / len - 0.05));
        double ux = (bx - ax) / l, uz = (bz - az) / l;
        // the inward side: to the left of a -> b
        double nx = uz, nz = -ux;
        if (P.Dist(ax + ux * l / 2 + nx * 2, az + uz * l / 2 + nz * 2) > P.Dist(ax + ux * l / 2 - nx * 2, az + uz * l / 2 - nz * 2)) { nx = -nx; nz = -nz; }
        double rot = Math.Atan2(nx, nz);
        for (int k = 0; k < n; k++)
        {
            double t = (k + 0.5) / n * l;
            B.Piece("own/" + kinds[(k + (int)(Math.Abs(ax + az) * 3)) % kinds.Length], ax + ux * t, az + uz * t, rot);
        }
    }

    public override void Dress()
    {
        string[] tall = { "vault_wall_a", "vault_wall_b", "vault_wall_c", "vault_wall_a", "vault_wall_c" };
        // ---------------------------------------------------------------- the court --
        // Its north wall is the facade with the door in it; solid but for the door (the gate's line holds
        // the doorway until it opens).
        B.Piece("own/vault_facade", 0, 22, 0);
        B.Slab(-8.2, 22, 6.45, 0.65, 0);
        B.Slab(8.2, 22, 6.45, 0.65, 0);
        B.Piece("own/vault_door", 0, 22, 0);
        // The sigil's light, out until it wakes (the handle "vaultsigil" sets its level).
        int sigil = B.Glow(0, 23.0, "#9a6cff", 7, height: 1.75, flicker: 0, range: 10);
        B.Lights[sigil].Dial = "vaultsigil";
        // Its sides: the forecourt's enclosure, low and fallen, outside its floor.
        Run(-14.8, 22.8, -14.8, 41.2, new[] { "vault_wall_low" });
        Run(14.8, 22.8, 14.8, 41.2, new[] { "vault_wall_low" });
        // The south edge: knee-high stubs either side of the way in, a heap or two.
        Run(-14.8, 41.4, -4.6, 41.4, new[] { "vault_stub" }, 3);
        Run(4.6, 41.4, 14.8, 41.4, new[] { "vault_stub" }, 3);
        B.Piece("own/vault_rubble", -10.5, 39.6, 0.4);
        B.Piece("own/vault_rubble", 11.8, 25.5, 2.1, 0.9);

        // ----------------------------------------------------------------- the hall --
        Run(-11.6, 21.4, -11.6, -19.4, tall);
        Run(11.6, 21.4, 11.6, -19.4, tall);

        // --------------------------------------------------------- the stair head --
        // The landing steps out to 30 m: its returns, its sides, its north wall either side of the mouth.
        Run(-11.0, -19.0, -16.2, -19.0, new[] { "vault_wall_c" });
        Run(11.0, -19.0, 16.2, -19.0, new[] { "vault_wall_c" });
        Run(-15.6, -19.4, -15.6, -38.6, tall);
        Run(15.6, -19.4, 15.6, -38.6, tall);
        Run(-16.0, -38.6, -4.6, -38.6, new[] { "vault_wall_b", "vault_wall_a" });
        Run(16.0, -38.6, 4.6, -38.6, new[] { "vault_wall_c", "vault_wall_b" });
        // The stair, and its mouth's jambs standing into the landing.
        B.Piece("own/vault_stair", 0, MouthZ, 0);
        B.Slab(-3.75, MouthZ + 0.1, 0.85, 0.7, 0);
        B.Slab(3.75, MouthZ + 0.1, 0.85, 0.7, 0);
    }
}
