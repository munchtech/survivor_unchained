using System;

namespace SurvivorUnchained.Play;

/// <summary>A failed optional frame step stays off until its place is rebuilt.</summary>
public sealed class FrameGuard
{
    public bool Failed { get; private set; }

    public void Reset() => Failed = false;

    public void Run<T>(T owner, double dt, Action<T, double> tick, Action<Exception> report)
    {
        if (Failed) return;
        try { tick(owner, dt); }
        catch (Exception e)
        {
            // Latch before reporting so another frame cannot repeat the same failure.
            Failed = true;
            report(e);
        }
    }
}
