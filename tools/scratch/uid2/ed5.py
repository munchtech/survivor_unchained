exec(open(__file__.replace('ed5.py', 'edlib.py')).read())
p = 'godot/src/Ui/CreateLook.cs'
s = open(p, encoding='utf-8', newline='').read().replace('\r\n', '\n')
a = s.index('    /// <summary>The right-hand plate on the look step')
b = s.index('    /// <summary>The look in a line (read back on the name step).</summary>')
new = '''    /// <summary>The right-hand plate on the look step: the part's choice read
    /// closely, the whole likeness, and how to turn the figure and come near.</summary>
    Control LookDetail(Archetype a)
    {
        string title, name, words;
        var k = Kit;
        switch (Section)
        {
            case "Hair" when k != null:
                var cut = k.Cuts.FirstOrDefault(h => h.Id == d.HairStyle) ?? k.Cuts[0];
                (title, name, words) = ($"{Their} hair", cut.Name, cut.Words);
                break;
            case "Face" when k != null:
                var f = k.Faces.FirstOrDefault(x => x.Id == d.FaceShape) ?? k.Faces.FirstOrDefault();
                (title, name, words) = ($"{Their} face", (f?.Name ?? "Their own") + (Shaped(k, f) ? ", shaped" : ""), f?.Words ?? "");
                break;
            case "Paint" when k != null:
                var p = k.Paints.FirstOrDefault(x => x.Id == d.Paint) ?? k.Paints[0];
                (title, name, words) = ("Paint", p.Name, p.Words);
                break;
            case "Hair":
                (title, name, words) = ($"{Their} hair", HairNames.GetValueOrDefault(d.HairStyle, d.HairStyle), d.Headgear && d.Archetype != "reaver" ? "Worn under the calling's hood." : "Worn as it grew.");
                break;
            default:
                (title, name, words) = ($"{Their} body", $"{a.Name}'s colours", a.Palettes.FirstOrDefault(x => x.Id == d.Palette)?.Name ?? "");
                break;
        }
        var v = Style.V(8, Style.Cap(title, 24), Style.Label(name, Style.Display, 20, Style.GoldHi), Style.Label(words, Style.TextItalic, 16, new Color("#c8a878"), true), Style.Rule());
        v.AddChild(Style.SubLabel($"{Their} likeness"));
        foreach (var (key, val) in Likeness()) v.AddChild(Line(key, val));
        v.AddChild(Style.Rule());
        // How to turn the figure and come near, for the device in hand.
        bool pad = Controls.Instance.UsingPad;
        string them = Her ? "her" : "him";
        v.AddChild(pad ? Style.H(8, Style.PadButton("Right stick"), Style.Label($"turn {them}, come near", Style.Ui, Style.Caption, Style.InkDim))
            : Style.Label($"Drag to turn {them}; the wheel brings {them} near; a double click goes to {Their.ToLowerInvariant()} face.", Style.Ui, Style.Caption, Style.InkDim, true));
        if (Sections.Length > 1)
            v.AddChild(Style.H(8, pad ? Style.PadButton("LT") : Style.Key(","), pad ? Style.PadButton("RT") : Style.Key("."), Style.Label("the parts of the look", Style.Ui, Style.Caption, Style.InkDim)));
        return v;
    }

    /// <summary>The whole likeness, a line a part.</summary>
    IEnumerable<(string, string)> Likeness()
    {
        string Of(List<LookChoice> l, string id) => l.FirstOrDefault(c => c.Id == id)?.Name ?? id;
        var k = Kit;
        yield return ("Skin", Of(Lore.Skins, d.Skin));
        string cut = k != null ? k.Cuts.FirstOrDefault(h => h.Id == d.HairStyle)?.Name ?? d.HairStyle : HairNames.GetValueOrDefault(d.HairStyle, d.HairStyle);
        yield return ("Hair", $"{cut}, {Of(Lore.Hairs, d.Hair).ToLowerInvariant()}");
        if (k == null) yield break;
        var f = k.Faces.FirstOrDefault(x => x.Id == d.FaceShape) ?? k.Faces.FirstOrDefault();
        if (f != null || k.Sliders.Count > 0) yield return ("Face", (f?.Name ?? "Their own") + (Shaped(k, f) ? ", shaped" : ""));
        if (k.Eyes.Count > 0) yield return ("Eyes", Of(k.Eyes, d.Eyes));
        if (k.Paints.Count > 0) yield return ("Paint", k.Paints.FirstOrDefault(x => x.Id == d.Paint)?.Name ?? k.Paints[0].Name);
    }

'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', '\r\n'))
print('ok')
