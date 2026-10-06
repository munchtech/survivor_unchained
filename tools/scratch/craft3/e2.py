"""The bench's irreversible acts held, not asked twice (UI design's hold-to-confirm rule)."""
from ed import sub
F = "src/Ui/Forge.cs"
sub(F, [
    ("    bool breaking, steeping;\n    /// <summary>The donor a binding is armed to unmake (\"uid:index\"): asked once, done the second time.</summary>\n    string? unmaking;\n", ""),
    ("        void Open() { if (making) return; making = true; sel = null; breaking = false; Sound.Sfx.Click(); Refresh(); }",
     "        void Open() { if (making) return; making = true; sel = null; Sound.Sfx.Click(); Refresh(); }"),
])
sub(F, [("        seam = -1;\n        breaking = false;\n        making = false;", "        seam = -1;\n        making = false;")])
sub(F, [("        seam = k;\n        breaking = false;\n", "        seam = k;\n")])
# Break down: held.
sub(F, [("""            row.AddChild(Tile(breaking ? "Break it down for good?" : "Break down", $"For {gives}. It cannot be undone.", q, () =>
            {
                if (!breaking) { breaking = true; Sound.Sfx.Hover(); Refresh(); return; }
                breaking = false;
                Work(q, Sound.Sfx.Shatter, off: true);
            }, breaking ? "Break it" : "Break down", "break", worn ? "Worn: take it off first to break it down." : q.Ok ? null : q.Blocked));""",
"""            row.AddChild(Tile("Break down", $"For {gives}. It cannot be undone.", q, () => Work(q, Sound.Sfx.Shatter, off: true),
                "Break down", "break", worn ? "Worn: take it off first to break it down." : q.Ok ? null : q.Blocked, hold: true));""")])
# Bind: held.
sub(F, [("""            string key = $"{d.Uid}:{i}";
            bool armed = unmaking == key;
            var dd = Items.Get(d.Def);""", """            var dd = Items.Get(d.Def);"""),
("""            string note = armed ? $"Your {Inventory.Name(d)} is unmade for it. Press again to bind."
                : roll.Tier > grade ? $"From your {Inventory.Name(d)}, where it is grade {Crafting.Grade(roll.Tier)}; {Crafting.Article(rarity)} piece holds {Crafting.Grade(grade)}"
                : $"From your {Inventory.Name(d)}";
            var card = Craft(armed ? "Unmake it" : "Bind", q, () =>
            {
                if (unmaking != key) { unmaking = key; Sound.Sfx.Hover(); Refresh(); return; }
                unmaking = null;
                Work(q, () => { Sound.Sfx.Cage(); Sound.Sfx.Discovery(); });
            }, lead, ItemPhotos.Icon(dd.Icon, 44, Style.RarityOf(d.Rarity)), $"bind:{n++}", note, armed);""",
"""            // What it costs is said on the card, since it is held, not asked twice: the donor is unmade.
            string note = $"Out of your {Inventory.Name(d)}, which is unmade"
                + (roll.Tier > grade ? $" (grade {Crafting.Grade(roll.Tier)} there; {Crafting.Article(rarity)} piece holds {Crafting.Grade(grade)})" : "");
            var card = Craft("Bind", q, () => Work(q, () => { Sound.Sfx.Cage(); Sound.Sfx.Discovery(); }),
                lead, ItemPhotos.Icon(dd.Icon, 44, Style.RarityOf(d.Rarity)), $"bind:{n++}", note, hold: true);""")])
# Steep: held.
sub(F, [("""        words.AddChild(Style.Label(steeping ? "Whatever it comes to, it is set for good: no hand will work it again." : "Whatever it comes to, it is set for good after.",
            Style.UiBold, Style.Small, steeping ? Style.Bad : Style.Ink, true));""",
"""        words.AddChild(Style.Label("Whatever it comes to, it is set for good after: no hand will work it again.", Style.UiBold, Style.Small, Style.Ink, true));"""),
("""        var b = Press(Style.Button(steeping ? "Steep it" : "Steep", null, q.Ok, true), q, () =>
        {
            if (!steeping) { steeping = true; Sound.Sfx.Hover(); Refresh(); return; }
            steeping = false;
            Work(q, Sound.Sfx.Pour);
        }, "steep");
        if (steeping) b.AddThemeColorOverride("font_color", Style.Bad);
""", """        var b = Hold("Steep", q, () => Work(q, Sound.Sfx.Pour), "steep");
"""),
("""        var panel = Style.Panel(Style.Box(new Color("#11170f"), (steeping ? Style.Bad : ItemViews.SlurryGreen) with { A = steeping ? 0.8f : 0.45f }, steeping ? 2 : 1, 6, 16), slab);""",
"""        var panel = Style.Panel(Style.Box(new Color("#11170f"), ItemViews.SlurryGreen with { A = 0.45f }, 1, 6, 16), slab);""")])
sub(F, [("""        if (a == Act.Cancel && breaking) { breaking = false; Refresh(); return true; }
        if (a == Act.Cancel && (steeping || unmaking != null)) { steeping = false; unmaking = null; Refresh(); return true; }
""", "")])
# Craft and Tile take a held press.
sub(F, [("""    Control Craft(string title, Quote q, Action act, string lead, Control? icon, string navId, string? note = null, bool warn = false)""",
         """    Control Craft(string title, Quote q, Action act, string lead, Control? icon, string navId, string? note = null, bool warn = false, bool hold = false)"""),
("""        var b = Press(Style.Button(title, null, q.Ok, true), q, act, navId);
        if (warn) b.AddThemeColorOverride("font_color", Style.Bad);
        b.SizeFlagsVertical = SizeFlags.ShrinkCenter;""",
"""        var b = hold ? Hold(title, q, act, navId) : Press(Style.Button(title, null, q.Ok, true), q, act, navId);
        if (warn) b.AddThemeColorOverride("font_color", Style.Bad);
        b.SizeFlagsVertical = SizeFlags.ShrinkCenter;"""),
("""    Control Tile(string title, string? after, Quote q, Action act, string button, string navId, string? quiet)""",
 """    Control Tile(string title, string? after, Quote q, Action act, string button, string navId, string? quiet, bool hold = false)"""),
("""        var b = Press(Style.Button(button, null, q.Ok, true), q, act, navId);
        b.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;""",
 """        var b = hold ? Hold(button, q, act, navId) : Press(Style.Button(button, null, q.Ok, true), q, act, navId);
        b.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;"""),
("""    /// <summary>A craft as a row: what it does (before and after), what it takes, and the press. A note""",
 """    /// <summary>A press for what cannot be undone: held to full (Style.HoldButton), never asked twice; while
    /// under the pointer or the focus, the heat gauge shows what it may spend, as a press does.</summary>
    Button Hold(string title, Quote q, Action act, string navId)
    {
        var b = Style.HoldButton(title, () => { if (q.Ok) act(); else Sound.Sfx.Deny(); });
        b.Disabled = !q.Ok;
        void Show() => gauge?.Preview(q.HeatLo, q.HeatHi, q.Verb == Verb.Remake);
        void Hide() => gauge?.Clear();
        b.MouseEntered += Show;
        b.MouseExited += Hide;
        Nav.Mark(b, navId, b.Nudge, focus: Show, blur: Hide);
        return b;
    }

    /// <summary>A craft as a row: what it does (before and after), what it takes, and the press. A note"""),
])
