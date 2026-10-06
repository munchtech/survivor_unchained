"""The story lead's final words for the clock, the waking on Chid's bench, rises and straight on (run from godot/)."""
p = "logic/Play/Journey.Day.cs"
s = open(p, encoding="utf-8").read()
start = s.index("    /// <summary>The story's words for the clock's moments (the story lead's drafts).</summary>")
end = s.index("    /// <summary>The clock has started:")
new = '''    /// <summary>The story's words for the clock's moments (the story lead's).</summary>
    public static class DayLines
    {
        /// <summary>The town's own evening call, at dusk (the gate guard's).</summary>
        public const string Dusk = "Lamps are lit. Stay where they reach.";
        /// <summary>At dusk, after the call: the night's fight named, by StoryFights id ("" when none is called).</summary>
        public static readonly Dictionary<string, string> Tonight = new()
        {
            ["hollow"] = "Out past the lamps, the Pack has stopped howling.",
            ["roost"] = "Up the Old Road the Kerchiefs' fires are lit all along the ravine, the way a town lights its windows.",
            ["dig"] = "On the hill over the Dig, the lamps are all moving the same way.",
            ["vault"] = "Out in the Verge, the sealed door has woken. Its light is violet.",
            [""] = "Out in the Verge, the ember is coming up.",
        };
        /// <summary>Getting up in a story fight, the first time ever (the prologue's own words).</summary>
        public const string Rise = "You get up.";
        /// <summary>Getting up in a later fight.</summary>
        public const string RiseAgain = "You get up. It takes less than it did.";
        /// <summary>Half the night gone.</summary>
        public const string Nudge = "Half the night is gone. Up on the Toll Tower, the one lamp is still lit.";
        /// <summary>A night left alone, passing.</summary>
        public const string NightOut = "You see the night out on your feet. At first light the warmth comes back into your hands.";
        /// <summary>Answering a second fight the same night.</summary>
        public const string StraightOn = "You do not go back to the lamps. You go on.";
        /// <summary>The held key's words, and the card's for the night's other fights.</summary>
        public const string Answer = "Answer the night", AlsoOut = "Also out tonight:";
    }

    /// <summary>A rise in a story fight: its words, the first one ever the prologue's, every one
    /// after it in a later fight a little less (counted in story.rises).</summary>
    public string RiseLine()
    {
        double n = World.Fact("story.rises").Number;
        World.Facts["story.rises"] = n + 1;
        return n < 1 ? DayLines.Rise : DayLines.RiseAgain;
    }

    /// <summary>She has fought tonight already (back from a fight into this same night).</summary>
    public bool FoughtTonight => World.Time == TimeOfDay.Night && World.Fact("night.fought").Number == World.Day;

'''
s = s[:start] + new + s[end:]

old = '''    /// <summary>A story fight lost (the owner: "having to die for a time"): the night is lost, and
    /// she wakes in town the next morning, carried home, healed by the bed she was put in, with a
    /// day to make ready before she tries again. What the night brought, as lines.</summary>
    public List<string> WakeAfterLoss(Battle? b, Func<double> rng)
    {
        var report = Simulation.AdvanceDay(Ctx, rng);
        World.Time = TimeOfDay.Dawn;
        World.Clock = 0;
        Expedition = null;
        if (b != null) b.Player.Hp = b.MaxHp;
        var lines = new List<string> { DayLines.Carried };
        lines.AddRange(Overnight(report, atInn: true));
        OnTouch();
        return lines;
    }'''
new = '''    /// <summary>A story fight lost (the owner: "having to die for a time"): the night is lost, and
    /// she wakes on Chid's bench in the shrine the next morning, carried home in the dark, with a
    /// day to make ready before she tries again. It costs the night and nothing else: no wound
    /// comes with her. Chid's conversation tells the waking (CarriedHome); what the night brought
    /// in the town, as lines, comes after it.</summary>
    public List<string> WakeAfterLoss(Arena.ArenaSpec spec, Battle? b, Func<double> rng)
    {
        var report = Simulation.AdvanceDay(Ctx, rng);
        World.Time = TimeOfDay.Dawn;
        World.Clock = 0;
        Expedition = null;
        if (b != null) b.Player.Hp = b.MaxHp;
        CarriedHome(spec);
        var lines = Overnight(report, atInn: false);
        OnTouch();
        return lines;
    }'''
assert old in s
s = s.replace(old, new, 1)

old = '''    public void BackFromFight()
    {
        if (World.Time != TimeOfDay.Night) return;'''
new = '''    public void BackFromFight()
    {
        if (World.Time != TimeOfDay.Night) return;
        World.Facts["night.fought"] = World.Day;'''
assert old in s
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "logic/Play/Zones/Waystation.cs"
s = open(p, encoding="utf-8").read()
old = '''
        // Carried home after a story night lost: she wakes at the Last Lamp's door.
        if (from == "carried") { var inn = Way("inn"); return new(inn.X, inn.Z, 0); }'''
assert old in s
s = s.replace(old, "", 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "src/Game/Game.cs"
s = open(p, encoding="utf-8").read()
old = '''        if (result.WakesInTown)
        {
            // A story night lost (the owner: "having to die for a time"): carried home, she wakes
            // at the inn a day on, with a day to make ready before she tries again.
            var lines = Journey.WakeAfterLoss(null, Rng.NextDouble);
            Travel("waystation", "The Last Lamp", $"Day {World.Day}", null, from: "carried");
            if (leaving) Wait(0.8, () => screens.Close());
            if (leaving) Wait(2.8, () => Morning(lines));
            return;
        }'''
new = '''        if (result.WakesInTown)
        {
            // A story night lost (the owner: "having to die for a time"): carried home in the dark,
            // she wakes on Chid's bench in the shrine a day on, as from any fall, and he tells her
            // what it cost; the town's morning comes after him.
            var lines = Journey.WakeAfterLoss(s, null, Rng.NextDouble);
            Travel("waystation", "The shrine", $"Day {World.Day}", null, from: "death");
            if (leaving) Wait(0.8, () => screens.Close());
            Wait(3.9, () => { afterTalk = () => Morning(lines); Talk("chid"); });
            return;
        }'''
assert old in s
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
