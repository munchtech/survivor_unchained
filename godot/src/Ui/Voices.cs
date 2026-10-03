using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// Words over heads (the web game's hud/barks): names over the people who
/// live here, with a mark when someone has something for you, and things
/// said to the air that rise a little and fade. Drawn in the world at a
/// fixed size on screen, over everything.
/// </summary>
public partial class Voices : Node3D
{
    static Font? display, ui;
    readonly Dictionary<string, (Label3D Name, Label3D Mark)> plates = new();
    readonly List<(Label3D Label, double T, double Life)> barks = new();
    /// <summary>A conversation is on: the names and words step back.</summary>
    public bool Quiet;

    public Voices() { Name = "Voices"; }

    static Label3D Label(Font font, int size, Color color)
    {
        var l = new Label3D
        {
            Font = font, FontSize = size, Modulate = color, OutlineSize = 10, OutlineModulate = new Color(0.02f, 0.015f, 0.01f, 0.9f),
            Billboard = BaseMaterial3D.BillboardModeEnum.Enabled, NoDepthTest = true, FixedSize = true, PixelSize = 0.0011f,
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
    public void Plates(List<Plate> list)
    {
        var keep = new HashSet<string>();
        foreach (var p in list)
        {
            keep.Add(p.Id);
            if (!plates.TryGetValue(p.Id, out var pl))
            {
                pl = (Label(display!, 30, new Color("#e8dcc4")), Label(display!, 44, new Color("#f3d9a0")));
                AddChild(pl.Name);
                AddChild(pl.Mark);
                plates[p.Id] = pl;
            }
            pl.Name.Text = p.Role != null ? $"{p.Name}\n{p.Role}" : p.Name;
            pl.Name.Position = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
            pl.Mark.Text = p.Marker?.ToString() ?? "";
            pl.Mark.Visible = p.Marker != null;
            pl.Mark.Position = pl.Name.Position + Vector3.Up * 0.45f;
        }
        var gone = new List<string>();
        foreach (var id in plates.Keys) if (!keep.Contains(id)) gone.Add(id);
        foreach (var id in gone) { plates[id].Name.QueueFree(); plates[id].Mark.QueueFree(); plates.Remove(id); }
    }

    /// <summary>Something said to the air, over someone's head.</summary>
    public void Bark(string text, Vector3 at, string? speaker = null, bool alert = false, string? voice = null)
    {
        var l = Label(ui!, alert ? 34 : 30, alert ? new Color("#ffd07a") : new Color("#f0e6d2"));
        l.Text = speaker != null ? $"{speaker}: {text}" : text;
        l.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        l.Width = 520;
        l.Position = at + Vector3.Up * 2.1f;
        AddChild(l);
        double life = Mathf.Clamp(2.2 + text.Length * 0.05, 2.5, 6);
        // Heard, too, from where they stand (a named voice in a fight is the
        // game's to play, over everything; a caption is never spoken).
        if (!alert && speaker == null && Sound.VoiceOver.Instance?.Bark(text, this, at, voice) is double said and > 0)
            life = Mathf.Max(life, said + 0.8);
        barks.Add((l, 0, life));
        // Not too many at once: the oldest go first.
        while (barks.Count > 5) { barks[0].Label.QueueFree(); barks.RemoveAt(0); }
    }

    public void Clear()
    {
        foreach (var (l, _, _) in barks) l.QueueFree();
        barks.Clear();
        Plates(new());
    }

    public override void _Process(double delta)
    {
        float quiet = Quiet ? 0 : 1;
        foreach (var (n, m) in plates.Values) { n.Transparency = 1 - quiet; m.Transparency = 1 - quiet; }
        for (int i = barks.Count - 1; i >= 0; i--)
        {
            var (l, t, life) = barks[i];
            t += delta;
            if (t >= life) { l.QueueFree(); barks.RemoveAt(i); continue; }
            l.Position += Vector3.Up * (float)delta * 0.12f;
            float a = (float)Mathf.Min(1, Mathf.Min(t / 0.2, (life - t) / 0.6)) * quiet;
            l.Transparency = 1 - a;
            barks[i] = (l, t, life);
        }
    }
}
