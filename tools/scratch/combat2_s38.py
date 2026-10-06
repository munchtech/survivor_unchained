W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Content/Enemies.cs": [
        ("""        /* ---------------------------------------------------- your own, raised -- */""",
         """        /* ------------------------------------------- the Kindling (minute 15) -- */
        // (docs/bosses/SURVIVORS_BOSSES.md 9.) The heart of the ember scar the arena was opened from,
        // and round it what rules the people's own creature, with one of its ruler's verbs: the
        // night's first verse of its boss. Drawn by the zone (an orb and its light), not the crowd.
        new() { Id = "ember_core", Name = "The Ember-Core", Family = Family.Elemental, Faction = Faction.Wild, Visual = "view:ember_core",
            Health = 100, Speed = 0, Damage = 0, Radius = 1.2, Mass = 999, Xp = 0, Behavior = Behavior.Stationary, AttackEvery = 1e9,
            Note = "Raw ember the size of a cart wheel, come up out of the scar the arena was opened from. Broken quickly, it gives more than it takes." },
        new() { Id = "lt_pack", Name = "The Pack-Mother's Yearling", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf_alpha", Scale = 1.2, Tint = (1.12, 0.98, 0.86),
            Health = 400, Speed = 5.0, Damage = 14, Radius = 0.75, Mass = 4, Xp = 30, Resists = Beast, Behavior = Behavior.Pack,
            Lunge = new(10, 5, 0.8, 0.45, 18), Summon = new(13, 5, "wolf", 1.3, SpawnStyle.Walk, 10, AtTarget: true, Max: 15, Word: "A rising howl"),
            Elite = true, Tags = [Tag.Nature], AttackEvery = 0.9,
            Lesson = "She herds as her mother will: the wolves close round you, and she runs the gap. Go through the wolves.",
            Note = "Her mother's eldest, and as sure as her already of where you will run." },
        new() { Id = "lt_dead", Name = "The Barrow Lord's Hornblower", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_warrior_elite", Scale = 1.3, Tint = (0.95, 1.02, 0.84),
            Health = 420, Speed = 2.4, Damage = 16, Radius = 0.85, Mass = 6, Xp = 30, Resists = Undead, Behavior = Behavior.Guard,
            Guard = new(1.6, 0.5), Summon = new(13, 4, "risen_warrior", 1.3, SpawnStyle.Rise, 8, AtTarget: true, Max: 12, Word: "Iungite!"),
            Elite = true, AttackEvery = 1.2,
            Lesson = "A horn, and shields rise in a line. Go round the line's end.",
            Note = "He blew the Seventh's calls at the ford, and he blows them still. The dead dress their line to him." },
        new() { Id = "lt_lamplings", Name = "The Sapper-Foreman", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling_sapper", Scale = 1.4, Tint = (0.92, 0.98, 1.3), Glow = 0.35,
            Health = 380, Speed = 3.4, Damage = 12, Radius = 0.8, Mass = 5, Xp = 30, Behavior = Behavior.Tunneler, Resists = new() { [School.Fire] = 0.3, [School.Frost] = -0.3 },
            Slam = new(3.2, 6, 1.0, 3, 1.3, Self: true, Word: "Up!"), Elite = true, AttackEvery = 1.1,
            Lesson = "A mound runs at you, and it bursts up where it stops. Be gone from there.",
            Note = "One lamp, and the Dig's way of coming up out of the ground. Gutterwick taught it, and it shows." },
        new() { Id = "lt_kerchiefs", Name = "The Toll-Taker", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_enforcer", Scale = 1.3, Tint = (1.08, 1.06, 0.8),
            Health = 420, Speed = 3.8, Damage = 15, Radius = 0.8, Mass = 6, Xp = 30, Gold = 15, Resists = Kerchief, Behavior = Behavior.Chase,
            Lunge = new(8, 5, 0.8, 0.4, 16), Summon = new(13, 3, "footpad", 1.2, SpawnStyle.Walk, 10, AtTarget: true, Max: 9, Word: "Toll!"),
            Elite = true, AttackEvery = 1.0,
            Lesson = "It takes the Red Hand's toll before he does, and its runners come for what you carry.",
            Note = "Keeps the Red Hand's tally of who has paid. Everyone owes." },

        /* ---------------------------------------------------- your own, raised -- */"""),
    ],
    W + "logic/Sim/Battle.cs": [
        ("""    public int GreatOwed;""", """    public int GreatOwed;
    /// <summary>Cards more on the next great blessing (the ember-core broken in time).</summary>
    public int GreatExtra;"""),
    ],
    W + "logic/Sim/LevelUp.cs": [
        ("""        if (GreatNext(b)) return m.Cards = m.Greats >= 1 || b.Omens ? 4 : 3;""",
         """        if (GreatNext(b)) return m.Cards = (m.Greats >= 1 || b.Omens ? 4 : 3) + b.GreatExtra;"""),
        ("""        if (great) { b.GreatOwed = System.Math.Max(0, b.GreatOwed - 1); m.Greats++; }""",
         """        if (great) { b.GreatOwed = System.Math.Max(0, b.GreatOwed - 1); m.Greats++; b.GreatExtra = 0; }"""),
    ],
}
