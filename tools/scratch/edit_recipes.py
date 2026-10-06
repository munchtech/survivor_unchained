import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Sim/Battle.cs', [
("""    /// <summary>Why the draft dealt it (shown on the card): on your path, familiar, evolves something.</summary>
    public readonly List<string> Why = new();""", """    /// <summary>Why the draft dealt it (shown on the card): on your path, attuned, evolves something.</summary>
    public readonly List<string> Why = new();
    /// <summary>A combat skill's recipes: what evolves it, into what, and what it joins.</summary>
    public string? Recipe;"""),
])

edit('logic/Sim/LevelUp.cs', [
("""    /// <summary>The unions whose two halves are carried, both evolved.</summary>""",
"""    /// <summary>What becomes of a combat skill, in a line: each evolution and
    /// the passives that make it, and the union it is half of.</summary>
    public static string Recipe(string weaponId)
    {
        if (!Content.Weapons.All.TryGetValue(weaponId, out var d) || d.Evolutions.Length == 0) return "";
        var parts = d.Evolutions.Select(e => $"{e.Name} with {Names(e.Catalysts)}").ToList();
        string s = $"Evolves: {string.Join("; ", parts)}.";
        if (Unions.Of(weaponId) is { } u)
            s += $" With {Content.Weapons.All[u.A == weaponId ? u.B : u.A].Name}, both evolved: {u.Name}.";
        return s;
    }

    /// <summary>A carried combat skill as the draft's arsenal shows it.</summary>
    public sealed record ArsenalLine(string Id, string Name, string Icon, School School, int Rank, bool Evolved, string Note, bool Ready);

    /// <summary>The arsenal, each skill with where it stands: what evolves it,
    /// whether it can now, what it joins.</summary>
    public static List<ArsenalLine> Arsenal(Battle b)
    {
        var o = new List<ArsenalLine>();
        foreach (var w in b.Weapons)
        {
            string note;
            bool ready = false;
            if (w.Evolution != null)
            {
                var u = Unions.Of(w.Id);
                var mate = u == null ? null : b.Weapons.Find(x => x.Id == (u.A == w.Id ? u.B : u.A));
                note = u == null ? (w.Honed > 0 ? $"Honed {w.Honed}" : "Evolved")
                    : mate?.Evolution != null ? $"Unites now: {u.Name}" : $"Joins {Content.Weapons.All[u.A == w.Id ? u.B : u.A].Name} for {u.Name}";
                ready = mate?.Evolution != null;
            }
            else if (w.Def.Evolutions.Length == 0) note = w.Honed > 0 ? $"Honed {w.Honed}" : "";
            else
            {
                var held = w.Def.Evolutions.Where(e => e.Catalysts.Any(c => b.Boons.GetValueOrDefault(c) > 0)).ToList();
                ready = held.Count > 0 && w.Rank >= Content.Weapons.MaxRank;
                note = held.Count > 0
                    ? (ready ? $"Evolves now: {string.Join(" or ", held.Select(e => e.Name))}" : $"At rank 8: {string.Join(" or ", held.Select(e => e.Name))}")
                    : $"Needs {Names(w.Def.Evolutions.SelectMany(e => e.Catalysts).Distinct())}";
            }
            o.Add(new ArsenalLine(w.Id, w.Evolution?.Name ?? w.Def.Name, w.Evolution?.Art ?? w.Def.Art, w.School, w.Rank, w.Evolution != null, note, ready));
        }
        return o;
    }

    /// <summary>The unions whose two halves are carried, both evolved.</summary>"""),
("""            var o = new Offer
            {
                Kind = OfferKind.Rank, Id = w.Id, Rarity = Rarity.Common, Title = w.Evolution?.Name ?? w.Def.Name,""",
"""            var o = new Offer
            {
                Kind = OfferKind.Rank, Id = w.Id, Rarity = Rarity.Common, Title = w.Evolution?.Name ?? w.Def.Name, Recipe = w.Evolution == null ? Recipe(w.Id) : null,"""),
("""                var o = new Offer { Kind = OfferKind.Weapon, Id = id, Rarity = Rarity.Uncommon, Title = d.Name, Text = d.Description, Icon = d.Art, Tags = d.Tags, From = 0, To = 1 };""",
"""                var o = new Offer { Kind = OfferKind.Weapon, Id = id, Rarity = Rarity.Uncommon, Title = d.Name, Text = d.Description, Icon = d.Art, Tags = d.Tags, From = 0, To = 1, Recipe = Recipe(id) };"""),
])

edit('src/Game/Controls.cs', [
("""    Pause, Confirm, Cancel, Reroll, Banish, Pick1, Pick2, Pick3, Pick4, TabNext, TabPrev, Arts,
}""", """    Pause, Confirm, Cancel, Reroll, Banish, Pick1, Pick2, Pick3, Pick4, TabNext, TabPrev, Arts, Skip,
}"""),
("""        [Act.TabNext] = ["BracketRight"], [Act.TabPrev] = ["BracketLeft"], [Act.Arts] = ["KeyK"],
    };""", """        [Act.TabNext] = ["BracketRight"], [Act.TabPrev] = ["BracketLeft"], [Act.Arts] = ["KeyK"], [Act.Skip] = ["KeyV"],
    };"""),
("""    public static readonly Act[] Rebindable = [Act.Up, Act.Left, Act.Down, Act.Right, Act.Dash, Act.Ability, Act.Ultimate, Act.Interact, Act.Inventory, Act.Character, Act.Arts, Act.Journal, Act.Map, Act.Reroll, Act.Banish];""",
"""    public static readonly Act[] Rebindable = [Act.Up, Act.Left, Act.Down, Act.Right, Act.Dash, Act.Ability, Act.Ultimate, Act.Interact, Act.Inventory, Act.Character, Act.Arts, Act.Journal, Act.Map, Act.Reroll, Act.Banish, Act.Skip];"""),
("""        [Act.TabNext] = [JoyButton.RightShoulder], [Act.TabPrev] = [JoyButton.LeftShoulder], [Act.Reroll] = [JoyButton.X], [Act.Banish] = [JoyButton.Y],
    };""", """        [Act.TabNext] = [JoyButton.RightShoulder], [Act.TabPrev] = [JoyButton.LeftShoulder], [Act.Reroll] = [JoyButton.X], [Act.Banish] = [JoyButton.Y],
        [Act.Skip] = [JoyButton.RightStick],
    };"""),
])
print('ok')
