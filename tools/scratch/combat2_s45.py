W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Sim/LevelUp.cs": [
        ("""public enum ChestItemKind { Evolution, Rank, Passive, Gold }""",
         """public enum ChestItemKind { Evolution, Rank, Passive, Gold, Gear }"""),
    ],
    W + "logic/Play/Zones/MapRun.cs": [
        # The breath before the ruler: no packs on the last way.
        ("""        foreach (var s in map.Packs)
        {
            var a = map.Areas[Math.Clamp(s.Area, 0, map.Areas.Count - 1)];
            bool clearing = (s.X - a.X) * (s.X - a.X) + (s.Z - a.Z) * (s.Z - a.Z) < a.R * a.R;
            if (rng.Next() >= (clearing ? 0.75 : 0.35)) continue;""",
         """        foreach (var s in map.Packs)
        {
            var a = map.Areas[Math.Clamp(s.Area, 0, map.Areas.Count - 1)];
            bool clearing = (s.X - a.X) * (s.X - a.X) + (s.Z - a.Z) * (s.Z - a.Z) < a.R * a.R;
            // A breath before the ruler: the last way to its clearing is left empty.
            if (!clearing && s.Area == map.Boss.Index - 1) continue;
            if (rng.Next() >= (clearing ? ClearingKeep : WayKeep)) continue;"""),
        ("""    public const int FallsAllowed = 3;""",
         """    public const int FallsAllowed = 3;
    /// <summary>The share of MapGen's pack spots set: in clearings, and along the ways (a pack about
    /// every 14 s: the experience lead's density, the ARPG's clear-speed fantasy).</summary>
    public static double ClearingKeep = 0.8, WayKeep = 0.5;"""),
        # The ruler's sign at its clearing's edge, as the way's last stretch begins.
        ("""        // The ruler, in its clearing.
        var bc = map.Boss;""",
         """        // The ruler's sign at its clearing's edge, as the last stretch of way begins.
        var bc = map.Boss;
        if (!signed && Near(p, bc.X, bc.Z, bc.R + 34)) Sign(p);
        if (eventAt >= 0) Event();
        // The ruler, in its clearing."""),
        ("""    /* -------------------------------------------------------- the altars -- */""",
         """    /* -------------------------------------------------- the ruler's sign -- */

    bool signed;

    /// <summary>The night's run-up, small: a sound and a light at the edge of the ruler's clearing,
    /// on the side the way comes in, so the survivor walks the last stretch toward it.</summary>
    void Sign(PlayerState p)
    {
        signed = true;
        var bc = map.Boss;
        double a = Math.Atan2(p.Z - bc.Z, p.X - bc.X);
        double x = bc.X + Math.Cos(a) * (bc.R - 2), z = bc.Z + Math.Sin(a) * (bc.R - 2);
        G.Look.AddLight(x, 2.5, z, "#ff6a3a", 3.2, 16, 0.25, 0.12, "#ff8a5a");
        string sign = people.Id switch
        {
            "pack" => "A howl from the far side of the trees; the wolves lift their heads.",
            "dead" => "A drum, slow, under everything; the dead turn to face it.",
            "lamplings" => "A blasting thump, and the ground shivers; picks rattle somewhere.",
            "kerchiefs" => "A whistle, three notes, and an answering whistle.",
            _ => "Something is waiting.",
        };
        B!.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z + 3, Text = sign });
        G.Announce(new Announcement($"{people.BossName} waits", "At the end of the way", "danger", 2.6));
    }

    /* -------------------------------------------------------- the altars -- */"""),
        # The event: the people's question, 45-60 s, ending in a strongbox.
        ("""        if (eventLit) return;
        eventLit = true;
        var p = B!.Player;
        B.Charges.Spikes = true;
        B.Charges.Spike(B, quiet: false);
        int n = (int)Math.Round((10 + Chart.Tier) * Chart.PackSize);
        string def = PickKind(people);
        var ring = new List<(double X, double Z)>();
        for (int i = 0; i < n; i++)
        {
            double ang = (double)i / n * Math.Tau, rr = 11 + R() * 2;
            double x = p.X + Math.Cos(ang) * rr, z = p.Z + Math.Sin(ang) * rr;
            if (map.CanStand(x, z) && !B.Collision.Blocked(x, z, 0.6)) ring.Add((x, z));
        }
        foreach (var (x, z) in ring)
            B.Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Circle, X = x, Z = z, Radius = 0.9, Duration = 1.3, Hostile = true, Kind = TelegraphKind.Ground });
        G.After(1.3, () =>
        {
            if (B == null || over) return;
            foreach (var (x, z) in ring)
                if (Put(def, x, z, (x, z)) is { } e) B.Rouse(e);
            double ang = R() * Math.Tau;
            if (Put(people.Champion, p.X + Math.Cos(ang) * 14, p.Z + Math.Sin(ang) * 14, (p.X, p.Z), elite: true, levelUp: 1) is { } c)
            {
                c.MaxHp = c.Hp = c.MaxHp * 1.5;
                Sign(c, people, 1 + Chart.Tier / 6);
                carriers[c.Id] = 2;
                B.Rouse(c);
            }
            G.After(12, () => { if (B != null) B.Charges.Spikes = false; });
        });
    }""",
         """        // The first lit is the map's event; with the atlas's "twice lit", a later one may be too.
        if (eventLit && !(eventsLit < 2 && R() < Atlas.Rank(G.Journey.World, Atlas.TwiceLit) / 3.0)) return;
        eventLit = true;
        eventsLit++;
        eventAt = Seconds;
        eventWave = 0;
        eventAltar = a.Area;
        eventFoes.Clear();
        B!.Charges.Spikes = true;
        G.Announce(new Announcement(EventName, "Hold the altar", "danger", 3, people.Name));
    }

    /* The map's event (the experience lead's shape): the people's own question, asked three times
     * over about fifty seconds at the lit altar, its tell first; then, its last asker down (or a
     * minute gone), a strongbox at the altar: three to five things at the map's level, and a chart
     * now and then. */
    double eventAt = -1;
    int eventWave, eventsLit;
    Area? eventAltar;
    readonly List<(Enemy E, double Seed)> eventFoes = new();

    string EventName => people.Id switch
    {
        "pack" => "The Hunt", "dead" => "The Ford Rises", "lamplings" => "The Dig Opens", "kerchiefs" => "The Ambush", _ => "The Question",
    };

    void Event()
    {
        if (B == null || eventAltar == null) return;
        double t = Seconds - eventAt;
        if (eventWave < 3 && t >= eventWave * 17)
        {
            Wave(eventWave);
            eventWave++;
        }
        bool clear = eventFoes.All(f => !f.E.Alive || f.E.Seed != f.Seed || f.E.State == EnemyState.Dying);
        if ((eventWave >= 3 && t >= 45 && clear) || t >= 60)
        {
            var at = eventAltar;
            eventAt = -1;
            B.Charges.Spikes = false;
            B.SpawnPickup(PickupKind.Chest, at.X, at.Z, 1, "strongbox");
            B.Events.Emit(new Ev.Shake { Amount = 0.3 });
            G.Announce(new Announcement("A strongbox", "The altar gives up what it kept", "reward", 2.6));
        }
    }

    /// <summary>One asking of the people's question: a ring of them up round her, then a line from
    /// one side with a champion leading it, then the ring again with more.</summary>
    void Wave(int k)
    {
        var p = B!.Player;
        string def = PickKind(people);
        int n = (int)Math.Round((8 + Chart.Tier + 3 * k) * Chart.PackSize);
        B.Charges.Spike(B, quiet: false);
        var at = new List<(double X, double Z)>();
        double a0 = R() * Math.Tau;
        for (int i = 0; i < n; i++)
        {
            double x, z;
            if (k == 1)
            {
                // A line across one side.
                double sx = -Math.Sin(a0), sz = Math.Cos(a0), off = (i - (n - 1) / 2.0) * 1.6;
                x = p.X + Math.Cos(a0) * 14 + sx * off; z = p.Z + Math.Sin(a0) * 14 + sz * off;
            }
            else
            {
                double ang = (double)i / n * Math.Tau + R() * 0.2, rr = 10 + R() * 3;
                x = p.X + Math.Cos(ang) * rr; z = p.Z + Math.Sin(ang) * rr;
            }
            if (!map.CanStand(x, z) || B.Collision.Blocked(x, z, 0.6)) continue;
            at.Add((x, z));
            B.Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Circle, X = x, Z = z, Radius = 0.9, Duration = 1.3, Hostile = true, Kind = TelegraphKind.Ground });
        }
        G.After(1.3, () =>
        {
            if (B == null || over) return;
            foreach (var (x, z) in at)
                if (Put(def, x, z, (x, z)) is { } e) { B.Rouse(e); eventFoes.Add((e, e.Seed)); }
            if (k != 1) return;
            if (Put(people.Champion, p.X + Math.Cos(a0) * 15, p.Z + Math.Sin(a0) * 15, (p.X, p.Z), elite: true, levelUp: 1) is { } c)
            {
                c.MaxHp = c.Hp = c.MaxHp * 1.5;
                Sign(c, people, 1 + Chart.Tier / 6);
                carriers[c.Id] = 2;
                B.Rouse(c);
                eventFoes.Add((c, c.Seed));
            }
        });
    }"""),
        # The strongbox, opened.
        ("""    bool OnPickup(Pickup p)
    {
        if (p.Kind == PickupKind.Material && p.Ref != null) picked[p.Ref] = picked.GetValueOrDefault(p.Ref) + (int)Math.Max(1, Math.Round(p.Value));
        return true;
    }""",
         """    int opened;

    bool OnPickup(Pickup p)
    {
        if (p.Kind == PickupKind.Material && p.Ref != null) picked[p.Ref] = picked.GetValueOrDefault(p.Ref) + (int)Math.Max(1, Math.Round(p.Value));
        if (p.Kind == PickupKind.Chest && p.Ref == "strongbox" && B != null) Strongbox(p.X, p.Z);
        return true;
    }

    /// <summary>The event's strongbox: three to five things at the map's level (the atlas's "the
    /// keeper's due" adds), now and then a chart; flung out round it, and its opening shown.</summary>
    void Strongbox(double x, double z)
    {
        var loot = new List<Loot>();
        int n = 3 + (R() < 0.5 * Chart.Quantity ? 1 : 0) + (R() < 0.25 * Chart.Quantity ? 1 : 0) + Atlas.Rank(G.Journey.World, Atlas.KeepersDue);
        for (int k = 0; k < n; k++) loot.Add(Gear(1.3, 1));
        if (R() < 0.25 * Chart.Quantity) loot.Add(new Loot(PickupKind.Item, Charts.Ref(Charts.Roll(rng, Chart.Tier, Chart.People, Chart.RarityBonus)), 1, true, 2));
        var shown = new List<ChestItem>();
        foreach (var l in loot)
        {
            double a = R() * Math.Tau, d = 1.2 + R() * 1.6;
            if (B!.SpawnPickup(l.Kind, x + Math.Cos(a) * d, z + Math.Sin(a) * d, l.Value, l.Ref) is { } pk)
            {
                pk.Persistent = true;
                if (l.Rarity is { } r) pk.Tier = r;
                pk.Lean = l.Lean;
            }
            if (l.Ref == null) continue;
            var chart = Charts.FromRef(l.Ref);
            var def = Items.Find(chart != null ? Charts.Item : l.Ref);
            shown.Add(new ChestItem(ChestItemKind.Gear, def?.Id ?? l.Ref, chart != null ? Charts.Title(chart) : def?.Name ?? l.Ref, def?.Icon ?? "chest", 0, 0,
                (Rarity)Math.Clamp(l.Rarity ?? 0, 0, 4), null, null));
        }
        opened++;
        G.Chest(new ChestOpened(x, z, opened, shown, "The strongbox", opened));
    }"""),
    ],
}
