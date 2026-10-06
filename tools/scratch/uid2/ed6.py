exec(open(__file__.replace('ed6.py', 'edlib.py')).read())
edit('godot/src/Ui/CreateLook.cs', [
('b.CustomMinimumSize = new Vector2(Her ? 96 : 140, 40);', 'b.CustomMinimumSize = new Vector2(Sections.Length > 2 ? 96 : 140, 40);'),
])
edit('godot/src/Ui/Front.cs', [
('''        Face = Sex == Sex.Female ? new Dictionary<string, double>(Face) : null, Eyes = Sex == Sex.Female ? Eyes : null, Paint = Sex == Sex.Female ? Paint : null,''',
'''        // (a hero's own body's face, eyes and paint: Loadouts.HeroKit)
        Face = Loadouts.HeroKit(Sex) != null ? new Dictionary<string, double>(Face) : null,
        Eyes = Loadouts.HeroKit(Sex) != null ? Eyes : null, Paint = Loadouts.HeroKit(Sex) != null ? Paint : null,'''),
('''    /// <summary>A body chosen: her own hairstyle or his, kept if it is one of theirs.</summary>
    public void SetSex(Sex sx)
    {
        Sex = sx;
        if (sx == Sex.Female) HairStyle = Loadouts.HerHair(HairStyle);
        else if (!Lore.HairStyles(sx).Contains(HairStyle) && HairStyle != "none") HairStyle = Lore.HairStyles(sx)[0];
        Section = 0;
    }''',
'''    /// <summary>A body chosen: its own hairstyle kept if it is one of its own,
    /// its own first otherwise; a hero's own eyes, paint and face start as theirs.</summary>
    public void SetSex(Sex sx)
    {
        Sex = sx;
        Section = FaceGroup = 0;
        if (Loadouts.HeroKit(sx) is { } kit)
        {
            HairStyle = sx == Sex.Female ? Loadouts.HerHair(HairStyle) : kit.Cuts.Any(c => c.Id == HairStyle) ? HairStyle : kit.Cuts[0].Id;
            Eyes = kit.Eyes.FirstOrDefault()?.Id ?? "";
            Paint = kit.Paints.FirstOrDefault()?.Id ?? "none";
            FaceShape = kit.Faces.FirstOrDefault()?.Id ?? "";
            Face = new Dictionary<string, double>(kit.Faces.FirstOrDefault()?.Shape ?? new());
        }
        else if (!Lore.HairStyles(sx).Contains(HairStyle) && HairStyle != "none") HairStyle = Lore.HairStyles(sx)[0];
    }'''),
])
edit('godot/tests/LoadoutTests.cs', [
('World.Lore.Eyes.First(e => e.Id == "cornflower")', 'World.Lore.Her.Eyes.First(e => e.Id == "cornflower")'),
('var ids = World.Lore.Sliders.Select(s => s.Id).ToHashSet();', 'var her = World.Lore.Her;\n        var ids = her.Sliders.Select(s => s.Id).ToHashSet();'),
('Assert.All(World.Lore.Sliders, s =>', 'Assert.All(her.Sliders, s =>'),
('Assert.All(World.Lore.Faces, f =>', 'Assert.All(her.Faces, f =>'),
('var s = World.Lore.Sliders.First(x => x.Id == kv.Key);', 'var s = her.Sliders.First(x => x.Id == kv.Key);'),
('World.Lore.HerHairs.Select(h => h.Id)', 'her.Cuts.Select(h => h.Id)'),
('Assert.Contains(World.Lore.Paints, p => p.Id == "none");', 'Assert.Contains(her.Paints, p => p.Id == "none");\n        // A man (a kit body until the male hero\'s is worn) is shaped without one.\n        Assert.Null(Loadouts.HeroKit(Sex.Male));'),
])
print('ok')
