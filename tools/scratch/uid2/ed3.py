exec(open(__file__.replace('ed3.py', 'edlib.py')).read())
edit('godot/logic/Play/Loadout.cs', [
('''    /// <summary>Her hairstyle: the one chosen if it is one of hers (Lore.HerHairs),
    /// the nearest of hers to an older save's cut, her first otherwise.</summary>
    public static string HerHair(string? style)
    {
        if (Lore.HerHairs.Any(h => h.Id == style)) return style!;
        return style switch { "Hair_BuzzedFemale" or "Hair_Buzzed" or "none" => "pixie", "Hair_Buns" => "bob", _ => Lore.HerHairs[0].Id };
    }''',
'''    /// <summary>Her hairstyle: the one chosen if it is one of hers (Lore.Her.Cuts),
    /// the nearest of hers to an older save's cut, her first otherwise.</summary>
    public static string HerHair(string? style)
    {
        var cuts = Lore.Her.Cuts;
        if (cuts.Any(h => h.Id == style)) return style!;
        return style switch { "Hair_BuzzedFemale" or "Hair_Buzzed" or "none" => "pixie", "Hair_Buns" => "bob", _ => cuts[0].Id };
    }'''),
('''        var eyes = Lore.Eyes.FirstOrDefault(e => e.Id == ch.Eyes);''',
'''        // A hero's own body is shaped by what it offers (Lore.Hero): hers now;
        // the male hero's when his body wears one (his cuts then come in here too).
        var kit = her ? Lore.Hero(sex) : null;
        var eyes = kit?.Eyes.FirstOrDefault(e => e.Id == ch.Eyes);'''),
('''            // Her face, eyes and paint are her body's own.
            Face = her && ch.Face is { Count: > 0 } face ? new Dictionary<string, double>(face) : null,
            Eyes = her && eyes != null && eyes.Color != "" ? eyes.Color : null,
            EyeRing = her && eyes != null && eyes.Ring != "" ? eyes.Ring : null,
            Paint = her && Lore.Paints.Any(p => p.Id == ch.Paint && p.Id != "none") ? ch.Paint : null,''',
'''            // A hero's face, eyes and paint are their body's own.
            Face = kit != null && ch.Face is { Count: > 0 } face ? new Dictionary<string, double>(face) : null,
            Eyes = eyes != null && eyes.Color != "" ? eyes.Color : null,
            EyeRing = eyes != null && eyes.Ring != "" ? eyes.Ring : null,
            Paint = kit != null && kit.Paints.Any(p => p.Id == ch.Paint && p.Id != "none") ? ch.Paint : null,'''),
])
edit('godot/logic/Rpg/Character.cs', [
('''    /// her face's sliders (Lore.Sliders, -1 to 1; none set is her own face), her
    /// eyes' colour (Lore.Eyes) and the paint she wears (Lore.Paints).</summary>''',
'''    /// her face's sliders (Lore.Hero's, -1 to 1; none set is her own face), her
    /// eyes' colour and the paint she wears (both Lore.Hero's).</summary>'''),
])
edit('godot/src/Actors/People.cs', [
('/// <summary>The paint on her face (Lore.Paints), or none.</summary>', '/// <summary>The paint on her face (Lore.Her.Paints), or none.</summary>'),
('/// <summary>Paint on her face (Lore.Paints: art/people/paint/ID.png, laid', '/// <summary>Paint on her face (Lore.Her.Paints: art/people/paint/ID.png, laid'),
('SurvivorUnchained.World.Lore.Paints.FirstOrDefault(x => x.Id == paint)', 'SurvivorUnchained.World.Lore.Her.Paints.FirstOrDefault(x => x.Id == paint)'),
])
print('ok')
