import os
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot\tests"
FILES = {
os.path.join(ROOT, "EncounterTests.cs"): [
("""        var far = One(b, "wolf", -20, 0);
        string? word = null;""",
"""        var far = One(b, "wolf", -20, 0);
        // (Held where it stands, out of the howl's reach.)
        far.Speed = 0;
        string? word = null;"""),
("""        var b = Bare(39);
        var d = One(b, "drowned", 0.9);
        for (double t = 0; t < 3 && b.Player.SlowT <= 0; t += 1 / 60.0) b.Tick(1 / 60.0, 0, 0);
        Assert.True(b.Player.SlowT > 0);""",
"""        var b = Bare(39);
        var d = One(b, "drowned", 0.9);
        // Its blow chills; and its wet ground, though it hurts, buys no moment of grace from the blow.
        bool bitten = false;
        for (double t = 0; t < 3 && !bitten; t += 1 / 60.0)
        {
            b.Tick(1 / 60.0, 0, 0);
            bitten = b.Events.Drain().OfType<Ev.PlayerHit>().Any(h => h.Source == "Drowned" && h.Amount > 0);
        }
        Assert.True(bitten);
        Assert.True(b.Player.SlowT > 0);"""),
],
}
