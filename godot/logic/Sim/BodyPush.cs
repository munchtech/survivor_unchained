using System;

namespace SurvivorUnchained.Sim;

/// <summary>
/// Her body against theirs (the owner, 19 Nov: "being able to shove the boss wherever we want is probably unintended"
/// / "by simply running into him"). A boss or an elite holds its ground: she stops against it. A common foe yields a
/// little, by mass, and never more than <see cref="MaxYield"/> of her own step, so walking cannot bulldoze a crowd.
/// </summary>
public sealed partial class Battle
{
    public const double MaxYield = 0.3;

    /// <summary>Share of an overlap a foe gives way: none for bosses and elites, else 0.3 for a light one, less for heavy.</summary>
    public static double BodyYield(Enemy e) => e.Boss || e.Elite ? 0 : MaxYield * Math.Min(1, 2 / Math.Max(0.5, e.Mass));

    /// <summary>Only against a body she walked into this step (wasX, wasZ: where she was): not a charger on its run, not a foe
    /// that walked onto her (its own step pushes it out).</summary>
    void PushOutOfBodies(double wasX, double wasZ)
    {
        var p = Player;
        if (!p.Alive) return;
        Spatial.Query(p.X, p.Z, p.Radius + 3.0, AiScratch);
        foreach (var id in AiScratch)
        {
            var o = Enemies.Items[id];
            if (!o.Alive || o.State is EnemyState.Dying or EnemyState.Lunging or EnemyState.Windup || o.Disposition == Disposition.Ally) continue;
            double dx = p.X - o.X, dz = p.Z - o.Z, min = p.Radius + o.Radius;
            double d2 = dx * dx + dz * dz;
            if (d2 >= min * min || d2 < 1e-9) continue;
            if ((p.X - wasX) * -dx + (p.Z - wasZ) * -dz <= 0) continue;   // not walking into it
            double d = Math.Sqrt(d2), over = min - d, ux = dx / d, uz = dz / d;
            double give = BodyYield(o);
            o.X -= ux * over * give; o.Z -= uz * over * give;
            Collision.Resolve(ref o.X, ref o.Z, o.Radius);
            p.X += ux * over * (1 - give); p.Z += uz * over * (1 - give);
        }
        Collision.Resolve(ref p.X, ref p.Z, p.Radius, true);
    }
}
