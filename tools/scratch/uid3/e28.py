import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Ui/MapTable.cs', [
    ('''            L($"Held by {people.Name}", Style.TextItalic, Style.Body, Ink),
            L($"Ruled by {MapOffers.InSentence(people.BossName)}",Style.Text, Style.Small, InkSoft),
            L($"Their bane: {Bane(people.Lean)}", Style.TextItalic, Style.Caption, Answer),
            Style.Rule());''', '''            L($"Held by {people.Name}; ruled at the end by {MapOffers.InSentence(people.BossName)}", Style.TextItalic, Style.Small, Ink));
        // What it pays, before what it asks (the experience director's finding: the table said
        // nothing of it): what the night leaves in the fist, drawn; the gear it leans to; a tome's chance.
        v.AddChild(Pays(o, people));
        v.AddChild(Style.Rule());'''),
    ('''    static string Bane(string[] lean)''', '''    /// <summary>What a map pays, in the Wayfinder's hand: the things a night among that people leaves
    /// in the fist, drawn (ember shards, the people's own); the gear its spoils lean to, which is
    /// what answers them; and on a win, a tome one time in three.</summary>
    static Control Pays(MapOffer o, Denizens people)
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
        v.AddChild(L($"Its gear leans to {Bane(MapOffers.Lean(o.Spec, o.People))}: what answers them.", Style.TextItalic, Style.Caption, Answer));
        v.AddChild(L($"Won, a tome to write one time in {System.Math.Round(1 / SurvivorUnchained.Arena.Arenas.TableTome)}; experience and gold for every minute held.", Style.TextItalic, Style.Caption, InkSoft));
        return v;
    }

    static string Bane(string[] lean)'''),
])
