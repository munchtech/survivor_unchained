"""Journey's rest section: the skips keep the clock, and the overnight talk is shared (one-off edit)."""
import sys

path = sys.argv[1]
s = open(path, encoding="utf-8").read()
old_night = '''    /// <summary>Wait for nightfall.</summary>
    public void Nightfall() => World.Time = TimeOfDay.Night;
'''
new_night = '''    /// <summary>Wait for nightfall: a shortcut through what is left of the day (the clock would
    /// bring it anyway).</summary>
    public void Nightfall()
    {
        World.Time = TimeOfDay.Night;
        World.Clock = DayClock.NightAt;
    }
'''
assert old_night in s
s = s.replace(old_night, new_night, 1)

old_sleep_tail = '''        var report = Simulation.AdvanceDay(Ctx, rng);
        World.Time = TimeOfDay.Day;
        Expedition = null;
        if (b != null) b.Player.Hp = b.MaxHp;
        var lines = new List<string>(report.Lines);
        // The talk of the town: who heard what, overnight.
        var short_ = new Dictionary<string, string> { ["holloway"] = "Holloway", ["harlan"] = "Harlan", ["pell"] = "Pell", ["keegan"] = "Keegan" };
        var byEvent = new List<(string Event, List<string> Who)>();
        foreach (var h in report.Heard)
        {
            if (Lore.Person(h.Npc) == null) continue;
            var entry = byEvent.FirstOrDefault(x => x.Event == h.Event);
            if (entry.Who == null) byEvent.Add(entry = (h.Event, new()));
            entry.Who.Add(short_.GetValueOrDefault(h.Npc) ?? Lore.NameOf(h.Npc));
        }
        foreach (var (id, who) in byEvent.Take(2))
        {
            var ev = World.History.FirstOrDefault(h => h.Id == id);
            if (ev == null) continue;
            var names = who.Count == 1 ? who[0] : $"{string.Join(", ", who.Take(who.Count - 1))} and {who[^1]}";
            lines.Add($"By breakfast, {names} had heard that you {ev.Text}.");
        }
        if (Flask() is { } flask) lines.Add(flask);
        Crafting.Morning(World);
        if (lines.Count == 0) lines.Add("A quiet night. Rook's bread is hot, and nobody died.");
        OnTouch();
        return lines;
    }
'''
new_sleep_tail = '''        var report = Simulation.AdvanceDay(Ctx, rng);
        World.Time = TimeOfDay.Day;
        World.Clock = DayClock.DayAt;
        Expedition = null;
        if (b != null) b.Player.Hp = b.MaxHp;
        var lines = Overnight(report, atInn: true);
        if (lines.Count == 0) lines.Add("A quiet night. Rook's bread is hot, and nobody died.");
        OnTouch();
        return lines;
    }

    /// <summary>What the night brought, as lines: the world's own news, the talk of the town (who
    /// heard what), and, for a night spent at the inn, Wenna's flask filled; and the smith's morning.</summary>
    List<string> Overnight(DayReport report, bool atInn)
    {
        var lines = new List<string>(report.Lines);
        var short_ = new Dictionary<string, string> { ["holloway"] = "Holloway", ["harlan"] = "Harlan", ["pell"] = "Pell", ["keegan"] = "Keegan" };
        var byEvent = new List<(string Event, List<string> Who)>();
        foreach (var h in report.Heard)
        {
            if (Lore.Person(h.Npc) == null) continue;
            var entry = byEvent.FirstOrDefault(x => x.Event == h.Event);
            if (entry.Who == null) byEvent.Add(entry = (h.Event, new()));
            entry.Who.Add(short_.GetValueOrDefault(h.Npc) ?? Lore.NameOf(h.Npc));
        }
        foreach (var (id, who) in byEvent.Take(2))
        {
            var ev = World.History.FirstOrDefault(h => h.Id == id);
            if (ev == null) continue;
            var names = who.Count == 1 ? who[0] : $"{string.Join(", ", who.Take(who.Count - 1))} and {who[^1]}";
            lines.Add($"By breakfast, {names} had heard that you {ev.Text}.");
        }
        if (atInn && Flask() is { } flask) lines.Add(flask);
        Crafting.Morning(World);
        return lines;
    }
'''
assert old_sleep_tail in s
s = s.replace(old_sleep_tail, new_sleep_tail, 1)
open(path, "w", encoding="utf-8", newline="").write(s)
print("ok")
