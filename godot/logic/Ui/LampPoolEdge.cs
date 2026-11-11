using System;


namespace SurvivorUnchained.Ui;

/// <summary>(L1 lead 26, M4 row b) The held lamp's pool edge on the ground (src/Fx/BattleFx.LampPool.cs draws it): the
/// place to hold, shown only while a caught, lit lamp's pool is somewhere she is NOT. No Godot types, so it is tested.</summary>
public static class LampPoolEdge
{
    /// <summary>Seconds the ring takes to come in or go as she crosses the edge.</summary>
    public const float Fade = 0.2f;

    /// <summary>On: the lamp is caught and lit and she stands outside its pool (on the edge counts as inside).</summary>
    public static bool Show(SurvivorUnchained.Sim.LampMark? l, double px, double pz)
    {
        if (l is not { Caught: true, Lit: true } || l.Pool <= 0) return false;
        double dx = px - l.X, dz = pz - l.Z;
        return dx * dx + dz * dz > l.Pool * l.Pool;
    }

    /// <summary>The ring's coverage stepped toward on (1) or off (0) over <see cref="Fade"/> seconds.</summary>
    public static float Step(float a, bool on, float dt)
    {
        float k = dt / Fade;
        return on ? MathF.Min(1f, a + k) : MathF.Max(0f, a - k);
    }
}
