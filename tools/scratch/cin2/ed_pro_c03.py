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
# C03 in OnWardenDown
('''        Go(Stage.Victory);
        cutT = 0;
        Objective([("Cross at the Low Ford", true, false)]);
    }''',
'''        Go(Stage.Victory);
        cutT = 0;
        Objective([("Cross at the Low Ford", true, false)]);
        // C03 (docs/cinematics/shoot/c03.md), where he fell: he kneels where he
        // is, facing south, and she is put 4 m before him on the cut after the
        // blow. What it sets is set at the hand-back, so a skip sets it too.
        var marks = new Dictionary<string, double[]> { ["w"] = [e.X, e.Z, 0], ["her"] = [e.X, e.Z + 4, Math.PI] };
        if (G.Cinematic("c03", HeartGone, marks)) { victoryByCine = true; wardenInCine = true; }
    }

    bool victoryByCine;

    /// <summary>C03's events: Grimtunnel coming up under her hand, and going down with the heart.</summary>
    void GrimUp()
    {
        if (B == null) return;
        grim = B.Enemies.Living().FirstOrDefault(x => x.Tag == "grim");
        if (grim == null) return;
        grim.State = EnemyState.Surfacing; grim.StateT = 0.55;
        grim.Facing = Math.Atan2(B.Player.Z - grim.Z, B.Player.X - grim.X);
        B.Events.Emit(new Ev.Spawn { Enemy = grim.Id, X = grim.X, Z = grim.Z, Def = "grimtunnel", Style = SpawnStyle.Burrow });
    }

    void GrimDown()
    {
        if (B == null || (grim ??= B.Enemies.Living().FirstOrDefault(x => x.Tag == "grim")) is not { Alive: true } g) return;
        g.State = EnemyState.Burrowed;
        B.Events.Emit(new Ev.Spawn { Enemy = g.Id, X = g.X, Z = g.Z, Def = "grimtunnel", Style = SpawnStyle.Burrow });
        B.Events.Emit(new Ev.Shake { Amount = 0.4 });
    }

    /// <summary>C03 handed back (or skipped): the heart is gone, and the dawn is coming.</summary>
    void HeartGone()
    {
        wardenInCine = false;
        GrimDown();
        if (grim != null) { if (grim.Alive) B?.Enemies.Release(grim); grim = null; }
        shown.Add("grimGone");
        Taken();
        // The cinematic began the dawn (a fifth of the way); the road holds there until C04 finishes it.
        dawnK = 0.287;
        Dawnbreak();
    }'''),
# RunVictory skips when the cinematic plays; its end factored out
('''    void RunVictory(double dt)
    {
        if (B == null) return;
        cutT += dt;''',
'''    void RunVictory(double dt)
    {
        if (B == null || victoryByCine) return;
        cutT += dt;'''),
('''            grim = null;
            shown.Add("grimGone");
            G.Apply("""
                [
                  { "learn": "grimtunnel", "text": "You have seen Grimtunnel. The lamplings are digging for something." },
                  { "history": { "id": "ford_warden_slain", "text": "put down the Ford-Warden at the Low Ford", "tags": ["deed", "undead"], "spread": 2, "sentiment": { "respect": 10 } } },
                  { "history": { "id": "core_stolen", "text": "let a lampling steal the Warden's heart", "tags": ["lampling"], "spread": 1 } },
                  { "give": "grimtunnels_lamp" }
                ]
                """);
            G.Toast(new Toast(ToastKind.Lore, "Grimtunnel took the Warden's heart", "They went down, not away. In the churned mud where he went: a lamp on a snapped strap, still warm. His.", Life: 8));
        }
        if (cutT > 13)
        {
            G.Showcase(null);
            G.Capture(false);
            Go(Stage.Dawn);
            dawnK = 0;
            B.Collision.RemoveTagged("gate");
            G.Say("Grey light, then gold. Up the road, the Waystation's gate is opening.", null, 6);
            Objective([("Walk up the road to the Waystation", false, false)]);
            W.Time = TimeOfDay.Dawn;
        }
    }''',
'''            grim = null;
            shown.Add("grimGone");
            Taken();
        }
        if (cutT > 13)
        {
            G.Showcase(null);
            G.Capture(false);
            dawnK = 0;
            Dawnbreak();
        }
    }

    /// <summary>What the night's end leaves: the Warden's heart is Grimtunnel's, and you know it.</summary>
    void Taken()
    {
        G.Apply("""
            [
              { "learn": "grimtunnel", "text": "You have seen Grimtunnel. The lamplings are digging for something." },
              { "history": { "id": "ford_warden_slain", "text": "put down the Ford-Warden at the Low Ford", "tags": ["deed", "undead"], "spread": 2, "sentiment": { "respect": 10 } } },
              { "history": { "id": "core_stolen", "text": "let a lampling steal the Warden's heart", "tags": ["lampling"], "spread": 1 } },
              { "give": "grimtunnels_lamp" }
            ]
            """);
        G.Toast(new Toast(ToastKind.Lore, "Grimtunnel took the Warden's heart", "They went down, not away. In the churned mud where he went: a lamp on a snapped strap, still warm. His.", Life: 8));
    }

    /// <summary>The gate opens and the night is over: the walk to the Waystation.</summary>
    void Dawnbreak()
    {
        if (B == null) return;
        Go(Stage.Dawn);
        B.Collision.RemoveTagged("gate");
        G.Say("Grey light, then gold. Up the road, the Waystation's gate is opening.", null, 6);
        Objective([("Walk up the road to the Waystation", false, false)]);
        W.Time = TimeOfDay.Dawn;
    }'''),
# Dawn: C04 A waits for her on the north bank
('''            case Stage.Dawn:
            {
                dawnK = Math.Min(1, dawnK + dt / 10);
                // The sun clears the trees, and the ember goes out.
                if (!doused && dawnK > 0.3) { doused = true; Douse(); }''',
'''            case Stage.Dawn:
            {
                // C04 A (docs/cinematics/shoot/c04a.md): the sun waits for her on the
                // north bank (or 25 s, if she stays to loot the ford), and comes up in it.
                if (!doused && G.CanCinematic("c04a"))
                {
                    if (p.Z < -50 || stageT > 25) FirstLight(p.Z >= -50);
                    break;
                }
                dawnK = Math.Min(1, dawnK + dt / 10);
                // The sun clears the trees, and the ember goes out.
                if (!doused && dawnK > 0.3) { doused = true; Douse(); }'''),
# Douse: the caption only without the cinematic
('''    void Douse()
    {
        if (B == null) return;''',
'''    /// <summary>C04 A: the ember goes out in it (its "douse" event), and the narrator says what Douse's caption did.</summary>
    void FirstLight(bool south)
    {
        doused = true;
        W.Facts["prologue.dawn_south"] = south;
        if (!G.Cinematic("c04a", () => { dawnK = 1; G.SetAtmosphere(Atmospheres.Dawn); if (!dousedByCine) Douse(false); })) { Douse(); return; }
    }

    bool dousedByCine;

    public override void CineEvent(string name)
    {
        switch (name)
        {
            // The cinematic's Warden is on: ours hides until it hands him back.
            case "warden_cine": wardenInCine = true; break;
            case "warden_up": WardenUp(); break;
            case "grim_up": GrimUp(); break;
            case "grim_down": GrimDown(); break;
            case "douse": dousedByCine = true; Douse(false); break;
        }
    }

    void Douse(bool caption = true)
    {
        if (B == null) return;'''),
('''        G.After(1.2, () => G.Say("As the sun clears the trees, the ember goes out of you and back into the ground, and everything it gave you goes with it. What you carry, and what you have learned, are still yours. When the dark comes again, it will burn again, from nothing. You try to call up your mother's face, and find it is not quite where you left it.", null, 11));
        G.After(11.5,''',
'''        if (caption) G.After(1.2, () => G.Say("As the sun clears the trees, the ember goes out of you and back into the ground, and everything it gave you goes with it. What you carry, and what you have learned, are still yours. When the dark comes again, it will burn again, from nothing. You try to call up your mother's face, and find it is not quite where you left it.", null, 11));
        G.After(caption ? 11.5 : 4.5,'''),
# remove the earlier CineEvent (now above)
('''    public override void CineEvent(string name)
    {
        switch (name)
        {
            // The cinematic's Warden is on: ours hides until it hands him back.
            case "warden_cine": wardenInCine = true; break;
            case "warden_up": WardenUp(); break;
        }
    }''', ''),
# Grimtunnel surfacing while the zone is held
('''        if (wardenGone) return;
        if (wardenInCine) { wardenView.Hide(); return; }''',
'''        // C03's Grimtunnel comes up while the zone's director waits: his surfacing is kept here.
        if (victoryByCine && grim is { Alive: true, State: EnemyState.Surfacing } gs) { gs.StateT -= dt; if (gs.StateT <= 0) gs.State = EnemyState.Active; }
        if (wardenGone) return;
        if (wardenInCine) { wardenView.Hide(); return; }'''),
])
print("ok")
