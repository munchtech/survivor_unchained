"""The dead rise in the Verge at nightfall while she is there (run from godot/)."""
p = "logic/Play/Zones/Verge.cs"
s = open(p, encoding="utf-8").read()
reps = [
("""    /// <summary>The wood's packs, laid out as the survivor comes in: where each
    /// people keeps to, as many as the world has left of them, resting.</summary>
    void PlacePacks()
    {
        if (B == null) return;
        var taken = new List<(double X, double Z)>();""",
"""    /// <summary>The wood's packs, laid out as the survivor comes in: where each
    /// people keeps to, as many as the world has left of them, resting. `deadOnly`: only the
    /// night's dead, rising where she is not (nightfall while she is in the wood).</summary>
    void PlacePacks(bool deadOnly = false)
    {
        if (B == null) return;
        var her = B.Player;
        var taken = new List<(double X, double Z)>();"""),
("""                if (x < -96 || !OpenGround(x, z) || !where(x, z)) continue;""",
"""                if (x < -96 || !OpenGround(x, z) || !where(x, z)) continue;
                if (deadOnly && Dist(x, z, her.X, her.Z) < 32) continue;"""),
("""        bool night = W.Time == TimeOfDay.Night;
        double pop = F("beasts.population").IsNull ? 60 : F("beasts.population").Number;""",
"""        bool night = W.Time == TimeOfDay.Night;
        deadUp |= night;
        if (deadOnly) { RaiseTheDead(); return; }
        double pop = F("beasts.population").IsNull ? 60 : F("beasts.population").Number;"""),
("""        // After dark the dead are up, thickest round the vault.
        if (night)
        {
            var vault = V("vault");
            for (int k = 0; k < 5; k++)
                if (Spot((x, z) => k < 2 ? Dist(x, z, vault.X, vault.Z) < 50 : true) is { } at)
                    Pack(k % 3 == 2 ? "risen_warrior" : "risen", 4 + (int)(R() * 3), at, SpawnStyle.Rise, mix: "risen_archer", mixK: 0.25);
        }
    }""",
"""        if (night) RaiseTheDead();

        // After dark the dead are up, thickest round the vault.
        void RaiseTheDead()
        {
            var vault = V("vault");
            for (int k = 0; k < 5; k++)
                if (Spot((x, z) => k < 2 ? Dist(x, z, vault.X, vault.Z) < 50 : true) is { } at)
                    Pack(k % 3 == 2 ? "risen_warrior" : "risen", 4 + (int)(R() * 3), at, SpawnStyle.Rise, mix: "risen_archer", mixK: 0.25);
        }
    }

    /// <summary>The night's dead are up in the wood (laid out by night, or risen at nightfall).</summary>
    bool deadUp;"""),
("""    public override void TimeTurned(TimeOfDay now)
    {
        if (now == TimeOfDay.Night && scars.Count == 0) OpenScars();""",
"""    public override void TimeTurned(TimeOfDay now)
    {
        if (now == TimeOfDay.Night && scars.Count == 0) OpenScars();
        // Nightfall in the wood: the dead get up out of it, away from her.
        if (now == TimeOfDay.Night && !deadUp) { deadUp = true; PlacePacks(deadOnly: true); }"""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
