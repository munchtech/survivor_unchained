import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/logic/Rpg/Crafting.cs', [
    ('''    public static NightYield Night(string people, int tier, bool story, int ember, double minutesPast, bool won, bool fell,''',
     '''    /// <summary>What a night among a people can leave in the fist (Night's materials), in the
    /// order a table says them: ember shards, then the people's own.</summary>
    public static List<string> NightMaterials(string people) =>
        new[] { Shard }.Concat((Rules.Night.Peoples.GetValueOrDefault(people) ?? new()).Select(p => p.Material)).Distinct().ToList();

    public static NightYield Night(string people, int tier, bool story, int ember, double minutesPast, bool won, bool fell,'''),
])
edit('godot/logic/Arena/Arena.cs', [
    ('''        var choices = new List<string>();
        if (won && (spec.Story || b.Rng.Next() < 0.35))''', '''        var choices = new List<string>();
        if (won && (spec.Story || b.Rng.Next() < TableTome))'''),
    ('''    public static ArenaResult Finish(Journey j, Battle b, ArenaSpec spec, bool won, string? killer = null)''',
     '''    /// <summary>How often a table's night won gives a tome (a story fight always does); the table says so.</summary>
    public const double TableTome = 0.35;

    public static ArenaResult Finish(Journey j, Battle b, ArenaSpec spec, bool won, string? killer = null)'''),
])
edit('godot/src/Ui/MapTable.cs', [
    ('''        var v = Style.V(6,
            Style.H(8, Style.Label($"TIER {o.Spec.Tier}", Style.UiHeavy, Style.Caption, InkSoft, false, HorizontalAlignment.Left, false), Style.Gems(System.Math.Min(o.Spec.Tier - 1, 5), 6)),
            L(o.Spec.Name.ToUpperInvariant(), Style.Display, 30, Ink),
            L($"Held by {people.Name}", Style.TextItalic, Style.Body, Ink),
            L($"Ruled by {people.BossName}", Style.Text, Style.Small, InkSoft),
            L($"Their bane: {string.Join(", ", people.Lean.Select(a => SurvivorUnchained.Rpg.Items.Affix(a)?.Name ?? a))} gear", Style.TextItalic, Style.Caption, Answer),
            Style.Rule());''', '''        var v = Style.V(6,
            Style.H(8, Style.Label($"TIER {o.Spec.Tier}", Style.UiHeavy, Style.Caption, InkSoft, false, HorizontalAlignment.Left, false), Style.Gems(System.Math.Min(o.Spec.Tier - 1, 5), 6)),
            L(o.Spec.Name.ToUpperInvariant(), Style.Display, 30, Ink),
            L($"Held by {people.Name}; ruled at the end by {SurvivorUnchained.Maps.MapOffers.InSentence(people.BossName)}", Style.TextItalic, Style.Small, Ink));
        // What it pays, before what it asks (the experience director's finding: the table said
        // nothing of it): what the night leaves in the fist, drawn; the gear it leans to; a tome's chance.
        v.AddChild(Pays(o, people));
        v.AddChild(Style.Rule());'''),
    ('''    /// <summary>One map: a sheet of parchment in a wooden frame, lettered by the Wayfinder.</summary>''',
     '''    /// <summary>What a map pays, in the Wayfinder's hand: the things a night among that people leaves
    /// in the fist, drawn (ember shards, the people's own); the gear its spoils lean to; and on a win,
    /// a tome one time in three.</summary>
    Control Pays(MapOffer o, SurvivorUnchained.Maps.Denizens people)
    {
        Label L(string t, Font f, int sz, Color c) => Style.Label(t, f, sz, c, true, HorizontalAlignment.Left, false);
        var v = Style.V(4, Style.Label("WHAT IT PAYS", Style.UiHeavy, Style.Badge, InkSoft, false, HorizontalAlignment.Left, false));
        var things = Style.H(6);
        foreach (var m in SurvivorUnchained.Rpg.Crafting.NightMaterials(o.People).Take(4))
        {
            var def = SurvivorUnchained.Rpg.Items.Get(m);
            var cell = Style.V(0, ItemPhotos.Icon(def.Icon, 44, InkSoft), Style.Label(def.Plural ?? def.Name.ToLowerInvariant(), Style.Ui, 12, Ink, true, HorizontalAlignment.Center, false));
            cell.CustomMinimumSize = new Vector2(76, 0);
            cell.TooltipText = def.Description;
            things.AddChild(cell);
        }
        v.AddChild(things);
        var lean = SurvivorUnchained.Maps.MapOffers.Lean(o.Spec, o.People).Select(a => SurvivorUnchained.Rpg.Items.Affix(a)?.Name ?? a).Distinct().Take(3).ToList();
        if (lean.Count > 0) v.AddChild(L($"Its gear leans to {string.Join(", ", lean).ToLowerInvariant()}: what answers them.", Style.TextItalic, Style.Caption, Answer));
        v.AddChild(L($"Won, a tome to write one time in {System.Math.Round(1 / SurvivorUnchained.Arena.Arenas.TableTome)}; experience and gold for every minute held.", Style.TextItalic, Style.Caption, InkSoft));
        return v;
    }

    /// <summary>One map: a sheet of parchment in a wooden frame, lettered by the Wayfinder.</summary>'''),
])
