using System;
using System.Collections.Generic;

namespace SurvivorUnchained.View;

/// <summary>
/// The Verge's wolves and boars as modelled, rigged and animated animals
/// (art/beasts; credits in public/assets/CREDITS.md), baked into the crowd
/// like the people. Where a model has a clip for what a crowd creature does
/// (a run, a creeping stalk, an idle), it plays it; where it has none (a
/// bite, a charge, a fall), the move is composed over one of its poses, bones
/// turned in the model's own space, as the web game's code-built beasts moved
/// (Creatures.cs, still used for the lamplings).
///
/// One wolf serves every wolf: the alpha is larger and darker, the blighted
/// sick-green, the spirit pale and glowing (Visuals.Tint, Size here).
/// </summary>
public static class Beasts
{
    public sealed record Def(string Key, string Path, float Height, string Pelvis, string Head, List<Vat.Role> Roles, int Budget = 8000);

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

    /// <summary>The modelled beast a visual is drawn as, if it is one.</summary>
    public static Def? Of(string visual) => visual switch
    {
        "wolf" or "wolf_alpha" or "wolf_blighted" or "wolf_spirit" => Wolf,
        "boar" => Boar,
        _ => null,
    };

    /// <summary>How large this one is against the shared model.</summary>
    public static float Size(string visual) => visual switch { "wolf_alpha" => 1.15f, "wolf_blighted" => 0.95f, _ => 1 };
}
