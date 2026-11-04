using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>One lamp on the Ford-Warden's bar: an iron cage round a flame, drawn in code. It tracks whether it
/// should burn and plays LampMarkAnim's flare, fade and bloom when that changes. 16 x 22.</summary>
public partial class LampMark : Control
{
    public const float W = 16, H = 22;
    bool lit = true;
    float since = float.PositiveInfinity;

    public LampMark()
    {
        Size = CustomMinimumSize = new Vector2(W, H);
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
        var c = new Vector2(W / 2, 11);
        var halo = new Color("8ac8ff");
        if (b > 0.01f)
            for (int i = 0; i < 5; i++)
            {
                float f = i / 4f; // 0 outer .. 1 inner
                DrawCircle(c, 11f * hs * (1f - f * 0.75f), new Color(halo, 0.35f * 0.22f * (1f + f * 1.5f) * Mathf.Min(b, 1.4f)));
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
    const float Gap = 10, LabelW = 46, LabelGap = 6;
    readonly Label label;
    LampMark[] marks = System.Array.Empty<LampMark>();

    public LampMarks()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        label = Style.Label("LAMPS", Style.Text, 13, Style.InkDim, false, HorizontalAlignment.Right);
        label.MouseFilter = MouseFilterEnum.Ignore;
        AddChild(label);
        Visible = false;
    }

    /// <summary>Shows `count` marks (hidden at 0) with `lit` burning; right edge at `rightX`, centered on `midY` in the parent.</summary>
    public void Feed(int count, int lit, float rightX, float midY)
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
            label.Position = new Vector2(0, (LampMark.H - 18) / 2);
            label.Size = new Vector2(LabelW, 18);
        }
        for (int i = 0; i < marks.Length; i++) marks[i].Burning = i < lit;
        Position = new Vector2(rightX - Size.X, midY - LampMark.H / 2);
    }
}
