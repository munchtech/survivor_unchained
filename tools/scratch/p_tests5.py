import os
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot\tests"
FILES = {
os.path.join(ROOT, "ArenaTests.cs"): [
("""        for (double t = 0; t < 90 && !s.Host.Announced.Any(a => a.Title == "Old Tusk"); t += 1)
        {
            Run(s, 1);
            boarBefore |= s.B.Enemies.Living().Any(e => e.Def.Id == "boar");
        }""",
"""        for (double t = 0; t < 90 && !s.Host.Announced.Any(a => a.Title == "Old Tusk"); t += 1)
        {
            Run(s, 1);
            // (He comes with a few of his own beside him: those count from his coming.)
            if (!s.Host.Announced.Any(a => a.Title == "Old Tusk")) boarBefore |= s.B.Enemies.Living().Any(e => e.Def.Id == "boar");
        }"""),
],
}
