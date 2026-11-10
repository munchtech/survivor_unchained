using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/// <summary>
/// --aim-nearest (pictures, M4 §5's routes frame): a scripted shot has no hand on the mouse, so her priority target
/// (Battle.Priority, the foe FoeMarks rings in bone) is only ever what the desktop's real pointer happens to lie over.
/// With this flag her target is the nearest foe she may hit, set each frame; run it with --no-pointer so Game.Priority()
/// leaves it be. It logs the target when it changes and every crit that lands (a foe's life fell and its last blow was
/// a crit), so the frame showing the ellipse and a white number is picked by fact. DevSlots.Tick ticks it.
/// </summary>
public static class DevAim
{
    static readonly bool On = Args.Has("aim-nearest");
    const double Reach = 30;
    static Battle? aimFor;
    static int aimed = -2, said;
    static double[] hp = [];

    public static void Tick(Battle b)
    {
        if (!On || !b.Combat || !b.Player.Alive) return;
        if (!ReferenceEquals(aimFor, b)) { aimFor = b; aimed = -2; hp = []; }
        var p = b.Player;
        var items = b.Enemies.Items;
        if (hp.Length < items.Length) Array.Resize(ref hp, items.Length);
        Enemy? best = null;
        double bd = Reach * Reach;
        for (int i = 0; i < items.Length; i++)
        {
            var e = items[i];
            // (a crit landed since the last frame: the white number is on screen from now)
            double now = e.Alive ? Math.Max(0, e.Hp) : 0;
            if (now < hp[i] - 1e-6 && e.LastCrit && said++ < 60)
                GD.Print($"aim: crit {hp[i] - now:0} on #{e.Id} {e.Def.Id} at {b.Time:0.00}{(e.Id == b.Priority ? " (her target)" : "")}{(now <= 0 ? " (it fell)" : "")}");
            hp[i] = now;
            if (!e.Alive || e.State == EnemyState.Dying || !b.Targetable(e) || !b.HostileToPlayer(e)) continue;
            double d = (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z);
            if (d < bd) { bd = d; best = e; }
        }
        int id = best?.Id ?? -1;
        b.Priority = id;
        if (id == aimed) return;
        aimed = id;
        if (said++ < 60)
            GD.Print(best != null ? $"aim: target #{id} {best.Def.Id} at {Math.Sqrt(bd):0.0} m, fight {b.Time:0.00}" : $"aim: no target, fight {b.Time:0.00}");
    }
}
