p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot\src\Fx\Hits.cs'
s = open(p, encoding='utf-8').read()
old = '''    readonly List<(MeshInstance3D Mesh, ShaderMaterial Mat, float T, float Life)> arcs = new();
    int nextSpray, nextNumber, nextArc;'''
new = '''    readonly List<(MeshInstance3D Mesh, ShaderMaterial Mat, float T, float Life)> arcs = new();
    /// <summary>A boss's words: its moves' names and the BREAK. Their own few, held as long as
    /// the mark they name: in the numbers' pool, a fast build's hits took them in a frame.</summary>
    readonly List<(Label3D Label, float T, float Life, Vector3 At)> words = new();
    int nextSpray, nextNumber, nextArc, nextWord;'''
assert old in s; s = s.replace(old, new)
old = '''        var shader = GD.Load<Shader>("res://shaders/slash.gdshader");'''
new = '''        for (int i = 0; i < 8; i++)
        {
            var l = new Label3D
            {
                Billboard = BaseMaterial3D.BillboardModeEnum.Enabled, NoDepthTest = true, FontSize = 64, OutlineSize = 18,
                PixelSize = 0.006f, OutlineModulate = new Color(0.06f, 0.02f, 0.01f), Visible = false,
                Shaded = false, RenderPriority = 12, OutlineRenderPriority = 11,
            };
            if (UiFont() is { } font) l.Font = font;
            AddChild(l);
            words.Add((l, 1, 1, Vector3.Zero));
        }
        var shader = GD.Load<Shader>("res://shaders/slash.gdshader");'''
assert old in s; s = s.replace(old, new)
old = '''    /// <summary>A word or number that rises from where something happened and fades.</summary>'''
new = '''    /// <summary>A boss's word over its mark: steady for `life` seconds, then gone in a breath.</summary>
    public void Word(Vector3 at, string text, Color color, int size, float life)
    {
        int i = nextWord++ % words.Count;
        var l = words[i].Label;
        l.Text = text;
        l.FontSize = size;
        l.Modulate = color;
        l.GlobalPosition = at;
        l.Visible = true;
        words[i] = (l, 0, Mathf.Max(0.6f, life), at);
    }

    static Font? font;
    /// <summary>The interface's heavy face, so a move's name reads as the HUD does.</summary>
    static Font? UiFont() => font ??= ResourceLoader.Exists("res://art/fonts/alegreya-sans-800.woff2") ? GD.Load<Font>("res://art/fonts/alegreya-sans-800.woff2") : null;

    /// <summary>A word or number that rises from where something happened and fades.</summary>'''
assert old in s; s = s.replace(old, new)
old = '''        for (int i = 0; i < arcs.Count; i++)
        {
            var (m, mat, t, life) = arcs[i];'''
new = '''        for (int i = 0; i < words.Count; i++)
        {
            var (l, t, life, at) = words[i];
            if (t >= 1) continue;
            t += dt / life;
            // In quickly, a slow lift while it holds, out over its last fifth.
            float a = Mathf.Min(1, t * life / 0.12f) * (t < 0.8f ? 1 : 1 - (t - 0.8f) / 0.2f);
            l.GlobalPosition = at + Vector3.Up * 0.35f * t;
            var c = l.Modulate; c.A = a; l.Modulate = c;
            l.OutlineModulate = new Color(l.OutlineModulate, a);
            if (t >= 1) l.Visible = false;
            words[i] = (l, t, life, at);
        }
        for (int i = 0; i < arcs.Count; i++)
        {
            var (m, mat, t, life) = arcs[i];'''
assert old in s; s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot\src\Fx\BattleFx.cs'
s = open(p, encoding='utf-8').read()
old = '''                    // A boss's move, named over it for a moment.
                    if (e.Label is { Length: > 0 } label)
                        Hits.Text(V(e.X, Y(e.X, e.Z) + 2.2, e.Z), label, col with { A = 1 }, 40);'''
new = '''                    // A boss's move, named over its mark for as long as the mark stands (a lane or a
                    // cone from the boss is named over the boss, where the eye already is).
                    if (e.Label is { Length: > 0 } label)
                        Hits.Word(V(e.X, Y(e.X, e.Z) + 3.4, e.Z), label.ToUpperInvariant(), WordColour(col), 46, (float)Math.Min(2.5, e.Duration + 0.3));'''
assert old in s; s = s.replace(old, new)
old = '''                    Hits.Text(at, $"BREAK {Math.Round(br.Amount):N0}", new Color(2.4f, 1.9f, 0.6f), 76);'''
new = '''                    Hits.Word(at, $"BREAK {Math.Round(br.Amount):N0}", new Color(2.4f, 1.9f, 0.6f), 84, 2.2f);'''
assert old in s; s = s.replace(old, new)
old = '''    /* ------------------------------------------------------------- events -- */'''
new = '''    /// <summary>A mark's colour lifted for its word: the ground's tint is dim by design, the word must read over a crowd.</summary>
    static Color WordColour(Color c)
    {
        var h = c with { A = 1 };
        float m = Mathf.Max(h.R, Mathf.Max(h.G, h.B));
        return m < 1.4f ? new Color(h.R / Mathf.Max(0.01f, m) * 1.4f, h.G / Mathf.Max(0.01f, m) * 1.4f, h.B / Mathf.Max(0.01f, m) * 1.4f) : h;
    }

    /* ------------------------------------------------------------- events -- */'''
assert old in s; s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print("ok")
