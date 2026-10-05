using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using Style = SurvivorUnchained.Ui.Style;

namespace SurvivorUnchained.View;

/// <summary>
/// Words over heads (the web game's hud/barks): names over the people who
/// live here, with a mark when someone has something for you, drawn in the
/// world at a fixed size on screen; and things said to the air, over the
/// speaker's head, that rise a little and fade. Those are drawn on the screen
/// (under the HUD) so that they never cross: one speaker says one line at a
/// time, the next waiting its turn; lines from different speakers stack, the
/// newer moved up clear of the older.
/// </summary>
public partial class Voices : Node3D
{
    static Font? display, ui;
    readonly Dictionary<string, (Label3D Name, Label3D Mark)> plates = new();

    /// <summary>A line on screen: who says it (its queue), where in the world, how long it lives.</summary>
    sealed class Said
    {
        public required Control Box;
        public required string Key;
        public required Vector3 At;
        public required string Text;
        public double T, Life;
        /// <summary>How far it is moved up to stand clear of the lines before it (eased).</summary>
        public float Lift;
    }

    /// <summary>A line waiting for its speaker's last to finish.</summary>
    sealed record Waiting(string Text, Vector3 At, string? Speaker, bool Alert, string? Voice, Func<double>? Shown);

    readonly List<Said> barks = new();
    readonly Dictionary<string, Queue<Waiting>> waiting = new();
    CanvasLayer? layer;
    /// <summary>A conversation is on: the names and words step back.</summary>
    public bool Quiet;

    public Voices() { Name = "Voices"; }

    static Label3D Label(Font font, int size, Color color)
    {
        var l = new Label3D
        {
            Font = font, FontSize = size, Modulate = color, OutlineSize = 8, OutlineModulate = new Color(0.02f, 0.015f, 0.01f, 0.9f),
            Billboard = BaseMaterial3D.BillboardModeEnum.Enabled, NoDepthTest = true, FixedSize = true, PixelSize = 0.0007f,
            Shaded = false, RenderPriority = 20, OutlineRenderPriority = 19, DoubleSided = true,
        };
        return l;
    }

    public override void _Ready()
    {
        display ??= GD.Load<Font>("res://art/fonts/cinzel-600.woff2");
        ui ??= GD.Load<Font>("res://art/fonts/alegreya-sans-500.woff2");
    }

    /// <summary>The names to show now (near the survivor): the rest go.</summary>
    // What each plate says now, so its words are made and set only when they
    // change (every frame for everyone was a frame's worth of garbage), and
    // the sets kept from frame to frame.
    readonly Dictionary<string, (string Name, string? Role, char? Marker)> said = new();
    readonly HashSet<string> keep = new();
    readonly List<string> gone = new();

    public void Plates(List<Plate> list)
    {
        keep.Clear();
        foreach (var p in list)
        {
            keep.Add(p.Id);
            if (!plates.TryGetValue(p.Id, out var pl))
            {
                pl = (Label(display!, 22, new Color("#e8dcc4")), Label(display!, 34, new Color("#f3d9a0")));
                AddChild(pl.Name);
                AddChild(pl.Mark);
                plates[p.Id] = pl;
                said.Remove(p.Id);
            }
            if (!said.TryGetValue(p.Id, out var was) || was.Name != p.Name || was.Role != p.Role || was.Marker != p.Marker)
            {
                said[p.Id] = (p.Name, p.Role, p.Marker);
                pl.Name.Text = p.Role != null ? $"{p.Name}\n{p.Role}" : p.Name;
                pl.Mark.Text = p.Marker?.ToString() ?? "";
                pl.Mark.Visible = p.Marker != null;
            }
            var at = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
            if (pl.Name.Position != at)
            {
                pl.Name.Position = at;
                pl.Mark.Position = at + Vector3.Up * 0.45f;
            }
        }
        gone.Clear();
        foreach (var id in plates.Keys) if (!keep.Contains(id)) gone.Add(id);
        foreach (var id in gone) { plates[id].Name.QueueFree(); plates[id].Mark.QueueFree(); plates.Remove(id); said.Remove(id); }
    }

    /// <summary>Something said to the air, over someone's head. Their line before
    /// still showing, it waits its turn (the same words again only keep that
    /// one up longer); `shown` runs when it shows (a named voice heard then,
    /// returning how long it speaks).</summary>
    public void Bark(string text, Vector3 at, string? speaker = null, bool alert = false, string? voice = null, Func<double>? shown = null)
    {
        // Whose turn it is: a named speaker's own; else whatever stands there.
        string key = speaker ?? $"@{Mathf.RoundToInt(at.X / 3)},{Mathf.RoundToInt(at.Z / 3)}";
        if (barks.FirstOrDefault(b => b.Key == key) is { } now)
        {
            if (now.Text == text) { now.Life = Math.Max(now.Life, now.T + 1.6); return; }
            // The line showing stays only until it has been read (a scene's lines keep near their beats);
            // an alert is only ever about now, so the newer takes its place at once.
            now.Life = Math.Max(now.T + 0.25, Math.Min(now.Life, alert ? 0 : 1.0 + now.Text.Length * 0.045));
            if (!waiting.TryGetValue(key, out var q)) waiting[key] = q = new();
            if (q.Any(w => w.Text == text)) return;
            q.Enqueue(new Waiting(text, at, speaker, alert, voice, shown));
            // (a speaker who says too much drops what is oldest unsaid, not what is newest)
            while (q.Count > 3) q.Dequeue();
            return;
        }
        Show(key, new Waiting(text, at, speaker, alert, voice, shown));
    }

    void Show(string key, Waiting w)
    {
        if (layer == null) { layer = new CanvasLayer { Layer = 5 }; AddChild(layer); }
        var box = Style.V(0);
        box.MouseFilter = Control.MouseFilterEnum.Ignore;
        // A named speaker's name over their words, small and gold; the words in the hand.
        if (w.Speaker != null)
            box.AddChild(Style.Label(w.Speaker.ToUpperInvariant(), Style.UiHeavy, 15, new Color("#e0b868"), false, HorizontalAlignment.Center));
        var words = Style.Label(w.Text, Style.Ui, w.Alert ? 26 : 23, w.Alert ? new Color("#ffd07a") : new Color("#f0e6d2"), true, HorizontalAlignment.Center);
        words.AddThemeConstantOverride("outline_size", 7);
        words.AddThemeColorOverride("font_outline_color", new Color(0.02f, 0.015f, 0.01f, 0.92f));
        words.CustomMinimumSize = new Vector2(Math.Min(460, Style.Ui.GetStringSize(w.Text, HorizontalAlignment.Left, -1, w.Alert ? 26 : 23).X + 8), 0);
        box.AddChild(words);
        box.Modulate = new Color(1, 1, 1, 0);
        layer.AddChild(box);
        double life = Mathf.Clamp(2.2 + w.Text.Length * 0.05, 2.5, 6);
        // Heard, too, from where they stand (a named voice in a fight is the
        // game's to play, over everything; a caption is never spoken).
        if (!w.Alert && w.Speaker == null && Sound.VoiceOver.Instance?.Bark(w.Text, this, w.At, w.Voice) is double said and > 0)
            life = Mathf.Max(life, said + 0.8);
        if (w.Shown?.Invoke() is double spoken and > 0) life = Mathf.Max(life, spoken + 0.6);
        barks.Add(new Said { Box = box, Key = key, At = w.At, Text = w.Text, Life = life });
        // Not too many at once: the oldest go first.
        while (barks.Count > 6) { barks[0].Box.QueueFree(); barks.RemoveAt(0); }
    }

    public void Clear()
    {
        foreach (var b in barks) b.Box.QueueFree();
        barks.Clear();
        waiting.Clear();
        Plates(new());
    }

    public override void _Process(double delta)
    {
        float quiet = Quiet ? 0 : 1;
        foreach (var (n, m) in plates.Values) { n.Transparency = 1 - quiet; m.Transparency = 1 - quiet; }
        for (int i = barks.Count - 1; i >= 0; i--)
        {
            var b = barks[i];
            b.T += delta;
            if (b.T < b.Life) continue;
            b.Box.QueueFree();
            barks.RemoveAt(i);
            // That speaker's next line, now theirs is done.
            if (waiting.TryGetValue(b.Key, out var q) && q.Count > 0) Show(b.Key, q.Dequeue());
        }
        Place(delta, quiet);
    }

    /// <summary>Each line over its speaker's head, as the camera sees them now, the
    /// older first; a newer one that would cross an older is lifted clear of it.</summary>
    void Place(double delta, float quiet)
    {
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null) return;
        var placed = new List<Rect2>();
        float ease = 1 - Mathf.Exp(-10f * (float)delta);
        foreach (var b in barks)
        {
            var head = b.At + Vector3.Up * 2.1f;
            if (cam.IsPositionBehind(head)) { b.Box.Visible = false; continue; }
            b.Box.Visible = true;
            var size = b.Box.GetCombinedMinimumSize();
            // (rising a little as it is said)
            var at = cam.UnprojectPosition(head) - new Vector2(size.X / 2, size.Y + (float)Math.Min(b.T, 3) * 6);
            // A speaker at the top of the screen says it under their feet, not under the HUD's bars.
            if (at.Y < Ui.GameHud.TopClear) at.Y = Math.Max(Ui.GameHud.TopClear, cam.UnprojectPosition(b.At).Y + 14);
            at.X = Mathf.Clamp(at.X, 16, 1904 - size.X);
            // Never inside the banner's words, nor beside them on their line (read across, a howl's
            // caption and the banner's title made one sentence): under them (over them is the boss's bar).
            if (Ui.GameHud.Banner is Rect2 band && band.GrowIndividual(140, 6, 140, 6).Intersects(new Rect2(at, size))) at.Y = band.End.Y + 10;
            float want = 0;
            for (int pass = 0; pass < 8; pass++)
            {
                var r = new Rect2(at - new Vector2(0, want), size).Grow(4);
                var hit = placed.FirstOrDefault(p => p.Intersects(r));
                if (hit.Size == Vector2.Zero) break;
                want = at.Y + size.Y + 4 - hit.Position.Y;
            }
            b.Lift = b.T < 0.05 ? want : Mathf.Lerp(b.Lift, want, ease);
            b.Box.Position = at - new Vector2(0, b.Lift);
            b.Box.Size = size;
            placed.Add(new Rect2(at - new Vector2(0, want), size));
            float a = (float)Mathf.Min(1, Mathf.Min(b.T / 0.2, (b.Life - b.T) / 0.6)) * quiet;
            b.Box.Modulate = new Color(1, 1, 1, a);
        }
    }
}
