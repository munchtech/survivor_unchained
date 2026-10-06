import io
R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src'

def edit(path, pairs):
    p = R + '\\' + path
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:60])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit(r'Game\Controls.cs', [(
    '["ArrowUp"] = "↑", ["ArrowDown"] = "↓", ["ArrowLeft"] = "←", ["ArrowRight"] = "→",',
    '["ArrowUp"] = "Up", ["ArrowDown"] = "Down", ["ArrowLeft"] = "Left", ["ArrowRight"] = "Right",')])

edit(r'Ui\ArtsScreen.cs', [(
    'Style.Label(f.Name + (on ? "  ✓" : ""),',
    'Style.Label(f.Name + (on ? "  ·  chosen" : ""),')])

edit(r'Ui\Book.cs', [(
    'Text = (def.Mystery ? "◦ " : "• ") + def.Name,',
    'Text = (def.Mystery ? "? " : "• ") + def.Name,')])

edit(r'Ui\GameHud.cs', [(
    '''            // Evolved: a star; ready to evolve: an arrow up; otherwise the rank.
            rankText.Text = evolved ? "★" : canEvolve ? "▲" : rank.ToString();''',
    '''            // The rank, gold on ember when it has evolved or is ready to (the rim says which: steady or breathing).
            rankText.Text = rank.ToString();''')])

edit(r'Ui\Style.cs', [(
    '''    /// <summary>Rarity is never colour alone: each also has a count of marks (◆).</summary>
    public static string RarityMarks(int r) => new('◆', Math.Clamp(r, 0, Rarity.Length - 1) + 1);''',
    '''    /// <summary>Rarity is never colour alone: each also has a count of small
    /// diamonds, one for common up to six (drawn, not typed: the faces lack them).</summary>
    public static HBoxContainer Gems(int r, float size = 7)
    {
        int n = Math.Clamp(r, 0, Rarity.Length - 1) + 1;
        var h = new HBoxContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
        h.AddThemeConstantOverride("separation", (int)(size * 0.9f));
        for (int i = 0; i < n; i++)
        {
            var box = new Control { CustomMinimumSize = new Vector2(size * 1.2f, size * 1.6f), MouseFilter = Control.MouseFilterEnum.Ignore };
            box.AddChild(new ColorRect { Color = RarityOf(r), Size = new Vector2(size, size), Position = new Vector2(size * 0.6f, size * 0.1f), Rotation = Mathf.Pi / 4, MouseFilter = Control.MouseFilterEnum.Ignore });
            h.AddChild(box);
        }
        return h;
    }'''), (
    '''        bool face = PadColours.TryGetValue(name, out var col);
        string text = name.StartsWith("D-pad ") ? name[6..] switch { "up" => "▲", "down" => "▼", "left" => "◀", _ => "▶" } : name;''',
    '''        if (name.StartsWith("D-pad")) return Dpad(name.Length > 6 ? name[6..] : "");
        bool face = PadColours.TryGetValue(name, out var col);
        string text = name;'''), (
    '''    /// <summary>The key or button for an action, as the device last touched has it.</summary>''',
    '''    /// <summary>The D-pad as a little cross, the arm meant lit (none: all four).</summary>
    static Control Dpad(string arm)
    {
        var c = new Control { CustomMinimumSize = new Vector2(26, 26), MouseFilter = Control.MouseFilterEnum.Ignore };
        var back = new Panel { Size = new Vector2(26, 26), MouseFilter = Control.MouseFilterEnum.Ignore };
        back.AddThemeStyleboxOverride("panel", Box(new Color("#0d0c10"), GoldDim, 1, 6, 0));
        c.AddChild(back);
        void Arm(string which, Vector2 at, Vector2 size) =>
            c.AddChild(new ColorRect { Position = at, Size = size, Color = arm == "" || arm == which ? GoldHi : GoldDim with { A = 0.6f }, MouseFilter = Control.MouseFilterEnum.Ignore });
        Arm("up", new Vector2(10, 4), new Vector2(6, 7));
        Arm("down", new Vector2(10, 15), new Vector2(6, 7));
        Arm("left", new Vector2(4, 10), new Vector2(7, 6));
        Arm("right", new Vector2(15, 10), new Vector2(7, 6));
        return c;
    }

    /// <summary>The key or button for an action, as the device last touched has it.</summary>''')])
print('done')
