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
    public const double MouthZ = -38, Tread = 0.62, Rise = 0.28, Threshold = 1.0, InnerX = 2.9, OuterX = 4.4, WallTop = 2.6;
    public const int Steps = 26;
    /// <summary>(C13 set) The transverse arches across the flight (vault_stair's "arches", m down from the mouth; each 1.4 m
    /// through, springing ArchClear over its tread, segmental, to the walls' top). The first steps open to the moon to the
    /// first; past it the treads lie in the arches' moon shadow, each next arch's ring and face lit over the one before
    /// (16.4 the last, so Jessop's tread, the 23rd, lies in the gap before it, seen from the head); the walls stand to
    /// WallTop from the mouth on (round 3's kerb, the open stretch, read from every camera as a strip in a field).</summary>
    public static readonly double[] Arches = { 5.0, 9.0, 16.4 };
    public const double ArchClear = 2.6;
    /// <summary>(Round 3) The barrow outside the walls: a shelf ShelfH m over the floor out to ShelfTo m, then rising BankRise a metre.</summary>
    public const double ShelfH = 0.9, ShelfTo = 6.5, BankRise = 0.4;
    /// <summary>The side walls' top (m over the mouth's floor) at a distance down the flight (sz under 0).</summary>
    public static double CutTop(double sz) => WallTop;
    /// <summary>A tread's top under the mouth's floor, and the z (world) of its back edge (the riser above it).</summary>
    public static double TreadY(int k) => -Rise * k;
    public static double TreadBack(int k) => MouthZ - Threshold - (k - 1) * Tread;
    /// <summary>The ground under the treads, m under the mouth's floor, at a distance down the flight: (C13 set) the line
    /// through each tread's top a fifth of a tread in from its riser, so what stands a hand in from a riser (the stair's
    /// points) stands on the tread, not 6 cm into it (round 3: the line through the inner corners); the sliver it leaves
    /// over each inner corner is hidden behind the nose above from the head, and painted as grit (Paint).</summary>
    static double UnderTreads(double sz)
    {
        if (sz > -Threshold) return 0;
        double k = 1 + (-Threshold - sz) / Tread;
        return Math.Max(-Rise * (k - 0.2), -Rise * Steps);
    }

    /// <summary>(C13 set) The grazing light's intensity (three.js units; under 8, so the one-shadow arbiter never offers or
    /// takes its shadow) and its falloff (ZoneView's 1.7 burnt out the first steps and left the 23rd unlit).</summary>
    const double GrazeI = 5.0, GrazeAtt = 0.7;

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
        // (C13 set: to inside the end wall, 22.5 m, no longer 26: the pit it left over the recess showed from above)
        if (sz <= 0.5 && sz > -22.5 && ax <= InnerX + 0.5) return floor + UnderTreads(sz) - 0.01;
        // (From a metre in: the ground cells at the mouth stay the landing's, so no earth rises before the jambs.)
        if (sz <= -0.9 && sz > -26)
        {
            double top = floor + CutTop(sz) - 0.2;
            if (ax <= OuterX + 0.4) return top;
            // (Round 3) The barrow falls to the cut's walls' tops (C13: whole, WallTop, from the mouth on) no steeper than BankRise, under
            // the moon's 42 degrees, so it throws no shadow into the cut and catches the light itself.
            return Math.Max(top, Math.Min(h, top + BankRise * (ax - OuterX - 0.4)));
        }
        // The place's floor is paved and level; just outside it the walls stand on it; then the barrow's
        // earth banked against them, never under the floor.
        double d = P.Dist(x, z);
        if (d < 0.3) return floor;
        // (Round 3, measured: the barrow rose from the walls' feet at 37 degrees to 6 m by |x| 20, so the west bank faced away
        // from the south-west moon and the east lay in its wall's shadow: a quarter of every hall frame flat black.) Now the
        // earth banked against the walls is a shelf ShelfH over the floor, then the barrow rising no steeper than BankRise
        // (about 22 degrees), so the moon lies on the shelf and the slope and the walls' outer faces stand in it.
        double shelf = floor + MathX.Smoothstep(0.3, 2.5, d) * ShelfH;
        return Math.Max(shelf, Math.Min(h, floor + ShelfH + BankRise * Math.Max(0, d - ShelfTo)));
    }

    public override void Paint(double x, double z, double inn, ref ArenaPaint p)
    {
        double n1 = Noise.Noise(x * 0.09, z * 0.09), n2 = Noise.Noise(x * 0.23 + 4, z * 0.23), n3 = Noise.Noise(x * 0.5 + 11, z * 0.5 - 3);
        p.Open = 1;
        // (C13 set) In the stair's cut (the ground there is only the sliver over each tread's inner corner): grit, no turf.
        if (z - MouthZ < 0 && z - MouthZ > -22.5 && Math.Abs(x) < InnerX + 0.6)
        {
            p.L5 = 1; p.L2 = 0; p.BaseB = 0; p.Grass = 0; p.Moss = 0; p.Trod = 0; p.Char = 0.35; p.Leaves = 0;
            return;
        }
        if (inn > -0.4)
        {
            // The Legion's paving (layer 2, the way's slabs), whole down the middle; at the walls' feet the
            // fallen stone and grit (5); broken through in a few places to the earth (the turf's patches).
            double broken = MathX.Smoothstep(0.45, 0.7, Noise.Noise(x * 0.06 + 13, z * 0.06 - 7) + n2 * 0.25);
            p.L2 = 1 - broken * 0.85;
            double foot = MathX.Smoothstep(3.2, 0.8, inn + n1 * 0.8);
            p.L5 = Math.Max(foot * (0.55 + 0.45 * MathX.Smoothstep(-0.2, 0.3, n3)), broken * 0.5);
            p.L2 *= 1 - p.L5 * 0.6;
            // (Round 3: the bare ground is the barrow's chalk now, pale; inside, where the flags are lost, mostly the turf.)
            p.BaseB = 0.3;
            // The court is the forecourt, older and more open: more of its paving lost to the turf.
            if (z > 22.5) p.L2 *= 0.75 + 0.25 * MathX.Smoothstep(0.1, 0.5, n1);
            // Worn down the middle, where the files came and went.
            p.Trod = (1 - MathX.Smoothstep(2.5, 6, Math.Abs(x) + n1 * 1.5)) * 0.45;
            p.Grass = broken * MathX.Smoothstep(0.2, 0.6, n3) * 0.35;
            p.Moss = foot * MathX.Smoothstep(0.25, 0.6, n2) * 0.25;
        }
        else
        {
            // The barrow's turf, banked against the walls: dead grass over chalk, bare where it slid; (round 2) the chalk
            // and fallen stone come through it in drifts, so the banks at the frame's sides read as ground, not flat black.
            p.BaseB = MathX.Smoothstep(-0.2, 0.45, Noise.Noise(x * 0.04 + 40, z * 0.04 - 13) + n2 * 0.3);
            p.L5 = Math.Max(MathX.Smoothstep(-0.5, -2.5, inn) * (1 - MathX.Smoothstep(-2.5, -5, inn)) * 0.6,
                0.55 * MathX.Smoothstep(-0.15, 0.35, n1 + 0.4 * n3));
            p.Grass = MathX.Smoothstep(-1.5, -4, inn) * (0.55 + 0.45 * MathX.Smoothstep(-0.3, 0.3, n1));
        }
        // The ember's char where each gate burns.
        foreach (var g in P.Gates)
        {
            double d = MathX.DistToSegment(x, z, g.X0, g.Z0, g.X1, g.Z1) + n2 * 0.4;
            // (Round 2: at 0.8 the char was a 4 m band of flat black across the hall and the court in every play frame.)
            p.Char = Math.Max(p.Char, (1 - MathX.Smoothstep(0.6, 1.8, d)) * 0.4);
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
        // The sigil's light on the stone round it, out until it wakes (the handle "vaultsigil" sets its level) and gone
        // down with the door ("vaultdoor"); a little under the sigil and a hand out, its specular low, so the glass-black
        // face shows violet light, not the bulb's disc (round 1: 7 at 0.75 m, always on, a disc as wide as the arms).
        // (C13 set r2) The notch's own light: at the sigil's heart a quarter metre out, about 2 m of reach, casting, up as the
        // sigil wakes and gone down with the door: the face round the cut takes violet (and the bloom over it something to
        // lie on), the jambs' insides and the sill too (round 1's, under the sigil, sat on the gloss as a hot spot below the
        // notch: the "glossy marble").
        int sigil = B.Glow(0, 22.5, "#9355ff", 3.0, height: 1.6, flicker: 0, range: 2.2);
        B.Lights[sigil].Dial = "vaultsigil";
        B.Lights[sigil].DialOff = "vaultdoor";
        B.Lights[sigil].Specular = 0.5;
        B.Lights[sigil].Shadow = true;
        // (C13 set r2) The court as the door's polished stone reflects it (ZoneMeta.Probes, on the gloss alone): the box the
        // court's floor, walls and sky, captured from the doorway's recess at her chest.
        double fy = B.HeightAt(0, 23.0);
        B.Probes.Add(new SurvivorUnchained.World.ProbeDef { X = 0, Y = fy + 3.975, Z = 31.55, Sx = 29.6, Sy = 8.05, Sz = 19.7, Ox = 0, Oy = fy + 1.6, Oz = 22.6 });
        // (C13 set) A cold light raking the door's face from its east jamb, low and close: the black stone takes a soft sheen
        // falling across it and its edges catch, so the face reads as a slab, not a hole (round 3: glass-black, no light but
        // the bulbs' dots); out with the door as it sinks.
        int rake = B.Glow(2.1, 22.5, "#93a6d8", 2.6, height: 3.4, flicker: 0, range: 4.6);
        B.Lights[rake].DialOff = "vaultdoor";
        B.Lights[rake].Specular = 0.3;   // (r2: at 1 its bulb sat in the clearcoat as a white dot from the side)
        // The cut letters over the door catch the violet only as the wake reaches the arms' ends.
        // (Round 3: from 5.2 m, under the lines at 5.7-6.1, at 2.0 they barely showed, and its bulb sat on the glass door.)
        // (C13 build: at 1.2 m out and 3.2 m of range its falloff left a pink hotspot on the face over the door; now well
        // out from the wall and above the lines, broader and softer, so the letters take an even wash, not a spot.)
        // (C13 set r2: at 5.5 the moon outlit it on the near-black panel tenfold; the letters showed no violet at k1)
        int letters = B.Glow(0, 25.0, "#9a6cff", 22, height: 7.2, flicker: 0, range: 6.5);
        B.Lights[letters].Dial = "vaultsigil";
        B.Lights[letters].DialFrom = 0.8;
        B.Lights[letters].DialOff = "vaultdoor";
        B.Lights[letters].Specular = 0;
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
        // (C13 set) The flight's read: one cold light grazing down it from just inside the threshold, a hand over the noses'
        // line, casting (LightDef.Shadow): each nose a lit line over the dark band of the tread below, down the flight and
        // falling to black at its foot. (Round 3's four fill glows down the flight went: they lifted every shadow, so the
        // moon, straight down the cut's axis, lit the treads as one even surface.)
        int graze = B.Glow(0, MouthZ - 1.6, "#a3b8e6", GrazeI, flicker: 0, range: 18);
        B.Lights[graze].Y = floor + 0.02;
        B.Lights[graze].Shadow = true;
        B.Lights[graze].Attenuation = GrazeAtt;
        B.Lights[graze].ShadowNormal = 0.3;
        B.Slab(-3.75, MouthZ + 0.1, 0.85, 0.7, 0);
        B.Slab(3.75, MouthZ + 0.1, 0.85, 0.7, 0);
    }
}
