using System;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The day's book's tabs riding a chain (the owner: "maybe we slide along the chain as we slide
/// tabs in that part of the ui, that could be really cool, especially with a sound - an organic
/// chain not just the same image either"). A run of links lies under the names, face-on and
/// edge-on in turn; under the open tab one link is pried open, ember in the break. Turning a tab
/// slides the whole chain until that link settles under the new one, with a little overshoot, the
/// links swinging as they go and stilling after, and a rattle (Sfx.Chain).
///
/// Each link is itself: its size, its tone, its tilt and (once UI art paints them) its picture
/// come from which link it is, not where it is, so the chain moves as one thing and never reads as
/// one image repeated. Art: art/ui/chain/face_0..3.png, edge_0..3.png and open.png, drawn at their
/// own size; until they land the links are drawn.
/// </summary>
public partial class ChainTabs : Control
{
    /// <summary>Between links, centre to centre.</summary>
    const float Gap = 13;
    readonly int on;
    readonly HBoxContainer row;
    // Each tab is a screen of its own: the chain's place is kept across them, so the slide starts
    // where the last screen left it.
    static float lastX = float.NaN;
    static ulong lastAt;
    float x, v, chainY;
    double t = 10;
    bool placed;

    public ChainTabs((string Name, string Key)[] tabs, int on, Action<int> pick)
    {
        this.on = on;
        MouseFilter = MouseFilterEnum.Ignore;
        bool pad = Controls.Instance?.UsingPad == true;
        row = Style.H(26);
        if (pad) row.AddChild(Style.PadButton("LB"));
        for (int i = 0; i < tabs.Length; i++)
        {
            int k = i;
            var b = new Button { FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand, Flat = true };
            foreach (var s in new[] { "normal", "hover", "pressed", "focus" })
                b.AddThemeStyleboxOverride(s, new StyleBoxEmpty { ContentMarginLeft = 0, ContentMarginRight = 0 });
            var inner = Style.H(8, Style.Label(tabs[i].Name, Style.UiBold, 16, i == on ? Kit.Ink : Kit.Dim, false, HorizontalAlignment.Left, false));
            if (!pad) inner.AddChild(Style.Key(tabs[i].Key));
            inner.MouseFilter = MouseFilterEnum.Ignore;
            b.AddChild(inner);
            b.CustomMinimumSize = inner.GetCombinedMinimumSize();
            b.MouseEntered += () => { if (k != on) inner.Modulate = new Color(1.25f, 1.2f, 1.1f); };
            b.MouseExited += () => inner.Modulate = Colors.White;
            b.Pressed += () => { if (k != on) pick(k); };
            // The tabs are turned with LB and RB (or [ and ]), not walked to.
            Nav.Skip(b);
            row.AddChild(b);
        }
        if (pad) row.AddChild(Style.PadButton("RB"));
        AddChild(row);
        var min = row.GetCombinedMinimumSize();
        chainY = min.Y + 11;
        CustomMinimumSize = new Vector2(min.X, chainY + 9);
    }

    /// <summary>The open tab's middle, in this control's own pixels.</summary>
    float Target()
    {
        int i = 0;
        foreach (var c in row.GetChildren())
        {
            if (c is not Button b) continue;
            if (i++ == on) return b.Position.X + b.Size.X / 2;
        }
        return 0;
    }

    public override void _Process(double delta)
    {
        float goal = Target();
        if (!placed)
        {
            if (row.Size.X <= 0) return;
            placed = true;
            bool fresh = !float.IsNaN(lastX) && Time.GetTicksMsec() - lastAt < 1500;
            x = fresh ? lastX : goal;
            if (fresh && Math.Abs(goal - x) > 2)
            {
                t = 0;
                Sound.Sfx.Chain(Math.Sign(goal - x), Math.Abs(goal - x) / 600f);
            }
        }
        // A spring a little under its damping: it runs, overshoots by a link or so, and settles.
        float dt = (float)Math.Min(delta, 1 / 30.0);
        const float k = 210, c = 18.5f;
        v += ((goal - x) * k - v * c) * dt;
        x += v * dt;
        if (Math.Abs(goal - x) < 0.05f && Math.Abs(v) < 0.5f) { x = goal; v = 0; }
        t += delta;
        lastX = x;
        lastAt = Time.GetTicksMsec();
        QueueRedraw();
    }

    static float Hash(int k, int salt)
    {
        uint h = (uint)(k * 374761393 + salt * 668265263);
        h = (h ^ (h >> 13)) * 1274126177;
        return ((h ^ (h >> 16)) & 0xffff) / 65535f;
    }

    public override void _Draw()
    {
        float x0 = -16, x1 = Size.X + 16;
        // The links swing while the chain runs, and still after.
        float sway = Mathf.Clamp(Math.Abs(v) / 900f, 0, 1) + (float)Math.Max(0, 0.6 - t) * 0.5f;
        int kFirst = (int)Math.Floor((x0 - x) / Gap), kLast = (int)Math.Ceiling((x1 - x) / Gap);
        for (int k = kFirst; k <= kLast; k++)
        {
            float lx = x + k * Gap;
            if (lx < x0 || lx > x1) continue;
            // (fading into the panel at both ends, so the chain has no cut end)
            float fade = Mathf.Clamp(Math.Min(lx - x0, x1 - lx) / 46f, 0, 1);
            float tone = 0.78f + 0.3f * Hash(k, 1), tilt = (Hash(k, 2) - 0.5f) * 0.12f + sway * 0.25f * Mathf.Sin((float)t * 17 + k * 1.7f);
            float dy = (Hash(k, 3) - 0.5f) * 1.2f + sway * 1.6f * Mathf.Sin((float)t * 13 + k * 2.3f);
            var at = new Vector2(lx, chainY + dy);
            var iron = new Color(0.56f * tone, 0.52f * tone, 0.47f * tone, 0.95f * fade);
            DrawSetTransform(at, tilt);
            if (k == 0)
            {
                // The opened link: its ring sprung, the ember glowing in the gap.
                if (UiArt.Art("chain/open.png") is { } open) DrawTexture(open, -open.GetSize() / 2);
                else
                {
                    DrawCircle(new Vector2(6, 0), 7, new Color(1, 0.5f, 0.15f, 0.18f));
                    DrawArc(Vector2.Zero, 8.5f, 0.75f, Mathf.Tau - 0.75f, 18, new Color("#c9a46c"), 2.2f, true);
                    DrawCircle(new Vector2(6.5f, 0), 2.6f, Style.Ember);
                    DrawCircle(new Vector2(6.5f, 0), 1.2f, Style.EmberHi);
                }
            }
            else if ((k & 1) == 0)
            {
                int pick = (int)(Hash(k, 4) * 4) % 4;
                if (UiArt.Art($"chain/face_{pick}.png") is { } face) DrawTexture(face, -face.GetSize() / 2, Colors.White with { A = fade });
                else
                {
                    float rx = 7.4f + Hash(k, 5) * 1.2f, ry = 4.4f + Hash(k, 6) * 0.8f;
                    var pts = new Vector2[17];
                    for (int i = 0; i <= 16; i++) pts[i] = new Vector2(Mathf.Cos(i * Mathf.Tau / 16) * rx, Mathf.Sin(i * Mathf.Tau / 16) * ry);
                    DrawPolyline(pts, iron, 2.1f, true);
                    // the light catching its upper edge
                    DrawArc(new Vector2(0, -0.6f), rx - 1.2f, Mathf.Pi * 1.15f, Mathf.Pi * 1.85f, 8, new Color(1, 0.93f, 0.8f, 0.28f * fade), 1, true);
                }
            }
            else
            {
                int pick = (int)(Hash(k, 4) * 4) % 4;
                if (UiArt.Art($"chain/edge_{pick}.png") is { } edge) DrawTexture(edge, -edge.GetSize() / 2, Colors.White with { A = fade });
                else
                {
                    float hw = 6.5f + Hash(k, 5);
                    DrawLine(new Vector2(-hw, 0), new Vector2(hw, 0), iron.Darkened(0.12f), 3.2f, true);
                    DrawLine(new Vector2(-hw + 1, -1), new Vector2(hw - 1, -1), new Color(1, 0.93f, 0.8f, 0.22f * fade), 1, true);
                }
            }
        }
        DrawSetTransform(Vector2.Zero);
    }
}
