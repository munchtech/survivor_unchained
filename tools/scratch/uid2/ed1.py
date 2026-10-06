p = 'godot/src/Ui/Front.cs'
s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
s = s.replace('\r\n', '\n')
a = s.index('    Control NameLook(Archetype a)')
b = s.index('    static Label Line(string bold, string text)')
new = '''    /// <summary>The last step: their name (typed, or one from the road), and
    /// who they are, read back before the journey begins.</summary>
    Control NamePage(Archetype a)
    {
        var v = Style.V(8, Style.SubLabel("Name"));
        nameBox = new LineEdit { Text = d.Name, PlaceholderText = "Your name", MaxLength = 18, CustomMinimumSize = new Vector2(360, 38), SizeFlagsHorizontal = SizeFlags.ExpandFill };
        Style.Font(nameBox, Style.Display, 20, Style.GoldHi, false);
        nameBox.AddThemeStyleboxOverride("normal", Style.Box(new Color("#0d0c10"), Style.GoldDim, 1, 4, 10));
        nameBox.AddThemeStyleboxOverride("focus", Style.Box(new Color("#0d0c10"), Style.LineHi, 1, 4, 10));
        nameBox.TextChanged += t =>
        {
            var clean = new string(t.Where(c => char.IsLetter(c) || c is '\\'' or ' ' or '-').ToArray());
            d.Name = clean;
            if (clean != t) { nameBox.Text = clean; nameBox.CaretColumn = clean.Length; }
        };
        nameBox.TextSubmitted += _ => Begin();
        v.AddChild(Style.H(8, Nav.Skip(nameBox), Nav.Id(Style.Button("A name from the road", () => Set(() => d.Name = Names[Random.Shared.Next(Names.Length)]), false, true), "roadname")));
        // The keyboard types at once; a pad cannot type, so it is offered names instead.
        if (!Controls.Instance.UsingPad) Callable.From(() => nameBox?.GrabFocus()).CallDeferred();
        else if (d.Name.Trim() == "") Nav.Prefer = "roadname";
        // Who they are, each step's answer on its medallion; a press goes back to it.
        v.AddChild(Style.Gap(6));
        v.AddChild(Style.SubLabel(d.Sex == Sex.Female ? "Who she is" : "Who he is"));
        var bg = Callings.Background(d.Background);
        var ab = Abilities.ById(d.Ability);
        v.AddChild(Recall(0, ClassGlyph.GetValueOrDefault(d.Archetype, "sword"), a.Name, a.Tagline));
        v.AddChild(Recall(1, ab.Icon, Items.Get(d.WeaponItem).Name, $"and {ab.Name} in hand"));
        v.AddChild(Recall(2, BgGlyph.GetValueOrDefault(d.Background, "map"), bg.Name, bg.Summary));
        v.AddChild(Recall(LookStep, "mask", d.Sex == Sex.Female ? "Her look" : "His look", LookWords()));
        return v;
    }

    /// <summary>A step's answer, read back: pressed, it goes back to that step.</summary>
    Button Recall(int step, string glyph, string name, string words)
    {
        var b = Style.Button("", () => Set(() => d.Step = step));
        b.CustomMinimumSize = new Vector2(470, 70);
        Nav.Id(b, $"recall:{step}");
        foreach (var x in new[] { "normal", "hover", "pressed" })
            b.AddThemeStyleboxOverride(x, x == "normal" ? new StyleBoxEmpty() : Style.Slab(0));
        var row = Style.H(12, new Medallion(52, "", glyph) { Ring = Style.GoldDim, Ink = Style.GoldHi });
        var w = Style.V(0, Style.Label(name, Style.UiBold, Style.Small, Style.GoldHi), Style.Label(words, Style.Ui, Style.Caption, Style.InkDim, true));
        w.CustomMinimumSize = new Vector2(380, 0);
        w.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        row.AddChild(w);
        row.Position = new Vector2(8, 9);
        row.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(row);
        return b;
    }

'''
s = s[:a] + new + s[b:]
old1 = '''        if (a == Act.TabNext) { Set(() => d.Step = Math.Min(3, d.Step + 1)); return true; }
        if (a == Act.TabPrev) { Set(() => d.Step = Math.Max(0, d.Step - 1)); return true; }'''
assert old1 in s
s = s.replace(old1, '''        if (a == Act.TabNext) { Set(() => d.Step = Math.Min(NameStep, d.Step + 1)); return true; }
        if (a == Act.TabPrev) { Set(() => d.Step = Math.Max(0, d.Step - 1)); return true; }
        // The look's parts, on the triggers (or , and .).
        if (d.Step == LookStep && a is Act.SubNext or Act.SubPrev)
        {
            int n = Sections.Length;
            Set(() => d.Section = (d.Section + (a == Act.SubNext ? 1 : n - 1)) % n);
            Sound.Sfx.Page();
            return true;
        }''')
old2 = '            if (d.Step < 3) Set(() => d.Step++); else Begin();'
assert old2 in s
s = s.replace(old2, '            if (d.Step < NameStep) Set(() => d.Step++); else Begin();')
open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))
print('ok', nl == '\r\n')
