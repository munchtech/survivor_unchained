import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/logic/World/Lore.cs', [
    ('''public sealed class HeroLook
{
    public List<HairCut> Cuts = new();''', '''public sealed class HeroLook
{
    public List<HairCut> Cuts = new();
    /// <summary>His beards (the male hero's: none, stubble, short, full...), as cuts are; hers none.</summary>
    public List<HairCut> Beards = new();'''),
    ('''/// <summary>A face to start from: her face's sliders (-1 to 1), set together.</summary>
public sealed class FaceShape
{
    public string Id = "", Name = "", Words = "";''', '''/// <summary>A face to start from: her face's sliders (-1 to 1), set together;
/// and, for a face that has its own, a skin (Lore.Skins) and eyes (the hero's).</summary>
public sealed class FaceShape
{
    public string Id = "", Name = "", Words = "";
    public string? Skin, Eyes;'''),
    ('''    public List<string>? Outfit;
    public bool? Beard;''', '''    public List<string>? Outfit;
    public bool? Beard;
    /// <summary>A hero's own beard (Lore.Hero's beards: the male hero's), or none.</summary>
    public string? BeardStyle;'''),
])
edit('godot/logic/Rpg/Character.cs', [
    ('''    public string? HairStyle;
    public bool? Beard;
    public double? Figure;''', '''    public string? HairStyle;
    public bool? Beard;
    /// <summary>A hero's own beard (Lore.Hero's beards), where their body has them.</summary>
    public string? BeardStyle;
    public double? Figure;'''),
    ('''    public string? Model, Cloak, Skin, Hair, HairStyle, Eyes, Paint;''', '''    public string? Model, Cloak, Skin, Hair, HairStyle, Eyes, Paint, BeardStyle;'''),
    ('''            Beard = c.Beard, Figure = c.Figure, Attributes = Callings.StartAttributes(c.Archetype),''', '''            Beard = c.Beard, BeardStyle = c.BeardStyle, Figure = c.Figure, Attributes = Callings.StartAttributes(c.Archetype),'''),
])
edit('godot/logic/Play/Loadout.cs', [
    ('''    public static HeroLook? HeroKit(Sex sex) => sex == Sex.Female ? Lore.Hero(sex) : null;''',
     '''    /// (His is looks.json's heroes.male, written once his body is playable.)
    public static HeroLook? HeroKit(Sex sex) => Lore.Hero(sex);'''),
    ('''            Beard = sex == Sex.Male && (ch.Beard ?? true),''', '''            Beard = sex == Sex.Male && (ch.Beard ?? true),
            BeardStyle = kit is { Beards.Count: > 0 } ? (kit.Beards.Any(b => b.Id == ch.BeardStyle) ? ch.BeardStyle : kit.Beards[0].Id) : null,'''),
])
