W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Content/Enemies.cs": [
        ("""        /* ------------------------------------------- the Kindling (minute 15) -- */""",
         """        // The Lamplings' champion, until the Blasting-Cart has its art: a ganger of the Dig. Their
        // heralds were a lampling's body at twenty health, down in four seconds (every other people's
        // herald took twenty to forty), so their nights asked nothing of a draft's single-target reach.
        new() { Id = "lampling_ganger", Name = "Ganger of the Dig", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling", Scale = 1.35, Tint = (1.15, 1.02, 0.86), Glow = 0.12,
            Health = 460, Speed = 3.4, Damage = 14, Radius = 0.75, Mass = 5, Xp = 40, Behavior = Behavior.Tunneler, Resists = new() { [School.Fire] = 0.3, [School.Frost] = -0.3 },
            Slam = new(3, 7, 1.0, 2.6, 1.2, Self: true), Elite = true, AttackEvery = 1.1, Loot = "elite",
            Note = "One of the Dig's gangers: a pick, a lamp, and a gang under the ground behind it." },

        /* ------------------------------------------- the Kindling (minute 15) -- */"""),
    ],
    W + "logic/Maps/MapOffers.cs": [
        ("""            [("lampling", 5, 0), ("lampling_wick", 3, 3), ("lampling_sapper", 3.5, 7), ("lampling_lamp", 1.5, 12), ("lampling_fuse", 1.2, 16)], "lampling",""",
         """            [("lampling", 5, 0), ("lampling_wick", 3, 3), ("lampling_sapper", 3.5, 7), ("lampling_lamp", 1.5, 12), ("lampling_fuse", 1.2, 16)], "lampling_ganger","""),
    ],
}
