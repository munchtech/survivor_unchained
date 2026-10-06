import os
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot\logic\Play\Zones"
FILES = {
os.path.join(ROOT, "ArenaRun.cs"): [
("""    /// <summary>What the night calls the boss's coming, and its middle, in words.</summary>
    string HourName => Spec.Minutes switch { 30 => "the half hour", 20 => "the twentieth minute", 15 => "the quarter hour", _ => "the boss's hour" };
    string MiddleName => Spec.Minutes switch { 30 => "The fifteenth minute", 20 => "The tenth minute", _ => "Midnight" };
    static string Cap(string s) => s.Length == 0 ? s : char.ToUpperInvariant(s[0]) + s[1..];""",
"""    /// <summary>What the night calls the boss's coming and its middle: a table's by its half hour,
    /// a story's in the story lead's words.</summary>
    string Nears => Spec.Story ? "It is nearly here" : "The half hour nears";
    string Comes => Spec.Story ? "The night's end" : "The half hour";
    string Past => Spec.Story ? "past its coming" : "past the half hour";
    string Middle => Spec.Story ? "Halfway through the dark" : "The fifteenth minute";
    static string Cap(string s) => s.Length == 0 ? s : char.ToUpperInvariant(s[0]) + s[1..];"""),
("""            G.Announce(new Announcement(MiddleName, "A great blessing", "reward", 2.6));""",
"""            G.Announce(new Announcement(Middle, "A great blessing", "reward", 2.6));"""),
("""            : new Announcement($"{Cap(HourName)} nears", "It comes from where the sign was", "danger", 2.6));""",
"""            : new Announcement(Nears, "It comes from where the sign was", "danger", 2.6));"""),
("""            again ? (returns == 1 ? "Again" : $"Again, the {Ordinal(returns + 1)} time") : Cap(HourName)));""",
"""            again ? (returns == 1 ? "Again" : $"Again, the {Ordinal(returns + 1)} time") : Comes));"""),
("""            Hint = () => $"Won. Or stay: {Clock(Seconds - End)} past {HourName}",""",
"""            Hint = () => Spec.Story ? "Won" : $"Won. Or stay: {Clock(Seconds - End)} {Past}","""),
("""            steps.Add(new Step($"Stay as long as you dare: {Clock(Seconds - End)} past {HourName}", Optional: true));""",
"""            if (!Spec.Story) steps.Add(new Step($"Stay as long as you dare: {Clock(Seconds - End)} {Past}", Optional: true));"""),
("""        if (won) LongNight();""",
"""        // A story's night ends on its beat: no long night after it (the experience lead's loop; the
        // bible's pacing). The long night is the table's, where staying is the point.
        if (won && !Spec.Story) LongNight();"""),
("""        // The horde kept up: groups from out of sight, all round.
        spawnT -= dt;
        if (spawnT <= 0 && alive < Target() && !bossUp)""",
"""        // The horde kept up: groups from out of sight, all round (a story's night, won, is over).
        spawnT -= dt;
        if (won && Spec.Story) { }
        else if (spawnT <= 0 && alive < Target() && !bossUp)"""),
("""        eventT -= dt;
        if (eventT <= 0 && !bossUp && won)""",
"""        eventT -= dt;
        if (eventT <= 0 && !bossUp && won && !Spec.Story)"""),
("""        Arenas.Won(G.Journey, Spec);""",
"""        Arenas.Won(G.Journey, Spec);
        // A story's night is over at its boss's fall: its people draw back into the dark.
        if (Spec.Story) { bossShare = 0; MakeWay(0); }"""),
],
}
