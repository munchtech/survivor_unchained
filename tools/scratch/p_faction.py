import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot\logic"
FILES = {
os.path.join(G, r"Sim\Events.cs"): [
("""        /// <summary>Who marked it, where it stood (its name is said over it, not over the survivor).</summary>
        public double? ByX, ByZ;""",
"""        /// <summary>Who marked it, where it stood (its name is said over it, not over the survivor).</summary>
        public double? ByX, ByZ;
        /// <summary>The people whose mark it is (a rally's ring in its colour, a call, a slam).</summary>
        public Faction? Faction;"""),
],
os.path.join(G, r"Sim\Ai.cs"): [
("""                Hostile = false, Label = aura.Word.Length > 0 ? aura.Word : null, ByX = e.X, ByZ = e.Z,
            });""",
"""                Hostile = false, Label = aura.Word.Length > 0 ? aura.Word : null, ByX = e.X, ByZ = e.Z, Faction = e.Faction,
            });"""),
("""                b.Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Circle, X = x, Z = z, Radius = 0.8, Duration = su.Cast, Hostile = true, Kind = TelegraphKind.Ground });""",
"""                b.Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Circle, X = x, Z = z, Radius = 0.8, Duration = su.Cast, Hostile = true, Kind = TelegraphKind.Ground, Faction = e.Faction });"""),
("""                Label = sl.Word.Length > 0 ? sl.Word : null, ByX = e.X, ByZ = e.Z,
            });""",
"""                Label = sl.Word.Length > 0 ? sl.Word : null, ByX = e.X, ByZ = e.Z, Faction = e.Faction,
            });"""),
],
}
