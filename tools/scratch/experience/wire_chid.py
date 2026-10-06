"""Chid's waking after a loss, straight on, the night's card (run from godot/)."""
p = "src/Game/GameMenus.cs"
s = open(p, encoding="utf-8").read()
old = """    string? afterTalk;
"""
new = """    string? afterTalk;
    /// <summary>What follows this conversation's end (the town's morning after Chid's waking).</summary>
    Action? talkDone;
"""
assert old in s
s = s.replace(old, new, 1)
old = """        if (afterTalk is string next) { afterTalk = null; Open(next); }
    }"""
new = """        if (afterTalk is string next) { afterTalk = null; Open(next); }
        if (talkDone is { } done) { talkDone = null; done(); }
    }"""
assert old in s
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "src/Game/Game.cs"
s = open(p, encoding="utf-8").read()
old = "Wait(3.9, () => { afterTalk = () => Morning(lines); Talk(\"chid\"); });"
assert old in s
s = s.replace(old, "Wait(3.9, () => { talkDone = () => Morning(lines); Talk(\"chid\"); });", 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "src/Game/GameClock.cs"
s = open(p, encoding="utf-8").read()
old = """        if (zone == null || Battle is not { } b) return;
        var p = b.Player;
        if (Journey.Tonight is { } f) { EnterArena(StoryFights.Spec(f.Id, Journey.Ctx, zone.Id, p.X, p.Z, p.Facing)); return; }"""
new = """        if (zone == null || Battle is not { } b) return;
        var p = b.Player;
        // A second fight the same night: she does not go back to the lamps.
        if (Journey.FoughtTonight) Say(Journey.DayLines.StraightOn, null, 3.5);
        if (Journey.Tonight is { } f) { EnterArena(StoryFights.Spec(f.Id, Journey.Ctx, zone.Id, p.X, p.Z, p.Facing)); return; }"""
assert old in s
s = s.replace(old, new, 1)
old = """        if (zone is not { ClockRuns: true } || World.Time != TimeOfDay.Night) return list;
        string what = Journey.Tonight is { } f ? $"{f.Verb}: {f.Place}"
            : zone is Verge { HasScars: true } ? "Step into an ember scar" : "The Wayfinder's table";
        var steps = new List<Step> { new(what), new($"Hold {KeyLabel("answer")} to answer the night", Optional: true) };
        return new List<Tracked> { new("tonight", "Tonight", TrackTone.Main, steps) }.Concat(list).ToList();"""
new = """        if (zone is not { ClockRuns: true } || World.Time != TimeOfDay.Night) return list;
        // The night's fight first, then what else is out tonight, then how to answer it.
        var called = StoryFights.Called(Journey.Ctx);
        bool scars = zone is Verge { HasScars: true };
        string what = called.FirstOrDefault() is { } f ? $"{f.Verb}: {f.Place}" : scars ? "Step into an ember scar" : "The Wayfinder's table";
        var others = called.Skip(1).Select(o => o.Place).ToList();
        if (scars && called.Count > 0) others.Add("the ember scars");
        var steps = new List<Step> { new(what) };
        if (others.Count > 0) steps.Add(new($"{Journey.DayLines.AlsoOut} {string.Join(", ", others)}", Optional: true));
        steps.Add(new($"{Journey.DayLines.Answer}: hold {KeyLabel("answer")}", Optional: true));
        return new List<Tracked> { new("tonight", "Tonight", TrackTone.Main, steps) }.Concat(list).ToList();"""
assert old in s
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "logic/Play/Zone.cs"
s = open(p, encoding="utf-8").read()
old = """    /// left, after a beat, and lets the night go when she has none.</summary>
    void StoryFall("""
new = """    /// left, after a beat, and lets the night go when she has none. A rise's words are
    /// Journey.RiseLine (counted, so the host asks for them once a rise).</summary>
    void StoryFall("""
assert old in s
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
