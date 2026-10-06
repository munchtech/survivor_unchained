import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Arena/Arena.cs', [
("""    /// <summary>Evolutions and unions made here for the first time (now in the codex).</summary>
    public List<string> Recorded { get; init; } = new();
}""", """    /// <summary>Evolutions and unions made here for the first time (now in the codex).</summary>
    public List<string> Recorded { get; init; } = new();
    /// <summary>What the tome was written with, once it has been.</summary>
    public string? Inscribed { get; set; }
}"""),
("""    /// <summary>Write a tome won in an arena with one of its choices: the tome
    /// goes into the pack, ready to be read. False if it was not one of them.</summary>
    public static bool Inscribe(Journey j, ArenaResult r, string id) =>
        r.TomeChoices.Contains(id) && j.GiveItem(SkillBook.Tome(id), 1);""",
"""    /// <summary>Write a tome won in an arena with one of its choices: the tome
    /// goes into the pack, ready to be read. Once only; false if it was not
    /// one of them (or the pack is full).</summary>
    public static bool Inscribe(Journey j, ArenaResult r, string id)
    {
        if (r.Inscribed != null || !r.TomeChoices.Contains(id) || !j.GiveItem(SkillBook.Tome(id), 1)) return false;
        r.Inscribed = id;
        return true;
    }"""),
])

edit('src/Game/Game.cs', [
("""    public void LeaveArena(ArenaResult result)
    {
        var s = result.Spec;""", """    public void LeaveArena(ArenaResult result)
    {
        var s = result.Spec;
        // A tome left blank is written with the first of what it offered.
        if (result.Inscribed == null && result.TomeChoices.Count > 0) Arenas.Inscribe(Journey, result, result.TomeChoices[0]);"""),
])

edit('src/Ui/ArenaResult.cs', [
("""        if (r.Tome is { } tome) outv.AddChild(Line("book", $"A tome: {Weapons.All[tome].Name}", new Color("#b8a8d8")));""",
"""        // A tome won is the survivor's to write: one of what burned here.
        if (r.Inscribed is { } tome) outv.AddChild(Line("book", $"A tome: {Weapons.All[tome].Name}", new Color("#b8a8d8")));
        else if (r.TomeChoices.Count > 0)
        {
            outv.AddChild(Line("book", "A blank tome: write it with one of what burned", new Color("#b8a8d8")));
            var pick = Style.H(8);
            foreach (var id in r.TomeChoices)
            {
                var w = Weapons.All[id];
                var btn = Style.Button(w.Name, () => { if (Arenas.Inscribe(G.Journey, r, id)) Refresh(); }, false, true);
                btn.TooltipText = $"{w.Description} By day it asks {SkillBook.Need} {SkillBook.Attribute(id)}.";
                pick.AddChild(btn);
            }
            outv.AddChild(pick);
        }
        foreach (var made in r.Recorded)
            outv.AddChild(Line("scroll", made.StartsWith("evo:") ? $"In the codex: {EvolutionName(made[4..])}" : $"In the codex: the union {Unions.Find(made[6..])?.Name}", Style.GoldHi));"""),
("""    static readonly string[] Numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"];""",
"""    static string EvolutionName(string id) => Weapons.All.Values.SelectMany(w => w.Evolutions).FirstOrDefault(e => e.Id == id)?.Name ?? id;

    static readonly string[] Numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"];"""),
("""using SurvivorUnchained.Play;""", """using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;"""),
])
print('ok')
