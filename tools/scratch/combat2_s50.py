W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Content/Enemies.cs": [
        ("""    public (double Factor, double Duration)? Slow;
    public string? Art;
}""",
         """    public (double Factor, double Duration)? Slow;
    public string? Art;
    /// <summary>Seconds planted and aiming before it looses (a crossbow's kneel): its aim is fixed
    /// as it begins, so stepping off the line in time is a dodge, as a lunge's wind-up is. 0: none.</summary>
    public double Aim;
}"""),
        # The levy crossbows and the Scorpion kneel to shoot.
        ("""            Ranged = new() { Range = 10, Cooldown = 3.6, Speed = 12, School = School.Physical, Count = 3, Spread = 0.22, Art = "bolt_bone" }, Loot = "kerchief",""",
         """            Ranged = new() { Range = 10, Cooldown = 3.6, Speed = 12, School = School.Physical, Count = 3, Spread = 0.22, Art = "bolt_bone", Aim = 0.55 }, Loot = "kerchief","""),
        ("""            Ranged = new() { Range = 11, Cooldown = 2.6, Speed = 12, School = School.Physical, Count = 5, Spread = 0.2, Art = "bolt_bone" },""",
         """            Ranged = new() { Range = 11, Cooldown = 2.6, Speed = 12, School = School.Physical, Count = 5, Spread = 0.2, Art = "bolt_bone", Aim = 0.55 },"""),
        ("""            Ranged = new() { Range = 11, Cooldown = 2.8, Speed = 13, School = School.Physical, Count = 5, Spread = 0.18, Art = "bolt_bone" },""",
         """            Ranged = new() { Range = 11, Cooldown = 2.8, Speed = 13, School = School.Physical, Count = 5, Spread = 0.18, Art = "bolt_bone", Aim = 0.55 },"""),
    ],
    W + "logic/Sim/Entities.cs": [
        ("""    public double LungeX, LungeZ;""", """    public double LungeX, LungeZ;
    /// <summary>How far its target stood when it knelt to aim (RangedSpec.Aim).</summary>
    public double AimReach;"""),
        ("""public enum CastKind { None, Raise, Summon, Slam, Aura }""",
         """/// <summary>Aim: a crossbow planted and aiming (RangedSpec.Aim), its line fixed.</summary>
public enum CastKind { None, Raise, Summon, Slam, Aura, Aim }"""),
    ],
    W + "logic/Sim/Ai.cs": [
        ("""        // Its own verbs: a rallying pulse, a call for its kind, a blow on the ground.
        if ((def.Aura != null || def.Summon != null || def.Slam != null) && Verbs(b, e, def, tgt, dist, dt)) return;""",
         """        // Aiming (a crossbow's kneel): planted on its line until it looses, then up again.
        if (e.State == EnemyState.Casting && e.Cast == CastKind.Aim && def.Ranged is { } aimed)
        {
            e.StateT -= dt;
            e.Vx = e.Vz = 0;
            e.Anim = EnemyAnim.Windup;
            e.Facing = Math.Atan2(e.LungeZ, e.LungeX);
            if (e.StateT <= 0)
            {
                e.State = EnemyState.Active;
                e.Cast = CastKind.None;
                // At the line it chose as it knelt, as far as the target then was.
                var at = tgt;
                double reach = Math.Max(1, e.AimReach);
                at.X = e.X + e.LungeX * reach; at.Z = e.Z + e.LungeZ * reach;
                Shoot(b, e, at);
                e.RangedT = aimed.Cooldown * (0.85 + b.Rng.Next() * 0.3);
            }
            b.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
            return;
        }

        // Its own verbs: a rallying pulse, a call for its kind, a blow on the ground.
        if ((def.Aura != null || def.Summon != null || def.Slam != null) && Verbs(b, e, def, tgt, dist, dt)) return;"""),
        ("""            if (e.RangedT <= 0 && dist < ranged.Range && b.Collision.Raycast(e.X, e.Z, tgt.X, tgt.Z, 0.1) == null)
            {
                Shoot(b, e, tgt);
                e.RangedT = ranged.Cooldown * (0.85 + b.Rng.Next() * 0.3);
            }""",
         """            if (e.RangedT <= 0 && dist < ranged.Range && b.Collision.Raycast(e.X, e.Z, tgt.X, tgt.Z, 0.1) == null)
            {
                if (ranged.Aim > 0)
                {
                    // Kneel and aim: the line is fixed now, so a step off it in time is a dodge.
                    e.State = EnemyState.Casting;
                    e.Cast = CastKind.Aim;
                    e.StateT = ranged.Aim;
                    e.Anim = EnemyAnim.Windup;
                    e.AnimT = 0;
                    e.LungeX = dx / dist; e.LungeZ = dz / dist;
                    e.AimReach = dist;
                    e.Vx = e.Vz = 0;
                    return;
                }
                Shoot(b, e, tgt);
                e.RangedT = ranged.Cooldown * (0.85 + b.Rng.Next() * 0.3);
            }"""),
    ],
}
