using System;

namespace SurvivorUnchained.Play;

/// <summary>Her gait (animation 51): one stride phase shared by her walk and her run so the feet stay on the same foot
/// through the blend. Weights say how much of idle, walk and run show; the period says how long a stride pair takes at
/// her ground speed; the phase advances by it.</summary>
public static class Stride
{
    static float Smooth(float a, float b, float x)
    {
        if (b <= a) return x >= b ? 1f : 0f;
        var t = Math.Clamp((x - a) / (b - a), 0f, 1f);
        return t * t * (3f - 2f * t);
    }

    /// <summary>(walk over idle, run over walk). Without a walk: no walk and the old standing-to-running blend.</summary>
    public static (float Walk, float Run) Weights(float speed, float walkSpeed, float runSpeed, bool hasWalk)
        => hasWalk ? (Smooth(0.15f, 0.7f, speed), Smooth(walkSpeed * 1.25f, runSpeed * 0.6f, speed))
                   : (0f, Smooth(0.25f, 2.2f, speed));

    /// <summary>Seconds per stride pair at this ground speed. runScale is the run's old time scale (clamped speed over its natural speed).</summary>
    public static float Period(float speed, float walkLen, float walkSpeed, float runLen, float runScale, float wRun, bool hasWalk)
    {
        float pRun = runLen / Math.Max(runScale, 1e-3f);
        if (!hasWalk) return pRun;
        float pWalk = walkLen / Math.Clamp(speed / Math.Max(walkSpeed, 1e-3f), 0.5f, 1.6f);
        return pWalk + (pRun - pWalk) * Math.Clamp(wRun, 0f, 1f);
    }

    /// <summary>The run's time scale as it was: ground speed over the clip's natural speed, clamped.</summary>
    public static float RunScale(float speed, float natural) => Math.Clamp(speed / Math.Max(natural, 1e-3f), 0.55f, 1.5f);

    /// <summary>Phase after dt seconds of a stride of `period`, in [0,1).</summary>
    public static float Advance(float phase, float dt, float period)
    {
        if (period <= 1e-4f) return phase;
        var p = (phase + dt / period) % 1f;
        return p < 0 ? p + 1f : p;
    }
}
