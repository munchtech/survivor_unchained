p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Panels.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

# The night pauses: dark at the edges, the ember's fire behind the cards.
rep("""        AddChild(Style.Scrim(null, 0.74f));
        var col = Style.V(Style.Gap2);""", """        AddChild(new Backdrop(null, 0.8f));
        var fire = new TextureRect
        {
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(1, 0.42f, 0.12f, 0.26f), new Color(0.8f, 0.2f, 0.05f, 0.1f), new Color(0.6f, 0.1f, 0.02f, 0) }, Offsets = new[] { 0f, 0.5f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f), Width = 256, Height = 256,
            },
            Position = new Vector2(160, 160), Size = new Vector2(1600, 900),
        };
        AddChild(fire);
        var col = Style.V(Style.Gap2);""")
rep("""        col.AddChild(Style.Label(head.ToUpperInvariant(), Style.Display, 48, new Color("#ffe6b8"), false, HorizontalAlignment.Center));
        col.AddChild(Style.Flourish());""", """        var plaque = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        plaque.AddChild(new Plaque(head, 46, 170, new Color("#ffe6b8")));
        col.AddChild(plaque);""")
# The build strip on a slab of its own.
rep("""    Control BuildStrip(Battle b)
    {
        var strip = Style.H(Style.Gap2);
        strip.Alignment = BoxContainer.AlignmentMode.Center;
        strip.AddChild(Style.Label("YOUR BUILD", Style.UiHeavy, Style.Caption, Style.Gold));""", """    Control BuildStrip(Battle b)
    {
        var strip = Style.H(Style.Gap2);
        strip.Alignment = BoxContainer.AlignmentMode.Center;
        var slab = Style.Panel(Style.Slab(12), strip);
        slab.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        strip.AddChild(Style.Label("YOUR BUILD", Style.UiHeavy, Style.Caption, Style.Gold));""")
rep("""            buildChips[id] = chip;
            strip.AddChild(chip);
        }
        return strip;
    }""", """            buildChips[id] = chip;
            strip.AddChild(chip);
        }
        return slab;
    }""")
# The icon on a medallion in its colour; the frame a crested card (drawn in Mark).
rep("""        var art = new CenterContainer { CustomMinimumSize = new Vector2(CardW - 44, 128), MouseFilter = MouseFilterEnum.Ignore };
        var disc = new Panel { CustomMinimumSize = new Vector2(112, 112), MouseFilter = MouseFilterEnum.Ignore };
        var ds = Style.Box(color.Darkened(0.82f) with { A = 0.95f }, color with { A = 0.7f }, 2, 56, 0);
        ds.ShadowColor = color with { A = 0.25f };
        ds.ShadowSize = 16;
        disc.AddThemeStyleboxOverride("panel", ds);
        var glyph = Glyphs.Icon(o.Icon, 68, color);
        glyph.Position = new Vector2(22, 22);
        glyph.Size = new Vector2(68, 68);
        disc.AddChild(glyph);
        art.AddChild(disc);
        v2.AddChild(art);""", """        var art = new CenterContainer { CustomMinimumSize = new Vector2(CardW - 44, 132), MouseFilter = MouseFilterEnum.Ignore };
        var medal = new Medallion(124, "", o.Icon) { Ring = color, Ink = color.Lightened(0.15f), Core = color.Darkened(0.82f), Name = "Medal" };
        art.AddChild(medal);
        v2.AddChild(art);""")
rep("""            var edge = banishing ? new Color("#ff6a4a") : ch ? Style.GoldHi : rc with { A = on ? 0.95f : 0.55f };
            var s = Style.Box(new Color(0.09f, 0.075f, 0.1f, 0.98f).Lerp(rc, banishing && on ? 0.0f : 0.05f), edge, ch ? 3 : on ? 2 : 1, 10, 0);
            s.ShadowColor = on ? (banishing ? new Color("#ff6a4a") : rc) with { A = 0.4f } : new Color(0, 0, 0, 0.7f);
            s.ShadowSize = on ? 30 : 18;
            panel.AddThemeStyleboxOverride("panel", UiArt.Has((string)panel.GetMeta("frame")) ? UiArt.Frame((string)panel.GetMeta("frame"), s) : s);""",
"""            var edge = banishing && on ? new Color("#ff6a4a") : ch ? Style.GoldHi : rc;
            // A crested card: its rarity in the crest and the corners, a glow when lifted.
            var s = OrnateBox.Make(OrnateBox.Kind.Card, 0, edge);
            s.Crest = 120;
            s.Glow = on ? 1.4f : 0;
            s.Top = new Color("#211c26").Lerp(rc, 0.05f);
            panel.AddThemeStyleboxOverride("panel", UiArt.Has((string)panel.GetMeta("frame")) ? UiArt.Frame((string)panel.GetMeta("frame"), s) : s);
            if (b.FindChild("Medal", true, false) is Medallion m) { m.Lit = on; m.QueueRedraw(); }""")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
