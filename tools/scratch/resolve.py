import os, re, shutil
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c')
SP = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad'

def sub(s, old, new, n=1):
    assert s.count(old) == n, (old[:100], s.count(old))
    return s.replace(old, new)

def hunks(path, pick):
    """Resolve conflict hunks in order with pick(i, ours, theirs) -> text."""
    s = open(path, encoding='utf-8').read()
    out, i, pos = [], 0, 0
    pat = re.compile(r'<<<<<<< [^\n]*\n(.*?)=======\n(.*?)>>>>>>> [^\n]*\n', re.S)
    for m in pat.finditer(s):
        out.append(s[pos:m.start()])
        out.append(pick(i, m.group(1), m.group(2)))
        pos = m.end()
        i += 1
    out.append(s[pos:])
    open(path, 'w', encoding='utf-8').write(''.join(out))
    return i

# Controls: both sides' new actions.
def controls(i, ours, theirs):
    if i == 0:
        return theirs.replace('TabNext, TabPrev, Arts,\n', 'TabNext, TabPrev, Arts, Skip,\n')
    if i == 1:
        t = theirs.replace('[Act.Arts] = ["KeyK"],\n', '[Act.Arts] = ["KeyK"], [Act.Skip] = ["KeyV"],\n')
        t = t.replace('Act.Reroll, Act.Banish];', 'Act.Reroll, Act.Banish, Act.Skip];')
        return t
    if i == 2:
        return '        [Act.Skip] = [JoyButton.RightStick],\n' + theirs
    raise Exception(i)
print('controls', hunks('godot/src/Game/Controls.cs', controls))

def gamemenus(i, ours, theirs):
    return theirs.replace('great, b));', 'great, b, LevelUp.CanSkip(b) ? Skip : null));')
print('gamemenus', hunks('godot/src/Game/GameMenus.cs', gamemenus))

def menus(i, ours, theirs):
    return theirs.replace('("Draft: banish", [Act.Banish], "Y"),', '("Draft: banish", [Act.Banish], "Y"), ("Draft: skip", [Act.Skip], "R3"),')
print('menus', hunks('godot/src/Ui/Menus.cs', menus))

def result(i, ours, theirs):
    return ours + '\n' + theirs
print('result', hunks('godot/src/Ui/ArenaResult.cs', result))

def arts(i, ours, theirs):
    if i == 0:
        return theirs.replace('"  ·  carried"', '"  ·  carried, banked"')
    if i == 1:
        return ('            Style.UiBold, Style.Small, meets ? Style.Good : Style.Bad, true));\n'
                '        d.AddChild(Style.Label($"By day it is rank {Ranks[SkillBook.Rank(ch)]}, and grows with you (every third level). In the night\'s arenas the ember starts from nothing, but what you carry by day is banked: it sleeps in you through the day, the ember offers it in its first drafts, and it comes in at rank {Ranks[SkillBook.NightRank(ch)]}" +\n'
                '            (ch.Level < 10 ? " (rank III from the tenth level)." : "."), Style.Ui, Style.Caption, Style.InkDim, true));\n')
    raise Exception(i)
print('arts', hunks('godot/src/Ui/ArtsScreen.cs', arts))

# The draft panel: the UI owner's design, with the skill system's words put back in it.
p = 'godot/src/Ui/Panels.cs'
s = open(SP + r'\theirs_panels.cs', encoding='utf-8').read()
s = sub(s, """/// <summary>What the level-up draft shows, and what picking does; the fight, for the build beside the cards.</summary>
public sealed record DraftView(int Level, bool Blessing, List<Offer> Offers, int Rerolls, int Banishes, int Queued, string? Tip, HashSet<Tag> Build,
    Action<int> Pick, Action Reroll, Action<int> Banish, string? Great = null, Battle? Battle = null);""",
"""/// <summary>What the level-up draft shows, and what picking does; the fight, for the build beside the cards;
/// a skip, when one is allowed (docs/SKILLS_DESIGN.md, "The offer").</summary>
public sealed record DraftView(int Level, bool Blessing, List<Offer> Offers, int Rerolls, int Banishes, int Queued, string? Tip, HashSet<Tag> Build,
    Action<int> Pick, Action Reroll, Action<int> Banish, string? Great = null, Battle? Battle = null, Action? Skip = null);""")
s = sub(s, """/// cards appear none can be taken, so a key still held from the fight does
/// not spend a level by accident.
/// </summary>""", """/// cards appear none can be taken, so a key still held from the fight does
/// not spend a level by accident. The skill system's words ride on each card
/// (docs/SKILLS_DESIGN.md): why the ember dealt it (banked, on your path,
/// your calling's own), what a combat skill becomes, the path it belongs to;
/// a great blessing says what it is for; V (or R3) skips for ember back.
/// </summary>""")
s = sub(s, "    const float CardW = 320, CardH = 452;", "    const float CardW = 320, CardH = 500;")
s = sub(s, """    static string Kicker(Offer o) => o.Kind switch
    {
        OfferKind.Weapon => "New combat skill",
        OfferKind.Rank => $"Combat skill · rank {o.From} to {o.To}",
        OfferKind.Evolve => "Evolution",
        OfferKind.Boon when o.Great => o.From is int g && g > 0 ? $"Great blessing · rank {g} to {o.To}" : "Great blessing",""",
"""    static string Role(string id) => Boons.GreatRoles.TryGetValue(id, out var r) ? r switch
    {
        Boons.GreatRole.Ward => "ward",
        Boons.GreatRole.Answer => "answer",
        Boons.GreatRole.Tempo => "quickening",
        _ => "power",
    } : "great";

    static string Kicker(Offer o) => o.Kind switch
    {
        OfferKind.Weapon => o.To is int r && r > 1 ? $"New combat skill · rank {r}" : "New combat skill",
        OfferKind.Rank => $"Combat skill · rank {o.From} to {o.To}",
        OfferKind.Evolve => "Evolution",
        OfferKind.Union => "Union",
        OfferKind.Hone => $"Honing · {o.To} of {LevelUp.MaxHone}",
        // A great blessing says what it is for: power, ward, answer, quickening.
        OfferKind.Boon when o.Great => o.From is int g && g > 0 ? $"{Role(o.Id)} · rank {g} to {o.To}" : $"Great blessing · {Role(o.Id)}",""")
# Header: the paths the build walks.
s = sub(s, """        if (v.Queued > 0) col.AddChild(Style.Label($"{v.Queued} more to choose after this", Style.UiBold, Style.Small, Style.InkDim, false, HorizontalAlignment.Center));""",
"""        if (v.Queued > 0) col.AddChild(Style.Label($"{v.Queued} more to choose after this", Style.UiBold, Style.Small, Style.InkDim, false, HorizontalAlignment.Center));
        if (v.Battle != null && LevelUp.BuildPaths(v.Battle) is { Count: > 0 } paths)
            col.AddChild(Style.Label($"Walking {string.Join(" and ", paths.Select(p => p.Name))}", Style.TextItalic, Style.Small, Style.EmberHi, false, HorizontalAlignment.Center));""")
# Footer: the skip.
s = sub(s, """        banish.Disabled = v.Banishes <= 0;
        foot.AddChild(banish);
    }""", """        banish.Disabled = v.Banishes <= 0;
        foot.AddChild(banish);
        if (v.Skip != null)
        {
            var skip = Style.Button("", () => { if (armed && chosen == null) v.Skip(); }, false, true);
            Inside(skip, Style.H(6, Style.Prompt(Act.Skip), Style.Label("Skip", Style.UiBold, Style.Caption, Style.GoldHi)));
            skip.TooltipText = $"Take none: {LevelUp.SkipRefund * 100:0}% of the level's ember comes back, so the next level comes sooner.";
            foot.AddChild(skip);
        }
    }""")
# Unions wear the evolution's crown.
s = sub(s, """        var r = o.Kind == OfferKind.Evolve ? 4 : (int)o.Rarity;
        var rc = Style.RarityOf(r);
        var school = SchoolOf(o);
        var color = o.Kind == OfferKind.Evolve ? new Color("#ffd88a") : school is School s ? ItemViews.SchoolColors[s] : rc;""",
"""        bool crown = o.Kind is OfferKind.Evolve or OfferKind.Union;
        var r = crown ? 4 : (int)o.Rarity;
        var rc = Style.RarityOf(r);
        var school = SchoolOf(o);
        var color = crown ? new Color("#ffd88a") : school is School s ? ItemViews.SchoolColors[s] : rc;""")
s = sub(s, """        panel.SetMeta("frame", o.Kind == OfferKind.Evolve ? "card_evolve" : $"card_{Math.Min(r, 4)}");""",
"""        panel.SetMeta("frame", crown ? "card_evolve" : $"card_{Math.Min(r, 4)}");""")
s = sub(s, """        var foot = Style.H(Style.Gap2, Style.Label(o.Kind == OfferKind.Evolve ? "Legendary" : o.Rarity.ToString(), Style.UiBold, Style.Caption, rc), Style.Gems(r, 6));""",
"""        var foot = Style.H(Style.Gap2, Style.Label(crown ? "Legendary" : o.Rarity.ToString(), Style.UiBold, Style.Caption, rc), Style.Gems(r, 6));""")
# Why it was dealt, and what a combat skill becomes.
s = sub(s, """        var body = Style.Label(text, Style.Text, Style.Body, Style.Ink, true, HorizontalAlignment.Center);
        body.SizeFlagsVertical = SizeFlags.ExpandFill;
        v2.AddChild(body);""",
"""        var body = Style.Label(text, Style.Text, Style.Body, Style.Ink, true, HorizontalAlignment.Center);
        body.SizeFlagsVertical = SizeFlags.ExpandFill;
        v2.AddChild(body);
        // Why the ember dealt it: banked from the day, on your path, your calling's own, a duo; a trap said plainly.
        foreach (var why in o.Why.Where(w => o.Path == null || !w.StartsWith("On your path")).Take(2))
            v2.AddChild(Style.Label(why, Style.UiBold, Style.Caption, why.StartsWith("Little") ? Style.InkDim : Style.EmberHi, true, HorizontalAlignment.Center));
        // What a combat skill becomes, and with what.
        if (o.Recipe is { Length: > 0 } recipe)
            v2.AddChild(Style.Label(recipe, Style.TextItalic, Style.Badge, Style.InkDim, true, HorizontalAlignment.Center));""")
s = sub(s, """        if (fits)
        {
            var fl = Style.H(4, Glyphs.Icon("flame", 15, Style.EmberHi), Style.Label("Fits your build", Style.UiBold, Style.Caption, Style.EmberHi));
            fl.Alignment = BoxContainer.AlignmentMode.Center;
            v2.AddChild(fl);
        }""", """        // The path it belongs to, or (if none) that it fits what the build already does.
        if (o.Path is { } pid && Content.Paths.Find(pid) is { } path)
            v2.AddChild(Style.Label(path.Name, Style.DisplayLight, Style.Small, Style.Gold, false, HorizontalAlignment.Center));
        else if (fits)
        {
            var fl = Style.H(4, Glyphs.Icon("flame", 15, Style.EmberHi), Style.Label("Fits your build", Style.UiBold, Style.Caption, Style.EmberHi));
            fl.Alignment = BoxContainer.AlignmentMode.Center;
            v2.AddChild(fl);
        }""")
s = sub(s, """            case Act.Cancel: if (banishing) { banishing = false; Mark(); Prompts(); } break;""",
"""            case Act.Cancel: if (banishing) { banishing = false; Mark(); Prompts(); } break;
            case Act.Skip: if (armed && chosen == null && v.Skip != null) v.Skip(); else Sound.Sfx.Deny(); break;""")
# Keep anything of ours outside the draft panel: take the merged file's tail after the draft panel.
merged = open(p, encoding='utf-8').read()
assert '<<<<<<<' in merged
open(p, 'w', encoding='utf-8').write(s)
print('panels written')
