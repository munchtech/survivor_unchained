using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>One lamp on the Ford-Warden's bar: an iron cage round a flame, drawn in code. It tracks whether it
/// should burn and plays LampMarkAnim's flare, fade and bloom when that changes. Drawn on a 16 x 22 grid and
/// scaled to its size (24 x 32 on the boss bar, 18 x 24 for the off-screen pointers).</summary>
public partial class LampMark : Control
{
    public const float W = 24, H = 32;
    const float GridW = 16, GridH = 22;
    bool lit = true;
    float since = float.PositiveInfinity;

    public LampMark() : this(W, H) { }

    public LampMark(float w, float h)
    {
        Size = CustomMinimumSize = new Vector2(w, h);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    /// <summary>Where the mark should be; a change starts its animation.</summary>
    public bool Burning
    {
        get => lit;
        set { if (value != lit) { lit = value; since = 0; } }
    }

    public override void _Process(double delta)
    {
        if (float.IsPositiveInfinity(since)) return;
        since += (float)delta;
        if (since > 1.5f) since = float.PositiveInfinity;
        QueueRedraw();
    }

    public override void _Draw()
    {
        float b = LampMarkAnim.Brightness(lit, since), hs = LampMarkAnim.HaloScale(lit, since);
        DrawSetTransform(Vector2.Zero, 0, new Vector2(Size.X / GridW, Size.Y / GridH));
        var c = new Vector2(GridW / 2, 11);
        var halo = new Color("8ac8ff");
        if (b > 0.01f)
            for (int i = 0; i < 5; i++)
            {
                float f = i / 4f; // 0 outer .. 1 inner
                DrawCircle(c, 11.3f * hs * (1f - f * 0.75f), new Color(halo, 0.35f * 0.22f * (1f + f * 1.5f) * Mathf.Min(b, 1.4f)));
            }
        var iron = new Color("6b5434"); var dark = new Color("2a2016");
        // The flame: a diamond/teardrop core over a blue body, or dark glass.
        if (b > 0.01f)
        {
            float k = Mathf.Min(b, 1.4f);
            var body = new Vector2[] { new(c.X, 4.5f), new(c.X + 3.6f, 12f), new(c.X, 17f), new(c.X - 3.6f, 12f) };
            DrawColoredPolygon(body, new Color(halo, Mathf.Clamp(k, 0, 1)));
            var core = new Vector2[] { new(c.X, 7.5f), new(c.X + 1.9f, 12.5f), new(c.X, 15f), new(c.X - 1.9f, 12.5f) };
            DrawColoredPolygon(core, new Color(new Color("e8f6ff"), Mathf.Clamp(k, 0, 1)).Lerp(new Color(1, 1, 1, 1), Mathf.Clamp(k - 1f, 0, 0.4f)));
        }
        if (b < 1f)
        {
            var glass = new Color(new Color("1c2430"), 1f - Mathf.Clamp(b, 0, 1));
            DrawColoredPolygon(new Vector2[] { new(c.X, 4.5f), new(c.X + 3.6f, 12f), new(c.X, 17f), new(c.X - 3.6f, 12f) }, glass);
        }
        // The cage: two side bars, a cap and a base, each with a dark outline.
        DrawRect(new Rect2(2, 2, 12, 3), dark); DrawRect(new Rect2(3, 3, 10, 1), iron);        // cap
        DrawRect(new Rect2(2, 19, 12, 3), dark); DrawRect(new Rect2(3, 20, 10, 1), iron);      // base
        DrawRect(new Rect2(2, 4, 3, 15), dark); DrawRect(new Rect2(3, 4, 1, 15), iron);        // left bar
        DrawRect(new Rect2(11, 4, 3, 15), dark); DrawRect(new Rect2(12, 4, 1, 15), iron);      // right bar
    }
}

/// <summary>The row of lamp marks beside the boss's name: a small "LAMPS" label and N marks 10 px apart.
/// Rebuilds only when the count changes; Feed sets how many burn (marks 0..lit-1, so they go out from the right).</summary>
public partial class LampMarks : Control
{
    const float Gap = 12, LabelW = 58, LabelGap = 8;
    readonly Label label;
    LampMark[] marks = System.Array.Empty<LampMark>();

    public LampMarks()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        label = Style.Label("LAMPS", Style.Text, 15, Style.InkDim, false, HorizontalAlignment.Left);
        label.MouseFilter = MouseFilterEnum.Ignore;
        AddChild(label);
        Visible = false;
    }

    /// <summary>Shows `count` marks (hidden at 0) with `lit` burning; left edge at `leftX`, centered on `midY` in the parent.</summary>
    public void Feed(int count, int lit, float leftX, float midY)
    {
        Visible = count > 0;
        if (count <= 0) return;
        if (count != marks.Length)
        {
            foreach (var m in marks) m.QueueFree();
            marks = new LampMark[count];
            for (int i = 0; i < count; i++)
            {
                marks[i] = new LampMark { Position = new Vector2(LabelW + LabelGap + i * (LampMark.W + Gap), 0), Burning = i < lit };
                AddChild(marks[i]);
            }
            float mw = count * LampMark.W + (count - 1) * Gap;
            Size = new Vector2(LabelW + LabelGap + mw, LampMark.H);
            label.Position = new Vector2(0, (LampMark.H - 21) / 2);
            label.Size = new Vector2(LabelW, 21);
        }
        for (int i = 0; i < marks.Length; i++) marks[i].Burning = i < lit;
        Position = new Vector2(leftX, midY - LampMark.H / 2);
    }
}

/// <summary>Off-screen pointers to the Ford-Warden's lit lamp posts: at the screen edge, a small lit lamp mark and a
/// bronze chevron pointing out along the line from the screen's middle to the post. Each fades over 0.2 s.</summary>
public partial class LampPointers : Control
{
    public readonly record struct Pointer(int Id, Vector2 At, Vector2 Dir);
    const float FadeTime = 0.2f;
    static readonly Color Chevron = new("#c8a060");
    sealed class Slot { public LampMark Mark = null!; public Vector2 At, Dir; public float A; public bool Want; }
    readonly System.Collections.Generic.Dictionary<int, Slot> slots = new();

    public LampPointers() { MouseFilter = MouseFilterEnum.Ignore; }

    public void Show(System.Collections.Generic.IEnumerable<Pointer> list)
    {
        foreach (var s in slots.Values) s.Want = false;
        foreach (var p in list)
        {
            if (!slots.TryGetValue(p.Id, out var s))
            {
                s = new Slot { Mark = new LampMark(18, 24) };
                AddChild(s.Mark);
                s.Mark.Modulate = new Color(1, 1, 1, 0);
                slots[p.Id] = s;
            }
            s.At = p.At; s.Dir = p.Dir; s.Want = true;
            s.Mark.Position = p.At - s.Mark.Size / 2;
        }
    }

    public override void _Process(double delta)
    {
        bool any = false;
        foreach (var s in slots.Values)
        {
            s.A = Mathf.MoveToward(s.A, s.Want ? 1 : 0, (float)delta / FadeTime);
            s.Mark.Modulate = new Color(1, 1, 1, s.A);
            s.Mark.Visible = s.A > 0;
            any |= s.A > 0;
        }
        if (any) QueueRedraw();
    }

    public override void _Draw()
    {
        foreach (var s in slots.Values)
        {
            if (s.A <= 0) continue;
            var c = Chevron with { A = s.A };
            var d = s.Dir; var side = new Vector2(-d.Y, d.X);
            var tip = s.At + d * 34; // 12 px of gap beyond the mark's half height at most
            DrawPolyline(new[] { tip - d * 9 + side * 8, tip, tip - d * 9 - side * 8 }, new Color(0.1f, 0.08f, 0.05f, 0.7f * s.A), 6, true);
            DrawPolyline(new[] { tip - d * 9 + side * 8, tip, tip - d * 9 - side * 8 }, c, 3, true);
        }
    }
}
