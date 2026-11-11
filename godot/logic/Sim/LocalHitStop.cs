using System;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/// <summary>A continuous hold has one budget, so a stream of hits cannot pin an actor forever.</summary>
public sealed class HitStopClock
{
    public double Remaining { get; private set; }
    public double Total { get; private set; }
    public double LastHeld { get; private set; }
    double elapsed;
    public bool Held => Remaining > 0;

    public void Raise(double seconds, double cap)
    {
        if (seconds <= 0) return;
        Remaining = Math.Max(0, Math.Min(cap - elapsed, Math.Max(Remaining, seconds)));
    }

    public double Step(double dt)
    {
        double held = Math.Min(dt, Remaining);
        LastHeld = held;
        Remaining = Math.Max(0, Remaining - held);
        elapsed += held;
        Total += held;
        if (dt > held) elapsed = 0;
        return dt - held;
    }

    public void Clear() { Remaining = elapsed = Total = LastHeld = 0; }
}

public sealed partial class Battle
{
    public HitStopDef LocalHitStop = Content.HitStop.File;
    /// <summary>The live view supplies the camera's frustum; headless runs use the data's play-camera footprint.</summary>
    public Func<Enemy, bool>? HitStopOnScreen;
    public bool LocalHitStopOn => LocalHitStop.Enabled;

    Enemy? HitStopSource(Projectile pr)
    {
        if (pr.OwnerId < 0 || pr.OwnerId >= Enemies.Capacity) return null;
        var e = Enemies.Items[pr.OwnerId];
        // A missile can outlive its caster and the pool slot can already belong to someone else.
        return e.Alive && e.Seed == pr.HitStopOwnerSeed ? e : null;
    }

    int HitStopCrowd()
    {
        int n = 0;
        foreach (var e in Enemies.Items)
            if (e.Alive && e.Hp > 0 && e.State is not (EnemyState.Dying or EnemyState.Burrowed) && e.Disposition == Disposition.Hostile &&
                (HitStopOnScreen?.Invoke(e) ?? (Math.Abs(e.X - Player.X) <= LocalHitStop.HeadlessScreen.HalfWidth &&
                    Math.Abs(e.Z - Player.Z) <= LocalHitStop.HeadlessScreen.HalfDepth))) n++;
        return n;
    }

    void StopHit(Enemy target, HitClass kind, Enemy? attacker = null, bool byPlayer = true)
    {
        if (!LocalHitStopOn || LocalHitStop.DurationMs[kind] <= 0) return;
        double seconds = LocalHitStop.Seconds(kind, HitStopCrowd()), cap = LocalHitStop.CapMs / 1000;
        target.HitStop.Raise(seconds, cap);
        if (attacker != null) attacker.HitStop.Raise(seconds, cap);
        else if (byPlayer) Player.HitStop.Raise(seconds, cap);
    }

    void StopPlayerHit(Enemy from)
    {
        if (!LocalHitStopOn) return;
        double seconds = LocalHitStop.Seconds(from.Boss || from.Elite ? HitClass.Heavy : HitClass.Trash, HitStopCrowd());
        Player.HitStop.Raise(seconds, LocalHitStop.CapMs / 1000);
        from.HitStop.Raise(seconds, LocalHitStop.CapMs / 1000);
    }

    void HoldPlayerDeadlines(double dt)
    {
        // Absolute contact and chain beats must wait with her cooldowns, without moving the world's clock.
        if (Player.AttackAnim is { } a) Player.AttackAnim = a with { Held = a.Held + dt };
        for (int i = 0; i < pendingBlows.Count; i++)
        {
            var p = pendingBlows[i]; p.At += dt; p.Due += dt; pendingBlows[i] = p;
        }
        foreach (var w in chains)
        {
            if (w.Chain is not { Live: true } c) continue;
            c.ContactAt += dt; c.CancelAt += dt; c.PeriodEnd += dt;
            c.ReleasedAt += dt; c.ReleaseAt += dt; c.GraceUntil += dt;
            c.From += dt; c.PayTo += dt; w.PaidTo += dt;
        }
    }
}
