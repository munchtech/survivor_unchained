"""The bench to the owner's tightened rules (UI design's notes on brannoc.jpg): seams as ledger rows,
crafts as type, the heat as a chain of UI art's links, the likeness fading into the panel, the worn
row as one line of nine."""
import os
from ed import ROOT
P = os.path.join(ROOT, "src/Ui/Forge.cs")
s = open(P, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace("\r\n", "\n")

def between(start, end):
    a = s.index(start)
    b = s.index(end, a)
    return a, b

def replace_block(start, end, new):
    global s
    a, b = between(start, end)
    s = s[:a] + new + s[b:]

def rep(old, new):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:120])
    s = s.replace(old, new, 1)

# ---------------------------------------------------------------- the seams as ledger rows
replace_block("    Control SeamRow(ItemInstance it, int k, int cap)", "    /// <summary>The crafts for the chosen seam",
'''    Control SeamRow(ItemInstance it, int k, int cap)
    {
        bool open = k >= it.Affixes.Count;
        var a = open ? null : it.Affixes[k];
        var ad = a != null ? Items.Affix(a.Id) : null;
        bool coal = ad?.Kindled != null, skill = ad?.Grants != null, slurry = ad?.Slurry == true, mark = ad?.Mark == true, on = k == seam && SeamCrafts;
        // A ledger's row (the owner: no boxes holding words): the grade's numeral, its words, a fine
        // rule under it; the seam at the anvil has a thin ember mark at its left and its words in full ink.
        var row = Style.Panel(new StyleBoxEmpty { ContentMarginTop = 6, ContentMarginBottom = 6 });
        row.MouseFilter = MouseFilterEnum.Stop;
        var h = Style.H(14);
        h.AddChild(new ColorRect { Color = on ? Style.Ember : Colors.Transparent, CustomMinimumSize = new Vector2(2, 0), MouseFilter = MouseFilterEnum.Ignore });
        var badge = new GradeBadge(open ? GradeBadge.Mark.Open : coal ? GradeBadge.Mark.Coal : skill ? GradeBadge.Mark.Skill : slurry ? GradeBadge.Mark.Slurry
            : mark ? GradeBadge.Mark.Inscribed : GradeBadge.Mark.Grade, a?.Tier ?? 0, cap);
        badge.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        h.AddChild(badge);
        var words = Style.V(0);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        words.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        string title = open ? "An open seam" : ad?.Text(a!.Tier) ?? a!.Id;
        string rarity = Inventory.RarityName(it).ToLowerInvariant();
        bool bright = !open && !mark && a!.Tier >= Crafting.Bright;
        string note = open ? (Crafting.Does(crafter, Verb.Cage) ? "work a material in, or cage a coal" : Crafting.Does(crafter, Verb.WorkIn) ? "work a material in"
                : Crafting.Does(crafter, Verb.Mark) ? "bind a power into it, or write a mark" : Crafting.Does(crafter, Verb.Bind) ? "bind a power into it" : "empty")
            : coal ? $"{ad!.Name}: a caged coal, it shapes the ember's draft"
            : skill ? $"{ad!.Name}: a worn skill, it has no grades"
            : slurry ? $"{ad!.Name}: the slurry's, past its seams; it has no grades"
            : mark ? $"{ad!.Name}  ·  a mark at grade {Crafting.Grade(a!.Tier)}: it works in the Wayfinder's maps"
            : bright ? $"{ad?.Name}  ·  the bright grade, V: past every forge"
            : a!.Tier > cap ? $"{ad?.Name}  ·  grade {Crafting.Grade(a.Tier)}, past what the forge makes of {Crafting.Article(rarity)} piece"
            : a!.Tier >= cap ? $"{ad?.Name}  ·  grade {Crafting.Grade(a.Tier)}, as fine as {Crafting.Article(rarity)} piece is made"
            : $"{ad?.Name}  ·  grade {Crafting.Grade(a.Tier)}; tempers to {Crafting.Grade(cap)}";
        // Its own colour where the power has one (a coal's ember, the slurry's green, a mark's violet);
        // otherwise ink, full at the anvil and a step back elsewhere.
        var ink = coal ? Style.EmberHi : slurry ? ItemViews.SlurryGreen : mark ? ItemViews.MarkInk : bright ? ItemViews.BrightGrade : on ? Kit.Ink : Kit.Ink2;
        words.AddChild(Style.Label(title, open ? Style.TextItalic : Style.UiBold, 17, open ? (on ? Kit.Ink : Kit.Ink2) : ink, true));
        words.AddChild(Style.Label(note, Style.TextItalic, 15, Kit.Dim, true));
        h.AddChild(words);
        row.AddChild(h);
        if (SeamCrafts)
        {
            row.MouseDefaultCursorShape = CursorShape.PointingHand;
            row.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) Pick(k); };
            Nav.Mark(row, $"seam:{k}", () => Pick(k));
        }
        rows[k] = (row, badge);
        var v = Style.V(0, row, Kit.RuleH());
        return v;
    }

''')

# ---------------------------------------------------------------- the crafts as type
replace_block("    /// <summary>A craft as a card, two to a row (the approved bench)", "    void Work(Quote q, Action? sound = null, bool off = false)",
'''    /// <summary>
    /// A craft as type, two to a row (the owner: no boxes holding words, words as type rather than
    /// buttons): its name is the act, in display type, held for what cannot be undone; then what it
    /// makes of the seam or the piece, before and after with the after in ember (as Self's preview);
    /// where it comes from; and what it takes, in small type, or why it cannot be done. lit: the one
    /// the night leans toward (a coal your skills evolve with) is named in ember. (verb: the act's
    /// word when it was a button; the name is the act now.)
    /// </summary>
    Control Card(string title, Quote q, Action act, string verb, string navId, Control? icon = null, string? note = null, bool hold = false, Color? ink = null, bool lit = false)
    {
        var v = Style.V(3);
        v.CustomMinimumSize = new Vector2(CardW, 0);
        v.SetMeta("ok", q.Ok);
        var top = Style.H(10);
        if (icon != null) { icon.SizeFlagsVertical = SizeFlags.ShrinkCenter; top.AddChild(icon); }
        var word = Act(title, q, act, navId, hold, lit ? Style.EmberHi : ink ?? Kit.Ink);
        word.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        top.AddChild(word);
        v.AddChild(top);
        if (q.Before != null && q.After != null)
        {
            var flow = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
            flow.AddThemeConstantOverride("h_separation", 6);
            flow.AddChild(Style.Label(q.Before, Style.Ui, 15, Kit.Dim, false, HorizontalAlignment.Left, false));
            flow.AddChild(new Arrow(Style.Ember) { SizeFlagsVertical = SizeFlags.ShrinkCenter });
            flow.AddChild(Style.Label(q.After, Style.UiBold, 15, Style.EmberHi, false, HorizontalAlignment.Left, false));
            v.AddChild(flow);
        }
        else if (q.After != null) v.AddChild(Style.Label(q.After, Style.UiBold, 15, Style.EmberHi, true));
        if (note != null) v.AddChild(Style.Label(note, Style.TextItalic, 15, lit ? Style.Ember : Kit.Dim, true));
        string cost = Cost(q);
        if (hold && q.Ok) cost = cost == "" ? "held: it cannot be undone" : $"{cost}  ·  held: it cannot be undone";
        if (cost != "") v.AddChild(Style.Label(cost, Style.Ui, 14, q.Ok ? Kit.Ink2 : Kit.Faint, true));
        if (!q.Ok && q.Blocked != closed) v.AddChild(Style.Label(q.Blocked!, Style.TextItalic, 14, Style.Bad, true));
        return v;
    }

    /// <summary>A craft's name as its act: a word in display type, lit under the pointer; held to full
    /// for what cannot be undone (the fill rising under the word); while under the pointer or the
    /// focus, the heat gauge shows what it may spend. What cannot be done now is a faint word.</summary>
    Button Act(string title, Quote q, Action act, string navId, bool hold, Color ink)
    {
        Button b;
        if (hold)
        {
            var h = Style.HoldButton(title, () => { if (q.Ok) act(); else Sound.Sfx.Deny(); });
            h.Text = title;
            Nav.Mark(h, navId, h.Nudge, focus: () => gauge?.Preview(q.HeatLo, q.HeatHi, q.Verb == Verb.Remake), blur: () => gauge?.Clear());
            b = h;
        }
        else
        {
            b = new Button { Text = title, FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand };
            Action press = q.Ok ? act : () => Sound.Sfx.Deny();
            b.Pressed += press;
            Nav.Mark(b, navId, press, focus: () => gauge?.Preview(q.HeatLo, q.HeatHi, q.Verb == Verb.Remake), blur: () => gauge?.Clear());
        }
        Style.Font(b, Style.TextBold, 20, q.Ok ? ink : Kit.Faint, false);
        b.AddThemeColorOverride("font_hover_color", q.Ok ? ink.Lightened(0.25f) : Kit.Faint);
        b.AddThemeColorOverride("font_pressed_color", Style.EmberHi);
        b.AddThemeColorOverride("font_disabled_color", Kit.Faint);
        foreach (var st in new[] { "normal", "hover", "pressed", "focus", "disabled" })
            b.AddThemeStyleboxOverride(st, new StyleBoxEmpty { ContentMarginLeft = 0, ContentMarginRight = 6, ContentMarginTop = 0, ContentMarginBottom = 2 });
        b.Disabled = !q.Ok;
        b.Alignment = HorizontalAlignment.Left;
        b.MouseEntered += () => gauge?.Preview(q.HeatLo, q.HeatHi, q.Verb == Verb.Remake);
        b.MouseExited += () => gauge?.Clear();
        return b;
    }

''')

# The rung row flares softly from its left, not as a box (the strike's moment on the new rows).
rep('''            var flare = new Panel { MouseFilter = MouseFilterEnum.Ignore, Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add } };
            flare.AddThemeStyleboxOverride("panel", Style.Box(fill, edge, 2, 5, 0));
            flare.Size = row.Size;''',
'''            // A light from the row's left edge across it, fading out, added to what is there: no box.
            var flare = new TextureRect
            {
                MouseFilter = MouseFilterEnum.Ignore, Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add },
                Texture = new GradientTexture2D { Width = 64, Height = 4, Gradient = new Gradient { Colors = new[] { edge, fill, fill with { A = 0 } }, Offsets = new[] { 0f, 0.25f, 1f } } },
                ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,
            };
            flare.Size = row.Size;''')

# ---------------------------------------------------------------- the likeness fades into the panel
rep('''        if (figure != null)
        {
            var frame = Style.Panel(Kit.WellBox(0));
            frame.CustomMinimumSize = new Vector2(size.X, size.Y);
            frame.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            frame.AddChild(figure);
            h.AddChild(frame);
        }''',
'''        if (figure != null)
        {
            // No frame: the likeness fades into the panel at its edges (as the counters' keepers do).
            figure.Material = Fade;
            figure.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            h.AddChild(figure);
        }''')
rep('''    /// <summary>Their terms along the panel's foot:''',
'''    static ShaderMaterial? fade;
    /// <summary>A likeness's edges faded into what is behind it (shaders/ui_likeness.gdshader).</summary>
    static ShaderMaterial Fade => fade ??= new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ui_likeness.gdshader") };

    /// <summary>Their terms along the panel's foot:''')

# ---------------------------------------------------------------- the worn row: one line of nine
rep('''        var worn = new GridContainer { Columns = 6, MouseFilter = MouseFilterEnum.Ignore };
        worn.AddThemeConstantOverride("h_separation", 8);
        worn.AddThemeConstantOverride("v_separation", 8);''',
'''        // One line of nine (three tiles under six read as a broken grid).
        var worn = new GridContainer { Columns = 9, MouseFilter = MouseFilterEnum.Ignore };
        worn.AddThemeConstantOverride("h_separation", 5);
        worn.AddThemeConstantOverride("v_separation", 5);''')
rep('''            var view = ItemViews.Slot(it, 72, it != null && it.Uid == sel && !making, null, false, it != null ? () => Choose(it.Uid) : null, null,
                over => Hover(it, over), glyph, name, $"worn:{i++}");''',
'''            var view = ItemViews.Slot(it, 50, it != null && it.Uid == sel && !making, null, false, it != null ? () => Choose(it.Uid) : null, null,
                over => Hover(it, over), glyph, name, $"worn:{i++}");''')
rep('''        v.AddChild(Style.Panel(Kit.WellBox(6), worn));
        if (fallback)''', '''        v.AddChild(worn);
        if (fallback)''')

open(P, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
print("ok")
