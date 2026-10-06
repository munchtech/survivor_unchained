from ed import sub

sub("logic/Play/Zones/MapRun.cs", [
("""    /// <summary>The event's strongbox: three to five things at the map's level (the atlas's "the
    /// keeper's due" adds), now and then a chart; flung out round it, and its opening shown.</summary>
    void Strongbox(double x, double z)
    {""",
"""    /// <summary>The event's strongbox: three to five things at the map's level (the atlas's "the
    /// keeper's due" adds), now and then a chart; flung out round it, and its opening shown
    /// (told: false spills it unshown, for a whole map cleared at once).</summary>
    void Strongbox(double x, double z, bool told = true)
    {"""),
("""        opened++;
        G.Chest(new ChestOpened(x, z, opened, shown, "The strongbox", opened));
    }
""",
"""        if (!told) return;
        opened++;
        G.Chest(new ChestOpened(x, z, opened, shown, "The strongbox", opened));
    }

    /// <summary>The whole map as a thorough survivor leaves it, at once: every pack and keeper set
    /// down and felled by her hand, the event's strongbox spilled at its altar, the ruler called and
    /// felled, and the gold drawn to her. What a map pays, seen without the walk (--clear T in the
    /// game; probes of the atlas's economy).</summary>
    public void ClearNow()
    {
        if (B == null || over || cleared) return;
        foreach (var k in packs) if (!k.Placed) Place(k);
        foreach (var a in altars) if (!a.Placed) Place(a);
        foreach (var e in B.Enemies.Living().ToList())
            if (e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying) B.KillEnemy(e, true, null);
        foreach (var a in altars) a.Lit = true;
        if (altars.FirstOrDefault() is { } first) { eventLit = true; Strongbox(first.Area.X, first.Area.Z, told: false); }
        if (!bossUp) Ruler(false);
        if (boss is { } b) B.KillEnemy(b, true, null);
        foreach (var p in B.Pickups.Items) if (p.Alive && p.Kind == PickupKind.Gold) p.Pulled = true;
    }
"""),
])
