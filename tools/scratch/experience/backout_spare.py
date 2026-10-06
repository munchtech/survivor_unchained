"""Back out experience's spare fields (the story lead owns them): run from godot/."""
p = "logic/Play/StoryFights.cs"
s = open(p, encoding="utf-8").read()
start = s.index('            case "hollow":')
end = s.index('            case "roost":')
new = '''            case "hollow":
            {
                // Greymuzzle let go (docs/STORY_BIBLE.md, "The nights"), narrowly: only if she knelt
                // and promised and the stream already runs clean. He goes down, gets up and goes to
                // his sick; beasts.outcome stands; Maeca hears of it, the one fight that raises her regard.
                bool spare = F(c, "promise.pack").Truthy && !F(c, "promise.broken").Truthy && StreamClean(c);
                var spec = Night("hollow_by_night", "The Hollow by Night", "pack", 311, "boss_pack", "Greymuzzle", "Who Kept the Cold Off",
                    spare
                        ? $$"""[{ "set": { "greymuzzle": "spared" } }, {{ZoneRuntime.Hist("spared_greymuzzle", "brought Greymuzzle down in his own Hollow by night, and let him get up and go to his sick", ["beasts", "wolves"], 2, null, """{ "maeca": { "affection": 15, "respect": 20 } }""")}}]"""
                        : $$"""[{ "set": { "greymuzzle": "dead", "hollow.hostile": true } }, { "add": { "beasts.population": -30 } }, { "quest": { "id": "beasts", "entry": "alpha_dead" } }, { "give": "greymuzzle_fang" }, {{ZoneRuntime.Hist("killed_greymuzzle", "killed Greymuzzle, the Pack's old dog-wolf, in his own Hollow by night", ["beasts", "wolves"], 2, null, """{ "maeca": { "affection": -50, "respect": -20 }, "holloway": { "respect": 20 } }""")}}]""",
                    """[{ "add": { "beasts.population": 10 } }, { "set": { "hollow.hostile": true } }, { "quest": { "id": "beasts", "entry": "hollow_lost" } }]""",
                    spare
                        ? "Behind you, in the den's mouth, an old wolf is breathing. You leave him to it."
                        : "The Hollow is quiet. The only breath in it is yours, and it does not show in the cold.",
                    "You come to at the Hollow's mouth with your collar wet from a wolf's jaws. Nothing ate you. Something carried you out.");
                spec.Spare = spare;
                return spec;
            }
'''
s = s[:start] + new + s[end:]
open(p, "w", encoding="utf-8", newline="").write(s)

p = "logic/Arena/Arena.cs"
s = open(p, encoding="utf-8").read()
for old, new in [
("""    /// <summary>Letting the boss go is offered (Greymuzzle, when the story allows it:
    /// docs/STORY_BIBLE.md, "The nights"). A runtime with the choice asks her at his side; one
    /// without it lets him go. OnWin is then the killed outcome, OnSpare the spared one.</summary>
    public bool Spare;
    /// <summary>The story's outcome and last line when she lets the boss go (Spare).</summary>
    public string? OnSpare, EndSpare;
""", """    /// <summary>The boss is brought down and let go, not killed (Greymuzzle, when the story
    /// allows it: docs/STORY_BIBLE.md, "The nights").</summary>
    public bool Spare;
"""),
("        Spare = lost.Spare, OnSpare = lost.OnSpare, EndSpare = lost.EndSpare, EndWon = lost.EndWon,", "        Spare = lost.Spare, EndWon = lost.EndWon,"),
("""    public static void Won(Journey j, ArenaSpec spec, bool spared = false)
    {
        var w = j.World;
        spared &= spec.Spare && spec.OnSpare != null;
        if ((spared ? spec.OnSpare : spec.OnWin) is { } outcome) j.Apply(outcome);
        w.Facts["arena.last.spared"] = spared;""", """    public static void Won(Journey j, ArenaSpec spec)
    {
        var w = j.World;
        if (spec.OnWin != null) j.Apply(spec.OnWin);"""),
("""    /// <summary>Won by letting the boss go (its spared outcome and line, not its death).</summary>
    public bool Spared { get; init; }
""", ""),
("""            w.Facts["arena.last.spared"] = false;
""", ""),
("""
            Spared = won && w.Fact("arena.last.spared").Truthy,""", ""),
]:
    assert old in s, old[:60]
    s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "logic/Play/Zones/ArenaRun.cs"
s = open(p, encoding="utf-8").read()
old = """        // This runtime has no choice to ask: a boss it may let go, it lets go.
        Arenas.Won(G.Journey, Spec, spared: Spec.Spare);"""
assert old in s
s = s.replace(old, "        Arenas.Won(G.Journey, Spec);", 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "src/Ui/ArenaResult.cs"
s = open(p, encoding="utf-8").read()
old = """r.Won ? (r.Spared ? r.Spec.EndSpare : null) ?? r.Spec.EndWon ?? "The valley will hear of it." """
assert old in s
s = s.replace(old, """r.Won ? r.Spec.EndWon ?? "The valley will hear of it." """, 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
