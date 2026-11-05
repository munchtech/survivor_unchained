using System;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>H6's two measuring hands (docs/team/hook/H6_combat_move.md item 1): what the night does to a player who
/// does nothing with her feet, and to one who does nothing else.
/// standing: never moves, never dodges (no dash of any kind); her weapons fire, the Flare is pressed as the Pilot
/// presses it, and she drinks when low. camper: the owner's demo-rc2 play: stands, except that when the board's lamp
/// catches she walks to it (and to its wick when it is out or snuffed) and stands there.
/// kiter: always moving, away from the press round her (weighted by nearness) with a sideways turn so the edge does
/// not pin her; with nothing within 9 m she circles the nearest foe at about 7 m. Reads no mark; dashes only out of
/// a crush.</summary>
public static class Bots
{
    public static bool Is(string bot) => bot is "standing" or "camper" or "kiter";

    public static (double X, double Z) Steer(string bot, Battle b, (double X, double Z)? goal, double boardR)
    {
        if (bot == "standing") return (0, 0);
        if (bot == "camper") return goal is var (gx, gz) && Dist(gx, gz, b.Player.X, b.Player.Z) > 1.2 ? Norm(gx - b.Player.X, gz - b.Player.Z) : (0, 0);
        return Kite(b, boardR);
    }

    public static bool Act(string bot, Battle b, Journey j, double mx, double mz, SurvivorUnchained.Play.Bosses.ArenaBoss? boss) =>
        Pilot.Act(b, j, mx, mz, boss, lunges: false, aimsFlare: true, rooted: false, crush: bot == "kiter");

    static (double X, double Z) Kite(Battle b, double boardR)
    {
        var p = b.Player;
        double ax = 0, az = 0; int n = 0;
        Enemy? nearest = null; double nd = double.MaxValue;
        foreach (var e in b.Enemies.Living())
        {
            if (e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            double dx = p.X - e.X, dz = p.Z - e.Z, d = Math.Sqrt(dx * dx + dz * dz);
            if (d < nd) { nd = d; nearest = e; }
            if (d > 9) continue;
            double w = 1 / Math.Max(0.5, d * d);
            ax += dx / Math.Max(0.01, d) * w; az += dz / Math.Max(0.01, d) * w; n++;
        }
        double mx, mz;
        if (n > 0)
        {
            (ax, az) = Norm(ax, az);
            // Away, a third of a turn round: straight back pins her to the edge in a minute.
            mx = ax * 0.8 - az * 0.6; mz = az * 0.8 + ax * 0.6;
        }
        else if (nearest != null)
        {
            double dx = nearest.X - p.X, dz = nearest.Z - p.Z, d = Math.Max(0.01, nd);
            double inward = d > 7 ? 0.6 : -0.3;
            mx = dx / d * inward - dz / d; mz = dz / d * inward + dx / d;
        }
        else { mx = -p.Z; mz = p.X; if (Math.Abs(mx) + Math.Abs(mz) < 1e-3) mx = 1; }
        // The board's edge: turn in before it.
        double far = Math.Sqrt(p.X * p.X + p.Z * p.Z), edge = Math.Max(10, boardR - 4);
        if (far > edge) { double k = Math.Min(1.5, (far - edge) / 3); mx -= p.X / far * k; mz -= p.Z / far * k; }
        (mx, mz) = Norm(mx, mz);
        if (b.Collision.Blocked(p.X + mx * 0.3, p.Z + mz * 0.3, p.Radius))
        {
            // The nearest clear turn, either hand.
            for (int i = 1; i <= 6; i++)
                foreach (int s in new[] { 1, -1 })
                {
                    double a = s * i * Math.PI / 8, c = Math.Cos(a), sn = Math.Sin(a);
                    double tx = mx * c - mz * sn, tz = mx * sn + mz * c;
                    if (!b.Collision.Blocked(p.X + tx * 0.3, p.Z + tz * 0.3, p.Radius)) return (tx, tz);
                }
        }
        return (mx, mz);
    }

    static (double, double) Norm(double x, double z) { double l = Math.Sqrt(x * x + z * z); return l < 1e-6 ? (0, 0) : (x / l, z / l); }
    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}
