using System;

namespace SurvivorUnchained.Play;

/// <summary>Her arm-hold switch (animation 55): when her walk and her run carry a piece in two different holds (the walk
/// thumb-forward, the run trailing it low and back from a bent elbow), a per-bone mix of the two turns the piece through
/// an orientation neither hold has (43-54 degrees off at 50/50, the sword into her legs). So her legs, hips and spine
/// keep the linear speed blend while her arms take one hold or the other: the run's once the run weight passes Up, back
/// to the walk's under Down (the gap keeps a held stick from flickering), and each change is crossfaded over Fade
/// seconds of time, not of speed (one quick re-grip). Carry is the share of the old hold still laid over the new (1 at
/// the switch, eased to 0): HerArmHold turns each arm bone from where it was toward the new hold by it, in the chest's
/// space, so the piece swings straight between the two holds rather than through a per-bone mix.</summary>
public sealed class ArmHold
{
    public const float Up = 0.6f, Down = 0.4f, Fade = 0.2f;

    /// <summary>True: the run's hold (her run or sprint); false: the walk's (or idle's).</summary>
    public bool Run { get; private set; }
    /// <summary>Time since the last switch over Fade, 0..1 (1: settled).</summary>
    public float X { get; private set; } = 1f;
    /// <summary>The old hold's share still laid over the new one: 1 at the switch, eased to 0 over Fade.</summary>
    public float Carry => 1f - Ease(X);
    float from;
    /// <summary>Where her arms are between the walk's hold (0) and the run's (1): eased from wherever the last switch
    /// caught them (a switch back mid-fade turns round without a jump).</summary>
    public float E => from + ((Run ? 1f : 0f) - from) * Ease(X);
    /// <summary>Mid-fade: her arms between the two holds (HerArmHold lays them).</summary>
    public bool Fading => X < 1f;

    /// <summary>The hold for a run weight, given the hold she is in (hysteresis between Down and Up).</summary>
    public static bool Target(bool run, float wRun) => run ? wRun >= Down : wRun > Up;

    /// <summary>Smoothstep on 0..1.</summary>
    public static float Ease(float x)
    {
        x = Math.Clamp(x, 0f, 1f);
        return x * x * (3f - 2f * x);
    }

    /// <summary>Settle at once in the hold this run weight asks (a fresh start, a clip swap): no crossfade.</summary>
    public void Reset(float wRun)
    {
        Run = wRun > 0.5f;
        X = 1f;
        from = Run ? 1f : 0f;
    }

    /// <summary>A frame of dt seconds at run weight wRun. Returns true on the frame the hold switches (the crossfade
    /// starts from wherever her arms are, so a switch back mid-fade is continuous).</summary>
    public bool Step(float wRun, float dt)
    {
        bool t = Target(Run, wRun);
        if (t != Run)
        {
            from = E;
            Run = t;
            X = 0f;
            return true;
        }
        X = Math.Min(1f, X + Math.Max(dt, 0f) / Fade);
        return false;
    }

    /// <summary>Whether an arm bone (by name) belongs to the switched arms: clavicle down to the fingertips, the twist
    /// and share bones, the shoulder's helpers (delt, trap, scap, pec, lat), both sides.</summary>
    public static bool IsArmBone(string name)
    {
        if (!(name.EndsWith("_l") || name.EndsWith("_r"))) return false;
        foreach (var p in Prefixes) if (name.StartsWith(p, StringComparison.Ordinal)) return true;
        return false;
    }

    static readonly string[] Prefixes = { "clavicle", "upperarm", "lowerarm", "hand", "index", "middle", "pinky", "ring", "thumb", "delt", "trap", "scap", "pec", "lat" };
}
