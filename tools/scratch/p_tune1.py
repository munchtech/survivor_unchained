import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot"
FILES = {
os.path.join(G, r"logic\Play\Zones\ArenaRun.cs"): [
("""    readonly HashSet<int> chests = new();""",
"""    readonly HashSet<int> chests = new();
    /// <summary>Those carrying a small chest (one card): the minibosses. A full chest each made the
    /// night's builds a tenth stronger at the boss (measured: the boss fell 12-25 s sooner).</summary>
    readonly HashSet<int> smallChests = new();"""),
("""        e.Named = new Named { Title = e.Def.Name };
        chests.Add(e.Id);
        miniboss = e;""",
"""        e.Named = new Named { Title = e.Def.Name };
        smallChests.Add(e.Id);
        miniboss = e;"""),
("""        bool carrier = chests.Remove(e.Id);
        if (carrier) o.Add(new Loot(PickupKind.Chest, null, 1, true));""",
"""        bool small = smallChests.Remove(e.Id), carrier = chests.Remove(e.Id) || small;
        if (carrier) o.Add(new Loot(PickupKind.Chest, small ? "small" : null, 1, true));"""),
("""        int n = p.Ref == "boss" ? (int)p.Value : 1 + (R() < 0.3 ? 1 : 0) + (R() < 0.1 ? 1 : 0);""",
"""        int n = p.Ref == "boss" ? (int)p.Value : p.Ref == "small" ? 1 : 1 + (R() < 0.3 ? 1 : 0) + (R() < 0.1 ? 1 : 0);"""),
],
os.path.join(G, r"logic\Content\Enemies.cs"): [
("""            Health = 380, Speed = 2.6, Damage = 10, Radius = 0.75, Mass = 4, Xp = 40, Resists = Undead, Behavior = Behavior.Ranged,
            Ranged = new() { Range = 11, Cooldown = 2.6, Speed = 12, School = School.Physical, Count = 5, Spread = 0.2, Art = "bolt_bone" },""",
"""            // (Measured: 52 s to kill, 126 at the slowest; a kiter that long is a chase, not a fight.)
            Health = 300, Speed = 2.4, Damage = 10, Radius = 0.75, Mass = 4, Xp = 40, Resists = Undead, Behavior = Behavior.Ranged,
            Ranged = new() { Range = 11, Cooldown = 2.6, Speed = 12, School = School.Physical, Count = 5, Spread = 0.2, Art = "bolt_bone" },"""),
("""            Health = 620, Speed = 2.4, Damage = 16, Radius = 0.95, Mass = 8, Xp = 40, Resists = Undead, Behavior = Behavior.Guard,
            Guard = new(1.6, 0.75),""",
"""            // (Measured: 49 s, 123 at the slowest, behind a three-quarter shield: now three fifths, as a champion's.)
            Health = 560, Speed = 2.4, Damage = 16, Radius = 0.95, Mass = 8, Xp = 40, Resists = Undead, Behavior = Behavior.Guard,
            Guard = new(1.6, 0.6),"""),
],
}
