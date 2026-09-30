using System;
using System.Collections.Generic;
using Godot;
using static SurvivorUnchained.View.Made;
using static SurvivorUnchained.View.Shapes;

namespace SurvivorUnchained.View;

/// <summary>
/// The Verge's wolves, boars and lamplings as modelled, rigged and animated
/// creatures (art/beasts; credits in public/assets/CREDITS.md), baked into
/// the crowd like the people. Where a model has a clip for what a crowd
/// creature does (a run, a creeping stalk, an idle), it plays it; where it
/// has none (a bite, a charge, a fall, digging), the move is composed over
/// one of its poses, bones turned in the model's own space, as the web
/// game's code-built beasts moved. What a model does not wear (a lampling's
/// hat and lamp) is made in code and carried on its bones.
///
/// One wolf serves every wolf: the alpha is larger and darker, the blighted
/// sick-green, the spirit pale and glowing (Visuals.Tint, Size here).
/// </summary>
public static class Beasts
{
    /// <summary>A modelled creature. Legs: the hip bones of one that walks
    /// upright, which say where its front is (a four-legged one faces from
    /// pelvis to head). Root: the bone a clip that walks off carries (root
    /// motion), held over the spot. Props: what it wears.</summary>
    public sealed record Def(string Key, string Path, float Height, string Pelvis, string Head, List<Vat.Role> Roles, int Budget = 8000,
        (string Left, string Right)? Legs = null, string? Root = null, List<Prop>? Props = null);

    /// <summary>Something made in code and worn, carried rigidly with a bone:
    /// set where the bone's Tip is as the model stands idle, upright along the
    /// bone toward it and facing the model's front, moved by Offset (metres)
    /// in that frame.</summary>
    public sealed record Prop(string Bone, string Tip, Func<Node3D> Make, Vector3 Offset);

    static double Ease(double t, double rate) { double k = Math.Min(1, t * rate); return 1 - (1 - k) * (1 - k); }

    /* -------------------------------------------------------------- wolf -- */

    const string Hips = "Becken_Wolf_Skeleton", Chest = "Brust_Wolf_Skeleton", Neck = "Hals_Wolf_Skeleton", Head = "Kopf_Wolf_Skeleton",
        Jaw = "Unterkiefer_Wolf_Skeleton", Tail = "Schwanz_Wolf_Skeleton", ForeL = "Oberarm_L_Wolf_Skeleton", ForeR = "Oberarm_R_Wolf_Skeleton",
        HindL = "Oberschenkel_L_Wolf_Skeleton", HindR = "Oberschenkel_R_Wolf_Skeleton";

    static readonly Def Wolf = new("beast_wolf", "res://art/beasts/wolf.glb", 0.95f, Hips, Head, new()
    {
        new("move", "Wolf_Run_", 0, 0.6),
        new("idle", "Wolf_Idle_", 2.0, 3.0, Seam: true),
        new("rise", "Wolf_Idle_", 2.0, 3.0, Seam: true),
        // Stalking in, low, lips back.
        new("windup", "Wolf_creep", 0, 1.33, t => new Vat.Moves().Bone(Jaw, 0.25 + 0.06 * Math.Sin(t * Math.Tau * 6))),
        // The lunge: in off the back legs, head up, jaws wide.
        new("attack", "Wolf_Run_", 0.15, 0.5, t =>
        {
            double k = Math.Sin(Math.Min(1, t * 1.6) * Math.PI);
            return new Vat.Moves { Move = new(0, 0, (float)(0.14 * k)) }
                .Bone(Hips, -0.15 * k).Bone(Chest, 0.2 * k).Bone(Neck, -0.35 * k).Bone(Head, 0.25 * k).Bone(Jaw, 0.6 * k)
                .Bone(ForeL, -0.8 * k).Bone(ForeR, -0.7 * k);
        }, Hold: true),
        new("hit", "Wolf_Idle_", 2.0, 0.3, t =>
        {
            double k = Math.Sin(t * Math.PI);
            return new Vat.Moves { Move = new(0, 0, (float)(-0.06 * k)) }.Bone(Chest, 0, 0, 0.15 * k).Bone(Neck, -0.2 * k).Bone(Head, -0.25 * k, 0.2 * k);
        }, Hold: true),
        // Over onto its side, legs gone slack.
        new("die", "Wolf_Idle_", 2.0, 0.9, t =>
        {
            double e = Ease(t, 1.5);
            return new Vat.Moves { Turn = new(0, 0, (float)(1.45 * e)), Move = new(0, (float)(-0.05 * e), 0) }
                .Shift(Hips, 0, -0.2 * e, 0).Bone(Neck, 0.3 * e).Bone(Head, 0.2 * e).Bone(Jaw, 0.35 * e)
                .Bone(ForeL, -0.5 * e).Bone(ForeR, 0.3 * e).Bone(HindL, 0.4 * e).Bone(HindR, -0.3 * e).Bone(Tail, 0.5 * e);
        }, Hold: true),
    });

    /* -------------------------------------------------------------- boar -- */

    const string BHips = "Hips_04", BChest = "Spine1_06", BHead = "Head_021", BForeL = "LEFT_FrontLeg_HipSHJnt_08", BForeR = "RIGHT_FrontLeg_HipSHJnt_013",
        BHindR = "RIGHT_HindLeg_HipSHJnt_046", BTail = "Tail_01_01SHJnt_00";

    static readonly Def Boar = new("beast_boar", "res://art/beasts/boar.glb", 0.9f, BHips, BHead, new()
    {
        new("move", "Armature|run", 0, 0.53),
        new("idle", "Armature|observing", 2.5, 3.5, Seam: true),
        new("rise", "Armature|observing", 2.5, 3.5, Seam: true),
        // Pawing the ground, head down, tail lashing.
        new("windup", "Armature|observing", 2.5, 0.6, t =>
        {
            double a = t * Math.Tau;
            return new Vat.Moves { Move = new(0, -0.04f, 0) }.Bone(BHips, 0.1).Bone(BHead, 0.35)
                .Bone(BForeL, -0.6 + Math.Max(0, Math.Sin(a * 2)) * 0.9).Bone(BForeR, 0.1).Bone(BTail, -0.4, Math.Sin(a * 6) * 0.3);
        }, Hold: true),
        // The charge's hook: tusks up through whatever is there.
        new("attack", "Armature|run", 0.1, 0.45, t =>
        {
            double k = Math.Sin(t * Math.PI);
            return new Vat.Moves().Bone(BHead, -0.5 * k).Shift(BHead, 0, 0.05 * k, 0.1 * k).Bone(BChest, -0.1 * k).Bone(BForeL, -0.4 * k).Bone(BForeR, -0.4 * k);
        }, Hold: true),
        new("hit", "Armature|observing", 2.5, 0.3, t =>
        {
            double k = Math.Sin(t * Math.PI);
            return new Vat.Moves().Bone(BChest, 0, 0, 0.12 * k).Bone(BHead, -0.3 * k);
        }, Hold: true),
        new("die", "Armature|observing", 2.5, 0.8, t =>
        {
            double e = Ease(t, 1.4);
            return new Vat.Moves { Turn = new(0, 0, (float)(-1.5 * e)) }.Shift(BHips, 0, -0.15 * e, 0).Bone(BHead, 0.3 * e).Bone(BForeL, 0.6 * e).Bone(BHindR, -0.5 * e);
        }, Hold: true),
    });

    /* --------------------------------------------------------- lamplings -- */

    const string LHips = "mixamorig_Hips_56", LSpine = "mixamorig_Spine_45", LChest = "mixamorig_Spine2_43", LNeck = "mixamorig_Neck_2",
        LHead = "mixamorig_Head_1", LTop = "mixamorig_HeadTop_End_0", LArmL = "mixamorig_LeftArm_21", LArmR = "mixamorig_RightArm_41",
        LLegL = "mixamorig_LeftUpLeg_50", LLegR = "mixamorig_RightUpLeg_55";

    /// <summary>The diggers: pale from living under the ground, a hat on
    /// each with a lamp hung out in front of its face on a crooked iron
    /// stalk, the light they dig toward carried with them. A sapper's hat is
    /// painted red, and it carries its powder on its back; Grimtunnel, their
    /// foreman, wears three lamps on a hat of black iron.</summary>
    static Def Lampling(string key, List<Prop> props) => new(key, "res://art/beasts/lampling.glb", 0.95f, LHips, LHead, new()
    {
        // Its walk hurried into a scurry, bent low over it.
        new("move", "Walk", 0, 1.2333 / Scurry, _ => new Vat.Moves().Bone(LSpine, 0.22).Bone(LHead, -0.18), Rate: Scurry),
        new("idle", "Idle", 1.8, 3.5, Seam: true),
        // A claw drawn back, shivering, the rest of it gathered to spring.
        new("windup", "Attack Combo", 0.42, 0.6, t => new Vat.Moves().Bone(LHead, 0, 0.08 * Math.Sin(t * Math.Tau * 5)).Bone(LChest, 0.05 * Math.Sin(t * Math.Tau * 10)), Hold: true),
        new("attack", "Attack Combo", 0.3, 0.55),
        new("hit", "Idle", 1.8, 0.3, t =>
        {
            double k = Math.Sin(t * Math.PI);
            return new Vat.Moves { Move = new(0, 0, (float)(-0.05 * k)) }.Bone(LChest, -0.3 * k).Bone(LHead, -0.3 * k, 0.2 * k);
        }, Hold: true),
        // Its knees go, and it goes over onto its back; the clip flings its
        // arms out wide as it lands, and they fall in along it instead.
        new("die", "Death", 0.35, 1.5, t =>
        {
            double w = Math.Clamp((t - 0.75) / 0.25, 0, 1);
            w = w * w * (3 - 2 * w);
            return new Vat.Moves().Bone(LArmL, 0, -1.15 * w).Bone(LArmR, 0, 1.15 * w);
        }),
        // Up out of the ground, clawing at the edge of the hole.
        new("rise", "Idle", 1.8, 0.66, t =>
        {
            double e = Ease(t, 1.2), u = 1 - e;
            return new Vat.Moves { Move = new(0, (float)(-0.75 * u), 0) }.Bone(LSpine, 0.6 * u).Bone(LHead, -0.4 * u)
                .Bone(LArmL, -1.8 * u + 0.3 * Math.Sin(t * Math.Tau * 2) * u).Bone(LArmR, -1.8 * u - 0.3 * Math.Sin(t * Math.Tau * 2) * u);
        }, Hold: true),
        // Under the ground: its back, its hat and its lamp going along above
        // the dirt, the claws working ahead of it.
        new("burrow", "Idle", 1.8, 0.5, t =>
        {
            double a = t * Math.Tau;
            return new Vat.Moves { Move = new(0, -0.2f, 0) }.Bone(LSpine, 0.8).Bone(LNeck, -0.3).Bone(LHead, -0.3, 0, 0.1 * Math.Sin(a))
                .Bone(LArmL, -1.3 + 0.8 * Math.Sin(a)).Bone(LArmR, -1.3 - 0.8 * Math.Sin(a));
        }, Hold: true),
    }, Budget: 6000, Legs: (LLegL, LLegR), Root: LHips, Props: props);

    static Prop Worn(string paint, float metal, int lamps) => new(LHead, LTop, () => Hat(paint, metal, lamps), new(0, -0.03f, -0.01f));

    /// <summary>How much faster than its walk a lampling's legs go.</summary>
    const double Scurry = 2.2;

    static readonly Def Tunneler = Lampling("beast_lampling", new() { Worn("#b08a38", 0.55f, 1) }),
        Sapper = Lampling("beast_lampling_sapper", new() { Worn("#7a2a1a", 0.35f, 1), new(LChest, LNeck, Satchel, new(0, -0.12f, -0.12f)) }),
        Foreman = Lampling("beast_grimtunnel", new() { Worn("#3e3a36", 0.8f, 3) });

    /// <summary>A digger's hat (origin at the crown of the head, +Z its
    /// front): a dented tin dome, a leather band, a brim, and a stalk with
    /// its lamp for each lamp it wears (more than one fanned out, the side
    /// ones shorter).</summary>
    static Node3D Hat(string paint, float metal, int lamps)
    {
        var root = new Node3D();
        const float R = 0.12f;
        var tin = new Build();
        Lathe(tin, Pts(R * 1.02f, -0.05f, R, -0.02f, R * 0.93f, 0.02f, R * 0.75f, 0.055f, R * 0.42f, 0.075f, 0, 0.08f), 14,
            warp: v => v + new Vector3(0, -0.006f * Noise(v.X * 40, v.Z * 40), 0));
        Lathe(tin, Pts(R * 0.98f, -0.07f, R * 1.36f, -0.078f, R * 1.38f, -0.068f, R * 1.34f, -0.06f, R * 0.98f, -0.045f), 14);
        Add(root, tin, Mat(paint, metal, 0.55f));
        var band = new Build();
        Lathe(band, Pts(R * 1.035f, -0.052f, R * 1.04f, -0.036f, R * 1.03f, -0.02f), 14);
        Add(root, band, Mat("#3a2616", 0, 0.85f));
        var iron = new Build();
        var flame = new Build();
        for (int n = 0; n < lamps; n++)
        {
            float side = lamps > 1 ? n / (lamps - 1f) * 2 - 1 : 0, reach = 1 - 0.3f * Mathf.Abs(side);
            var turn = new Basis(Vector3.Up, side * 0.75f);
            // The stalk: up off the back of the crown and over, the lamp hung from its end.
            Vector3 a = turn * new Vector3(0, 0.06f, -0.05f), c = turn * new Vector3(0, 0.3f * reach, -0.04f), b = turn * new Vector3(0, 0.25f * reach, 0.17f * reach);
            Tube(iron, Path(10, t => a * (1 - t) * (1 - t) + c * 2 * t * (1 - t) + b * t * t), 0.008f, 5);
            Tube(iron, new List<Vector3> { b, b + new Vector3(0, -0.035f, 0) }, 0.004f, 4);
            // The lamp: a cap, a base, four bars, a candle's worth of light between.
            var lamp = b + new Vector3(0, -0.075f, 0);
            Lathe(iron, Pts(0.024f, 0.03f, 0.03f, 0.028f, 0.012f, 0.042f, 0, 0.044f), 8, At(lamp.X, lamp.Y, lamp.Z));
            Lathe(iron, Pts(0, -0.04f, 0.026f, -0.038f, 0.026f, -0.028f, 0.02f, -0.026f), 8, At(lamp.X, lamp.Y, lamp.Z));
            for (int k = 0; k < 4; k++)
            {
                var d = new Vector3(Mathf.Cos(k * Mathf.Tau / 4 + 0.4f), 0, Mathf.Sin(k * Mathf.Tau / 4 + 0.4f)) * 0.024f;
                Tube(iron, new List<Vector3> { lamp + d + new Vector3(0, -0.03f, 0), lamp + d + new Vector3(0, 0.032f, 0) }, 0.003f, 3);
            }
            Lathe(flame, Pts(0, -0.022f, 0.016f, -0.01f, 0.017f, 0.004f, 0.01f, 0.018f, 0, 0.03f), 8, At(lamp.X, lamp.Y, lamp.Z));
        }
        Add(root, iron, Mat("#3a3836", 0.85f, 0.45f));
        Add(root, flame, Glow("#ffc060", 6, "#fff0c8"));
        return root;
    }

    /// <summary>A sapper's satchel of powder (origin between the shoulder
    /// blades): stitched leather, the flap buckled down over two iron shells,
    /// a fuse already alight.</summary>
    static Node3D Satchel()
    {
        var root = new Node3D();
        var leather = Mat("#5a3a22", 0, 0.85f);
        Add(root, new BoxMesh { Size = new Vector3(0.2f, 0.17f, 0.09f) }, leather);
        Add(root, new BoxMesh { Size = new Vector3(0.21f, 0.02f, 0.1f) }, Mat("#4a2e1a", 0, 0.8f), At(0, 0.09f, 0));
        Add(root, new BoxMesh { Size = new Vector3(0.03f, 0.05f, 0.006f) }, Brass(), At(0, 0.04f, -0.047f));
        var shell = Mat("#2a2826", 0.7f, 0.5f);
        Add(root, Ball(0.045f), shell, At(-0.05f, 0.12f, 0.005f));
        Add(root, Ball(0.04f), shell, At(0.055f, 0.115f, -0.005f));
        var fuse = new Build();
        Tube(fuse, new List<Vector3> { new(-0.05f, 0.16f, 0.005f), new(-0.055f, 0.19f, 0.01f), new(-0.045f, 0.21f, 0.02f) }, 0.005f, 4);
        Add(root, fuse, Mat("#8a7a5a", 0, 0.9f));
        Add(root, Ball(0.014f), Glow("#ff7a30", 8), At(-0.045f, 0.215f, 0.02f));
        return root;
    }

    /// <summary>The modelled beast a visual is drawn as, if it is one.</summary>
    public static Def? Of(string visual) => visual switch
    {
        "wolf" or "wolf_alpha" or "wolf_blighted" or "wolf_spirit" => Wolf,
        "boar" => Boar,
        "lampling" => Tunneler,
        "lampling_sapper" => Sapper,
        "grimtunnel" => Foreman,
        _ => null,
    };

    /// <summary>How large this one is against the shared model.</summary>
    public static float Size(string visual) => visual switch { "wolf_alpha" => 1.15f, "wolf_blighted" => 0.95f, _ => 1 };
}
