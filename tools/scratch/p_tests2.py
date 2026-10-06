import os
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot\tests"
FILES = {
os.path.join(ROOT, "EncounterTests.cs"): [
("""        string? word = null;
        Play(b, 10, _ =>
        {
            foreach (var ev in b.Events.Pending.OfType<Ev.Telegraph>()) if (ev.Label != null) word = ev.Label;
            if (near.HasteT > 0) return;
        });""",
"""        string? word = null;
        for (double t = 0; t < 10; t += 1 / 60.0)
        {
            b.Player.Hp = b.MaxHp;
            b.Tick(1 / 60.0, 0, 0);
            foreach (var ev in b.Events.Drain().OfType<Ev.Telegraph>()) if (ev.Label != null) word = ev.Label;
        }"""),
("""        var b = BattleTests.Arena(39);
        var d = One(b, "drowned", 0.9);""",
"""        var b = Bare(39);
        var d = One(b, "drowned", 0.9);"""),
],
}
