import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"


def edit(rel, pairs):
    p = os.path.join(G, rel)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old[:70])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)


edit(r"logic\Play\Zones\Prologue.cs", [
('''    bool wardenGone, chestOpened, finished, coreShown, doused;''',
'''    bool wardenGone, chestOpened, finished, coreShown, doused;
    /// <summary>A cinematic is playing the Warden with its own body (C02, C03): ours waits, hidden.</summary>
    bool wardenInCine;'''),
# StartIntro: C02 in place of the showcase and barks
('''        var ford = L("ford");
        ClearAround(ford.X, ford.Z, 30);
        B.WorldRate = 0.001; B.WorldRateT = 1e9;
        G.Showcase((wardenHome.X + 9, G.Look.HeightAt(wardenHome.X, wardenHome.Z) + 7, wardenHome.Z + 15), (wardenHome.X, 0.4, wardenHome.Z));
        G.SetHint(null);
    }''',
'''        var ford = L("ford");
        ClearAround(ford.X, ford.Z, 30);
        B.WorldRate = 0.001; B.WorldRateT = 1e9;
        G.SetHint(null);
        // C02 (docs/cinematics/shoot/c02.md): its last cue spawns him where it
        // leaves him (CineEvent "warden_up"); without it, the captions and barks.
        if (G.Cinematic("c02", () => { if (Now == Stage.Intro) WardenUp(); })) { introByCine = true; return; }
        G.Showcase((wardenHome.X + 9, G.Look.HeightAt(wardenHome.X, wardenHome.Z) + 7, wardenHome.Z + 15), (wardenHome.X, 0.4, wardenHome.Z));
    }

    bool introByCine;

    /// <summary>C02's end: the Warden up and facing her an arm's length off, the fight on.</summary>
    void WardenUp()
    {
        if (B == null || warden != null) return;
        wardenInCine = false;
        var p = B.Player;
        // Where the cinematic leaves him (its mark warden_end), facing her.
        double wx = 3.0, wz = -33.6;
        warden = B.SpawnEnemy("ford_warden", wx, wz, new Battle.SpawnOpts { Level = 1, Tag = "warden" });
        if (warden != null) { warden.Facing = Math.Atan2(p.Z - wz, p.X - wx); ai.Mode = "walk"; ai.T = 0; }
        wardenPos = (wx, wz, Math.PI / 2 - (warden?.Facing ?? 0));
        wardenView.Release();
        Go(Stage.Boss);
        Objective([("Cross at the Low Ford", false, false), ("Put out the lamps", false, true)]);
    }

    public override void CineEvent(string name)
    {
        switch (name)
        {
            // The cinematic's Warden is on: ours hides until it hands him back.
            case "warden_cine": wardenInCine = true; break;
            case "warden_up": WardenUp(); break;
        }
    }'''),
('''    void RunIntro(double dt)
    {
        if (B == null) return;
        cutT += dt;''',
'''    void RunIntro(double dt)
    {
        if (B == null || introByCine) return;
        cutT += dt;'''),
# the zone's view waits while the cinematic has him
('''    public override void Frame(double dt)
    {
        if (wardenGone) return;''',
'''    public override void Frame(double dt)
    {
        if (wardenGone) return;
        if (wardenInCine) { wardenView.Hide(); return; }'''),
])
print("ok")
