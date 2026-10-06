p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\GameHud.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

def cut(a, b, new):
    global s
    i = s.index(a)
    j = s.index(b, i)
    s = s[:i] + new + s[j:]

rep("""    TextureRect hpFill = null!;
    ColorRect hpTrail = null!, hpShield = null!, hpLow = null!;
    Label hpText = null!;
    HBoxContainer statuses = null!;
    Control heart = null!;""", """    // Health as a globe at the console's left end (docs/UI_DESIGN.md, "HUD").
    Globe globe = null!;
    HBoxContainer statuses = null!;
    Control heart = null!;
    /// <summary>The console's middle: the globe at its left, the art's ring at its right.</summary>
    const float ConsoleX = 600, ConsoleW = 720;""")
cut("""    void BuildVitals()
    {""", """    void BuildArsenal()""", """    void BuildVitals()
    {
        // The console: a forged plate along the foot, under the skills, the globe and the ring at its ends.
        var plate = new Panel { Position = new Vector2(ConsoleX, 1080 - 98), Size = new Vector2(ConsoleW, 130), MouseFilter = Control.MouseFilterEnum.Ignore };
        plate.AddThemeStyleboxOverride("panel", UiArt.Frame("console", OrnateBox.Make(OrnateBox.Kind.Plate, 0)));
        combat.AddChild(plate);
        globe = new Globe(66) { Position = new Vector2(ConsoleX - 150, 1080 - 156) };
        globe.PivotOffset = globe.Size / 2;
        heart = globe;
        play.AddChild(globe);
        // What is on you (burning, shielded, quickened), over the globe.
        statuses = Style.H(6);
        statuses.Position = new Vector2(ConsoleX - 150, 1080 - 156 - 40);
        play.AddChild(statuses);
    }

""")
rep("""        col.Position = new Vector2(460, 1080 - 26 - 140);
        col.Size = new Vector2(1000, 140);""", """        col.Position = new Vector2(ConsoleX, 1080 - 14 - 150);
        col.Size = new Vector2(ConsoleW, 150);""")
cut("""    void BuildHands()
    {""", """    static readonly string[] Numerals = ["I", "II", "III", "IV", "V"];""", """    void BuildHands()
    {
        // The art's ring at the console's right end, the draught and the dash beside it.
        var h = Style.H(22);
        h.Alignment = BoxContainer.AlignmentMode.Begin;
        h.Position = new Vector2(ConsoleX + ConsoleW + 14, 1080 - 14 - 150);
        h.Size = new Vector2(460, 150);
        combat.AddChild(h);
        Control Hand(Control art, Act key, string label, out Label name)
        {
            var v = Style.V(8);
            v.Alignment = BoxContainer.AlignmentMode.End;
            var c = new CenterContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
            c.AddChild(art);
            v.AddChild(c);
            name = Style.Label(label, Style.UiBold, Style.Caption, Style.Ink);
            var row = Style.H(5, Style.Prompt(key), name);
            row.Alignment = BoxContainer.AlignmentMode.Center;
            handKeys.Add((key, row));
            v.AddChild(row);
            h.AddChild(v);
            return v;
        }
        const float R = 116;
        var ab = new Control { CustomMinimumSize = new Vector2(R, R), MouseFilter = Control.MouseFilterEnum.Ignore };
        abilityRing = new Ring { Size = new Vector2(R, R), MouseFilter = Control.MouseFilterEnum.Ignore };
        ab.AddChild(abilityRing);
        // The art's ring painted over the drawn one (hud/ring_art.png, a ring with an empty middle).
        if (UiArt.Art("hud/ring_art.png") is { } ringArt)
        {
            var rr = new TextureRect { Texture = ringArt, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, MouseFilter = Control.MouseFilterEnum.Ignore, Size = ringArt.GetSize() * (R / 89f) };
            rr.Position = (new Vector2(R, R) - rr.Size) / 2;
            ab.AddChild(rr);
        }
        abilityGlyph = Glyphs.Icon("shield", 54);
        abilityGlyph.Position = new Vector2((R - 54) / 2, (R - 54) / 2); abilityGlyph.Size = new Vector2(54, 54);
        ab.AddChild(abilityGlyph);
        abilityCd = Style.Label("", Style.Display, 28, Colors.White, false, HorizontalAlignment.Center);
        abilityCd.Size = new Vector2(R, R);
        abilityCd.VerticalAlignment = VerticalAlignment.Center;
        ab.AddChild(abilityCd);
        Hand(ab, Act.Ability, "", out abilityName);
        var q = new Panel { CustomMinimumSize = new Vector2(60, 60), MouseFilter = Control.MouseFilterEnum.Ignore };
        q.AddThemeStyleboxOverride("panel", OrnateBox.Make(OrnateBox.Kind.Slab, 0));
        var qi = ItemPhotos.Icon("potion", 50, Hex("#ff8a80"));
        qi.Position = new Vector2(5, 3); qi.Size = new Vector2(50, 50);
        q.AddChild(qi);
        quickQty = Style.Label("", Style.UiHeavy, 14, Colors.White);
        quickQty.Position = new Vector2(44, 40);
        q.AddChild(quickQty);
        quick = Hand(q, Act.Ultimate, "Draught", out _);
        dashPips = Style.H(5);
        Hand(dashPips, Act.Dash, "Dash", out _);
    }

""")
# The globe takes the bar's work.
rep("""        hpShown = k;
        hpFill.Size = new Vector2(360 * k, 24);
        hpShield.Size = new Vector2(360 * (float)Math.Clamp(p.Shield / max, 0, 1), 7);
        hpText.Text = $"{Math.Ceiling(Math.Max(p.Hp, 0))}  /  {Math.Round(max)}";""", """        hpShown = k;
        globe.Level = k;
        globe.Shield = (float)Math.Clamp(p.Shield / max, 0, 1);
        globe.Number = $"{Math.Ceiling(Math.Max(p.Hp, 0))}";
        globe.QueueRedraw();""")
rep("""        // The trail behind health catches up after a moment.
        float trail = hpTrail.Size.X / 360;
        if (trail > hpShown) { trailWait += dt; trailShown = trailWait > 0.35f ? Mathf.MoveToward(trail, hpShown, dt * 1.6f) : trail; }
        else { trailWait = 0; trailShown = hpShown; }
        hpTrail.Size = new Vector2(360 * trailShown, 24);
        bool low = hpShown < 0.35f && combat.Visible;
        float now = Time.GetTicksMsec() / 1000f;
        float beat = low ? 1 + 0.12f * Mathf.Max(0, Mathf.Sin(now * 7)) : 1;
        heart.Scale = new Vector2(beat, beat);
        hpLow.Color = new Color(1, 0.24f, 0.24f, low ? 0.15f + 0.15f * Mathf.Sin(now * 7) : 0);""", """        // The trail behind health catches up after a moment.
        float trail = globe.Trail;
        if (trail > hpShown) { trailWait += dt; trailShown = trailWait > 0.35f ? Mathf.MoveToward(trail, hpShown, dt * 1.6f) : trail; }
        else { trailWait = 0; trailShown = hpShown; }
        globe.Trail = trailShown;
        bool low = hpShown < 0.35f && combat.Visible;
        float now = Time.GetTicksMsec() / 1000f;
        // Low, the globe beats like a heart and its glass flushes.
        float beat = low ? 1 + 0.06f * Mathf.Max(0, Mathf.Sin(now * 7)) : 1;
        heart.Scale = new Vector2(beat, beat);
        globe.Pulse = low ? 0.5f + 0.5f * Mathf.Sin(now * 7) : 0;
        globe.QueueRedraw();""")
# The hint now has the bottom-left to itself.
rep("""        hintBox.OffsetLeft = 34; hintBox.OffsetBottom = -134;""", """        hintBox.OffsetLeft = 34; hintBox.OffsetBottom = -40;""")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
