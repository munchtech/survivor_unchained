using System;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>A plain-minded survivor's hands (the tests' ArenaPlay bot, kept
/// as it was so the numbers mean the same): give ground when pressed, go to
/// the fight or the ember lying about when it is quiet, keep off the arena's
/// edge, dash out of a crush, use the art on a crowd, drink when low.</summary>
public static class Pilot
{
    public static (double X, double Z) Steer(Battle b)
    {
        var p = b.Player;
        double mx, mz;
        var press = b.HostilesInRadius(p.X, p.Z, 3.4);
        Enemy? nearest = null;
        double nd = double.MaxValue;
        foreach (var e in b.Enemies.Items)
        {
            if (!e.Alive || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            double d = (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z);
            if (d < nd) { nd = d; nearest = e; }
        }
        Pickup? stone = null;
        double sd = 144;
        foreach (var k in b.Pickups.Items)
        {
            if (!k.Alive || k.Kind != PickupKind.Ember) continue;
            double d = (k.X - p.X) * (k.X - p.X) + (k.Z - p.Z) * (k.Z - p.Z);
            if (d < sd) { sd = d; stone = k; }
        }
        double near = nearest == null ? double.MaxValue : Math.Sqrt(nd);
        if (press.Count >= 2)
        {
            double cx = press.Average(e => e.X) - p.X, cz = press.Average(e => e.Z) - p.Z;
            double cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
            // Away and round: a quarter turn off straight back.
            mx = -cx / cl * 0.7 - cz / cl * 0.7; mz = -cz / cl * 0.7 + cx / cl * 0.7;
        }
        else if (stone != null && near > 5) { mx = stone.X - p.X; mz = stone.Z - p.Z; }
        else if (nearest != null && near > 6) { mx = nearest.X - p.X; mz = nearest.Z - p.Z; }
        else if (nearest != null) { mx = -(nearest.Z - p.Z); mz = nearest.X - p.X; }
        else { mx = -p.X; mz = -p.Z; }
        double far = Math.Sqrt(p.X * p.X + p.Z * p.Z);
        if (far > 60) { mx = mx * 0.3 - p.X / far; mz = mz * 0.3 - p.Z / far; }
        if (b.Collision.Blocked(p.X + mx * 0.1, p.Z + mz * 0.1, p.Radius)) (mx, mz) = (-mz, mx);
        double ml = Math.Sqrt(mx * mx + mz * mz);
        if (ml > 1e-6) { mx /= ml; mz /= ml; }
        return (mx, mz);
    }

    /// <summary>The hands that are not the feet: a dash out of a crush, the art
    /// on a crowd, a draught when low.</summary>
    public static void Act(Battle b, Journey j, double mx, double mz)
    {
        var p = b.Player;
        if (p.DashCharges > 0 && b.HostilesInRadius(p.X, p.Z, 2.2).Count >= 3) b.Dash(mx, mz);
        if (p.AbilityCd <= 0 && b.HostilesInRadius(p.X, p.Z, 6).Count >= 5) b.UseAbility(mx, mz);
        if (p.Hp < b.MaxHp * 0.33) j.Quaff(b);
    }
}
