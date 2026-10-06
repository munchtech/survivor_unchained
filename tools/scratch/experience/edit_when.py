"""Morning and afternoon on the zone line (GameHud.ZoneInfo / Clock)."""
p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af2c026d86e1b532b\godot\src\Ui\GameHud.cs'
s = open(p, encoding='utf-8').read()
a = '''    public void ZoneInfo(string name, string? region, int day, TimeOfDay time)
    {
        zoneName.Text = name.ToUpperInvariant();
        foreach (var c in zoneSub.GetChildren()) if (c != dial) c.QueueFree();
        // Where the clock runs, its dial says the time of day; elsewhere a sun or a moon.
        if (!dial.Visible) zoneSub.AddChild(Glyphs.Icon(time == TimeOfDay.Night ? "moon" : "sun", 15, time == TimeOfDay.Night ? Hex("#b8ccff") : Hex("#ffd890")));
        zoneSub.AddChild(Style.Label($"{time}  ·  Day {day}" + (region != null ? $"  ·  {region}" : ""), Style.Ui, 17, Style.Ink with { A = 0.85f }));
    }'''
b = '''    Label? zoneWhen;
    (int Day, string? Region, TimeOfDay Time) zoneAt;
    double? zoneClock;

    public void ZoneInfo(string name, string? region, int day, TimeOfDay time)
    {
        zoneName.Text = name.ToUpperInvariant();
        foreach (var c in zoneSub.GetChildren()) if (c != dial) c.QueueFree();
        // Where the clock runs, its dial says the time of day; elsewhere a sun or a moon.
        if (!dial.Visible) zoneSub.AddChild(Glyphs.Icon(time == TimeOfDay.Night ? "moon" : "sun", 15, time == TimeOfDay.Night ? Hex("#b8ccff") : Hex("#ffd890")));
        zoneAt = (day, region, time);
        zoneWhen = Style.Label(When(), Style.Ui, 17, Style.Ink with { A = 0.85f });
        zoneSub.AddChild(zoneWhen);
    }

    /// <summary>The line under the place's name: the time of day, the day, the region. By day it is
    /// the morning or the afternoon where the clock runs, and daylight where it does not ("Day ·
    /// Day 1" said the one word twice).</summary>
    string When()
    {
        var (day, region, time) = zoneAt;
        const double noon = SurvivorUnchained.World.DayClock.DayAt + SurvivorUnchained.World.DayClock.DayLength / 2;
        string word = time switch
        {
            TimeOfDay.Day when zoneClock is double c => c < noon ? "Morning" : "Afternoon",
            TimeOfDay.Day => "Daylight",
            _ => time.ToString(),
        };
        return $"{word}  ·  Day {day}" + (region != null ? $"  ·  {region}" : "");
    }'''
assert s.count(a) == 1, 'zoneinfo'
s = s.replace(a, b)
a = '''        if (clock is double c) dial.Set(c, running);
    }'''
b = '''        if (clock is double c) dial.Set(c, running);
        // (the morning turns to the afternoon in the line's word as well as on the dial)
        zoneClock = clock;
        if (zoneWhen != null && IsInstanceValid(zoneWhen) && When() is var w && zoneWhen.Text != w) zoneWhen.Text = w;
    }'''
assert s.count(a) == 1, 'clock'
s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
