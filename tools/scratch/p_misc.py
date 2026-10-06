import os
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot"
FILES = {
os.path.join(ROOT, r"logic\Play\Zones\Verge.cs"): [
("""            Theme = people == "dead" ? "blight" : "wood", Story = true, Boss = boss, BossName = bossName, BossTitle = bossTitle,""",
"""            Theme = people == "dead" ? "blight" : "wood", Story = true, Boss = boss, BossName = bossName, BossTitle = bossTitle,
            // The story's nights are twenty minutes, the table's thirty (the owner: the story is to be
            // two fifths of the game early on): the same night, told quicker (ArenaRun.Minute).
            Minutes = 20,"""),
],
os.path.join(ROOT, r"logic\Arena\Arena.cs"): [
("""    public static double XpFor(ArenaSpec spec, double seconds, bool won) =>
        Math.Round(seconds / 60 * 30 * (1 + 0.3 * (spec.Tier - 1)) + (won ? 300 * spec.Tier : 0));""",
"""    public static double XpFor(ArenaSpec spec, double seconds, bool won)
    {
        // A shorter night is the same night told quicker: its minutes before the boss count as a
        // table night's would, so a story night teaches as much (past the boss, real minutes).
        double end = spec.Minutes * 60, night = Math.Min(seconds, end) * 30 / spec.Minutes + Math.Max(0, seconds - end);
        return Math.Round(night / 60 * 30 * (1 + 0.3 * (spec.Tier - 1)) + (won ? 300 * spec.Tier : 0));
    }"""),
],
os.path.join(ROOT, r"logic\Content\Enemies.cs"): [
("""            if (d.Raise != null) Visit(d.Raise.Into);
            if (d.Split != null) Visit(d.Split.Into);""",
"""            if (d.Raise != null) Visit(d.Raise.Into);
            if (d.Split != null) Visit(d.Split.Into);
            if (d.Summon != null) Visit(d.Summon.Into);"""),
],
os.path.join(ROOT, r"src\Actors\CrowdView.cs"): [
("""        var (tint, glow) = Visuals.Tint(e.Def.Visual);
        if (e.Elite) { glow = Math.Max(glow, 0.05f); tint *= new Color(1.08f, 1.02f, 0.92f); }""",
"""        var (tint, glow) = Visuals.Tint(e.Def.Visual);
        // A kind's own colour on a shared rig, and a champion's Signs (combat's, agreed with animation).
        if (e.Def.Tint is var (tr, tg, tb)) tint *= new Color((float)tr, (float)tg, (float)tb);
        if (e.Def.Glow is { } dg) glow = Math.Max(glow, (float)dg);
        if (e.Elite) { glow = Math.Max(glow, 0.05f); tint *= new Color(1.08f, 1.02f, 0.92f); }"""),
("""        if (!laidOut.Add((e.Id, e.Seed))) return;
        var (tint, glow) = Visuals.Tint(e.Def.Visual);""",
"""        if (!laidOut.Add((e.Id, e.Seed))) return;
        var (tint, glow) = Visuals.Tint(e.Def.Visual);
        if (e.Def.Tint is var (tr, tg, tb)) tint *= new Color((float)tr, (float)tg, (float)tb);
        if (e.Def.Glow is { } dg) glow = Math.Max(glow, (float)dg);"""),
],
}
