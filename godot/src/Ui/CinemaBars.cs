using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The frame of a cinematic: black bars that make the picture 2.39:1, the
/// subtitle in the lower bar (the speaker's name for people, none and in
/// italics for the narrator; two lines at most), the black of a shot that
/// is only sound, and the ring that fills while skip is held. Styling is the
/// UI's to make its own (docs/team/cinematics.md, notes for UI); the
/// geometry is the cinematics' (docs/cinematics/README.md section 4).
/// </summary>
public partial class CinemaBars : CanvasLayer
{
    const float Aspect = 2.39f;
    readonly ColorRect top = new() { Color = Colors.Black, MouseFilter = Control.MouseFilterEnum.Ignore };
    readonly ColorRect bottom = new() { Color = Colors.Black, MouseFilter = Control.MouseFilterEnum.Ignore };
    readonly ColorRect black = new() { Color = Colors.Black, MouseFilter = Control.MouseFilterEnum.Ignore };
    readonly Label who, words;
    readonly SkipRing ring = new();
    double sayT, sayFull;
    float barsK;

    public CinemaBars()
    {
        Layer = 20;
        Name = "CinemaBars";
        AddChild(black);
        AddChild(top);
        AddChild(bottom);
        who = Style.Label("", Style.UiBold, 18, new Color("#c8b48a"), false, HorizontalAlignment.Center);
        words = Style.Label("", Style.Text, 30, new Color("#ece4d4"), true, HorizontalAlignment.Center);
        words.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        AddChild(who);
        AddChild(words);
        AddChild(ring);
        Layout(0);
    }

    /// <summary>How far in the bars are (0..1); a fully black picture (0..1).</summary>
    public void Frame(float bars, float blackK)
    {
        barsK = bars;
        Layout(bars);
        black.Color = new Color(0, 0, 0, Mathf.Clamp(blackK, 0, 1));
    }

    void Layout(float k)
    {
        var size = GetViewport()?.GetVisibleRect().Size ?? new Vector2(1920, 1080);
        float full = Mathf.Max(0, (size.Y - size.X / Aspect) / 2);
        // Eased so the bars glide in and settle.
        float e = k * k * (3 - 2 * k);
        float h = full * e;
        top.Position = Vector2.Zero; top.Size = new Vector2(size.X, h);
        bottom.Position = new Vector2(0, size.Y - h); bottom.Size = new Vector2(size.X, h);
        black.Position = Vector2.Zero; black.Size = size;
        // The words sit in the lower bar, centred in it when it is full.
        float wide = Mathf.Min(1100, size.X - 120);
        float barTop = size.Y - full;
        words.Size = new Vector2(wide, 0);
        words.Position = new Vector2((size.X - wide) / 2, barTop + Mathf.Max(12, (full - words.Size.Y) / 2) + (who.Visible ? 8 : 0));
        who.Size = new Vector2(wide, 0);
        who.Position = new Vector2((size.X - wide) / 2, words.Position.Y - 24);
        ring.Position = new Vector2(size.X - 96, size.Y - Mathf.Max(full, 90) / 2 - 22);
    }

    /// <summary>A line under the picture for this long: the narrator's in italics, unnamed.</summary>
    public void Say(string text, string? speaker, double seconds)
    {
        // The script's '/' marks where a long line breaks.
        words.Text = text.Replace(" / ", "\n").Replace("/", "\n");
        words.AddThemeFontOverride("font", speaker == null ? Style.TextItalic : Style.Text);
        who.Text = speaker?.ToUpperInvariant() ?? "";
        who.Visible = speaker != null;
        sayT = sayFull = seconds;
        words.Modulate = who.Modulate = Colors.White;
    }

    public void Hush() { sayT = 0; words.Text = ""; who.Text = ""; }

    /// <summary>The skip ring: how far the hold has got (0 hides it).</summary>
    public void Skip(float k) { ring.K = k; ring.QueueRedraw(); }

    public override void _Process(double delta)
    {
        if (sayT > 0)
        {
            sayT -= delta;
            // Out over the last quarter second.
            float a = (float)Mathf.Clamp(sayT / 0.25, 0, 1);
            words.Modulate = who.Modulate = new Color(1, 1, 1, a);
            if (sayT <= 0) Hush();
        }
        Layout(barsK);
    }

    sealed partial class SkipRing : Control
    {
        public float K;
        public SkipRing() { MouseFilter = MouseFilterEnum.Ignore; Size = new Vector2(44, 44); }

        public override void _Draw()
        {
            if (K <= 0) return;
            var c = new Vector2(22, 22);
            DrawArc(c, 16, 0, Mathf.Tau, 48, new Color(1, 1, 1, 0.18f), 3, true);
            DrawArc(c, 16, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * Mathf.Clamp(K, 0, 1), 48, new Color("#e8c890"), 3, true);
            DrawString(Style.UiBold, new Vector2(-84, 28), "SKIP", HorizontalAlignment.Right, 76, 15, new Color(1, 1, 1, 0.55f));
        }
    }
}
