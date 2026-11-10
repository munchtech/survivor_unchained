using System;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* Kindled skills (ARPG.md, the hands rule): an auto skill with a "kindle" in skills.json fires itself only when its
 * wait is over AND the condition holds (Weapons.Tick asks here, only when its timer is ready). */
public sealed partial class Battle
{
    /// <summary>When she last blocked a blow (the battle's clock).</summary>
    public double BlockedAt = double.NegativeInfinity;

    internal bool Kindled(KindleDef k)
    {
        if (k.Any is { Length: > 0 } any)
        {
            foreach (var a in any) if (Kindled(a)) return true;
            if (k.When == null) return false;
        }
        var p = Player;
        switch (k.When)
        {
            case "crowd": return HostilesInRadius(p.X, p.Z, k.Radius ?? 3).Count >= (k.Count ?? 4);
            case "hurt": return p.Hp < k.Below.GetValueOrDefault(0.5) * MaxHp;
            case "block": return Time - BlockedAt <= 0.2;
            case "windup": return WindupAt(k.Radius ?? 3, k.Within ?? 0.6, k.Big == true);
            default: return true;
        }
    }

    static bool IsBig(Enemy? e) => e == null || e.Elite || e.Boss || e.Def.Slam != null || e.Def.Charge != null || (e.Def.Scale ?? 1) >= 1.15;

    /// <summary>A blow marked on her, a creature's marked circle or a foe's windup that lands on her or within `r` of her
    /// within `within` seconds (big: a brute's or elite's, a boss's, or one that would take a twentieth of her life).</summary>
    bool WindupAt(double r, double within, bool big)
    {
        var p = Player;
        foreach (var b in blows)
            if (b.T <= within && b.Hit(p.X, p.Z, p.Radius + r) && (!big || IsBig(b.From))) return true;
        foreach (var s in strikes)
            if (s.Owner == Side.Enemy && s.T <= within && Dist(s.X, s.Z, p.X, p.Z) <= s.R + p.Radius + r && (!big || s.Dmg >= MaxHp * 0.05)) return true;
        foreach (var e in HostilesInRadius(p.X, p.Z, r + 8))
        {
            if (e.State != EnemyState.Windup || e.StateT > within) continue;
            double dx = p.X - e.X, dz = p.Z - e.Z;
            if (e.LungeX * dx + e.LungeZ * dz <= 0 && Dist(e.X, e.Z, p.X, p.Z) > r + e.Radius + p.Radius + 1) continue;
            if (!big || IsBig(e)) return true;
        }
        return false;
    }
}
